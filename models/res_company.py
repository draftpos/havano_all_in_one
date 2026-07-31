from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _get_base_layout_selection(self):
        selection = [
            ('default', 'Default'),
            ('modern', 'Modern'),
            ('normal', 'Normal'),
            ('old', 'Old Standard'),
            ('fresh', 'Fresh Company (Fiscal Tax Invoice)'),
            ('custom_fiscal', 'Seller Buyer Layout')
        ]
        if 'trucking.load' in self.env:
            selection.append(('trucking', 'Trucking (Fiscal Tax Invoice)'))
        return selection

    base_layout = fields.Selection(
        selection='_get_base_layout_selection',
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

    hao_custom_balance_sheet_format = fields.Boolean(
        string="Custom Balance Sheet Format",
        default=False,
        help="Use a custom layout for the Balance Sheet: Assets -> Non-current/Current -> Total, Equity and Liabilities -> Equity/Non-current/Current -> Total."
    )

    def write(self, vals):
        res = super(ResCompany, self).write(vals)
        if 'hao_custom_balance_sheet_format' in vals:
            for company in self:
                company._apply_custom_balance_sheet_format(company.hao_custom_balance_sheet_format)
        return res
        
    @api.model_create_multi
    def create(self, vals_list):
        companies = super(ResCompany, self).create(vals_list)
        for company in companies:
            if company.hao_custom_balance_sheet_format:
                company._apply_custom_balance_sheet_format(company.hao_custom_balance_sheet_format)
        return companies
        
    def _apply_custom_balance_sheet_format(self, custom_format):
        # Apply for Community (account.financial.report)
        if 'account.financial.report' in self.env:
            try:
                reports = self.env['account.financial.report'].sudo().search([])
                bs_roots = reports.filtered(lambda r: r.name and r.name.lower() in ['balance sheet', 'bilan'] and not r.parent_id)
                for bs in bs_roots:
                    children = reports.filtered(lambda r: r.parent_id == bs)
                    
                    # Assets Rearrangement
                    assets = children.filtered(lambda r: r.name and ('asset' in r.name.lower() or 'actif' in r.name.lower()))
                    if assets:
                        asset_node = assets[0]
                        asset_children = reports.filtered(lambda r: r.parent_id == asset_node)
                        current_assets = asset_children.filtered(lambda r: r.name and 'current' in r.name.lower() and 'non' not in r.name.lower())
                        non_current_assets = asset_children.filtered(lambda r: r.name and ('non-current' in r.name.lower() or 'non current' in r.name.lower() or 'fixed' in r.name.lower()))
                        if current_assets and non_current_assets:
                            if custom_format:
                                non_current_assets.write({'sequence': 1})
                                current_assets.write({'sequence': 10})
                            else:
                                current_assets.write({'sequence': 1})
                                non_current_assets.write({'sequence': 10})
                    
                    # Liabilities & Equity Rearrangement
                    liabilities = children.filtered(lambda r: r.name and ('liabilit' in r.name.lower() or 'passif' in r.name.lower() or 'equity and liabilities' in r.name.lower()))
                    equity = children.filtered(lambda r: r.name and 'equity' in r.name.lower() and r not in liabilities)
                    
                    if liabilities:
                        liab = liabilities[0]
                        if custom_format:
                            liab.name = "Equity and Liabilities"
                            if equity:
                                equity.write({'parent_id': liab.id, 'sequence': -10})
                        else:
                            if liab.name == "Equity and Liabilities":
                                liab.name = "Liability"
                            
                            sub_equity = reports.filtered(lambda r: r.parent_id == liab and r.name and 'equity' in r.name.lower())
                            if sub_equity:
                                sub_equity.write({'parent_id': bs.id, 'sequence': liab.sequence + 1})
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Could not format community balance sheet: %s", e)

        # Apply for Enterprise (account.report.line)
        if 'account.report.line' in self.env:
            try:
                lines = self.env['account.report.line'].sudo().search([])
                
                # Check for Assets
                assets = lines.filtered(lambda r: not r.parent_id and r.name and ('asset' in r.name.lower() or 'actif' in r.name.lower()))
                if assets:
                    asset_node = assets[0]
                    asset_children = lines.filtered(lambda r: r.parent_id == asset_node)
                    current_assets = asset_children.filtered(lambda r: r.name and 'current' in r.name.lower() and 'non' not in r.name.lower())
                    non_current_assets = asset_children.filtered(lambda r: r.name and ('non-current' in r.name.lower() or 'non current' in r.name.lower() or 'fixed' in r.name.lower()))
                    
                    if current_assets and non_current_assets:
                        if custom_format:
                            non_current_assets.write({'sequence': 1})
                            current_assets.write({'sequence': 10})
                        else:
                            current_assets.write({'sequence': 1})
                            non_current_assets.write({'sequence': 10})
                            
                # Check for Liabilities and Equity
                liabilities = lines.filtered(lambda r: not r.parent_id and r.name and ('liabilit' in r.name.lower() or 'passif' in r.name.lower() or 'equity and liabilities' in r.name.lower()))
                equity = lines.filtered(lambda r: not r.parent_id and r.name and 'equity' in r.name.lower() and r not in liabilities)
                
                if liabilities:
                    liab = liabilities[0]
                    if custom_format:
                        liab.name = "Equity and Liabilities"
                        if equity:
                            equity.write({'parent_id': liab.id, 'sequence': -10})
                    else:
                        if liab.name == "Equity and Liabilities":
                            liab.name = "Liabilities"
                        sub_equity = lines.filtered(lambda r: r.parent_id == liab and r.name and 'equity' in r.name.lower())
                        if sub_equity:
                            sub_equity.write({'parent_id': False, 'sequence': liab.sequence + 1})
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Could not format enterprise balance sheet: %s", e)
