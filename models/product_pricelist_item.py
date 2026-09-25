from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    uom_id = fields.Many2one("uom.uom", string="Unit of Measure")
    uom_barcode = fields.Char(string="UoM Barcode")

    @api.constrains("uom_id", "product_tmpl_id", "product_id")
    def _check_uom_compatibility(self):
        for rule in self:
            if not rule.uom_id:
                continue
            product = rule.product_id or rule.product_tmpl_id.product_variant_id
            if not product:
                continue
            rule_ref_uom = rule.uom_id
            while rule_ref_uom.relative_uom_id:
                rule_ref_uom = rule_ref_uom.relative_uom_id
                
            product_ref_uom = product.uom_id
            while product_ref_uom.relative_uom_id:
                product_ref_uom = product_ref_uom.relative_uom_id
                
            if rule_ref_uom != product_ref_uom:
                raise ValidationError(
                    _(
                        "UoM '%(uom)s' is not compatible with product default UoM '%(default)s'.",
                        uom=rule.uom_id.display_name,
                        default=product.uom_id.display_name,
                    )
                )
