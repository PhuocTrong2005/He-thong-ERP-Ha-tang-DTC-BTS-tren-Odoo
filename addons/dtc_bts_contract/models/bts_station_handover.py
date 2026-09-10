from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class BtsStationHandover(models.Model):
    _name = 'bts.station.handover'
    _description = 'Hồ sơ bàn giao trạm BTS'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'handover_date desc, handover_code asc'

    # -------------------------------------------------------------------------
    # Fields định danh
    # -------------------------------------------------------------------------
    handover_code = fields.Char(
        string='Mã bàn giao',
        required=True,
        copy=False,
        index=True,
        default=lambda self: _('Mới'),
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Dự thảo'),
            ('handed_over', 'Đã bàn giao'),
            ('cancelled', 'Đã hủy'),
        ],
        string='Trạng thái',
        required=True,
        default='draft',
        tracking=True,
    )

    # -------------------------------------------------------------------------
    # Quan hệ
    # -------------------------------------------------------------------------
    station_id = fields.Many2one(
        comodel_name='project.task',
        string='Trạm BTS',
        required=True,
        index=True,
        ondelete='restrict',
        domain="[('project_id', '!=', False)]",
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Dự án',
        related='station_id.project_id',
        store=True,
        readonly=True,
    )
    handover_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người bàn giao',
        required=True,
        default=lambda self: self.env.uid,
        ondelete='restrict',
    )
    received_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người nhận',
        ondelete='restrict',
    )

    # -------------------------------------------------------------------------
    # Thông tin bàn giao
    # -------------------------------------------------------------------------
    handover_date = fields.Date(
        string='Ngày bàn giao',
        required=True,
        default=fields.Date.today,
        tracking=True,
    )
    checklist = fields.Text(
        string='Checklist hồ sơ',
        help='Danh sách hồ sơ cần bàn giao: hợp đồng thuê đất, biên bản nghiệm thu, ...',
    )
    notes = fields.Text(string='Ghi chú')

    # -------------------------------------------------------------------------
    # SQL Constraints
    # -------------------------------------------------------------------------
    _sql_constraints = [
        (
            'handover_code_unique',
            'unique(handover_code)',
            'Mã bàn giao đã tồn tại. Vui lòng dùng mã khác.',
        ),
        (
            'uq_handover_station',
            'unique(station_id)',
            'Mỗi trạm chỉ được có một hồ sơ bàn giao.',
        ),
    ]

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('handover_code') or vals.get('handover_code') == _('Mới'):
                vals['handover_code'] = (
                    self.env['ir.sequence'].next_by_code('dtc.bts.station.handover') or _('Mới')
                )
        return super().create(vals_list)

    # -------------------------------------------------------------------------
    # Actions chuyển trạng thái
    # -------------------------------------------------------------------------
    def action_handover(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError('Chỉ có thể bàn giao từ trạng thái Dự thảo.')
            rec.state = 'handed_over'
            # Cập nhật trạng thái trạm BTS thành Bàn giao
            if rec.station_id and hasattr(rec.station_id, 'handover_state'):
                rec.station_id.handover_state = 'handed'

    def action_cancel(self):
        for rec in self:
            if rec.state == 'handed_over':
                raise ValidationError('Không thể hủy hồ sơ đã bàn giao.')
            rec.state = 'cancelled'

    def action_reset_to_draft(self):
        for rec in self:
            if rec.state != 'cancelled':
                raise ValidationError('Chỉ có thể đặt lại về Dự thảo khi hồ sơ đã bị hủy.')
            rec.state = 'draft'
