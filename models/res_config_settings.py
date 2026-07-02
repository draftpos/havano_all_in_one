from odoo import _, api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Duplicate contacts
    hao_check_name_exact = fields.Boolean(
        string="Contact: Exact Name",
        default=True,
    )
    hao_check_email_only = fields.Boolean(
        string="Contact: Email Only",
        default=True,
    )
    hao_check_email_name = fields.Boolean(
        string="Contact: Name + Email",
        default=True,
    )
    hao_check_phone_only = fields.Boolean(
        string="Contact: Phone Only",
        default=True,
    )
    hao_check_phone_name = fields.Boolean(
        string="Contact: Name + Phone",
        default=True,
    )
    hao_check_name_address = fields.Boolean(
        string="Contact: Name + Address",
        default=True,
    )

    # Duplicate products
    hao_product_check_name = fields.Boolean(
        string="Product: Name",
        default=True,
    )
    hao_product_check_default_code = fields.Boolean(
        string="Product: Internal Reference",
        default=True,
    )

    # Customer/supplier split
    hao_show_only_customers_in_sales = fields.Boolean(
        string="Sales show customers only",
        default=True,
    )
    hao_show_only_suppliers_in_purchases = fields.Boolean(
        string="Purchases show suppliers only",
        default=True,
    )
    hao_auto_mark_customer_from_sales = fields.Boolean(
        string="Auto-mark customer from Sales",
        config_parameter="havano_all_in_one.auto_mark_customer_from_sales",
        default=True,
    )
    hao_auto_mark_supplier_from_purchase = fields.Boolean(
        string="Auto-mark supplier from Purchase",
        config_parameter="havano_all_in_one.auto_mark_supplier_from_purchase",
        default=True,
    )

    # Login Page Customization
    hao_login_orientation = fields.Selection(
        selection=[('default', 'Default'), ('left', 'Left'), ('middle', 'Middle'), ('right', 'Right')],
        string="Orientation",
        help="Type of login page visibility",
        config_parameter="havano_all_in_one.login_orientation",
        default="default"
    )
    hao_login_background = fields.Selection(
        selection=[('color', 'Color Picker'), ('image', 'Image'), ('url', 'URL')],
        string="Background",
        help="Background of the login page",
        config_parameter="havano_all_in_one.login_background"
    )
    hao_login_image = fields.Binary(
        string="Image", 
        help="Select background image of login page"
    )
    hao_login_url = fields.Char(
        string="URL", 
        help="Select and url of image",
        config_parameter="havano_all_in_one.login_url"
    )
    hao_login_color = fields.Char(
        string="Color", 
        help="Set a colour for background of login page",
        config_parameter="havano_all_in_one.login_color"
    )
    hao_redirect_home_to_login = fields.Boolean(
        string="Always Redirect Home to Login",
        help="If enabled, accessing the root URL '/' will automatically redirect to the login page.",
        config_parameter="havano_all_in_one.redirect_home_to_login",
        default=False
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        
        # Manually parse boolean config parameters that use default=True
        # because Odoo's default boolean casting evaluates bool("False") to True.
        res.update(
            hao_check_name_exact=params.get_param('havano_all_in_one.contact_check_name_exact', 'True') == 'True',
            hao_check_email_only=params.get_param('havano_all_in_one.contact_check_email_only', 'True') == 'True',
            hao_check_email_name=params.get_param('havano_all_in_one.contact_check_email_name', 'True') == 'True',
            hao_check_phone_only=params.get_param('havano_all_in_one.contact_check_phone_only', 'True') == 'True',
            hao_check_phone_name=params.get_param('havano_all_in_one.contact_check_phone_name', 'True') == 'True',
            hao_check_name_address=params.get_param('havano_all_in_one.contact_check_name_address', 'True') == 'True',
            hao_product_check_name=params.get_param('havano_all_in_one.product_check_name', 'True') == 'True',
            hao_product_check_default_code=params.get_param('havano_all_in_one.product_check_default_code', 'True') == 'True',
            hao_show_only_customers_in_sales=params.get_param('havano_all_in_one.show_only_customers_in_sales', 'True') == 'True',
            hao_show_only_suppliers_in_purchases=params.get_param('havano_all_in_one.show_only_suppliers_in_purchases', 'True') == 'True',
            hao_login_image=params.get_param('havano_all_in_one.login_image')
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        
        # Odoo's default set_values deletes the parameter if the boolean is False.
        # We must explicitly save it as the string "False" so that get_values knows it was unchecked.
        params.set_param('havano_all_in_one.contact_check_name_exact', str(self.hao_check_name_exact))
        params.set_param('havano_all_in_one.contact_check_email_only', str(self.hao_check_email_only))
        params.set_param('havano_all_in_one.contact_check_email_name', str(self.hao_check_email_name))
        params.set_param('havano_all_in_one.contact_check_phone_only', str(self.hao_check_phone_only))
        params.set_param('havano_all_in_one.contact_check_phone_name', str(self.hao_check_phone_name))
        params.set_param('havano_all_in_one.contact_check_name_address', str(self.hao_check_name_address))
        params.set_param('havano_all_in_one.product_check_name', str(self.hao_product_check_name))
        params.set_param('havano_all_in_one.product_check_default_code', str(self.hao_product_check_default_code))
        params.set_param('havano_all_in_one.show_only_customers_in_sales', str(self.hao_show_only_customers_in_sales))
        params.set_param('havano_all_in_one.show_only_suppliers_in_purchases', str(self.hao_show_only_suppliers_in_purchases))
        
        params.set_param('havano_all_in_one.login_image', self.hao_login_image)

    @api.onchange('hao_login_orientation')
    def onchange_hao_login_orientation(self):
        if self.hao_login_orientation == 'default':
            self.hao_login_background = False
            self.hao_login_color = False
            self.hao_login_image = False
            self.hao_login_url = False

    hao_activate_pharmacy = fields.Boolean(
        string="Allow Pharmacy Products",
        related="company_id.hao_activate_pharmacy",
        readonly=False,
        help="When enabled, products can be marked as pharmacy items with mandatory dosage.",
    )
    hao_activate_inventory_orders = fields.Boolean(
        string="Inventory Order Settings",
        related="company_id.hao_activate_inventory_orders",
        readonly=False,
        help="When enabled, products can use Order 1–5 flags on the Inventory tab.",
    )

    hao_rebrand_customers = fields.Char(string="Rename 'Customers' To", related="company_id.hao_rebrand_customers", readonly=False)
    hao_rebrand_vendors = fields.Char(string="Rename 'Vendors' To", related="company_id.hao_rebrand_vendors", readonly=False)

    hao_show_cust_invoices = fields.Boolean(related="company_id.hao_show_cust_invoices", readonly=False)
    hao_show_cust_credit_notes = fields.Boolean(related="company_id.hao_show_cust_credit_notes", readonly=False)
    hao_show_cust_payments = fields.Boolean(related="company_id.hao_show_cust_payments", readonly=False)
    hao_show_cust_products = fields.Boolean(related="company_id.hao_show_cust_products", readonly=False)
    hao_show_cust_customers = fields.Boolean(related="company_id.hao_show_cust_customers", readonly=False)

    hao_show_vend_bills = fields.Boolean(related="company_id.hao_show_vend_bills", readonly=False)
    hao_show_vend_refunds = fields.Boolean(related="company_id.hao_show_vend_refunds", readonly=False)
    hao_show_vend_payments = fields.Boolean(related="company_id.hao_show_vend_payments", readonly=False)
    hao_show_vend_expenses = fields.Boolean(related="company_id.hao_show_vend_expenses", readonly=False)
    hao_show_vend_products = fields.Boolean(related="company_id.hao_show_vend_products", readonly=False)
    hao_show_vend_vendors = fields.Boolean(related="company_id.hao_show_vend_vendors", readonly=False)

    hao_global_sales_automation_method = fields.Selection([
        ('full', 'Full Automate'),
        ('quote_invoice', 'Quote - Sales Invoice')
    ], string='Default Sales Automation Flow', config_parameter='havano_all_in_one.global_sales_automation_method', default='full')

    hao_global_purchase_automation_method = fields.Selection([
        ('full', 'Full Automate'),
        ('quote_invoice', 'Quote - Purchase Invoice')
    ], string='Default Purchase Automation Flow', config_parameter='havano_all_in_one.global_purchase_automation_method', default='full')

    def action_apply_automation_methods_to_all_users(self):
        for config in self:
            users = self.env['res.users'].search([('share', '=', False)])
            sales_vals = {
                'hao_enable_sales_automation': True,
                'hao_sales_automation_method': config.hao_global_sales_automation_method,
            }
            if config.hao_global_sales_automation_method == 'full':
                sales_vals.update({
                    'hao_auto_confirm_quotation': True,
                    'hao_auto_create_invoice': True,
                    'hao_auto_post_invoice': True,
                })
            else:
                sales_vals.update({
                    'hao_auto_confirm_quotation': False,
                    'hao_auto_create_invoice': False,
                    'hao_auto_post_invoice': False,
                })

            purchase_vals = {
                'hao_enable_purchase_automation': True,
                'hao_purchase_automation_method': config.hao_global_purchase_automation_method,
            }
            if config.hao_global_purchase_automation_method == 'full':
                purchase_vals.update({
                    'hao_auto_confirm_purchase': True,
                    'hao_auto_validate_receipt': True,
                    'hao_auto_create_vendor_bill': True,
                    'hao_auto_post_vendor_bill': True,
                })
            else:
                purchase_vals.update({
                    'hao_auto_confirm_purchase': False,
                    'hao_auto_validate_receipt': False,
                    'hao_auto_create_vendor_bill': False,
                    'hao_auto_post_vendor_bill': False,
                })
            
            users.write({**sales_vals, **purchase_vals})

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            hao_login_image=params.get_param('havano_all_in_one.login_image')
        )
        return res

    def set_values(self):
        super().set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('havano_all_in_one.login_image', self.hao_login_image)
        
        # Menu visibility toggles (Customers)
        self._toggle_menu('account.menu_action_move_out_invoice_type', self.hao_show_cust_invoices)
        self._toggle_menu('account.menu_action_move_out_refund_type', self.hao_show_cust_credit_notes)
        self._toggle_menu('account.menu_action_account_payments_receivable', self.hao_show_cust_payments)
        self._toggle_menu('account.product_product_menu_sellable', self.hao_show_cust_products)
        self._toggle_menu('account.menu_account_customer', self.hao_show_cust_customers)

        # Menu visibility toggles (Vendors)
        self._toggle_menu('account.menu_action_move_in_invoice_type', self.hao_show_vend_bills)
        self._toggle_menu('account.menu_action_move_in_refund_type', self.hao_show_vend_refunds)
        self._toggle_menu('account.menu_action_account_payments_payable', self.hao_show_vend_payments)
        self._toggle_menu('hr_expense.menu_hr_expense_account_employee_expenses', self.hao_show_vend_expenses)
        self._toggle_menu('account.product_product_menu_purchasable', self.hao_show_vend_products)
        self._toggle_menu('account.menu_account_supplier', self.hao_show_vend_vendors)

        # Rebranding logic for Customers
        if self.hao_rebrand_customers:
            cust_label = self.hao_rebrand_customers
            cust_menu_ids = [
                self.env.ref('account.menu_finance_receivables', raise_if_not_found=False).id if self.env.ref('account.menu_finance_receivables', raise_if_not_found=False) else False,
                self.env.ref('account.menu_account_customer', raise_if_not_found=False).id if self.env.ref('account.menu_account_customer', raise_if_not_found=False) else False,
            ]
            cust_menus = self.env['ir.ui.menu'].search([('id', 'in', [m for m in cust_menu_ids if m])])
            for menu in cust_menus:
                menu.name = cust_label

            cust_action_id = self.env.ref('account.res_partner_action_customer', raise_if_not_found=False)
            if cust_action_id:
                cust_actions = self.env['ir.actions.act_window'].search([('id', '=', cust_action_id.id)])
                for action in cust_actions:
                    action.name = cust_label

        # Rebranding logic for Vendors
        if self.hao_rebrand_vendors:
            vend_label = self.hao_rebrand_vendors
            vend_menu_ids = [
                self.env.ref('account.menu_finance_payables', raise_if_not_found=False).id if self.env.ref('account.menu_finance_payables', raise_if_not_found=False) else False,
                self.env.ref('account.menu_account_supplier', raise_if_not_found=False).id if self.env.ref('account.menu_account_supplier', raise_if_not_found=False) else False,
            ]
            vend_menus = self.env['ir.ui.menu'].search([('id', 'in', [m for m in vend_menu_ids if m])])
            for menu in vend_menus:
                menu.name = vend_label

            vend_action_id = self.env.ref('account.res_partner_action_supplier', raise_if_not_found=False)
            if vend_action_id:
                vend_actions = self.env['ir.actions.act_window'].search([('id', '=', vend_action_id.id)])
                for action in vend_actions:
                    action.name = vend_label

    def _toggle_menu(self, xml_id, active):
        menu = self.env.ref(xml_id, raise_if_not_found=False)
        if menu:
            menu.active = active
