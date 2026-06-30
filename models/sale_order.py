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

    hao_custom_status = fields.Selection([
        ('quote', 'Quote'),
        ('sales_invoice', 'Sales Invoice')
    ], string='Status', copy=False, readonly=True)

    hao_delivery_location_id = fields.Many2one(
        'stock.location', string='Delivery Location',
        domain=[('usage', '=', 'internal')]
    )
    hao_paid_amount = fields.Monetary(string="Paid Amount", compute="_compute_hao_paid_amount")

    def _compute_hao_paid_amount(self):
        for order in self:
            amount = 0.0
            for invoice in order.invoice_ids.filtered(lambda inv: inv.state == 'posted' and inv.move_type == 'out_invoice'):
                amount += invoice.amount_total - invoice.amount_residual
            order.hao_paid_amount = amount

    def action_hao_quote(self):
        for order in self:
            if not order.hao_custom_status and order.state in ('draft', 'sent'):
                order.hao_custom_status = 'quote'

    def action_hao_convert_to_invoice(self):
        for order in self:
            if order.hao_custom_status == 'quote':
                order.action_confirm()
                
                # Update delivery location and validate picking
                pickings = getattr(order, 'picking_ids', order.env['stock.picking']).filtered(lambda p: p.state not in ('done', 'cancel'))
                for picking in pickings:
                    if order.hao_delivery_location_id:
                        picking.location_dest_id = order.hao_delivery_location_id
                        for move in picking.move_ids:
                            move.location_dest_id = order.hao_delivery_location_id
                    
                    # Auto-deliver the products
                    for move in picking.move_ids:
                        if not move.quantity:
                            move.quantity = move.product_uom_qty
                    res = picking.button_validate()
                    if isinstance(res, dict) and res.get('res_model') == 'stock.immediate.transfer':
                        wizard = order.env['stock.immediate.transfer'].with_context(res.get('context', {})).create({'pick_ids': [(4, picking.id)]})
                        wizard.process()
                
                # Auto-deliver manual lines (services, consumables)
                for line in order.order_line:
                    if line.qty_delivered_method == 'manual' and line.qty_delivered < line.product_uom_qty:
                        line.qty_delivered = line.product_uom_qty

                # Create and post invoice
                invoices = order._create_invoices()
                draft_invoices = invoices.filtered(lambda inv: inv.state == "draft")
                if draft_invoices:
                    draft_invoices.action_post()
                
                order.hao_custom_status = 'sales_invoice'

    def action_hao_pay_invoice(self):
        self.ensure_one()
        if self.invoice_ids:
            invoice = self.invoice_ids.filtered(lambda i: i.state == 'posted' and i.payment_state in ('not_paid', 'partial'))
            if invoice:
                return invoice[0].action_register_payment()

    def action_hao_credit_note(self):
        self.ensure_one()
        if self.invoice_ids:
            invoice = self.invoice_ids.filtered(lambda i: i.state == 'posted')
            if invoice:
                action = self.env['ir.actions.act_window']._for_xml_id('account.action_view_account_move_reversal')
                action['context'] = {'active_model': 'account.move', 'active_ids': invoice.ids}
                return action

    def action_hao_reset_invoice_to_draft(self):
        self.ensure_one()
        if self.invoice_ids:
            invoice = self.invoice_ids.filtered(lambda i: i.state != 'draft')
            if invoice:
                invoice.button_draft()

    def action_hao_print_invoice(self):
        self.ensure_one()
        if self.invoice_ids:
            return self.env.ref('account.account_invoices').report_action(self.invoice_ids)

    def action_hao_print_delivery(self):
        self.ensure_one()
        pickings = getattr(self, 'picking_ids', self.env['stock.picking'])
        if pickings:
            return self.env.ref('stock.action_report_delivery').report_action(pickings)

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            user = order.user_id or self.env.user
            if not user.hao_enable_sales_automation:
                continue
            if user.hao_sales_automation_method != 'full':
                continue
            if user.hao_auto_validate_delivery and order.state in ("sale", "done"):
                pickings = getattr(order, 'picking_ids', order.env['stock.picking']).filtered(
                    lambda p: p.state not in ("done", "cancel")
                )
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
                and user.hao_sales_automation_method == 'full'
                and user.hao_auto_confirm_quotation
                and order.order_line
                and order.state in ("draft", "sent")
            ):
                order.action_confirm()
        return orders
