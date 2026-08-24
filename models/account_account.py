from odoo import fields, models
from odoo import api, fields, models

class AccountAccount(models.Model):
    _inherit = 'account.account'

    hao_custom_category = fields.Selection([
        ('none', 'None'),
        ('revenue', 'Revenue'),
        ('cogs', 'Cost of Goods Sold'),
        ('operating', 'Operating Expenses'),
        ('financing', 'Financing Expenses'),
        ('discontinued', 'Discontinued Operations'),
    ], string="Havano Custom Category", default='none', help="Used to group accounts on the Custom Profit and Loss report.")

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountAccount, self).create(vals_list)
        if any(rec.account_type in ['equity', 'equity_unallocated'] for rec in res):
            self.env['account.report']._sync_soce_columns()
        return res

    def write(self, vals):
        # Check if type changed to/from equity, or if name changed for an equity account
        was_equity = any(rec.account_type in ['equity', 'equity_unallocated'] for rec in self)
        res = super(AccountAccount, self).write(vals)
        is_equity = any(rec.account_type in ['equity', 'equity_unallocated'] for rec in self)
        
        if was_equity or is_equity:
            if 'account_type' in vals or 'name' in vals:
                self.env['account.report']._sync_soce_columns()
        return res

    def unlink(self):
        was_equity = any(rec.account_type in ['equity', 'equity_unallocated'] for rec in self)
        res = super(AccountAccount, self).unlink()
        if was_equity:
            self.env['account.report']._sync_soce_columns()
        return res
