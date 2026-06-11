from odoo import _, api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Duplicate contacts
    hao_check_name_exact = fields.Boolean(
        string="Contact: Exact Name",
        config_parameter="havano_all_in_one.contact_check_name_exact",
        default=True,
    )
    hao_check_email_only = fields.Boolean(
        string="Contact: Email Only",
        config_parameter="havano_all_in_one.contact_check_email_only",
        default=True,
    )
    hao_check_email_name = fields.Boolean(
        string="Contact: Name + Email",
        config_parameter="havano_all_in_one.contact_check_email_name",
        default=True,
    )
    hao_check_phone_only = fields.Boolean(
        string="Contact: Phone Only",
        config_parameter="havano_all_in_one.contact_check_phone_only",
        default=True,
    )
    hao_check_phone_name = fields.Boolean(
        string="Contact: Name + Phone",
        config_parameter="havano_all_in_one.contact_check_phone_name",
        default=True,
    )
    hao_check_name_address = fields.Boolean(
        string="Contact: Name + Address",
        config_parameter="havano_all_in_one.contact_check_name_address",
        default=True,
    )

    # Duplicate products
    hao_product_check_name = fields.Boolean(
        string="Product: Name",
        config_parameter="havano_all_in_one.product_check_name",
        default=True,
    )
    hao_product_check_default_code = fields.Boolean(
        string="Product: Internal Reference",
        config_parameter="havano_all_in_one.product_check_default_code",
        default=True,
    )

    # Customer/supplier split
    hao_show_only_customers_in_sales = fields.Boolean(
        string="Sales show customers only",
        config_parameter="havano_all_in_one.show_only_customers_in_sales",
        default=True,
    )
    hao_show_only_suppliers_in_purchases = fields.Boolean(
        string="Purchases show suppliers only",
        config_parameter="havano_all_in_one.show_only_suppliers_in_purchases",
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


