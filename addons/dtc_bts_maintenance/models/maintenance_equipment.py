from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    _BTS_MAINTENANCE_REMINDER_DAYS = 3
    _BTS_MAINTENANCE_ACTIVITY_MARKER = 'DTC_BTS_MAINTENANCE_DUE'

    station_id = fields.Many2one(
        comodel_name='project.task',
        string='Trạm BTS',
        index=True,
        tracking=True,
    )
    bts_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Dự án BTS',
        related='station_id.project_id',
        store=True,
        readonly=True,
    )
    station_code = fields.Char(
        string='Mã trạm',
        related='station_id.station_code',
        store=True,
        readonly=True,
    )
    station_type = fields.Selection(
        string='Loại trạm',
        related='station_id.project_id.station_type',
        store=True,
        readonly=True,
    )
    next_action_date = fields.Date(
        string='Ngày bảo trì tiếp theo',
        tracking=True,
    )
    bts_state = fields.Selection(
        selection=[
            ('active', 'Đang quản lý'),
            ('inactive', 'Ngừng quản lý'),
        ],
        string='Trạng thái quản lý',
        required=True,
        default='active',
        tracking=True,
    )
    last_repair_date = fields.Date(
        string='Ngày sửa chữa gần nhất',
        readonly=True,
        tracking=True,
    )
    last_repair_note = fields.Text(
        string='Kết quả sửa chữa gần nhất',
        readonly=True,
    )
    bts_due_mail_next_action_date = fields.Date(
        string='Kỳ bảo trì đã tạo email nhắc',
        readonly=True,
        copy=False,
    )

    _sql_constraints = [
        (
            'station_id_unique',
            'unique(station_id)',
            'Mỗi trạm BTS chỉ được có một hồ sơ thiết bị bảo trì.',
        ),
    ]

    def _raise_if_station_already_has_equipment(self, station_ids, excluded_ids=None):
        station_ids = [station_id for station_id in station_ids if station_id]
        if not station_ids:
            return
        if len(station_ids) != len(set(station_ids)):
            raise ValidationError(
                'Mỗi trạm BTS chỉ được có một hồ sơ thiết bị bảo trì.'
            )
        domain = [('station_id', 'in', station_ids)]
        if excluded_ids:
            domain.append(('id', 'not in', excluded_ids))
        if self.sudo().search_count(domain):
            raise ValidationError(
                'Mỗi trạm BTS chỉ được có một hồ sơ thiết bị bảo trì.'
            )

    def _get_station_equipment_values(self, station):
        project_acceptance_date = station.project_id.acceptance_date
        if not project_acceptance_date:
            raise ValidationError(
                'Dự án của trạm %s chưa có ngày nghiệm thu.'
                % station.display_name
            )
        name_parts = [part for part in (station.station_code, station.name) if part]
        return {
            'name': ' - '.join(name_parts),
            'effective_date': project_acceptance_date,
        }

    @api.onchange('station_id')
    def _onchange_station_id(self):
        if self.station_id:
            values = self._get_station_equipment_values(self.station_id)
            self.name = values['name']
            self.effective_date = values['effective_date']

    @api.model_create_multi
    def create(self, vals_list):
        self._raise_if_station_already_has_equipment(
            [vals.get('station_id') for vals in vals_list]
        )
        prepared_vals_list = []
        for vals in vals_list:
            prepared_vals = dict(vals)
            if prepared_vals.get('station_id'):
                station = self.env['project.task'].browse(prepared_vals['station_id'])
                station_values = self._get_station_equipment_values(station)
                if not prepared_vals.get('name'):
                    prepared_vals['name'] = station_values['name']
                prepared_vals['effective_date'] = station_values['effective_date']
            prepared_vals_list.append(prepared_vals)
        equipment = super().create(prepared_vals_list)
        equipment._schedule_bts_maintenance_activity()
        return equipment

    def write(self, vals):
        prepared_vals = dict(vals)
        must_reschedule = bool(
            {'next_action_date', 'bts_state', 'technician_user_id', 'active'}
            & set(prepared_vals)
        )
        if prepared_vals.get('station_id'):
            if len(self) > 1:
                raise ValidationError(
                    'Mỗi trạm BTS chỉ được có một hồ sơ thiết bị bảo trì.'
                )
            self._raise_if_station_already_has_equipment(
                [prepared_vals['station_id']],
                excluded_ids=self.ids,
            )
            station = self.env['project.task'].browse(prepared_vals['station_id'])
            station_values = self._get_station_equipment_values(station)
            if 'name' not in prepared_vals:
                prepared_vals['name'] = station_values['name']
            prepared_vals['effective_date'] = station_values['effective_date']
        result = super().write(prepared_vals)
        if (
            'next_action_date' in prepared_vals
            and not self.env.context.get('bts_sync_project_due_date')
        ):
            projects = self.mapped('bts_project_id')
            siblings = self.sudo().search([
                ('bts_project_id', 'in', projects.ids),
                ('id', 'not in', self.ids),
                ('active', '=', True),
                ('bts_state', '=', 'active'),
            ])
            siblings.with_context(bts_sync_project_due_date=True).write({
                'next_action_date': prepared_vals['next_action_date'],
            })
        if must_reschedule:
            self._clear_bts_maintenance_activities()
            self._schedule_bts_maintenance_activity()
        return result

    def _bts_maintenance_activity_domain(self):
        self.ensure_one()
        return [
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('note', 'ilike', self._BTS_MAINTENANCE_ACTIVITY_MARKER),
        ]

    def _clear_bts_maintenance_activities(self):
        activity_model = self.env['mail.activity'].sudo()
        for equipment in self:
            activity_model.search(
                equipment._bts_maintenance_activity_domain()
            ).unlink()

    def _get_bts_maintenance_responsible_users(self):
        self.ensure_one()
        if self.technician_user_id and self.technician_user_id.active:
            return self.technician_user_id
        infrastructure_group = self.env.ref(
            'dtc_bts_base.group_dtc_bts_infrastructure',
            raise_if_not_found=False,
        )
        users = (
            infrastructure_group.users.filtered(lambda user: user.active)
            if infrastructure_group
            else self.env['res.users']
        )
        return users or self.env.user

    def _schedule_bts_maintenance_activity(self, queue_email=True):
        today = fields.Date.context_today(self)
        reminder_limit = today + timedelta(
            days=self._BTS_MAINTENANCE_REMINDER_DAYS
        )
        activity_type = self.env.ref(
            'mail.mail_activity_data_todo',
            raise_if_not_found=False,
        )
        if not activity_type:
            return
        activity_model = self.env['mail.activity'].sudo()
        for equipment in self.filtered(
            lambda item: (
                item.active
                and item.bts_state == 'active'
                and item.next_action_date
                and item.next_action_date <= reminder_limit
            )
        ):
            reminder_date = equipment.next_action_date - timedelta(
                days=self._BTS_MAINTENANCE_REMINDER_DAYS
            )
            if reminder_date < today:
                reminder_date = today
            for user in equipment._get_bts_maintenance_responsible_users():
                existing = activity_model.search(
                    equipment._bts_maintenance_activity_domain()
                    + [('user_id', '=', user.id)],
                    limit=1,
                )
                if existing:
                    continue
                # Keep the maintenance task in Odoo without sending Odoo's
                # generic activity-assignment email. The configured BTS HTML
                # reminder is delivered separately.
                equipment.with_context(
                    mail_activity_quick_update=True,
                ).activity_schedule(
                    activity_type_id=activity_type.id,
                    date_deadline=reminder_date,
                    summary=_('Bảo trì trạm BTS sắp đến hạn'),
                    note=_(
                        '[%(marker)s] Trạm %(station)s cần được bảo trì vào '
                        'ngày %(date)s.',
                        marker=self._BTS_MAINTENANCE_ACTIVITY_MARKER,
                        station=equipment.station_id.display_name
                        or equipment.display_name,
                        date=equipment.next_action_date.strftime('%d/%m/%Y'),
                    ),
                    user_id=user.id,
                )
            if queue_email:
                equipment._queue_bts_maintenance_due_email()

    def _get_bts_maintenance_email_users(self):
        self.ensure_one()
        if self.technician_user_id and self.technician_user_id.active:
            return self.technician_user_id
        group = self.env.ref(
            'dtc_bts_base.group_dtc_bts_infrastructure',
            raise_if_not_found=False,
        )
        return (
            group.users.filtered(lambda user: user.active)
            if group
            else self.env['res.users']
        )

    def _queue_bts_maintenance_due_email(self):
        self.ensure_one()
        if (
            not self.next_action_date
            or self.bts_due_mail_next_action_date == self.next_action_date
        ):
            return self.env['mail.mail']
        return self._bts_queue_workflow_email(
            'dtc_bts_maintenance.mail_template_maintenance_due_reminder',
            self._get_bts_maintenance_email_users(),
            'maintenance_due_reminder',
            marker_values={
                'bts_due_mail_next_action_date': self.next_action_date,
            },
            extra_context={
                'maintenance_type': _('Bảo trì định kỳ'),
                'responsible_name': (
                    self.technician_user_id.display_name or ''
                ),
            },
        )

    @api.model
    def _cron_schedule_bts_maintenance_activities(self):
        today = fields.Date.context_today(self)
        reminder_limit = today + timedelta(
            days=self._BTS_MAINTENANCE_REMINDER_DAYS
        )
        equipment = self.search([
            ('active', '=', True),
            ('bts_state', '=', 'active'),
            ('station_id', '!=', False),
            ('next_action_date', '!=', False),
            ('next_action_date', '<=', reminder_limit),
        ])
        equipment._schedule_bts_maintenance_activity(queue_email=False)
        equipment._queue_bts_maintenance_due_digests()

    def _queue_bts_maintenance_due_digests(self):
        pending = self.filtered(
            lambda item: (
                item.next_action_date
                and item.bts_due_mail_next_action_date
                != item.next_action_date
            )
        )
        users = self.env['res.users']
        for equipment in pending:
            users |= equipment._get_bts_maintenance_email_users()
        for user in users.filtered(lambda item: item.active):
            user_equipment = pending.filtered(
                lambda item: (
                    user in item._get_bts_maintenance_email_users()
                    and item._bts_user_can_read_activity_record(user)
                )
            )
            if not user_equipment:
                continue
            projects = []
            for project in user_equipment.mapped('bts_project_id'):
                project_equipment = user_equipment.filtered(
                    lambda item: item.bts_project_id == project
                )
                projects.append({
                    'name': project.display_name,
                    'code': project.project_code,
                    'due_date': min(
                        project_equipment.mapped('next_action_date')
                    ),
                    'stations': ', '.join(
                        project_equipment.mapped('station_id.display_name')
                    ),
                })
            representative = user_equipment[0]
            mails = representative._bts_queue_workflow_email(
                'dtc_bts_maintenance.'
                'mail_template_maintenance_due_digest',
                user,
                'maintenance_due_digest',
                extra_context={'digest_projects': projects},
            )
            if mails:
                for equipment in user_equipment:
                    equipment.sudo().write({
                        'bts_due_mail_next_action_date':
                            equipment.next_action_date,
                    })
