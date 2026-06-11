import json
from urllib.parse import unquote_plus

from odoo import http
from odoo.http import request
from odoo.tools.safe_eval import safe_eval


class PreviewListPdfController(http.Controller):
    @http.route("/havano/preview/pdf/<string:model_name>", type="http", auth="user", methods=["GET"], csrf=False)
    def preview_pdf(self, model_name, domain="[]", fields="[]", labels="[]", limit=80, offset=0, **kwargs):
        try:
            parsed_domain = safe_eval(unquote_plus(domain)) if domain and domain != "[]" else []
        except Exception:
            parsed_domain = []
        try:
            parsed_fields = json.loads(unquote_plus(fields)) if fields and fields != "[]" else []
        except Exception:
            parsed_fields = []
        try:
            parsed_labels = json.loads(unquote_plus(labels)) if labels and labels != "[]" else []
        except Exception:
            parsed_labels = []
        limit = min(int(limit or 80), 200)
        offset = int(offset or 0)
        model = request.env[model_name].sudo()

        valid_fields, valid_labels = [], []
        for i, field_name in enumerate(parsed_fields):
            if field_name in model._fields and model._fields[field_name].type not in ("binary", "image"):
                valid_fields.append(field_name)
                valid_labels.append(parsed_labels[i] if i < len(parsed_labels) else field_name.replace("_", " ").title())
        if not valid_fields:
            valid_fields, valid_labels = ["display_name"], ["Name"]

        rows_data = model.search_read(parsed_domain, fields=valid_fields, limit=limit, offset=offset)
        total_count = model.search_count(parsed_domain)
        rows = []
        for row in rows_data:
            values = []
            for field_name in valid_fields:
                value = row.get(field_name)
                field_obj = model._fields.get(field_name)
                if field_obj and field_obj.type == "many2one" and isinstance(value, (list, tuple)) and len(value) >= 2:
                    values.append(str(value[1])[:80])
                elif isinstance(value, bool):
                    values.append("Yes" if value else "No")
                elif value is None or value is False:
                    values.append("")
                else:
                    values.append(str(value).replace("\n", " ").replace("\r", "")[:80])
            rows.append(values)

        report_data = {
            "model_name": model._description or model_name,
            "company_name": request.env.company.name,
            "table_chunks": [{"headers": valid_labels, "rows": rows}],
            "page_number": (offset // limit) + 1 if limit else 1,
            "total_pages": max(1, (total_count + limit - 1) // limit) if limit else 1,
            "showing_from": offset + 1 if total_count else 0,
            "showing_to": min(offset + limit, total_count),
            "total_records": total_count,
            "rows": rows,
        }
        html, _ = request.env["ir.actions.report"].sudo()._render_qweb_html(
            "havano_all_in_one.action_report_preview_list_pdf",
            data=report_data,
        )
        # Inject a small script to allow instant printing from the browser
        print_script = """
        <script>
            window.onload = function() {
                var btn = document.createElement('button');
                btn.innerHTML = '🖨️ Print / Save as PDF';
                btn.style.cssText = 'position:fixed;top:10px;right:10px;z-index:9999;padding:10px 20px;background:#0891b2;color:white;border:none;border-radius:5px;cursor:pointer;font-weight:bold;box-shadow:0 4px 6px rgba(0,0,0,0.1);';
                btn.onclick = function() { btn.style.display = 'none'; window.print(); btn.style.display = 'block'; };
                document.body.appendChild(btn);
            };
        </script>
        """.encode("utf-8")
        html += print_script

        headers = [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(html)))]
        return request.make_response(html, headers=headers)
