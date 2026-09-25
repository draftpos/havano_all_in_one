import os
import glob

dirs = ['/root/odoo19-docker/addons/havano_all_in_one/data', '/root/odoo19-docker/addons/havano_all_in_one/reports']

for d in dirs:
    for filepath in glob.glob(os.path.join(d, '*.xml')):
        with open(filepath, 'r') as f:
            content = f.read()
        
        if 'invoice_format_editor' in content:
            content = content.replace('invoice_format_editor', 'havano_all_in_one')
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"Updated {filepath}")
