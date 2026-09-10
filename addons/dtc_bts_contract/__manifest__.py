{
    'name': 'Quản lý hợp đồng BTS',
    'version': '1.2',
    'summary': 'Quản lý hợp đồng thuê đất, hạ tầng và hồ sơ trạm BTS',
    'description': """
Quản lý hợp đồng BTS
====================
- Hợp đồng thuê đất và thuê hạ tầng.
- Biên bản đàm phán là hồ sơ ký số độc lập theo trạm.
- Luồng ký duyệt: Tổ hạ tầng lập hồ sơ → BGĐ xác thực OTP và ký số nội bộ.
- Gia hạn hợp đồng: Tổ hạ tầng thực hiện.
- Hồ sơ bàn giao trạm BTS.
- Nhắc hạn hợp đồng qua mail.activity.
""",
    'category': 'Operations',
    'author': 'MIS Group',
    'depends': ['dtc_bts_base', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/dashboard_data.xml',
        'data/demo_user_data.xml',
        'data/demo_user_migration.xml',
        'data/activity_type_data.xml',
        'data/mail_template_migration.xml',
        'data/mail_template_data.xml',
        'data/mail_template_workflow_data.xml',
        'data/contract_due_cron.xml',
        'views/bts_contract_views.xml',
        'views/bts_contract_renewal_views.xml',
        'views/bts_negotiation_minutes_views.xml',
        'views/bts_station_handover_views.xml',
        'views/bts_contract_signature_batch_views.xml',
        'views/project_contract_views.xml',
        'views/bts_dashboard_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
