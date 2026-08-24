from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class AccountReport(models.Model):
    _inherit = 'account.report'

    @api.model
    def _sync_soce_columns(self):
        """
        Synchronizes the Statement of Changes in Equity (SOCE) report columns
        based on the actual accounts of type 'equity' and 'unallocated_earnings'
        in the database.
        """
        soce_report = self.env.ref('havano_all_in_one.hao_statement_of_changes_in_equity_report', raise_if_not_found=False)
        if not soce_report:
            return
            
        _logger.info("Synchronizing SOCE dynamic columns...")
        
        # 1. Get all equity accounts
        equity_accounts = self.env['account.account'].search([
            ('account_type', 'in', ['equity', 'equity_unallocated'])
        ], order='code ASC')
        
        # 2. Existing columns in the report
        existing_columns = self.env['account.report.column'].search([
            ('report_id', '=', soce_report.id)
        ])
        
        # We need a Total column at the end
        expected_columns = []
        seq = 10
        for acc in equity_accounts:
            expected_columns.append({
                'name': acc.name,
                'expression_label': f'acc_{acc.id}',
                'sequence': seq,
                'account_id': acc.id
            })
            seq += 10
            
        expected_columns.append({
            'name': 'Total Equity',
            'expression_label': 'tot',
            'sequence': seq,
            'account_id': False
        })
        
        # 3. Create or update columns
        ColumnObj = self.env['account.report.column']
        
        active_labels = []
        for col_data in expected_columns:
            active_labels.append(col_data['expression_label'])
            col = existing_columns.filtered(lambda c: c.expression_label == col_data['expression_label'])
            if col:
                if col.name != col_data['name'] or col.sequence != col_data['sequence']:
                    col.write({
                        'name': col_data['name'],
                        'sequence': col_data['sequence']
                    })
            else:
                ColumnObj.create({
                    'name': col_data['name'],
                    'expression_label': col_data['expression_label'],
                    'sequence': col_data['sequence'],
                    'report_id': soce_report.id,
                })
                
        # 4. Remove columns that no longer exist
        cols_to_unlink = existing_columns.filtered(lambda c: c.expression_label not in active_labels)
        if cols_to_unlink:
            cols_to_unlink.unlink()
            
        # 5. Sync expressions on lines
        # Lines are: OPEN, PROFIT, MOVEMENTS, CLOSE
        lines = self.env['account.report.line'].search([
            ('report_id', '=', soce_report.id)
        ])
        
        ExprObj = self.env['account.report.expression']
        
        for line in lines:
            code = line.code # SOCE_OPEN, SOCE_PROFIT, SOCE_MOVEMENTS, SOCE_CLOSE
            if not code:
                continue
                
            # Date scopes based on line code
            date_scope_map = {
                'SOCE_OPEN': 'to_beginning_of_fiscalyear',
                'SOCE_PROFIT': 'strict_range',
                'SOCE_MOVEMENTS': 'strict_range',
                'SOCE_CLOSE': 'from_beginning'
            }
            date_scope = date_scope_map.get(code, 'strict_range')
            
            existing_exprs = ExprObj.search([('report_line_id', '=', line.id)])
            
            for col_data in expected_columns:
                label = col_data['expression_label']
                acc_id = col_data['account_id']
                
                # Check if expression exists
                expr = existing_exprs.filtered(lambda e: e.label == label)
                
                if label == 'tot':
                    # Total column sums all previous columns
                    sum_formula = " + ".join([f"{code}.{c['expression_label']}" for c in expected_columns if c['expression_label'] != 'tot'])
                    if not sum_formula:
                        sum_formula = "0"
                        
                    if expr:
                        if expr.formula != sum_formula:
                            expr.write({'formula': sum_formula})
                    else:
                        ExprObj.create({
                            'label': label,
                            'engine': 'aggregation',
                            'formula': sum_formula,
                            'report_line_id': line.id,
                        })
                else:
                    acc = self.env['account.account'].browse(acc_id)
                    domain = "[]"
                    
                    if code == 'SOCE_PROFIT':
                        if acc.account_type == 'equity_unallocated':
                            domain = "[('account_id.account_type', 'in', ['income', 'income_other', 'expense', 'expense_depreciation', 'expense_direct_cost'])]"
                    elif code == 'SOCE_MOVEMENTS':
                        if acc.account_type == 'equity_unallocated':
                            # Exclude P&L accounts from movements, they are handled in profit
                            domain = f"[('account_id', '=', {acc_id})]" 
                            # Wait, the unallocated earnings account itself has movements? 
                            # Yes, manual dividends or adjustments to retained earnings.
                        else:
                            domain = f"[('account_id', '=', {acc_id})]"
                    else:
                        # OPEN and CLOSE
                        if acc.account_type == 'equity_unallocated':
                            domain = f"['|', ('account_id', '=', {acc_id}), ('account_id.account_type', 'in', ['income', 'income_other', 'expense', 'expense_depreciation', 'expense_direct_cost'])]"
                        else:
                            domain = f"[('account_id', '=', {acc_id})]"

                    if expr:
                        if expr.formula != domain or expr.date_scope != date_scope or expr.subformula != '-sum':
                            expr.write({
                                'formula': domain,
                                'date_scope': date_scope,
                                'subformula': '-sum'
                            })
                    else:
                        ExprObj.create({
                            'label': label,
                            'engine': 'domain',
                            'formula': domain,
                            'subformula': '-sum',
                            'date_scope': date_scope,
                            'report_line_id': line.id,
                        })
            
            # Remove old expressions
            exprs_to_unlink = existing_exprs.filtered(lambda e: e.label not in active_labels)
            if exprs_to_unlink:
                exprs_to_unlink.unlink()
                
        _logger.info("SOCE dynamic columns synchronization completed.")
