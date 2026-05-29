from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = "res.users"

    hao_enable_sales_automation = fields.Boolean(
        string="Enable sales automation",
        default=False,
    )
    hao_auto_confirm_quotation = fields.Boolean(
        string="Auto-confirm quotation",
        default=False,
    )
    hao_auto_create_invoice = fields.Boolean(
        string="Auto-create invoice",
        default=False,
    )
    hao_auto_post_invoice = fields.Boolean(
        string="Auto-post invoice",
        default=False,
    )
    hao_enable_purchase_automation = fields.Boolean(
        string="Enable purchase automation",
        default=False,
    )
    hao_auto_confirm_purchase = fields.Boolean(
        string="Auto-confirm purchase order",
        default=False,
    )
    hao_auto_validate_receipt = fields.Boolean(
        string="Auto-validate receipt",
        default=False,
    )
    hao_auto_create_vendor_bill = fields.Boolean(
        string="Auto-create vendor bill",
        default=False,
    )
    hao_auto_post_vendor_bill = fields.Boolean(
        string="Auto-post vendor bill",
        default=False,
    )
    is_pharmacist = fields.Boolean(
        string="Pharmacist",
        default=False,
        help="Additional pharmacy role. Requires User or Administrator.",
    )
    is_cashier = fields.Boolean(
        string="Cashier",
        default=False,
        help="Additional cashier / POS role. Requires User or Administrator.",
    )

    def _havano_has_base_role(self, user):
        return user.has_group("base.group_user") or user.has_group(
            "base.group_system"
        )

    @api.constrains("is_pharmacist", "is_cashier", "share")
    def _check_addon_roles_require_base(self):
        for user in self.filtered(lambda u: not u.share):
            if (user.is_pharmacist or user.is_cashier) and not self._havano_has_base_role(
                user
            ):
                raise ValidationError(
                    _(
                        "Pharmacist and Cashier must be used together with "
                        "the User or Administrator role."
                    )
                )

    def _havano_role_groups(self):
        return (
            self.env.ref("havano_all_in_one.group_havano_pharmacist"),
            self.env.ref("havano_all_in_one.group_havano_cashier"),
        )

    def _havano_apply_addon_roles(self):
        """Sync pharmacist / cashier booleans to security groups."""
        pharmacist_group, cashier_group = self._havano_role_groups()
        for user in self.filtered(lambda u: not u.share):
            if (user.is_pharmacist or user.is_cashier) and not self._havano_has_base_role(
                user
            ):
                raise ValidationError(
                    _(
                        "Pharmacist and Cashier must be used together with "
                        "the User or Administrator role."
                    )
                )
            groups = user.group_ids
            if user.is_pharmacist:
                groups |= pharmacist_group
            else:
                groups -= pharmacist_group
            if user.is_cashier:
                groups |= cashier_group
            else:
                groups -= cashier_group
            if groups != user.group_ids:
                user.with_context(havano_skip_addon_role_sync=True).sudo().write(
                    {"group_ids": [(6, 0, groups.ids)]}
                )

    def _havano_prepare_vals(self, vals, for_create=False):
        rec = dict(vals)
        if rec.get("is_pharmacist") or rec.get("is_cashier"):
            if rec.get("role") in (False, None, ""):
                if "role" in rec:
                    raise ValidationError(
                        _(
                            "Pharmacist and Cashier must be used together with "
                            "the User or Administrator role."
                        )
                    )
                if for_create:
                    rec["role"] = "group_user"
        return rec

    @api.model_create_multi
    def create(self, vals_list):
        prepared = [self._havano_prepare_vals(vals, for_create=True) for vals in vals_list]
        users = super().create(prepared)
        users.filtered(lambda u: not u.share)._havano_apply_addon_roles()
        return users

    def write(self, vals):
        if self.env.context.get("havano_skip_addon_role_sync"):
            return super().write(vals)
        vals = self._havano_prepare_vals(vals)
        res = super().write(vals)
        if {"is_pharmacist", "is_cashier", "role"}.intersection(vals):
            self.filtered(lambda u: not u.share)._havano_apply_addon_roles()
        return res

    def _havano_roles_payload(self):
        """Structured roles for API and integrations."""
        self.ensure_one()
        return {
            "role": self.role or False,
            "is_user": self.has_group("base.group_user"),
            "is_administrator": self.has_group("base.group_system"),
            "is_pharmacist": bool(self.is_pharmacist),
            "is_cashier": bool(self.is_cashier),
        }
