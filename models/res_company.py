from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    base_layout = fields.Selection(
        selection=[('default', 'Default'),
                   ('modern', 'Modern'),
                   ('normal', 'Normal'),
                   ('old', 'Old Standard')],
        string="Invoice Document Layout", default="default",
        help="base layout selection")
    document_layout_id = fields.Many2one("havano.invoice.template",
                                         string="Invoice Layout Configuration",
                                         help="Invoice layout configuration")

    hao_activate_pharmacy = fields.Boolean(
        string="Activate Pharmacy",
        default=True,
        help="Show pharmacy fields on products and expose pharmacy data via API.",
    )
    hao_activate_inventory_orders = fields.Boolean(
        string="Activate Inventory Order Settings",
        default=True,
        help="Show order checkboxes on product inventory tab and expose them via API.",
    )
   