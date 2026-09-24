from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PharmacyDosage(models.Model):
    _name = "pharmacy.dosage"
    _description = "Pharmacy Dosage"
    _order = "code"

    code = fields.Char(string="Code", required=True)
    description = fields.Text(string="Description", required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("pharmacy_dosage_code_uniq", "unique(code)", "Dosage code must be unique."),
    ]

    def name_get(self):
        return [(rec.id, f"{rec.code} — {rec.description}" if rec.description else rec.code) for rec in self]

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
        args = list(args or [])
        if name:
            domain = ["|", ("code", operator, name), ("description", operator, name)]
            return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        return super()._name_search(name, args, operator, limit, name_get_uid)
