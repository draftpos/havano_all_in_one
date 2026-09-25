from odoo import models, fields

class SaleReport(models.Model):
    _inherit = "sale.report"

    hao_business_sector = fields.Char(string="Business Sector", readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account", readonly=True)

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['hao_business_sector'] = "s.hao_business_sector"
        res['analytic_account_id'] = "(SELECT jsonb_object_keys::integer FROM jsonb_object_keys(COALESCE(l.analytic_distribution, '{}'::jsonb)) LIMIT 1)"
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += ", s.hao_business_sector, l.analytic_distribution"
        return res
