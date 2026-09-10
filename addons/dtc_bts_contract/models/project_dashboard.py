from odoo import models


class DtcBtsDashboard(models.Model):
    _inherit = 'dtc.bts.dashboard'

    def _get_dashboard_notifications(self):
        notifications = super()._get_dashboard_notifications()
        batch_model = self.env['bts.contract.signature.batch']
        if not batch_model.check_access_rights(
            'read',
            raise_exception=False,
        ):
            return notifications
        batches = batch_model.search([
            ('state', '=', 'done'),
            ('notification_user_ids', 'in', self.env.user.id),
        ], order='completed_date desc, id desc', limit=10)
        for batch in batches:
            phase_label = dict(batch._fields['phase'].selection).get(
                batch.phase,
                batch.phase,
            )
            notifications.append({
                'priority': 'green',
                'icon': '✓',
                'title': 'Batch hợp đồng đã ký đủ',
                'description': (
                    '%s · %s · %s hồ sơ đã hoàn tất.'
                    % (batch.project_id.display_name, phase_label, batch.line_count)
                ),
                'detail_url': (
                    '/web#id=%s&model=bts.contract.signature.batch&view_type=form'
                    % batch.id
                ),
                'detail_label': 'Xem batch',
                'action_url': (
                    '/dtc_bts_contract/signature_batch/%s/seen'
                    % batch.id
                ),
                'action_label': 'Đã xem',
            })
        return notifications
