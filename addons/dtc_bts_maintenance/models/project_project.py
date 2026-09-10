from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    state = fields.Selection(
        selection_add=[('handed_over', 'Hoàn tất bàn giao')],
        ondelete={'handed_over': 'set default'},
    )
    project_completed_mail_sent_at = fields.Datetime(
        string='Email hoàn tất dự án đã tạo lúc',
        readonly=True,
        copy=False,
    )
    maintenance_handover_mail_sent_at = fields.Datetime(
        string='Email bàn giao hạ tầng đã tạo lúc',
        readonly=True,
        copy=False,
    )
    maintenance_accepted_mail_sent_at = fields.Datetime(
        string='Email tiếp nhận bàn giao đã tạo lúc',
        readonly=True,
        copy=False,
    )
    maintenance_handover_state = fields.Selection(
        selection=[
            ('none', 'Chưa bàn giao'),
            ('pending', 'Chờ Tổ hạ tầng tiếp nhận'),
            ('accepted', 'Đã tiếp nhận bảo trì'),
        ],
        string='Trạng thái bàn giao bảo trì',
        required=True,
        default='none',
        tracking=True,
        copy=False,
    )
    maintenance_handover_date = fields.Date(
        string='Ngày bàn giao bảo trì',
        copy=False,
    )
    maintenance_handover_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người bàn giao bảo trì',
        copy=False,
    )
    maintenance_accepted_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người tiếp nhận bảo trì',
        copy=False,
    )
    maintenance_accepted_date = fields.Date(
        string='Ngày tiếp nhận bảo trì',
        copy=False,
    )
    bts_maintenance_due = fields.Boolean(
        string='Đến hạn bảo trì',
        compute='_compute_bts_maintenance_due',
        search='_search_bts_maintenance_due',
    )
    bts_maintenance_equipment_ids = fields.One2many(
        comodel_name='maintenance.equipment',
        inverse_name='bts_project_id',
        string='Hồ sơ thiết bị bảo trì',
    )
    bts_maintenance_batch_ids = fields.One2many(
        comodel_name='bts.maintenance.batch',
        inverse_name='project_id',
        string='Phiếu bảo trì dự án',
    )
    maintenance_next_due_date = fields.Date(
        string='Ngày bảo trì gần nhất',
        compute='_compute_maintenance_summary',
        store=True,
    )
    maintenance_equipment_count = fields.Integer(
        string='Số hồ sơ thiết bị',
        compute='_compute_maintenance_summary',
        store=True,
    )
    maintenance_open_batch_count = fields.Integer(
        string='Phiếu bảo trì đang mở',
        compute='_compute_maintenance_summary',
        store=True,
    )

    def write(self, vals):
        protected_handover_fields = {
            'maintenance_handover_state',
            'maintenance_handover_date',
            'maintenance_handover_by_id',
            'maintenance_accepted_by_id',
            'maintenance_accepted_date',
        }
        if (
            not self.env.su
            and (
                protected_handover_fields.intersection(vals)
                or vals.get('state') == 'handed_over'
            )
        ):
            raise AccessError(_(
                'Trạng thái bàn giao chỉ được cập nhật bằng nút workflow.'
            ))
        previous_states = {
            project.id: project.state
            for project in self
        } if 'state' in vals else {}
        result = super().write(vals)
        if 'state' in vals:
            for project in self:
                if (
                    previous_states.get(project.id) != 'done'
                    and project.state == 'done'
                ):
                    project._bts_queue_workflow_email(
                        'dtc_bts_maintenance.'
                        'mail_template_project_completed',
                        project.enterprise_director_id.filtered(
                            lambda user: user.active
                        ),
                        'project_completed',
                        marker_field='project_completed_mail_sent_at',
                    )
        return result

    def _get_infrastructure_users(self):
        group = self.env.ref(
            'dtc_bts_base.group_dtc_bts_infrastructure',
            raise_if_not_found=False,
        )
        return (
            group.users.filtered(lambda user: user.active)
            if group
            else self.env['res.users']
        )

    def action_handover_to_maintenance(self):
        is_system = self.env.user.has_group('base.group_system')
        is_ksgs = self.env.user.has_group(
            'dtc_bts_base.group_dtc_bts_ksgs'
        )
        if is_ksgs and not is_system:
            raise AccessError(_(
                'Kỹ sư giám sát không được bàn giao dự án sang Tổ hạ tầng.'
            ))
        if not (
            is_system
            or
            self.env.user.has_group(
                'dtc_bts_base.group_bts_enterprise_director'
            )
        ):
            raise AccessError(_('Bạn không có quyền bàn giao dự án sang bảo trì.'))

        if not self.env.user.has_group('base.group_system'):
            self.check_access_rights('read')
            self.check_access_rule('read')

        today = fields.Date.context_today(self)
        for project in self:
            stations = project.sudo().task_ids
            if not stations:
                raise UserError(_(
                    'Dự án chưa có trạm để bàn giao sang bảo trì.'
                ))
            if any(
                station.station_state not in ('handover', 'cancelled')
                for station in stations
            ):
                raise UserError(_(
                    'Chỉ được bàn giao sang bảo trì khi tất cả trạm ở trạng thái '
                    'Bàn giao hồ sơ hoặc Hủy.'
                ))
            project.sudo().write({
                'maintenance_handover_state': 'pending',
                'maintenance_handover_date': today,
                'maintenance_handover_by_id': self.env.user.id,
                'maintenance_accepted_by_id': False,
                'maintenance_accepted_date': False,
            })
            if hasattr(project, 'message_post'):
                project.sudo().message_post(
                    body=_('Dự án đã được bàn giao sang Tổ hạ tầng.')
                )
            project._bts_queue_workflow_email(
                'dtc_bts_maintenance.'
                'mail_template_project_handover',
                project._get_infrastructure_users(),
                'project_handover',
                marker_field='maintenance_handover_mail_sent_at',
                extra_context={
                    'accept_url': (
                        '%s/dtc_bts_maintenance/project/%s/accept_handover'
                        % (project.get_base_url().rstrip('/'), project.id)
                    ),
                },
            )
        return True

    def action_accept_maintenance_handover(self):
        if not (
            self.env.user.has_group('base.group_system')
            or
            self.env.user.has_group(
                'dtc_bts_base.group_dtc_bts_infrastructure'
            )
        ):
            raise AccessError(_('Bạn không có quyền tiếp nhận bàn giao bảo trì.'))

        if not self.env.user.has_group('base.group_system'):
            self.check_access_rights('read')
            self.check_access_rule('read')

        today = fields.Date.context_today(self)
        for project in self:
            if project.maintenance_handover_state != 'pending':
                raise UserError(_(
                    'Chỉ dự án đang chờ Tổ hạ tầng mới có thể được tiếp nhận.'
                ))
            handed_over_stations = project.sudo().task_ids.filtered(
                lambda station: station.station_state == 'handover'
            )
            project.sudo().write({
                'maintenance_handover_state': 'accepted',
                'maintenance_accepted_by_id': self.env.user.id,
                'maintenance_accepted_date': today,
                'state': 'handed_over',
            })
            handed_over_stations.sudo().write({'station_state': 'operating'})
            if hasattr(project, 'message_post'):
                project.sudo().message_post(
                    body=_(
                        'Tổ hạ tầng đã tiếp nhận bàn giao bảo trì. '
                        'Các trạm bàn giao hồ sơ đã được chuyển sang trạng thái '
                        'Vận hành.'
                    )
                )
            project._bts_queue_workflow_email(
                'dtc_bts_maintenance.'
                'mail_template_project_handover_accepted',
                project.enterprise_director_id.filtered(
                    lambda user: user.active
                ),
                'project_handover_accepted',
                marker_field='maintenance_accepted_mail_sent_at',
            )
        return True

    def action_open_maintenance_equipment_bulk_wizard(self):
        self.ensure_one()
        if self.maintenance_handover_state != 'accepted':
            raise UserError(_(
                'Dự án phải được tiếp nhận bàn giao trước khi tạo hồ sơ bảo trì.'
            ))
        if not self.acceptance_date:
            raise UserError(_(
                'Vui lòng nhập ngày nghiệm thu dự án trước khi tạo hồ sơ bảo trì.'
            ))
        if self.maintenance_equipment_count:
            raise UserError(_('Dự án đã có hồ sơ thiết bị bảo trì.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tạo hồ sơ bảo trì cho dự án'),
            'res_model': 'bts.maintenance.equipment.bulk.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'dtc_bts_maintenance.view_bts_maintenance_equipment_bulk_wizard_form'
            ).id,
            'target': 'new',
            'context': {
                'default_project_id': self.id,
            },
        }

    def _compute_bts_maintenance_due(self):
        today = fields.Date.context_today(self)
        due_project_ids = set(
            self.env['maintenance.equipment'].search([
                ('bts_project_id', 'in', self.ids),
                ('station_id', '!=', False),
                ('bts_state', '=', 'active'),
                ('next_action_date', '<=', today),
            ]).mapped('bts_project_id').ids
        )
        for project in self:
            project.bts_maintenance_due = project.id in due_project_ids

    @api.depends(
        'bts_maintenance_equipment_ids.next_action_date',
        'bts_maintenance_batch_ids.state',
    )
    def _compute_maintenance_summary(self):
        open_states = ('draft', 'generated', 'in_progress', 'submitted', 'reviewed')
        for project in self:
            active_equipment = project.bts_maintenance_equipment_ids.filtered(
                lambda equipment: equipment.active
                and equipment.bts_state == 'active'
            )
            due_dates = active_equipment.mapped('next_action_date')
            project.maintenance_next_due_date = min(due_dates) if due_dates else False
            project.maintenance_equipment_count = len(
                project.bts_maintenance_equipment_ids
            )
            project.maintenance_open_batch_count = len(
                project.bts_maintenance_batch_ids.filtered(
                    lambda batch: batch.state in open_states
                )
            )

    @api.model
    def _search_bts_maintenance_due(self, operator, value):
        if operator not in ('=', '!='):
            return [('id', '=', 0)]
        today = fields.Date.context_today(self)
        due_ids = self.env['maintenance.equipment'].search([
            ('station_id', '!=', False),
            ('bts_state', '=', 'active'),
            ('next_action_date', '<=', today),
        ]).mapped('bts_project_id').ids
        wants_due = (operator == '=' and value) or (operator == '!=' and not value)
        return [('id', 'in' if wants_due else 'not in', due_ids)]

    def action_create_maintenance_batch(self):
        self.ensure_one()
        if (
            'maintenance_handover_state' in self._fields
            and self.maintenance_handover_state != 'accepted'
        ):
            raise UserError(_(
                'Dự án phải được Tổ hạ tầng tiếp nhận trước khi tạo phiếu bảo trì.'
            ))
        equipment = self.bts_maintenance_equipment_ids.filtered(
            lambda item: (
                item.active
                and item.bts_state == 'active'
                and item.station_id
            )
        )
        if not equipment:
            raise UserError(_(
                'Dự án chưa có hồ sơ thiết bị bảo trì cho các trạm.'
            ))
        open_batch = self.bts_maintenance_batch_ids.filtered(
            lambda batch: batch.state in (
                'draft', 'generated', 'in_progress', 'submitted', 'reviewed'
            )
        ).sorted(key=lambda batch: (batch.maintenance_date, batch.id), reverse=True)[:1]
        if open_batch:
            batch = open_batch
        else:
            today = fields.Date.context_today(self)
            effective_dates = equipment.mapped('effective_date')
            effective_date = min(effective_dates) if effective_dates else False
            cycle = '1'
            if effective_date:
                delta = relativedelta(today, effective_date)
                elapsed_months = max(1, delta.years * 12 + delta.months)
                if elapsed_months % 6 == 0:
                    cycle = '6'
                elif elapsed_months % 3 == 0:
                    cycle = '3'
            batch = self.env['bts.maintenance.batch'].create({
                'project_id': self.id,
                'maintenance_date': today,
                'effective_date': effective_date,
                'maintenance_cycle_months': cycle,
                'technician_user_id': self.env.user.id,
            })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Phiếu bảo trì dự án'),
            'res_model': 'bts.maintenance.batch',
            'res_id': batch.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'dtc_bts_maintenance.view_bts_maintenance_batch_form'
            ).id,
            'target': 'current',
        }
