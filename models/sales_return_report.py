from odoo import models, fields, tools

class SalesReturnReport(models.Model):
    _name = 'havano.sales.return.report'
    _description = 'Sales Return Report'
    _auto = False

    name = fields.Char(string='Reference', readonly=True)
    payment_state = fields.Selection(selection=[
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy'),
    ], string='Payment Status', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)
    amount_untaxed_signed = fields.Monetary(string='Base Total', readonly=True, currency_field='currency_id')
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    m.id as id,
                    m.name,
                    m.payment_state,
                    m.partner_id,
                    m.invoice_date as date,
                    m.invoice_user_id as user_id,
                    m.amount_untaxed_signed,
                    m.state,
                    m.currency_id
                FROM
                    account_move m
                WHERE
                    m.move_type = 'out_refund'
            )
        """ % (self._table,))
