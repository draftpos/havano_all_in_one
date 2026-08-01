from odoo import fields, models

class AccountAccount(models.Model):
    _inherit = 'account.account'

    hao_custom_category = fields.Selection([
        ('none', 'None'),
        ('investing', 'Investing Expenses'),
        ('financing', 'Financing Expenses'),
        ('discontinued', 'Discontinued Operations'),
    ], string="Havano Custom Category", default='none', help="Used to group accounts on the Custom Profit and Loss report.")
