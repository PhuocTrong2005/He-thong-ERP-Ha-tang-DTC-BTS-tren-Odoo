from odoo import models


class DtcBtsProjectDashboard(models.Model):
    _inherit = 'dtc.bts.dashboard'

    def _get_dashboard_notifications(self):
        notifications = list(super()._get_dashboard_notifications())
        notification_model = self.env['bts.material.notification']
        if not notification_model.check_access_rights(
            'read',
            raise_exception=False,
        ):
            return notifications
        material_notifications = notification_model.search([
            ('user_id', '=', self.env.user.id),
            ('notification_type', '=', 'ready'),
            ('is_seen', '=', False),
            ('request_id.state', 'not in', ('issued', 'cancelled', 'rejected')),
        ], order='create_date desc, id desc', limit=20)

        notifications.extend({
            'priority': 'green',
            'icon': '✓',
            'title': 'Vật tư sẵn sàng cấp phát',
            'description': notification.message,
            'detail_url': (
                f'/web#id={notification.request_id.id}'
                '&model=bts.material.request&view_type=form'
            ),
            'detail_label': 'Xem yêu cầu',
            'action_url': (
                '/dtc_bts_inventory/notification/'
                f'{notification.id}/seen'
            ),
            'action_label': 'Đã xem',
        } for notification in material_notifications)
        return notifications
