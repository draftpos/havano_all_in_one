/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { onMounted, onWillStart } from "@odoo/owl";

patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.notification = useService("notification");
        this._haoPdfBtnAdded = false;
        this._haoOpenPdfBound = this._haoOpenPdf.bind(this);

        onWillStart(async () => {
            setTimeout(() => this._haoAddPdfButton(), 300);
        });
        onMounted(() => {
            setTimeout(() => this._haoAddPdfButton(), 300);
        });
    },

    getStaticActionMenuItems() {
        const items = super.getStaticActionMenuItems(...arguments);
        if (this.model?.root?.resModel) {
            items.previewPdf = {
                isAvailable: () => true,
                sequence: 15,
                icon: "fa fa-file-pdf-o",
                description: _t("Preview as PDF"),
                callback: () => this._haoOpenPdf(),
            };
        }
        return items;
    },

    _haoAddPdfButton() {
        if (this._haoPdfBtnAdded) {
            return;
        }
        const el = this.el || document;
        const main = el.querySelector(".o_control_panel_main");
        const addBtn = main?.querySelector(".o_list_button_add");
        if (!addBtn || el.querySelector(".o_preview_pdf_btn")) {
            if (addBtn) {
                this._haoPdfBtnAdded = true;
            }
            return;
        }

        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn btn-secondary o_preview_pdf_btn";
        btn.innerHTML = '<i class="fa fa-file-pdf-o me-1"></i>Preview PDF';
        btn.style.marginLeft = "4px";
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            this._haoOpenPdfBound();
        });
        addBtn.after(btn);
        this._haoPdfBtnAdded = true;
    },

    _haoOpenPdf() {
        if (!this.model?.root) {
            this.notification.add(_t("List view is not ready yet. Try again."), { type: "warning" });
            return;
        }

        const model = this.model.root.resModel;
        let columns = this._haoGetColumns();
        if (!columns.length) {
            columns = [{ name: "display_name", label: _t("Name") }];
        }

        const limit = this.model.root.limit || 80;
        const offset = this.model.root.offset || 0;
        const total = this.model.root.count || 0;
        const domain = JSON.stringify(this.model.root.domain || []);

        const params = new URLSearchParams({
            domain,
            fields: JSON.stringify(columns.map((c) => c.name)),
            labels: JSON.stringify(columns.map((c) => c.label)),
            limit: String(limit),
            offset: String(offset),
            total: String(total),
        });

        const pdfUrl = `/havano/preview/pdf/${encodeURIComponent(model)}?${params.toString()}`;
        
        const win = window.open(pdfUrl, "_blank");
        if (!win) {
            this.notification.add(_t("Allow pop-ups to open the PDF preview."), { type: "warning" });
        }
    },

    _haoGetColumns() {
        const skipPatterns = [
            "avatar", "image", "icon", "logo", "picture", "photo",
            "thumb", "signature", "barcode", "qr_code",
        ];
        const isImageOrBinaryField = (name) => {
            if (!name) {
                return false;
            }
            const lower = name.toLowerCase();
            return skipPatterns.some((pattern) => lower.includes(pattern));
        };

        const mapColumn = (c) => ({
            name: c.name,
            label: c.string || c.name.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
        });

        if (this.renderer?.columns) {
            const columns = this.renderer.columns
                .filter(
                    (c) =>
                        c.type === "field" &&
                        c.name &&
                        !c.invisible &&
                        !isImageOrBinaryField(c.name) &&
                        c.name !== "selector" &&
                        c.name !== "checkbox"
                )
                .map(mapColumn);
            if (columns.length) {
                return columns;
            }
        }

        if (this.model?.root?.columns) {
            const columns = this.model.root.columns
                .filter(
                    (c) =>
                        c.type === "field" &&
                        c.name &&
                        !c.invisible &&
                        !isImageOrBinaryField(c.name) &&
                        c.name !== "selector" &&
                        c.name !== "checkbox"
                )
                .map(mapColumn);
            if (columns.length) {
                return columns;
            }
        }

        const table = (this.el || document).querySelector(".o_list_table");
        if (table) {
            const columns = [];
            table.querySelectorAll("thead th").forEach((th) => {
                if (th.classList.contains("o_list_record_selector")) {
                    return;
                }
                const fieldName = th.getAttribute("data-name") || th.dataset?.name;
                if (!fieldName || isImageOrBinaryField(fieldName)) {
                    return;
                }
                const label = th.textContent.replace(/[\n\r\t]/g, " ").replace(/\s+/g, " ").trim();
                if (label) {
                    columns.push({ name: fieldName, label });
                }
            });
            if (columns.length) {
                return columns;
            }
        }

        return [];
    },
});
