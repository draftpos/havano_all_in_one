from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    partner_id = fields.Many2one(domain="[('is_supplier', '=', True)]")
