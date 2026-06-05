from odoo import api, fields, models

class HavanoInvoiceTemplate(models.Model):
    _name = "havano.invoice.template"
    _description = "Havano Invoice Template"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    is_default = fields.Boolean(string="Default Template")
    note = fields.Text()

    # Layout fields
    base_layout = fields.Selection(
        selection=[('default', 'Default'),
                   ('modern', 'Modern'),
                   ('normal', 'Normal'),
                   ('old', 'Old Standard')],
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
                    self.document_layout_id = t
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
                else:
                    template.preview = False
            except Exception as e:
                template.preview = f"<div>Error generating preview: {str(e)}</div>"

    def action_apply_layout(self):
        self.ensure_one()
        self.env.company.base_layout = self.base_layout
        self.env.company.document_layout_id = self.id
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

