from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _hao_customer_partner_domain(self):
        if (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("havano_all_in_one.show_only_customers_in_sales", "True")
            == "True"
        ):
            return [("is_customer", "=", True), ("is_doctor", "=", False)]
        return []

    partner_id = fields.Many2one(domain=lambda self: self._hao_customer_partner_domain())

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            user = order.user_id or self.env.user
            if not user.hao_enable_sales_automation:
                continue
            if user.hao_auto_create_invoice and order.state in ("sale", "done"):
                invoices = order._create_invoices()
                if user.hao_auto_post_invoice:
                    draft_invoices = invoices.filtered(lambda inv: inv.state == "draft")
                    draft_invoices.action_post()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            user = order.user_id or order.env.user
            if (
                user.hao_enable_sales_automation
                and user.hao_auto_confirm_quotation
                and order.order_line
                and order.state in ("draft", "sent")
            ):
                order.action_confirm()
        return orders
