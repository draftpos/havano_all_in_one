import re

from odoo import _, api, fields, models
from odoo.exceptions import RedirectWarning, ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    hao_activate_pharmacy = fields.Boolean(
        compute="_compute_hao_activate_pharmacy",
    )
    is_pharmacy = fields.Boolean(
        string="Is Pharmacy",
        default=False,
    )
    pharmacy_dosage_id = fields.Many2one(
        "pharmacy.dosage",
        string="Dosage",
        ondelete="restrict",
    )
    pharmacy_dosage_code = fields.Char(
        related="pharmacy_dosage_id.code",
        string="Dosage Code",
        readonly=True,
    )
    pharmacy_dosage_description = fields.Text(
        related="pharmacy_dosage_id.description",
        string="Dosage Description",
        readonly=True,
    )

    allow_multi_uom = fields.Boolean(
        string="Enable Multi UoM Pricing",
        default=False,
    )
    strict_uom_tracking = fields.Boolean(
        string="Allow Strict UoM Tracking on Sales Lines",
        default=False,
    )

    hao_activate_inventory_orders = fields.Boolean(
        compute="_compute_hao_activate_inventory_orders",
    )
    order_1 = fields.Boolean(string="Order 1", default=False)
    order_2 = fields.Boolean(string="Order 2", default=False)
    order_3 = fields.Boolean(string="Order 3", default=False)
    order_4 = fields.Boolean(string="Order 4", default=False)
    order_5 = fields.Boolean(string="Order 5", default=False)

    @api.depends("company_id", "company_id.hao_activate_pharmacy")
    def _compute_hao_activate_pharmacy(self):
        activated = bool(self.env.company.hao_activate_pharmacy)
        for product in self:
            product.hao_activate_pharmacy = activated

    @api.depends("company_id", "company_id.hao_activate_inventory_orders")
    def _compute_hao_activate_inventory_orders(self):
        activated = bool(self.env.company.hao_activate_inventory_orders)
        for product in self:
            product.hao_activate_inventory_orders = activated

    @api.constrains("is_pharmacy", "pharmacy_dosage_id", "company_id")
    def _check_pharmacy_dosage(self):
        for product in self:
            if not product.company_id.hao_activate_pharmacy:
                continue
            if product.is_pharmacy and not product.pharmacy_dosage_id:
                raise ValidationError(
                    _("Pharmacy products must have a dosage (code and description).")
                )

    @api.onchange("is_pharmacy")
    def _onchange_is_pharmacy(self):
        if not self.is_pharmacy:
            self.pharmacy_dosage_id = False

    @api.constrains("name")
    def _check_unique_name(self):
        for product in self:
            if not product.name or not self._is_enabled("product_check_name"):
                continue
            normalized_name = self._normalize_name(product.name)
            existing = self.search([("id", "!=", product.id), ("name", "!=", False)])
            for existing_product in existing:
                if normalized_name == self._normalize_name(existing_product.name):
                    raise ValidationError(
                        _("Product '%(name)s' already exists.", name=existing_product.display_name)
                    )

    @api.constrains("default_code")
    def _check_unique_default_code(self):
        for product in self:
            if not product.default_code or not self._is_enabled("product_check_default_code"):
                continue
            existing = self.search([("id", "!=", product.id), ("default_code", "=", product.default_code)], limit=1)
            if existing:
                raise ValidationError(
                    _("Internal Reference '%(code)s' already exists.", code=product.default_code)
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("default_code"):
                vals["default_code"] = self.env["ir.sequence"].next_by_code("product.item.code") or "101"
        records = super().create(vals_list)
        for product in records:
            product._raise_if_duplicate_product(product.name, product.default_code, current_id=product.id)
        return records

    def write(self, vals):
        res = super().write(vals)
        for product in self:
            name = vals.get("name", product.name)
            default_code = vals.get("default_code", product.default_code)
            product._raise_if_duplicate_product(name, default_code, current_id=product.id)
        return res

    def _normalize_name(self, value):
        return re.sub(r"\s+", " ", (value or "").strip()).lower()

    def _is_enabled(self, key, default="True"):
        return self.env["ir.config_parameter"].sudo().get_param(f"havano_all_in_one.{key}", default) == "True"

    def _raise_if_duplicate_product(self, name, default_code, current_id=False):
        domain = [("active", "in", [True, False])]
        if current_id:
            domain.append(("id", "!=", current_id))
        duplicate = False
        reason = ""
        if name and self._is_enabled("product_check_name"):
            candidates = self.search(domain + [("name", "=ilike", name)], limit=20)
            norm = self._normalize_name(name)
            duplicate = next((p for p in candidates if self._normalize_name(p.name) == norm), False)
            reason = _("Name") if duplicate else reason
        if not duplicate and default_code and self._is_enabled("product_check_default_code"):
            duplicate = self.search(domain + [("default_code", "=", default_code)], limit=1)
            reason = _("Internal Reference") if duplicate else reason
        if duplicate:
            action = self.env.ref("havano_all_in_one.action_hao_open_duplicate_product")
            raise RedirectWarning(
                _("Duplicate product detected by %(reason)s: %(name)s")
                % {"reason": reason, "name": duplicate.display_name},
                action.id,
                _("View Duplicate"),
                {"active_ids": [duplicate.id], "active_id": duplicate.id},
            )
