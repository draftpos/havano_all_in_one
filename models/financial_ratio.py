from odoo import models, fields, api

class HavanoFinancialRatio(models.Model):
    _name = 'havano.financial.ratio'
    _description = 'Financial Ratios'
    
    name = fields.Char(string='Ratio Name', required=True)
    category = fields.Selection([
        ('inv', 'Investment Ratios'),
        ('sol', 'Solvency Ratios'),
        ('liq', 'Liquidity Ratios'),
        ('eff', 'Efficiency Ratios'),
        ('prof', 'Profitability Ratios')
    ], string='Category', required=True)
    value = fields.Float(string='Value', required=True, digits=(16, 2))
    
    @api.model
    def action_compute_and_open_ratios(self, category):
        # Delete existing ratios for this user in this category
        self.search([
            ('create_uid', '=', self.env.user.id),
            ('category', '=', category)
        ]).unlink()
        
        # Calculate the base components (using all posted moves)
        def get_bal(domain):
            res = self.env['account.move.line'].search_read(
                [('parent_state', '=', 'posted')] + domain,
                ['balance']
            )
            return sum(r['balance'] for r in res)
            
        # Common aggregates
        net_profit = -get_bal([('account_id.internal_group', 'in', ['income', 'expense'])])
        revenue = -get_bal([('account_id.internal_group', '=', 'income')])
        cost_of_sales = get_bal([('account_id.account_type', '=', 'expense_direct_cost')])
        gross_profit = revenue - cost_of_sales
        op_expense = get_bal([('account_id.account_type', 'in', ['expense_depreciation', 'expense'])])
        op_profit = gross_profit - op_expense
        ebitda = op_profit # Simplified for this demo
        
        total_assets = get_bal([('account_id.internal_group', '=', 'asset')])
        total_liabilities = -get_bal([('account_id.internal_group', '=', 'liability')])
        total_equity = -get_bal([('account_id.internal_group', '=', 'equity')])
        
        current_assets = get_bal([('account_id.account_type', 'in', ['asset_cash', 'asset_current', 'asset_receivable', 'asset_prepayments'])])
        current_liabilities = -get_bal([('account_id.account_type', 'in', ['liability_current', 'liability_payable'])])
        
        cash = get_bal([('account_id.account_type', '=', 'asset_cash')])
        inventory = get_bal([('account_id.account_type', '=', 'asset_current'), ('account_id.name', 'ilike', 'inventory')])
        
        # Mocking averages by just using the current balance (since calculating opening balance dynamically is complex without a date range filter)
        avg_equity = total_equity or 1.0
        avg_assets = total_assets or 1.0
        avg_capital_employed = (total_assets - current_liabilities) or 1.0
        avg_invested_capital = (total_equity + current_liabilities - cash) or 1.0
        
        finance_costs = get_bal([('account_id.account_type', '=', 'expense'), ('account_id.name', 'ilike', 'interest')]) or 1.0
        
        op_cash_flow = cash
        debt_repayments = get_bal([('account_id.account_type', 'in', ['liability_non_current', 'liability_current']), ('account_id.name', 'ilike', 'loan')])
        
        eps = 5.0 # Mock value since it requires external input
        market_price = 50.0 # Mock value since it requires external input
        
        # Populate based on category
        ratios = []
        if category == 'inv':
            ratios = [
                ('ROE - Return on Equity (%)', (net_profit / avg_equity) * 100),
                ('ROCE - Return on Capital Employed (%)', (op_profit / avg_capital_employed) * 100),
                ('ROA - Return on Assets (%)', (net_profit / avg_assets) * 100),
                ('Cash ROI - Cash Return on Investment (%)', (op_cash_flow / avg_invested_capital) * 100),
                ('Earnings Yield (%)', (eps / market_price) * 100 if market_price else 0)
            ]
        elif category == 'sol':
            ratios = [
                ('Debt-to-Equity Ratio', total_liabilities / avg_equity),
                ('Debt-to-Asset Ratio', total_liabilities / avg_assets),
                ('Interest Coverage Ratio', op_profit / finance_costs),
                ('DSCR - Debt Service Coverage Ratio', op_profit / (debt_repayments or 1.0))
            ]
        elif category == 'liq':
            ratios = [
                ('Current Ratio', current_assets / (current_liabilities or 1.0)),
                ('Quick Ratio (Acid Test)', (current_assets - inventory) / (current_liabilities or 1.0)),
                ('Cash Ratio', cash / (current_liabilities or 1.0)),
                ('NWC - Net Working Capital', current_assets - current_liabilities)
            ]
        elif category == 'eff':
            ratios = [
                ('Asset Turnover Ratio', revenue / avg_assets),
                ('Inventory Turnover Ratio', cost_of_sales / (inventory or 1.0)),
                ('Receivables Turnover Ratio', revenue / avg_assets), # Simplified
                ('Payables Turnover Ratio', cost_of_sales / (current_liabilities or 1.0))
            ]
        elif category == 'prof':
            ratios = [
                ('Gross Profit Margin (%)', (gross_profit / (revenue or 1.0)) * 100),
                ('Operating Profit Margin (%)', (op_profit / (revenue or 1.0)) * 100),
                ('Net Profit Margin (%)', (net_profit / (revenue or 1.0)) * 100),
                ('EBITDA Margin (%)', (ebitda / (revenue or 1.0)) * 100)
            ]
            
        records = []
        for name, val in ratios:
            records.append({
                'name': name,
                'category': category,
                'value': val
            })
            
        self.create(records)
        
        # Return action
        menu_name_map = {
            'inv': 'Investment Ratios',
            'sol': 'Solvency Ratios',
            'liq': 'Liquidity Ratios',
            'eff': 'Efficiency Ratios',
            'prof': 'Profitability Ratios'
        }
        
        return {
            'type': 'ir.actions.act_window',
            'name': menu_name_map.get(category, 'Financial Ratios'),
            'res_model': 'havano.financial.ratio',
            'view_mode': 'list',
            'domain': [('category', '=', category), ('create_uid', '=', self.env.user.id)],
            'context': {'create': False, 'edit': False, 'delete': False}
        }
