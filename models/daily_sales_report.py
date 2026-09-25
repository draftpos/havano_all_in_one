from odoo import models, fields, tools

class DailySalesReport(models.Model):
    _name = 'havano.daily.sales.report'
    _description = 'Daily Sales Report'
    _auto = False

    date = fields.Date(string='Date', readonly=True)
    qty = fields.Float(string='Qty Sold', readonly=True)
    cost_price = fields.Monetary(string='Buy Price', readonly=True, currency_field='currency_id')
    selling_price = fields.Monetary(string='Sell Price', readonly=True, currency_field='currency_id')
    total_sales = fields.Monetary(string='Total Sales', readonly=True, currency_field='currency_id')
    profit = fields.Monetary(string='Profit', readonly=True, currency_field='currency_id')
    profit_margin = fields.Float(string='Profit Margin (%)', readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    MIN(l.id) as id,
                    m.invoice_date as date,
                    SUM(CASE WHEN m.move_type = 'out_refund' THEN -l.quantity ELSE l.quantity END) as qty,
                    
                    CASE 
                        WHEN SUM(CASE WHEN m.move_type = 'out_refund' THEN -l.quantity ELSE l.quantity END) > 0 
                        THEN SUM(CASE WHEN m.move_type = 'out_refund' THEN -l.quantity * COALESCE((p.standard_price->>m.company_id::text)::numeric, 0) ELSE l.quantity * COALESCE((p.standard_price->>m.company_id::text)::numeric, 0) END) / SUM(CASE WHEN m.move_type = 'out_refund' THEN -l.quantity ELSE l.quantity END)
                        ELSE 0 
                    END as cost_price,
                    
                    CASE 
                        WHEN SUM(CASE WHEN m.move_type = 'out_refund' THEN -l.quantity ELSE l.quantity END) > 0 
                        THEN SUM(CASE WHEN m.move_type = 'out_refund' THEN -l.price_subtotal ELSE l.price_subtotal END) / SUM(CASE WHEN m.move_type = 'out_refund' THEN -l.quantity ELSE l.quantity END)
                        ELSE 0 
                    END as selling_price,
                    
                    SUM(CASE WHEN m.move_type = 'out_refund' THEN -l.price_subtotal ELSE l.price_subtotal END) as total_sales,
                    
                    SUM(CASE WHEN m.move_type = 'out_refund' THEN -l.price_subtotal ELSE l.price_subtotal END) - 
                    SUM(CASE WHEN m.move_type = 'out_refund' THEN -l.quantity * COALESCE((p.standard_price->>m.company_id::text)::numeric, 0) ELSE l.quantity * COALESCE((p.standard_price->>m.company_id::text)::numeric, 0) END) as profit,
                    
                    CASE 
                        WHEN SUM(CASE WHEN m.move_type = 'out_refund' THEN -l.price_subtotal ELSE l.price_subtotal END) > 0 
                        THEN ((SUM(CASE WHEN m.move_type = 'out_refund' THEN -l.price_subtotal ELSE l.price_subtotal END) - SUM(CASE WHEN m.move_type = 'out_refund' THEN -l.quantity * COALESCE((p.standard_price->>m.company_id::text)::numeric, 0) ELSE l.quantity * COALESCE((p.standard_price->>m.company_id::text)::numeric, 0) END)) / SUM(CASE WHEN m.move_type = 'out_refund' THEN -l.price_subtotal ELSE l.price_subtotal END)) * 100
                        ELSE 0 
                    END as profit_margin,
                    
                    l.currency_id
                FROM
                    account_move_line l
                JOIN
                    account_move m ON m.id = l.move_id
                JOIN
                    product_product p ON p.id = l.product_id
                WHERE
                    m.state = 'posted' AND m.move_type IN ('out_invoice', 'out_refund') AND l.display_type = 'product'
                GROUP BY
                    m.invoice_date, l.currency_id
            )
        """ % (self._table,))
