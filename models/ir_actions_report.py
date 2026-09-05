from odoo import models

# Map of report_name → layout-specific paperformat external IDs
REPORT_PAPERFORMAT_MAP = {
    'puremetrix': 'havano_all_in_one.paperformat_puremetrix',
}

# Reports that should have their paperformat switched
INVOICE_REPORT_NAMES = {
    'account.report_invoice_with_payments',
    'account.report_invoice',
}
SALE_REPORT_NAMES = {
    'sale.report_saleorder_raw',
    'sale.report_saleorder_pro_forma',
}


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _get_rendering_context(self, report, docids, data):
        """
        Inject the correct paperformat into the rendering context
        so the Print button (Invoice PDF / PDF without Payment / Quotation PDF)
        automatically uses the layout's paperformat (e.g. Puremetrix Zero Margin A4).
        """
        context = super()._get_rendering_context(report, docids, data)
        report_name = report.report_name if report else self.report_name
        if report_name in INVOICE_REPORT_NAMES | SALE_REPORT_NAMES:
            layout = self.env.company.base_layout
            pf_ref = REPORT_PAPERFORMAT_MAP.get(layout)
            if pf_ref:
                pf = self.env.ref(pf_ref, raise_if_not_found=False)
                if pf:
                    context['paperformat'] = pf
        return context
