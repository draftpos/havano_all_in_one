from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    base_layout = fields.Selection(
        selection=[('default', 'Default'),
                   ('modern', 'Modern'),
                   ('normal', 'Normal'),
                   ('old', 'Old Standard'),
                   ('fresh', 'Fresh Company (Fiscal Tax Invoice)'),
                   ('trucking', 'Trucking (Fiscal Tax Invoice)')],
        string="Invoice Document Layout", default="default",
        help="base layout selection")
    hao_document_layout_id = fields.Many2one("havano.invoice.template",
                                         string="Invoice Layout Configuration",
                                         ondelete="set null",
                                         help="Invoice layout configuration")

    hao_activate_pharmacy = fields.Boolean(
        string="Activate Pharmacy",
        default=False,
        help="Show pharmacy fields on products and expose pharmacy data via API.",
    )
    hao_rebrand_customers = fields.Char(string="Rename 'Customers' To", default="Customers", help="Rename the Customers menu and UI throughout Accounting.")
    hao_rebrand_vendors = fields.Char(string="Rename 'Vendors' To", default="Vendors", help="Rename the Vendors menu and UI throughout Accounting.")

    hao_show_cust_invoices = fields.Boolean(string="Show Invoices in Customers", default=True)
    hao_show_cust_credit_notes = fields.Boolean(string="Show Credit Notes in Customers", default=True)
    hao_show_cust_payments = fields.Boolean(string="Show Payments in Customers", default=True)
    hao_show_cust_products = fields.Boolean(string="Show Products in Customers", default=True)
    hao_show_cust_customers = fields.Boolean(string="Show Customers in Customers", default=True)

    hao_show_vend_bills = fields.Boolean(string="Show Bills in Vendors", default=True)
    hao_show_vend_refunds = fields.Boolean(string="Show Refunds in Vendors", default=True)
    hao_show_vend_payments = fields.Boolean(string="Show Payments in Vendors", default=True)
    hao_show_vend_expenses = fields.Boolean(string="Show Employee Expenses in Vendors", default=True)
    hao_show_vend_products = fields.Boolean(string="Show Products in Vendors", default=True)
    hao_show_vend_vendors = fields.Boolean(string="Show Vendors in Vendors", default=True)

    hao_activate_inventory_orders = fields.Boolean(
        string="Activate Inventory Order Settings",
        default=True,
        help="Show order checkboxes on product inventory tab and expose them via API.",
    )
   
    hao_bank_account_name = fields.Char(string="Account Name")
    hao_bank_name = fields.Char(string="Bank")
    hao_bank_account_no = fields.Char(string="Account No")
    hao_bank_branch = fields.Char(string="Branch")
    hao_bank_branch_code = fields.Char(string="Branch Code")
    hao_bank_swift_code = fields.Char(string="Swift Code")

    hao_multi_bank = fields.Boolean(string="Allow Multi Bank Details", default=False)
    hao_bank_detail_ids = fields.One2many('hao.bank.detail', 'company_id', string="Bank Details")
