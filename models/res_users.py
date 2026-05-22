from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    hao_enable_sales_automation = fields.Boolean(
        string="Enable sales automation",
        default=False,
    )
    hao_auto_confirm_quotation = fields.Boolean(
        string="Auto-confirm quotation",
        default=False,
    )
    hao_auto_create_invoice = fields.Boolean(
        string="Auto-create invoice",
        default=False,
    )
    hao_auto_post_invoice = fields.Boolean(
        string="Auto-post invoice",
        default=False,
    )
