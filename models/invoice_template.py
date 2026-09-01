from odoo import api, fields, models

class HavanoInvoiceTemplate(models.Model):
    _name = "havano.invoice.template"
    _description = "Havano Invoice Template"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    is_default = fields.Boolean(string="Default Template")
    is_applied = fields.Boolean(
        string="Applied",
        compute="_compute_is_applied",
        inverse="_inverse_is_applied",
        search="_search_is_applied",
        help="Indicates whether this template is currently applied to the company."
    )
    note = fields.Text()

    @api.depends_context('company')
    def _compute_is_applied(self):
        current_layout_id = self.env.company.hao_document_layout_id.id
        current_base_layout = self.env.company.base_layout
        for rec in self:
            if current_layout_id:
                rec.is_applied = (rec.id == current_layout_id)
            else:
                rec.is_applied = (rec.base_layout == current_base_layout)

    def _inverse_is_applied(self):
        for rec in self:
            if rec.is_applied:
                rec.action_apply_layout()

    def _search_is_applied(self, operator, value):
        current_layout_id = self.env.company.hao_document_layout_id.id
        current_base_layout = self.env.company.base_layout
        if (operator == '=' and value) or (operator == '!=' and not value):
            if current_layout_id:
                return [('id', '=', current_layout_id)]
            return [('base_layout', '=', current_base_layout)]
        else:
            if current_layout_id:
                return [('id', '!=', current_layout_id)]
            return [('base_layout', '!=', current_base_layout)]

    # Layout fields
    def _get_base_layout_selection(self):
        selection = [
            ('default', 'Default'),
            ('modern', 'Modern'),
            ('normal', 'Normal'),
            ('old', 'Old Standard'),
            ('fresh', 'Fresh Company (Fiscal Tax Invoice)'),
            ('custom_fiscal', 'Seller Buyer Layout'),
            ('tripple_fresh', 'Tripple Fresh Letterhead'),
            ('puremetrix', 'Puremetrix Layout')
        ]
        if 'trucking.load' in self.env:
            selection.append(('trucking', 'Trucking (Fiscal Tax Invoice)'))
        return selection

    base_layout = fields.Selection(
        selection='_get_base_layout_selection',
        required=True, string="Base Layout", default="default")
    
    base_color = fields.Char(string="Base Color", default="#000000", help="Background color for the invoice")
    heading_text_color = fields.Char(string="Heading text Color", default="#ffffff", help="Heading Text color")
    text_color = fields.Char(string="Text Color", default="#000000", help="Text color of items")
    customer_text_color = fields.Char(string="Customer Text Color", default="#000000", help="Customer address text color")
    company_text_color = fields.Char(string="Company Text Color", default="#000000", help="Company address Text color")
    logo_position = fields.Selection([('left', 'Left'), ('right', 'Right')], string="Logo Position", default="left", help="Company logo position")
    tagline_position = fields.Selection([('left', 'Left'), ('right', 'Right')], string="Tagline Position", default="left", help="Company Tagline position")
    customer_position = fields.Selection([('left', 'Left'), ('right', 'Right')], string="Customer position", default="right", help="Customer address position")
    company_position = fields.Selection([('left', 'Left'), ('right', 'Right')], string="Company Address Position", default="left", help="Company address position")
    sales_person = fields.Boolean(string='Sales person', default=True, help="Sales Person of the layout")
    description = fields.Boolean(string='Description', default=True, help="Description of the layout")
    tax_value = fields.Boolean(string='Tax', default=True, help="Tax of the layout")
    reference = fields.Boolean(string='Customer Reference', default=True, help="Customer Reference")
    source = fields.Boolean(string='Source', default=False, help="Source Document of the layout")
    address = fields.Boolean(string='Address', default=True, help="Address of the document layout")
    city = fields.Boolean(string='City', default=True, help="City of the document layout")
    country = fields.Boolean(string='Country', default=True, help="Country of the document layout")
    vat = fields.Boolean(string='VAT', default=True, help='Customer vat id')

    preview = fields.Html(compute='_compute_preview', sanitize=False)

    @api.depends('base_layout', 'base_color', 'heading_text_color', 'text_color', 
                 'customer_text_color', 'company_text_color', 'logo_position', 
                 'tagline_position', 'customer_position', 'company_position',
                 'sales_person', 'description', 'tax_value', 'reference', 'source',
                 'address', 'city', 'country', 'vat')
    def _compute_preview(self):
        for template in self:
            class MockCompany:
                def __init__(self, t):
                    self.hao_document_layout_id = t
                    self.base_layout = t.base_layout
                    self.logo = False
                    self.name = "My Company"
                    self.company_details = "Company Details"
                    self.vat = "123456"
                    self.email = "info@company.com"
                    self.phone = "123456789"
                    self.website = "www.company.com"
                    self.report_header = "Report Header"
                    self.report_footer = "Report Footer"
                    self.external_report_layout_id = False
                    self.id = 1
                    self._fields = {}
                    self._name = "res.company"

            mock_company = MockCompany(template)

            values = {
                'company': mock_company,
                'is_html_empty': lambda v: not bool(v)
            }
            try:
                ir_ui_view = template.env['ir.ui.view']
                if template.base_layout == 'default':
                    template.preview = ir_ui_view._render_template('web.report_invoice_wizard_preview', values)
                elif template.base_layout == 'normal':
                    template.preview = ir_ui_view._render_template('havano_all_in_one.report_preview_normal', values)
                elif template.base_layout == 'modern':
                    template.preview = ir_ui_view._render_template('havano_all_in_one.report_preview_modern', values)
                elif template.base_layout == 'old':
                    template.preview = ir_ui_view._render_template('havano_all_in_one.report_preview_old', values)
                elif template.base_layout == 'fresh':
                    template.preview = "<div style='padding: 50px; text-align: center; color: #555; background: #fafafa; border-radius: 8px;'><h4>Preview not available here</h4><p>The Fresh Company layout requires a real invoice or quotation to accurately calculate inclusive taxes and line items. Please print a test document to see the exact design.</p></div>"
                elif template.base_layout == 'custom_fiscal':
                    template.preview = "<div style='padding: 50px; text-align: center; color: #555; background: #fafafa; border-radius: 8px;'><h4>Preview not available here</h4><p>The Seller Buyer Layout requires a real invoice. Please print a test document to see the exact design.</p></div>"
                elif template.base_layout == 'trucking':
                    template.preview = "<div style='padding: 50px; text-align: center; color: #555; background: #fafafa; border-radius: 8px;'><h4>Preview not available here</h4><p>The Trucking layout requires a real invoice linked to Trucking Loads to accurately display the load details and POD information. Please print a test document to see the exact design.</p></div>"
                elif template.base_layout == 'tripple_fresh':
                    template.preview = "<div style='padding: 50px; text-align: center; color: #555; background: #fafafa; border-radius: 8px;'><h4>Tripple Fresh Letterhead</h4><p>This layout uses a full-page custom letterhead background. Please print a test document to see the exact design.</p></div>"
                elif template.base_layout == 'puremetrix':
                    template.preview = "<div style='padding: 50px; text-align: center; color: #555; background: #fafafa; border-radius: 8px;'><h4>Puremetrix Layout</h4><p>This layout uses a custom Puremetrix header and footer. Please print a test document to see the exact design.</p></div>"
                else:
                    template.preview = False
            except Exception as e:
                template.preview = f"<div>Error generating preview: {str(e)}</div>"

    def action_apply_layout(self):
        self.ensure_one()
        self.env.company.base_layout = self.base_layout
        self.env.company.hao_document_layout_id = self.id
        if self.is_default:
            self.search([('id', '!=', self.id)]).write({'is_default': False})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Layout Applied',
                'message': f'Layout "{self.name}" has been applied to {self.env.company.name}.',
                'type': 'success',
                'sticky': False,
            }
        }

