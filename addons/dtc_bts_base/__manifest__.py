{
    'name': 'Quản lý dự án BTS',
    'version': '1.0',
    'summary': 'Quản lý dự án và trạm BTS',
    'description': """
Quản lý dự án BTS
=================

Ứng dụng demo quản lý dự án triển khai trạm BTS:
- Dự án BTS dùng model project.project.
- Trạm BTS dùng model project.task.
- Một dự án có nhiều trạm.
- Đối tác dùng model res.partner và được phân loại theo vai trò nghiệp vụ.
""",
    'category': 'Operations',
    'author': 'MIS Group',
    'depends': [
        'base',
        'project',
        'mail',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/demo_user_data.xml',
        'data/demo_user_migration.xml',
        'data/sequence_data.xml',
        'data/project_stage_data.xml',
        'data/activity_type_data.xml',
        'data/mail_template_data.xml',
        'data/mail_queue_cron.xml',
        'data/dashboard_data.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
        'views/project_acceptance_views.xml',
        'views/res_partner_views.xml',
        'views/dashboard_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
