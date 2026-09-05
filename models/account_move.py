from odoo import fields, models, api


# Layouts that use the Puremetrix custom paperformat
PUREMETRIX_PAPERFORMAT_LAYOUTS = {'puremetrix'}

# Layouts that have their own custom paperformat (not the default A4)
LAYOUT_PAPERFORMAT_MAP = {
    'puremetrix': 'havano_all_in_one.paperformat_puremetrix',
}


class AccountMove(models.Model):
    _inherit = "account.move"

    def _hao_ensure_purchase_invoice_date(self):
        """Use today when bill date is empty so vendor bills can post (Havano automation)."""
        today = fields.Date.context_today(self)
        for move in self.filtered(
            lambda m: m.is_purchase_document(include_receipts=True) and not m.invoice_date
        ):
            move.invoice_date = today

    def action_post(self):
        self._hao_ensure_purchase_invoice_date()
        return super().action_post()

    def _get_name_invoice_report(self):
        """
        Override to ensure the puremetrix layout (and all havano layouts)
        are routed through our inherited report template which does the
        layout switching based on company.base_layout.
        Always return 'account.report_invoice_document' so our template
        inheritance in report_invoice_templates.xml takes effect.
        """
        return 'account.report_invoice_document'

    @api.model
    def _hao_get_report_paperformat(self):
        """Return the correct ir.actions.report paperformat for this company's layout."""
        layout = self.env.company.base_layout
        ref_name = LAYOUT_PAPERFORMAT_MAP.get(layout)
        if ref_name:
            pf = self.env.ref(ref_name, raise_if_not_found=False)
            if pf:
                return pf
        return False
