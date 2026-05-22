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

    hao_tax_price_mode_label = fields.Char(
        compute="_compute_hao_tax_price_mode_label",
        string="Current tax price mode",
    )

    @api.depends("company_id", "company_id.account_price_include")
    def _compute_hao_tax_price_mode_label(self):
        for settings in self:
            mode = settings.company_id.account_price_include or "tax_excluded"
            settings.hao_tax_price_mode_label = (
                _("Tax Included") if mode == "tax_included" else _("Tax Excluded")
            )

    def _hao_sale_tax_multiplier(self, product):
        """Return 1 + sum of percentage sale tax rates on the product."""
        taxes = product.taxes_id.filtered(lambda tax: tax.type_tax_use == "sale" and tax.amount_type == "percent")
        if not taxes:
            company_tax = self.company_id.account_sale_tax_id
            if company_tax and company_tax.amount_type == "percent":
                return 1.0 + (company_tax.amount / 100.0)
            return 1.0
        return 1.0 + sum(taxes.mapped("amount")) / 100.0

    def _hao_convert_product_prices(self, from_mode, to_mode):
        self.ensure_one()
        if from_mode == to_mode:
            return 0
        Product = self.env["product.template"].sudo()
        products = Product.search([("list_price", ">", 0)])
        updated = 0
        for product in products:
            factor = self._hao_sale_tax_multiplier(product)
            if factor <= 0:
                continue
            old_price = product.list_price
            if from_mode == "tax_excluded" and to_mode == "tax_included":
                new_price = old_price * factor
            elif from_mode == "tax_included" and to_mode == "tax_excluded":
                new_price = old_price / factor
            else:
                continue
            if abs(new_price - old_price) > 0.0001:
                product.list_price = new_price
                updated += 1
        return updated

    def _hao_apply_tax_price_mode(self, target_mode):
        self.ensure_one()
        company = self.company_id
        current_mode = company.account_price_include or "tax_excluded"
        if current_mode == target_mode:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Tax price mode"),
                    "message": _("Already set to %s.", self.hao_tax_price_mode_label),
                    "type": "info",
                    "sticky": False,
                },
            }

        updated_products = self._hao_convert_product_prices(current_mode, target_mode)
        company.with_context(havano_bypass_tax_price_check=True).write(
            {"account_price_include": target_mode}
        )

        mode_label = _("Tax Included") if target_mode == "tax_included" else _("Tax Excluded")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Tax price mode updated"),
                "message": _(
                    "Switched to %(mode)s. Updated %(count)s product sales price(s). Reloading…",
                    mode=mode_label,
                    count=updated_products,
                ),
                "type": "success",
                "sticky": True,
                "next": {"type": "ir.actions.client", "tag": "reload"},
            },
        }

    def action_hao_switch_tax_included(self):
        return self._hao_apply_tax_price_mode("tax_included")

    def action_hao_switch_tax_excluded(self):
        return self._hao_apply_tax_price_mode("tax_excluded")
