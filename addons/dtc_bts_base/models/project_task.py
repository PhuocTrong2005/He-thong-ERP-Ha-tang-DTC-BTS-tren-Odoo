from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    _STATION_TO_PROJECT_STATE = {
        'survey': 'survey',
        'negotiating': 'in_progress',
        'contracted': 'approved',
        'construction': 'in_progress',
        'acceptance': 'in_progress',
        'station_lease_signed': 'in_progress',
        'handover': 'done',
        'operating': 'handed_over',
        'cancelled': 'cancelled',
    }

    station_code = fields.Char(
        string='Mã trạm BTS',
        required=True,
        copy=False,
        index=True,
        # See project.project.project_code: this default runs during schema
        # initialization and must not access the current user's language.
        default='Mới',
    )
    latitude = fields.Float(
        string='Vĩ độ',
        digits=(16, 8),
    )
    longitude = fields.Float(
        string='Kinh độ',
        digits=(16, 8),
    )
    site_address = fields.Char(string='Địa chỉ/Vị trí trạm')
    acceptance_date = fields.Date(string='Ngày nghiệm thu/Bàn giao')
    handover_state = fields.Selection(
        selection=[
            ('not_handed', 'Chưa bàn giao'),
            ('ready_to_handover', 'Sẵn sàng bàn giao'),
            ('handed', 'Đã bàn giao'),
            ('accepted', 'Đã tiếp nhận'),
        ],
        string='Trạng thái bàn giao',
        required=True,
        default='not_handed',
        tracking=True,
    )
    station_state = fields.Selection(
        selection=[
            ('survey', 'Khảo sát'),
            ('negotiating', 'Đàm phán'),
            (
                'contracted',
                'Đã kí hợp đồng thuê đất và biên bản đàm phán',
            ),
            ('construction', 'Thi công'),
            ('acceptance', 'Nghiệm thu'),
            ('station_lease_signed', 'Đã kí hợp đồng cho thuê trạm'),
            ('handover', 'Bàn giao hồ sơ'),
            ('operating', 'Vận hành'),
            # Legacy value kept last for existing records; not part of main flow.
            ('cancelled', 'Hủy'),
        ],
        string='Trạng thái trạm',
        required=True,
        default='survey',
        tracking=True,
    )
    assigned_user_id = fields.Many2one(
        comodel_name='res.users',
        string='KSGS phụ trách',
    )

    project_code_related = fields.Char(
        string='Mã dự án',
        related='project_id.project_code',
        store=True,
        readonly=True,
    )
    project_station_type = fields.Selection(
        string='Loại trạm',
        related='project_id.station_type',
        store=True,
        readonly=True,
    )
    project_province = fields.Char(
        string='Tỉnh/Thành phố',
        related='project_id.province',
        store=True,
        readonly=True,
    )
    project_district = fields.Char(
        string='Quận/Huyện',
        related='project_id.district',
        store=True,
        readonly=True,
    )
    project_commune = fields.Char(
        string='Xã/Phường',
        related='project_id.commune',
        store=True,
        readonly=True,
    )
    project_telecom_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Đối tác viễn thông',
        related='project_id.telecom_partner_id',
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        (
            'station_code_unique',
            'unique(station_code)',
            'Mã trạm BTS đã tồn tại. Vui lòng dùng mã khác.',
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('station_code') or vals.get('station_code') == _('Mới'):
                vals['station_code'] = self.env['ir.sequence'].next_by_code('dtc.bts.station') or _('Mới')
        tasks = super(
            ProjectTask,
            self.with_context(mail_auto_subscribe_no_notify=True),
        ).create(vals_list)
        tasks.project_id._sync_summary_from_stations()
        return tasks

    def write(self, vals):
        projects_before = self.project_id
        result = super().write(vals)
        if (
            {'project_id', 'station_state', 'acceptance_date'}.intersection(vals)
            and not self.env.context.get('bts_skip_project_summary_sync')
        ):
            (projects_before | self.project_id)._sync_summary_from_stations()
        return result

    def unlink(self):
        projects = self.project_id
        result = super().unlink()
        projects._sync_summary_from_stations()
        return result

    def _get_project_state_from_station_state(self, station_state):
        """Translate the detailed station workflow to the project workflow."""
        project_state = self._STATION_TO_PROJECT_STATE.get(station_state)
        if project_state == 'handed_over':
            available_states = dict(
                self.env['project.project']
                ._fields['state']._description_selection(self.env)
            )
            if project_state not in available_states:
                return 'done'
        return project_state

    @api.onchange('assigned_user_id')
    def _onchange_assigned_user_id(self):
        if self.assigned_user_id:
            self.user_ids = [(6, 0, [self.assigned_user_id.id])]

    @api.constrains('latitude', 'longitude')
    def _check_station_coordinates(self):
        for task in self:
            if task.latitude and not -90 <= task.latitude <= 90:
                raise ValidationError('Vĩ độ phải nằm trong khoảng từ -90 đến 90.')
            if task.longitude and not -180 <= task.longitude <= 180:
                raise ValidationError('Kinh độ phải nằm trong khoảng từ -180 đến 180.')


class ProjectProject(models.Model):
    _inherit = 'project.project'

    def _sync_summary_from_stations(self):
        """Keep project status and acceptance date derived from its stations."""
        for project in self.exists():
            stations = project.sudo().task_ids
            acceptance_dates = [
                acceptance_date
                for acceptance_date in stations.mapped('acceptance_date')
                if acceptance_date
            ]
            vals = {
                'acceptance_date': (
                    max(acceptance_dates) if acceptance_dates else False
                ),
            }
            station_states = set(stations.mapped('station_state'))
            if len(station_states) == 1:
                station_state = next(iter(station_states))
                project_state = (
                    self.env['project.task']
                    ._get_project_state_from_station_state(station_state)
                )
                if project_state:
                    vals['state'] = project_state
            changed_vals = {
                field_name: value
                for field_name, value in vals.items()
                if project[field_name] != value
            }
            if changed_vals:
                project.sudo().with_context(
                    bts_station_summary_sync=True,
                ).write(changed_vals)
