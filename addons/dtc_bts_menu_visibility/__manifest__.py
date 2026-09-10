{
    'name': 'DTC BTS Menu Visibility',
    'version': '1.0',
    'summary': 'Giới hạn app switcher về các phân hệ DTC BTS',
    'category': 'DTC BTS',
    'author': 'MIS Group',
    'depends': [
        'dtc_bts_base',
        'dtc_bts_inventory',
        'dtc_bts_maintenance',
        'dtc_bts_contract',
        'account',
        'project_todo',
        'spreadsheet_dashboard',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/core_menu_visibility.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
