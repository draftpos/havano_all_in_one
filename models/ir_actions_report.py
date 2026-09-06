from odoo import models

# Map of layout → layout-specific paperformat external IDs
REPORT_PAPERFORMAT_MAP = {
    'puremetrix': 'havano_all_in_one.paperformat_puremetrix',
}

# Reports that should have their paperformat switched
INVOICE_REPORT_NAMES = {
    'account.report_invoice_with_payments',
    'account.report_invoice',
    'account.report_original_vendor_bill',
}
SALE_REPORT_NAMES = {
    'sale.report_saleorder',
    'sale.report_saleorder_raw',
    'sale.report_saleorder_pro_forma',
}


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def get_paperformat(self):
        """
        Dynamically return the layout's custom paperformat (e.g. Puremetrix Zero Margin A4)
        when printing invoices or quotations for a company using that layout.
        This ensures wkhtmltopdf uses 6mm top margin instead of standard Odoo's 52mm margin.
        """
        report_name = self.report_name
        if report_name in (INVOICE_REPORT_NAMES | SALE_REPORT_NAMES):
            company = self.env.company
            layout = getattr(company, 'base_layout', False)
            pf_ref = REPORT_PAPERFORMAT_MAP.get(layout)
            if pf_ref:
                pf = self.env.ref(pf_ref, raise_if_not_found=False)
                if pf:
                    return pf
        return super().get_paperformat()

    def _run_wkhtmltopdf(
        self,
        bodies,
        report_ref=False,
        header=None,
        footer=None,
        landscape=False,
        specific_paperformat_args=None,
        set_viewport_size=False,
    ):
        """
        Inject specific paperformat arguments as a second layer of defense.
        Odoo's _build_wkhtmltopdf_args prioritizes specific_paperformat_args over
        the paperformat record itself, ensuring margin-top is 6mm and header-spacing is 0
        across all Linux and Windows wkhtmltopdf binaries.
        """
        report = self._get_report(report_ref) if report_ref else self
        if report and report.report_name in (INVOICE_REPORT_NAMES | SALE_REPORT_NAMES):
            company = self.env.company
            if getattr(company, 'base_layout', False) == 'puremetrix':
                if specific_paperformat_args is None:
                    specific_paperformat_args = {}
                specific_paperformat_args.setdefault('data-report-margin-top', 6.0)
                specific_paperformat_args.setdefault('data-report-header-spacing', 0)
                specific_paperformat_args.setdefault('data-report-margin-bottom', 12.0)
                specific_paperformat_args.setdefault('data-report-margin-left', 6.0)
                specific_paperformat_args.setdefault('data-report-margin-right', 6.0)

        return super()._run_wkhtmltopdf(
            bodies,
            report_ref=report_ref,
            header=header,
            footer=footer,
            landscape=landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size,
        )
