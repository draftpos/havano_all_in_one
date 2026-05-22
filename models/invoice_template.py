from odoo import fields, models


class HavanoInvoiceTemplate(models.Model):
    _name = "havano.invoice.template"
    _description = "Havano Invoice Template"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    is_default = fields.Boolean(string="Default Template")
    note = fields.Text()
