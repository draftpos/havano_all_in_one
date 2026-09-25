"""
Pre-migration script: Add new columns to res_company added in version 1.0.10.
"""


def migrate(cr, version):
    cr.execute("""
        ALTER TABLE res_company
        ADD COLUMN IF NOT EXISTS hao_custom_balance_sheet_format boolean DEFAULT false;
    """)
    cr.execute("""
        ALTER TABLE res_company
        ADD COLUMN IF NOT EXISTS hao_custom_pnl_format boolean DEFAULT false;
    """)
    cr.execute("""
        ALTER TABLE res_company
        ADD COLUMN IF NOT EXISTS custom_vat varchar;
    """)
    cr.execute("""
        ALTER TABLE res_company
        ADD COLUMN IF NOT EXISTS custom_tin varchar;
    """)
    cr.execute("""
        ALTER TABLE account_account
        ADD COLUMN IF NOT EXISTS hao_custom_category varchar;
    """)
