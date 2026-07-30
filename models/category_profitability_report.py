from odoo import models, fields, tools

class CategoryProfitabilityReport(models.Model):
    _name = 'havano.category.profitability.report'
    _description = 'Category Profitability Report'
    _auto = False

    category_id = fields.Many2one('product.category', string='Category', readonly=True)
    qty = fields.Float(string='Qty Sold', readonly=True)
    cost_price = fields.Monetary(string='Buy Price', readonly=True, currency_field='currency_id')
    selling_price = fields.Monetary(string='Sell Price', readonly=True, currency_field='currency_id')
    total_sales = fields.Monetary(string='Total Sales', readonly=True, currency_field='currency_id')
    profit = fields.Monetary(string='Profit', readonly=True, currency_field='currency_id')
    profit_margin = fields.Float(string='Profit Margin (%)', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    MIN(l.id) as id,
                    t.categ_id as category_id,
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
                    
                    m.invoice_date as date,
                    l.currency_id
                FROM
                    account_move_line l
                JOIN
                    account_move m ON m.id = l.move_id
                JOIN
                    product_product p ON p.id = l.product_id
                JOIN
                    product_template t ON t.id = p.product_tmpl_id
                WHERE
                    m.state = 'posted' AND m.move_type IN ('out_invoice', 'out_refund') AND l.display_type = 'product'
                GROUP BY
                    t.categ_id, m.invoice_date, l.currency_id
            )
        """ % (self._table,))
