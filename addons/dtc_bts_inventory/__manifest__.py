{
    'name': 'Quản lý mua hàng và kho vật tư BTS',
    'version': '1.0',
    'summary': 'Mua hàng, nhập kho, cấp phát vật tư theo dự án BTS',
    'description': """
Quản lý mua hàng và kho vật tư BTS
==================================

- Liên kết đơn mua hàng với dự án BTS.
- Nhập kho vật tư theo dự án.
- Yêu cầu cấp phát vật tư theo dự án BTS.
- Xuất kho từ yêu cầu cấp phát.
- Bảng tổng hợp vật tư theo dự án.
""",
    'category': 'Operations',
    'author': 'MIS Group',
    'depends': [
        'dtc_bts_base',
        'purchase',
        'stock',
        'purchase_stock',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/activity_type_data.xml',
        'data/mail_template_migration.xml',
        'data/mail_template_data.xml',
        'data/product_category_data.xml',
        'data/uom_data.xml',
        'data/inventory_dashboard_data.xml',
        'data/demo_material_data.xml',
        'views/product_views.xml',
        'views/project_project_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
        'views/bts_material_request_views.xml',
        'views/inventory_dashboard_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
