from odoo import _, api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("product_id", "order_id.pricelist_id")
    def _compute_allowed_uom_ids(self):
        super()._compute_allowed_uom_ids()
        for line in self:
            if not line.product_id or not line.product_id.product_tmpl_id.allow_multi_uom or not line.order_id.pricelist_id:
                continue
            rules = self.env["product.pricelist.item"].search(
                [
                    ("pricelist_id", "=", line.order_id.pricelist_id.id),
                    ("uom_id", "!=", False),
                    ("applied_on", "in", ["0_product_variant", "1_product", "2_product_category", "3_global"]),
                    "|",
                    ("product_id", "=", line.product_id.id),
                    "|",
                    ("product_tmpl_id", "=", line.product_id.product_tmpl_id.id),
                    "|",
                    ("categ_id", "=", line.product_id.categ_id.id),
                    ("categ_id", "=", False),
                ]
            )
            line.allowed_uom_ids = (line.allowed_uom_ids | rules.mapped("uom_id")).sorted()

    def _get_uom_specific_pricelist_price(self):
        self.ensure_one()
        if not self.order_id.pricelist_id or not self.product_id or not self.product_uom_id:
            return False
        pricelist = self.order_id.pricelist_id
        product = self.product_id
        qty = self.product_uom_qty or 1.0
        rule = self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", pricelist.id),
                ("uom_id", "=", self.product_uom_id.id),
                ("applied_on", "in", ["0_product_variant", "1_product", "2_product_category", "3_global"]),
                "|",
                ("product_id", "=", product.id),
                "|",
                ("product_tmpl_id", "=", product.product_tmpl_id.id),
                "|",
                ("categ_id", "=", product.categ_id.id),
                ("categ_id", "=", False),
                "|",
                ("min_quantity", "=", 0.0),
                ("min_quantity", "<=", qty),
            ],
            order="applied_on, min_quantity desc, id desc",
            limit=1,
        )
        if rule and rule.compute_price == "fixed":
            return rule.fixed_price
        return False

    @api.depends("product_id", "product_uom_id", "product_uom_qty", "order_id.pricelist_id")
    def _compute_price_unit(self):
        super()._compute_price_unit()
        for line in self:
            if not line.product_id or not line.product_uom_id or not line.order_id.pricelist_id or line.display_type:
                continue
            if not line.product_id.product_tmpl_id.allow_multi_uom:
                continue
            price = line._get_uom_specific_pricelist_price()
            if price is not False:
                line.price_unit = price

    @api.onchange("product_uom_id")
    def _onchange_product_uom_id(self):
        if self.product_id and self.product_uom_id and self.order_id.pricelist_id:
            self._compute_price_unit()

    @api.onchange("product_id")
    def _onchange_product_id(self):
        res = super()._onchange_product_id()
        if not self.product_id:
            return res
        template = self.product_id.product_tmpl_id
        if template.allow_multi_uom and template.strict_uom_tracking:
            self.product_uom_id = False
            return {
                "warning": {
                    "title": _("UoM Selection Required"),
                    "message": _(
                        "Strict UoM tracking is enabled for this product. "
                        "Please select the Unit of Measure before proceeding."
                    ),
                }
            }
        if template.allow_multi_uom:
            self.product_uom_id = self.product_id.uom_id
        return res
