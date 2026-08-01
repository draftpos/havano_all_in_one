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

    hao_custom_pnl_format = fields.Boolean(
        string="Custom Profit or Loss Format",
        default=False,
        help="Use a custom layout for the Profit and Loss report."
    )

    def write(self, vals):
        res = super(ResCompany, self).write(vals)
        if 'hao_custom_balance_sheet_format' in vals:
            for company in self:
                company._apply_custom_balance_sheet_format(company.hao_custom_balance_sheet_format)
        if 'hao_custom_pnl_format' in vals:
            for company in self:
                company._apply_custom_pnl_format(company.hao_custom_pnl_format)
        return res
        
    @api.model_create_multi
    def create(self, vals_list):
        companies = super(ResCompany, self).create(vals_list)
        for company in companies:
            if company.hao_custom_balance_sheet_format:
                company._apply_custom_balance_sheet_format(company.hao_custom_balance_sheet_format)
            if company.hao_custom_pnl_format:
                company._apply_custom_pnl_format(company.hao_custom_pnl_format)
        return companies
        
    def _apply_custom_balance_sheet_format(self, custom_format):
        if 'account.report' not in self.env:
            return

        custom = self.env.ref('havano_all_in_one.hao_balance_sheet', raise_if_not_found=False)
        base = self.env.ref('account_reports.balance_sheet', raise_if_not_found=False)

        try:
            if custom_format:
                if custom: custom.sudo().sequence = 1
                if base: base.sudo().sequence = 999
            else:
                if custom: custom.sudo().sequence = 999
                if base: base.sudo().sequence = 10
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Could not toggle enterprise balance sheet format: %s", e)

    def _apply_custom_pnl_format(self, custom_format):
        # Apply for Community (account.financial.report)
        if 'account.financial.report' in self.env:
            try:
                reports = self.env['account.financial.report'].sudo().search([])
                pnls = reports.filtered(lambda r: r.name and ('profit and loss' in r.name.lower() or 'compte de resultat' in r.name.lower()) and not r.parent_id)
                for pnl in pnls:
                    children = reports.filtered(lambda r: r.parent_id == pnl)
                    
                    if custom_format:
                        revenue = children.filtered(lambda r: 'income' in r.name.lower() or 'revenue' in r.name.lower())
                        if revenue:
                            revenue[0].name = "Revenue"
                            revenue[0].sequence = 1
                            
                        cost_of_sales = children.filtered(lambda r: 'cost of revenue' in r.name.lower() or 'cost of sales' in r.name.lower())
                        if cost_of_sales:
                            cost_of_sales[0].name = "Less Cost of Sales"
                            cost_of_sales[0].sequence = 2
                            
                        gross_profit = children.filtered(lambda r: 'gross profit' in r.name.lower())
                        if gross_profit:
                            gross_profit[0].name = "Gross Profit"
                            gross_profit[0].sequence = 3
                            
                        other_income = children.filtered(lambda r: 'other income' in r.name.lower() or 'unallocated' in r.name.lower())
                        if other_income:
                            other_income[0].name = "Other Income"
                            other_income[0].sequence = 4
                            
                        operating_expense = children.filtered(lambda r: 'operating expense' in r.name.lower() or 'expense' in r.name.lower() and r not in cost_of_sales)
                        if operating_expense:
                            operating_expense[0].name = "Less Operating Expenses"
                            operating_expense[0].sequence = 5

                        net_profit = children.filtered(lambda r: 'net profit' in r.name.lower())
                        if net_profit:
                            net_profit[0].name = "Net Profit"
                            net_profit[0].sequence = 10
                            
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Could not format community P&L: %s", e)

        # Apply for Enterprise (account.report.line)
        if 'account.report.line' in self.env:
            try:
                lines = self.env['account.report.line'].sudo().search([])
                
                # Find lines belonging to P&L report
                pnl_lines = lines.filtered(lambda r: r.report_id and ('profit and loss' in r.report_id.name.lower() or 'profit' in r.report_id.name.lower()))
                
                if pnl_lines:
                    if custom_format:
                        revenue = pnl_lines.filtered(lambda r: not r.parent_id and ('income' in r.name.lower() or 'revenue' in r.name.lower()))
                        if revenue:
                            revenue[0].name = "Revenue"
                            revenue[0].sequence = 1
                            
                        cost_of_sales = pnl_lines.filtered(lambda r: not r.parent_id and ('cost of revenue' in r.name.lower() or 'cost of sales' in r.name.lower()))
                        if cost_of_sales:
                            cost_of_sales[0].name = "Less Cost of Sales"
                            cost_of_sales[0].sequence = 2
                            
                        gross_profit = pnl_lines.filtered(lambda r: not r.parent_id and 'gross profit' in r.name.lower())
                        if gross_profit:
                            gross_profit[0].name = "Gross Profit"
                            gross_profit[0].sequence = 3
                            
                        other_income = pnl_lines.filtered(lambda r: not r.parent_id and ('other income' in r.name.lower() or 'unallocated' in r.name.lower()))
                        if other_income:
                            other_income[0].name = "Other Income"
                            other_income[0].sequence = 4
                            
                        operating_expense = pnl_lines.filtered(lambda r: not r.parent_id and ('operating expense' in r.name.lower() or 'expense' in r.name.lower()) and r not in cost_of_sales)
                        if operating_expense:
                            operating_expense[0].name = "Less Operating Expenses"
                            operating_expense[0].sequence = 5

                        net_profit = pnl_lines.filtered(lambda r: not r.parent_id and 'net profit' in r.name.lower())
                        if net_profit:
                            net_profit[0].name = "Net Profit"
                            net_profit[0].sequence = 10
                            
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Could not format enterprise P&L: %s", e)
