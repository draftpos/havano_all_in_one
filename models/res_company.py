from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    hao_activate_pharmacy = fields.Boolean(
        string="Activate Pharmacy",
        default=True,
        help="Show pharmacy fields on products and expose pharmacy data via API.",
    )
    havano_bypass_tax_price_check = fields.Boolean(
        string="Bypass Havano Tax Price Check",
        default=False,
    )
