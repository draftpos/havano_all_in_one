import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([])
    for company in companies:
        if company.account_price_include != "tax_included":
            company.account_price_include = "tax_included"
            _logger.info("Set tax price mode to included for company %s", company.display_name)
        if not company.hao_activate_pharmacy:
            company.hao_activate_pharmacy = True
            _logger.info("Activated pharmacy for company %s", company.display_name)
