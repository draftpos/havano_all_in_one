from odoo import models, fields

class HaoBankDetail(models.Model):
    _name = 'hao.bank.detail'
    _description = 'Company Bank Details'

    company_id = fields.Many2one('res.company', string='Company')
    account_name = fields.Char(string="Account Name")
    bank_name = fields.Char(string="Bank")
    account_no = fields.Char(string="Account No")
    branch = fields.Char(string="Branch")
    branch_code = fields.Char(string="Branch Code")
    swift_code = fields.Char(string="Swift Code")
    print_on_invoice = fields.Boolean(string="Print on Invoice", default=False)
