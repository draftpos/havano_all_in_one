from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.model
    def _hao_supplier_partner_domain(self):
        if (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("havano_all_in_one.show_only_suppliers_in_purchases", "True")
            == "True"
        ):
            return [("is_supplier", "=", True), ("is_doctor", "=", False)]
        return []

    partner_id = fields.Many2one(domain=lambda self: self._hao_supplier_partner_domain())

    def _hao_run_purchase_automation(self):
        """Auto-receive, bill, and post vendor bills when enabled for the user."""
        for order in self:
            user = order.user_id or self.env.user
            if not user.hao_enable_purchase_automation:
                continue
            if user.hao_auto_validate_receipt and order.state in ("purchase", "done"):
                pickings = order.picking_ids.filtered(
                    lambda p: p.state not in ("done", "cancel")
                )
                for picking in pickings:
                    for move in picking.move_ids:
                        if not move.quantity:
                            move.quantity = move.product_uom_qty
                    picking.button_validate()
            if user.hao_auto_create_vendor_bill and order.invoice_status in (
                "to invoice",
                "no",
            ):
                order.action_create_invoice()
                bills = order.invoice_ids.filtered(lambda inv: inv.state == "draft")
                bills.filtered(lambda inv: not inv.invoice_date).write(
                    {"invoice_date": fields.Date.context_today(order)}
                )
                if user.hao_auto_post_vendor_bill and bills:
                    bills.action_post()

    def button_approve(self, force=False):
        res = super().button_approve(force=force)
        self._hao_run_purchase_automation()
        return res

    def button_confirm(self):
        res = super().button_confirm()
        for order in self.filtered(lambda o: o.state == "purchase"):
            order._hao_run_purchase_automation()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            user = order.user_id or self.env.user
            if (
                user.hao_enable_purchase_automation
                and user.hao_auto_confirm_purchase
                and order.order_line
                and order.state in ("draft", "sent")
            ):
                order.button_confirm()
                if order.state == "to approve" and order._approval_allowed():
                    order.button_approve()
        return orders
