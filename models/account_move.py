from odoo import fields, models


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
