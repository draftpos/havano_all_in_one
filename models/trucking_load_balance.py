from odoo import models, fields, api

class TruckingLoad(models.Model):
    _inherit = 'trucking.load'

    transporter_balance_display = fields.Char(string='Transporter Balance Breakdown', compute='_compute_balance_display')
    customer_balance_display = fields.Char(string='Customer Balance Breakdown', compute='_compute_balance_display')

    bill_customer_qty = fields.Selection(selection_add=[('per_load', 'Per Load')], ondelete={'per_load': 'set default'})
    bill_transporter_qty = fields.Selection(selection_add=[('per_load', 'Per Load')], ondelete={'per_load': 'set default'})

    @api.depends('transporter_balance', 'customer_balance', 'total_demurrage', 'total_penalty', 'qty_tonnes', 'delivered_qty', 'rate_per_tonne', 'customer_rate', 'bill_transporter_qty', 'bill_customer_qty')
    def _compute_balance_display(self):
        for rec in self:
            currency = rec.currency_id.symbol or '$'
            
            # Transporter Display
            base_t = rec.total_per_load if rec.bill_transporter_qty in ('loaded', 'per_load') else (rec.delivered_qty * rec.rate_per_tonne if rec.delivered_qty else 0.0)
            t_str = f"Balance ( {currency}{base_t:,.2f} for load"
            if rec.total_demurrage:
                t_str += f" + {currency}{rec.total_demurrage:,.2f} demurrage"
            if rec.total_penalty:
                t_str += f" + {currency}{rec.total_penalty:,.2f} penalty"
            t_str += " )"
            rec.transporter_balance_display = t_str
            
            # Customer Display
            base_c = (rec.qty_tonnes * rec.customer_rate) if rec.bill_customer_qty in ('loaded', 'per_load') else (rec.delivered_qty * rec.customer_rate if rec.delivered_qty else 0.0)
            c_str = f"Balance ( {currency}{base_c:,.2f} for load"
            if rec.total_demurrage:
                c_str += f" + {currency}{rec.total_demurrage:,.2f} demurrage"
            if rec.total_penalty:
                c_str += f" + {currency}{rec.total_penalty:,.2f} penalty"
            c_str += " )"
            rec.customer_balance_display = c_str

    @api.depends('transporter_bill_id.state', 'transporter_bill_id.amount_residual', 'payment_ids.state', 'payment_ids.amount', 'fuel_amount', 'fuel_sales_invoice_id.state', 'deposit_amount', 'total_per_load', 'qty_tonnes', 'delivered_qty', 'bill_transporter_qty', 'rate_per_tonne', 'total_demurrage', 'total_penalty')
    def _compute_transporter_balance(self):
        # We call super to let the original logic run, then override the 'else' case
        super()._compute_transporter_balance()
        for rec in self:
            if not (rec.transporter_bill_id and rec.transporter_bill_id.state == 'posted'):
                variance_val = (rec.qty_tonnes - rec.delivered_qty) * rec.rate_per_tonne if rec.bill_transporter_qty == 'delivered' else 0.0
                base_total = rec.total_per_load - variance_val
                # Added demurrage and penalty to the transporter balance mathematically
                balance = base_total + rec.total_demurrage + rec.total_penalty - rec.deposit_amount - rec.fuel_amount
                rec.transporter_balance = balance

    def action_deliver(self):
        # Pre-capture draft charges to fix the bug where customer invoice marks them billed before transporter bill generation
        pre_deliver_charges = {}
        for rec in self:
            pre_deliver_charges[rec.id] = rec.charge_ids.filtered(lambda c: c.state == 'draft').ids

        res = super().action_deliver()

        for rec in self:
            # Fix per_load quantities for Customer Invoice
            if rec.bill_customer_qty == 'per_load' and rec.invoice_id:
                inv = rec.invoice_id
                was_posted = inv.state == 'posted'
                if was_posted:
                    inv.button_draft()
                for line in inv.invoice_line_ids:
                    # Only update the main freight product line
                    if line.product_id and line.product_id == rec.product_id:
                        line.quantity = rec.qty_tonnes
                if was_posted and inv.state == 'draft':
                    inv.action_post()
            
            # Fix per_load quantities for Vendor Bill and PO
            if rec.bill_transporter_qty == 'per_load':
                if rec.purchase_order_id:
                    for line in rec.purchase_order_id.order_line:
                        if line.product_id and line.product_id == rec.product_id:
                            line.product_qty = rec.qty_tonnes
                            line.qty_received = rec.qty_tonnes
                if rec.transporter_bill_id:
                    bill = rec.transporter_bill_id
                    was_posted = bill.state == 'posted'
                    if was_posted:
                        bill.button_draft()
                    for line in bill.invoice_line_ids:
                        if line.product_id and line.product_id == rec.product_id:
                            line.quantity = rec.qty_tonnes
                    if was_posted and bill.state == 'draft':
                        bill.action_post()

            if rec.transporter_type == 'external' and rec.id in pre_deliver_charges:
                missing_charges = self.env['trucking.load.charge'].browse(pre_deliver_charges[rec.id]).filtered(lambda c: not c.vendor_bill_id)
                if missing_charges and rec.transporter_bill_id:
                    bill = rec.transporter_bill_id
                    po = rec.purchase_order_id
                    company = rec.company_id
                    
                    was_posted = bill.state == 'posted'
                    if was_posted:
                        bill.button_draft()
                    
                    for charge in missing_charges:
                        product = company.trucking_demurrage_product_id if charge.charge_type == 'demurrage' else company.trucking_penalty_product_id
                        if not product:
                            continue
                            
                        # Add to PO
                        po_line = self.env['purchase.order.line'].create({
                            'order_id': po.id,
                            'product_id': product.id,
                            'name': f"{dict(charge._fields['charge_type'].selection).get(charge.charge_type)} - {charge.reason} ({rec.name})",
                            'product_qty': 1,
                            'qty_received': 1,
                            'price_unit': charge.amount,
                            'date_planned': fields.Datetime.now(),
                        })
                        
                        # Add to Bill
                        self.env['account.move.line'].create({
                            'move_id': bill.id,
                            'purchase_line_id': po_line.id,
                            'product_id': product.id,
                            'name': po_line.name,
                            'quantity': 1,
                            'price_unit': charge.amount,
                            'account_id': product.property_account_expense_id.id or product.categ_id.property_account_expense_categ_id.id,
                        })
                        
                        charge.vendor_bill_id = bill.id
                        charge.state = 'billed'
                        
                    if was_posted and bill.state == 'draft':
                        bill.action_post()
        return res
