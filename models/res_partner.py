from odoo import _, api, fields, models
from odoo.exceptions import RedirectWarning, ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_customer = fields.Boolean(string="Is Customer", default=True, tracking=True)
    is_supplier = fields.Boolean(string="Is Supplier", default=False, tracking=True)
    is_doctor = fields.Boolean(string="Is Doctor", default=False, tracking=True)
    doctor_reg_no = fields.Char(string="REG Number")
    doctor_certificate = fields.Binary(string="Certificate", attachment=True)
    doctor_certificate_filename = fields.Char(string="Certificate Filename")
    hao_activate_pharmacy = fields.Boolean(
        compute='_compute_hao_activate_pharmacy'
    )
    contact_type = fields.Selection(
        [
            ("customer", "Customer"),
            ("supplier", "Supplier"),
            ("both", "Both"),
            ("doctor", "Doctor"),
            ("none", "None"),
        ],
        compute="_compute_contact_type",
        store=True,
        string="Contact Type",
    )

    def _compute_hao_activate_pharmacy(self):
        for partner in self:
            company = partner.company_id or self.env.company
            partner.hao_activate_pharmacy = company.hao_activate_pharmacy

    @api.depends("is_customer", "is_supplier", "is_doctor")
    def _compute_contact_type(self):
        for partner in self:
            if partner.is_doctor:
                partner.contact_type = "doctor"
            elif partner.is_customer and partner.is_supplier:
                partner.contact_type = "both"
            elif partner.is_customer:
                partner.contact_type = "customer"
            elif partner.is_supplier:
                partner.contact_type = "supplier"
            else:
                partner.contact_type = "none"

    @api.model
    def _doctor_prefixed_name(self, name):
        name = " ".join((name or "").split())
        if not name:
            return name
        if name.casefold().startswith("dr "):
            return name
        return f"Dr {name}"

    def _apply_doctor_role_vals(self, vals):
        if vals.get("is_doctor"):
            vals["is_customer"] = False
            vals["is_supplier"] = False
            if vals.get("name"):
                vals["name"] = self._doctor_prefixed_name(vals["name"])
        elif vals.get("is_customer") or vals.get("is_supplier"):
            vals["is_doctor"] = False

    def _apply_partner_role_context(self, vals):
        """Apply defaults from Sales/Purchase role menus (customer, supplier, doctor)."""
        role = self.env.context.get("hao_partner_role")
        if role == "doctor":
            vals["is_doctor"] = True
            vals["is_customer"] = False
            vals["is_supplier"] = False
        elif role == "customer":
            vals["is_customer"] = True
            vals["is_supplier"] = False
            vals["is_doctor"] = False
            vals.setdefault("customer_rank", 1)
        elif role == "supplier":
            vals["is_supplier"] = True
            vals["is_customer"] = False
            vals["is_doctor"] = False
            vals.setdefault("supplier_rank", 1)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._raise_if_duplicate_for_values(vals)
            self._apply_partner_role_context(vals)
            self._apply_doctor_role_vals(vals)
            if (
                not vals.get("is_doctor")
                and "is_customer" not in vals
                and "is_supplier" not in vals
                and not self.env.context.get("hao_partner_role")
            ):
                vals.setdefault("is_customer", True)
            if self.env.context.get("from_sale_order") and self._is_enabled("auto_mark_customer_from_sales"):
                vals["is_customer"] = True
                vals["is_doctor"] = False
            if self.env.context.get("from_purchase_order") and self._is_enabled("auto_mark_supplier_from_purchase"):
                vals["is_supplier"] = True
                vals["is_doctor"] = False
                vals["supplier_rank"] = 1
        partners = super().create(vals_list)
        for partner, vals in zip(partners, vals_list):
            if vals.get("is_doctor") and partner.name:
                prefixed = partner._doctor_prefixed_name(partner.name)
                if prefixed != partner.name:
                    partner.name = prefixed
        return partners

    def write(self, vals):
        vals = dict(vals)
        self._apply_doctor_role_vals(vals)
        for partner in self:
            merged_vals = {
                "name": vals.get("name", partner.name),
                "email": vals.get("email", partner.email),
                "phone": vals.get("phone", partner.phone),
                "street": vals.get("street", partner.street),
                "city": vals.get("city", partner.city),
            }
            self._raise_if_duplicate_for_values(merged_vals, current_id=partner.id)
        if "is_supplier" in vals:
            if vals["is_supplier"]:
                vals["supplier_rank"] = max(1, max(self.mapped("supplier_rank")))
            elif all(p.supplier_rank == 1 for p in self):
                vals["supplier_rank"] = 0
        res = super().write(vals)
        if vals.get("is_doctor"):
            for partner in self.filtered("is_doctor"):
                prefixed = partner._doctor_prefixed_name(partner.name)
                if prefixed != partner.name:
                    super(ResPartner, partner).write({"name": prefixed})
        return res

    @api.constrains("is_customer", "is_supplier", "is_doctor")
    def _check_customer_or_supplier_required(self):
        for partner in self:
            if not partner.is_customer and not partner.is_supplier and not partner.is_doctor:
                raise ValidationError(
                    _("Select at least one role: customer, supplier, or doctor.")
                )

    @api.constrains("is_customer", "is_supplier", "is_doctor")
    def _check_doctor_exclusive(self):
        for partner in self:
            if partner.is_doctor and (partner.is_customer or partner.is_supplier):
                raise ValidationError(
                    _("A doctor cannot also be marked as customer or supplier. Clear customer and supplier first.")
                )

    @api.constrains("is_doctor", "doctor_reg_no")
    def _check_doctor_reg_no(self):
        for partner in self:
            if partner.is_doctor and not partner.doctor_reg_no:
                raise ValidationError(_("Doctors must have a REG Number."))

    @api.onchange("is_doctor")
    def _onchange_is_doctor(self):
        if self.is_doctor:
            self.is_customer = False
            self.is_supplier = False
            if self.name:
                self.name = self._doctor_prefixed_name(self.name)
        else:
            self.doctor_reg_no = False
            self.doctor_certificate = False
            self.doctor_certificate_filename = False

    @api.onchange("is_customer", "is_supplier")
    def _onchange_is_customer_supplier(self):
        if self.is_doctor and (self.is_customer or self.is_supplier):
            self.is_doctor = False
            self.doctor_reg_no = False
            self.doctor_certificate = False
            self.doctor_certificate_filename = False

    def _is_enabled(self, key, default="True"):
        return self.env["ir.config_parameter"].sudo().get_param(f"havano_all_in_one.{key}", default) == "True"

    def _normalize(self, value):
        return (value or "").strip().lower()

    def _normalize_name_key(self, value):
        return " ".join((value or "").split()).casefold()

    def _find_duplicate_candidate(self, data, current_id=False):
        domain = [("active", "in", [True, False])]
        if current_id:
            domain.append(("id", "!=", current_id))
        name = (data.get("name") or "").strip()
        email = self._normalize(data.get("email"))
        phone = self._normalize(data.get("phone"))
        street = self._normalize(data.get("street"))
        city = self._normalize(data.get("city"))

        if name and self._is_enabled("contact_check_name_exact"):
            normalized_input_name = self._normalize_name_key(name)
            candidates = self.search(domain + [("name", "=ilike", name)], limit=20)
            duplicate = next(
                (partner for partner in candidates if self._normalize_name_key(partner.name) == normalized_input_name),
                False,
            )
            if duplicate:
                return duplicate, _("Duplicate contact found by exact Name.")
        if email and self._is_enabled("contact_check_email_only"):
            duplicate = self.search(domain + [("email", "=ilike", email)], limit=1)
            if duplicate:
                return duplicate, _("Duplicate contact found by Email.")
        if name and email and self._is_enabled("contact_check_email_name"):
            duplicate = self.search(domain + [("name", "=ilike", name), ("email", "=ilike", email)], limit=1)
            if duplicate:
                return duplicate, _("Duplicate contact found by Name + Email.")
        if phone and self._is_enabled("contact_check_phone_only"):
            duplicate = self.search(domain + [("phone", "=ilike", phone)], limit=1)
            if duplicate:
                return duplicate, _("Duplicate contact found by Phone.")
        if name and phone and self._is_enabled("contact_check_phone_name"):
            duplicate = self.search(domain + [("name", "=ilike", name), ("phone", "=ilike", phone)], limit=1)
            if duplicate:
                return duplicate, _("Duplicate contact found by Name + Phone.")
        if name and street and city and self._is_enabled("contact_check_name_address"):
            duplicate = self.search(
                domain + [("name", "=ilike", name), ("street", "=ilike", street), ("city", "=ilike", city)],
                limit=1,
            )
            if duplicate:
                return duplicate, _("Duplicate contact found by Name + Address.")
        return False, False

    def _raise_if_duplicate_for_values(self, data, current_id=False):
        duplicate, reason = self._find_duplicate_candidate(data, current_id=current_id)
        if duplicate:
            action = self.env.ref("havano_all_in_one.action_hao_open_duplicate_partner")
            raise RedirectWarning(
                _("Duplicate Contact Detected.\n%(reason)s\nExisting contact: %(name)s")
                % {"reason": reason, "name": duplicate.display_name},
                action.id,
                _("View Duplicate"),
                {"active_ids": [duplicate.id], "active_id": duplicate.id},
            )
