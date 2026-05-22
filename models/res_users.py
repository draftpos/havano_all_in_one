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
    is_pharmacist = fields.Boolean(
        string="Pharmacist",
        default=False,
        help="Additional role for pharmacy workflows. Combine with User or Administrator.",
    )
    is_cashier = fields.Boolean(
        string="Cashier",
        default=False,
        help=(
            "Additional role for cashier / POS operations. "
            "Can be used alone without the User base role."
        ),
    )
    hao_cashier_only = fields.Boolean(
        string="Cashier-only account",
        default=False,
        copy=False,
        help="Internal flag: cashier role without User/Administrator base role.",
    )

    @api.constrains("is_pharmacist", "is_cashier", "share")
    def _check_role_combination(self):
        group_user = self.env.ref("base.group_user")
        group_system = self.env.ref("base.group_system")
        for user in self.filtered(lambda u: not u.share):
            if user.is_pharmacist and not (
                user.has_group("base.group_system")
                or user.has_group("base.group_user")
            ):
                raise ValidationError(
                    _(
                        "Pharmacist must be combined with the User or "
                        "Administrator role."
                    )
                )
            if user.active and not (
                user.is_cashier
                or user.is_pharmacist
                or user.has_group("base.group_user")
                or user.has_group("base.group_system")
            ):
                raise ValidationError(
                    _(
                        "Internal users need at least one role: User, "
                        "Administrator, Pharmacist, or Cashier."
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
        group_user = self.env.ref("base.group_user")
        group_system = self.env.ref("base.group_system")
        for user in self.filtered(lambda u: not u.share):
            if user.is_pharmacist and not (
                user.has_group("base.group_system")
                or user.role == "group_user"
            ):
                if not user.has_group("base.group_user") and user.role != "group_system":
                    raise ValidationError(
                        _(
                            "Pharmacist must be combined with the User or "
                            "Administrator role."
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
            cashier_only = user.hao_cashier_only or (
                user.is_cashier
                and not user.is_pharmacist
                and user.role not in ("group_user", "group_system")
            )
            if cashier_only:
                groups = cashier_group
            if groups != user.group_ids:
                user.with_context(havano_skip_addon_role_sync=True).sudo().write(
                    {"group_ids": [(6, 0, groups.ids)]}
                )

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for vals in vals_list:
            rec = dict(vals)
            if (
                rec.get("is_cashier")
                and not rec.get("is_pharmacist")
                and rec.get("role") in (False, None, "")
            ):
                rec["hao_cashier_only"] = True
            prepared.append(rec)
        users = super().create(prepared)
        users.filtered(lambda u: not u.share)._havano_apply_addon_roles()
        return users

    def write(self, vals):
        if self.env.context.get("havano_skip_addon_role_sync"):
            return super().write(vals)
        if (
            vals.get("is_cashier")
            and not vals.get("is_pharmacist")
            and vals.get("role") in (False, None, "")
        ):
            vals = dict(vals, hao_cashier_only=True)
        elif vals.get("role") in ("group_user", "group_system"):
            vals = dict(vals, hao_cashier_only=False)
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
            "cashier_only": bool(self.hao_cashier_only),
        }
