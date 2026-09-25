import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    duplicate_menu = env.ref(
        "havano_all_in_one.menu_hao_sale_customers", raise_if_not_found=False
    )
    if duplicate_menu:
        duplicate_menu.unlink()
    companies = env["res.company"].search([])
    for company in companies:
       
        if not company.hao_activate_pharmacy:
            company.hao_activate_pharmacy = True
            _logger.info("Activated pharmacy for company %s", company.display_name)
