from odoo import _, fields, models
from odoo.exceptions import AccessError


class BtsMaterialNotification(models.Model):
    _name = 'bts.material.notification'
    _description = 'Thông báo vật tư BTS'
    _order = 'create_date desc, id desc'

    request_id = fields.Many2one(
        comodel_name='bts.material.request',
        string='Yêu cầu vật tư',
        required=True,
        ondelete='cascade',
        index=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Người nhận',
        required=True,
        ondelete='cascade',
        index=True,
    )
    message = fields.Char(string='Nội dung', required=True)
    notification_type = fields.Selection(
        selection=[
            ('approval', 'Chờ phê duyệt'),
            ('incoming', 'Chờ nhập kho'),
            ('ready', 'Sẵn sàng cấp phát'),
            ('lock_po', 'Chờ khóa PO'),
        ],
        required=True,
        default='ready',
    )
    is_seen = fields.Boolean(string='Đã xem', default=False, index=True)
    seen_date = fields.Datetime(string='Thời điểm xem', readonly=True)

    _sql_constraints = [
        (
            'request_user_type_unique',
            'unique(request_id, user_id, notification_type)',
            'Thông báo cho yêu cầu và người dùng này đã tồn tại.',
        ),
    ]

    def action_mark_seen(self):
        broad_groups = (
            'base.group_system',
            'dtc_bts_base.group_dtc_bts_pkh',
            'dtc_bts_base.group_dtc_bts_warehouse',
        )
        can_manage = any(
            self.env.user.has_group(group) for group in broad_groups
        )
        for notification in self:
            if notification.user_id != self.env.user and not can_manage:
                raise AccessError(_('Bạn không có quyền xử lý thông báo này.'))
        self.write({
            'is_seen': True,
            'seen_date': fields.Datetime.now(),
        })
        return True
