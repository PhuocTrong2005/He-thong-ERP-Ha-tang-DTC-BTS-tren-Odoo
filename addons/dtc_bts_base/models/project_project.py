from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    _KSGS_READONLY_PROJECT_FIELDS = {
        'project_code',
        'station_type',
        'telecom_partner_id',
        'enterprise_director_id',
        'project_manager_id',
        'state',
        'province',
        'district',
        'commune',
        'planned_start_date',
        'planned_end_date',
        'acceptance_date',
    }

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        result = super().get_view(
            view_id=view_id,
            view_type=view_type,
            **options,
        )
        is_ksgs = (
            not self.env.user.has_group('base.group_system')
            and self.env.user.has_group(
                'dtc_bts_base.group_dtc_bts_ksgs'
            )
        )
        if view_type in ('tree', 'kanban') and is_ksgs:
            arch = etree.fromstring(result['arch'])
            arch.set('create', 'false')
            arch.set('delete', 'false')
            result['arch'] = etree.tostring(arch, encoding='unicode')
        elif view_type == 'form' and is_ksgs:
            arch = etree.fromstring(result['arch'])
            for node in arch.xpath(
                "//page[@name='dtc_bts_project_info']//field"
            ):
                node.set('readonly', '1')
            for button in arch.xpath(
                "//button[@name='action_handover_to_maintenance']"
            ):
                button.getparent().remove(button)
            result['arch'] = etree.tostring(arch, encoding='unicode')
        return result

    project_code = fields.Char(
        string='Mã dự án',
        required=True,
        copy=False,
        index=True,
        # Keep the schema default context-free: translated callables may read
        # res.users/res.partner before this module has created all columns.
        default='Mới',
    )
    telecom_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Đối tác viễn thông',
        domain="[('partner_type', '=', 'telecom_partner')]",
    )
    station_type = fields.Selection(
        selection=[
            ('macro', 'Trạm Macro'),
            ('cell', 'Trạm Cell'),
        ],
        string='Loại trạm',
        required=True,
        default='macro',
    )
    province = fields.Char(string='Tỉnh/Thành phố')
    district = fields.Char(string='Quận/Huyện')
    commune = fields.Char(string='Xã/Phường')
    planned_start_date = fields.Date(string='Ngày dự kiến bắt đầu')
    planned_end_date = fields.Date(string='Ngày dự kiến kết thúc')
    acceptance_date = fields.Date(string='Ngày nghiệm thu')
    project_manager_id = fields.Many2one(
        comodel_name='res.users',
        string='KSGS phụ trách dự án',
        tracking=True,
        index=True,
    )
    enterprise_director_id = fields.Many2one(
        comodel_name='res.users',
        string='Giám đốc Xí nghiệp',
        tracking=True,
        index=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Dự thảo'),
            ('survey', 'Khảo sát'),
            ('approved', 'Đã phê duyệt'),
            ('in_progress', 'Đang triển khai'),
            ('done', 'Hoàn thành'),
            ('cancelled', 'Đã hủy'),
        ],
        string='Trạng thái dự án',
        required=True,
        default='draft',
        tracking=True,
    )
    station_count = fields.Integer(
        string='Số lượng trạm',
        compute='_compute_station_count',
    )

    _sql_constraints = [
        (
            'project_code_unique',
            'unique(project_code)',
            'Mã dự án đã tồn tại. Vui lòng dùng mã khác.',
        ),
    ]

    @api.depends('task_ids')
    def _compute_station_count(self):
        for project in self:
            project.station_count = len(project.task_ids)

    @api.model
    def default_get(self, fields_list):
        """Default the KSGS at record-creation time, after registry setup.

        A callable field default is evaluated by ``_auto_init`` when the
        column is first added to an existing ``project_project`` table.  It
        must not read ``res.users`` then because this module also adds a
        required column to ``res.partner`` in the same registry update.
        """
        values = super().default_get(fields_list)
        if (
            'project_manager_id' in fields_list
            and not values.get('project_manager_id')
            and self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs')
        ):
            values['project_manager_id'] = self.env.uid
        return values

    @api.model_create_multi
    def create(self, vals_list):
        is_system = self.env.user.has_group('base.group_system')
        if (
            not is_system
            and self.env.user.has_group(
                'dtc_bts_base.group_dtc_bts_ksgs'
            )
        ):
            raise AccessError(_(
                'Kỹ sư giám sát không được tạo dự án.'
            ))
        is_enterprise_director = self.env.user.has_group(
            'dtc_bts_base.group_bts_enterprise_director'
        )
        for vals in vals_list:
            self._check_enterprise_director_assignment(vals)
            self._check_ksgs_assignment(vals)
            if is_enterprise_director and not is_system:
                director_id = vals.get('enterprise_director_id')
                if director_id and director_id != self.env.uid:
                    raise AccessError(_(
                        'Giám đốc Xí nghiệp chỉ được tạo dự án trong phạm vi của mình.'
                    ))
                vals['enterprise_director_id'] = self.env.uid
            elif not is_system and vals.get('enterprise_director_id'):
                raise AccessError(_(
                    'Bạn không có quyền gán Giám đốc Xí nghiệp cho dự án.'
                ))
            if not vals.get('project_code') or vals.get('project_code') == _('Mới'):
                vals['project_code'] = self.env['ir.sequence'].next_by_code('dtc.bts.project') or _('Mới')
        projects = super().create(vals_list)
        projects._sync_ksgs_assignment_activities()
        projects._queue_ksgs_assignment_emails(
            sender_user=self.env.user,
        )
        for project in projects.filtered(
            lambda record: (
                record.enterprise_director_id
                and record.enterprise_director_id != self.env.user
            )
        ):
            project.message_post(body=_(
                'Dự án được giao cho Giám đốc Xí nghiệp %(director)s.',
                director=project.enterprise_director_id.display_name,
            ))
        return projects

    def write(self, vals):
        is_system = self.env.user.has_group('base.group_system')
        is_ksgs = self.env.user.has_group(
            'dtc_bts_base.group_dtc_bts_ksgs'
        )
        is_enterprise_director = self.env.user.has_group(
            'dtc_bts_base.group_bts_enterprise_director'
        )
        if (
            is_ksgs
            and not is_system
            and not self.env.context.get('bts_station_summary_sync')
            and self._KSGS_READONLY_PROJECT_FIELDS.intersection(vals)
        ):
            raise AccessError(_(
                'Kỹ sư giám sát chỉ được xem Thông tin dự án. '
                'Trạng thái và ngày nghiệm thu dự án được hệ thống '
                'tự động tổng hợp từ các trạm.'
            ))
        self._check_enterprise_director_assignment(vals)
        self._check_ksgs_assignment(vals)
        if (
            'enterprise_director_id' in vals
            and not is_system
            and not is_ksgs
        ):
            if not is_enterprise_director or vals['enterprise_director_id'] != self.env.uid:
                raise AccessError(_(
                    'Bạn không có quyền chuyển dự án sang phạm vi Xí nghiệp khác.'
                ))
        if 'project_manager_id' in vals and not is_system:
            if not is_enterprise_director and not is_ksgs:
                raise AccessError(_(
                    'Chỉ Giám đốc Xí nghiệp được phân công KSGS cho dự án.'
                ))

        previous_directors = {
            project.id: project.enterprise_director_id for project in self
        }
        previous_managers = {
            project.id: project.project_manager_id for project in self
        }
        result = super().write(vals)
        if 'project_manager_id' in vals:
            for project in self:
                old_user = previous_managers[project.id]
                project_after_write = project.sudo()
                if old_user != project_after_write.project_manager_id:
                    project_after_write._sync_ksgs_assignment_activities(
                        old_user=old_user,
                    )
                    project_after_write._queue_ksgs_assignment_emails(
                        sender_user=self.env.user,
                    )
                    project_after_write.message_post(body=_(
                        'KSGS phụ trách dự án được đổi từ %(old)s sang %(new)s.',
                        old=old_user.display_name or _('Chưa phân công'),
                        new=(
                            project_after_write.project_manager_id.display_name
                            or _('Chưa phân công')
                        ),
                    ))
        if 'enterprise_director_id' in vals:
            for project in self:
                old_director = previous_directors[project.id]
                project_after_write = project.sudo()
                if old_director != project_after_write.enterprise_director_id:
                    project_after_write.message_post(body=_(
                        'Giám đốc Xí nghiệp được đổi từ %(old)s sang %(new)s.',
                        old=old_director.display_name or _('Chưa phân công'),
                        new=(
                            project_after_write.enterprise_director_id.display_name
                            or _('Chưa phân công')
                        ),
                    ))
        return result

    def unlink(self):
        if (
            not self.env.user.has_group('base.group_system')
            and self.env.user.has_group(
                'dtc_bts_base.group_dtc_bts_ksgs'
            )
        ):
            raise AccessError(_(
                'Kỹ sư giám sát chỉ được xem dự án được phân công.'
            ))
        return super().unlink()

    def action_open_new_station(self):
        self.ensure_one()
        self.check_access_rule('read')
        self.env['project.task'].check_access_rights('create')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Thêm trạm BTS'),
            'res_model': 'project.task',
            'view_mode': 'form',
            'views': [(
                self.env.ref(
                    'dtc_bts_base.view_dtc_bts_station_form'
                ).id,
                'form',
            )],
            'target': 'current',
            'context': {
                'default_project_id': self.id,
            },
        }

    def _check_enterprise_director_assignment(self, vals):
        director_id = vals.get('enterprise_director_id')
        if not director_id:
            return
        director = self.env['res.users'].browse(director_id).exists()
        if not director or not director.has_group(
            'dtc_bts_base.group_bts_enterprise_director'
        ):
            raise ValidationError(_(
                'Người quản lý phải thuộc nhóm Giám đốc Xí nghiệp.'
            ))

    def _check_ksgs_assignment(self, vals):
        manager_id = vals.get('project_manager_id')
        if not manager_id:
            return
        manager = self.env['res.users'].browse(manager_id).exists()
        if not manager or not manager.has_group(
            'dtc_bts_base.group_dtc_bts_ksgs'
        ):
            raise ValidationError(_(
                'Người phụ trách dự án phải thuộc nhóm Kỹ sư giám sát.'
            ))

    def _sync_ksgs_assignment_activities(self, old_user=None):
        activity_xmlid = 'dtc_bts_base.mail_activity_type_project_assignment'
        for project in self:
            if old_user and old_user != project.project_manager_id:
                project._bts_close_activities(
                    activity_xmlid,
                    user=old_user,
                    feedback=_('Phân công KSGS đã được thay đổi.'),
                )
            user = project.project_manager_id
            if not user:
                continue
            project._bts_schedule_activity_once(
                activity_xmlid,
                user=user,
                summary=_('Dự án BTS mới được phân công'),
                deadline=fields.Date.context_today(project),
                note=_(
                    'Bạn được phân công phụ trách dự án %(project)s (%(code)s).',
                    project=project.display_name,
                    code=project.project_code,
                ),
            )

    def _queue_ksgs_assignment_emails(self, sender_user=None):
        for project in self:
            manager = project.project_manager_id
            if not manager:
                continue
            project._bts_queue_workflow_email(
                'dtc_bts_base.mail_template_project_assignment',
                manager,
                'project_assignment',
                extra_context={
                    'sender_email': (
                        sender_user.email_formatted
                        if sender_user and sender_user.email
                        else False
                    ),
                },
            )

    @api.onchange('telecom_partner_id')
    def _onchange_telecom_partner_id(self):
        if self.telecom_partner_id and self.telecom_partner_id.partner_type != 'telecom_partner':
            self.telecom_partner_id = False
            return {
                'warning': {
                    'title': 'Đối tác không hợp lệ',
                    'message': 'Đối tác viễn thông phải có loại là Đối tác viễn thông.',
                }
            }
        return {}

    @api.constrains('planned_start_date', 'planned_end_date')
    def _check_planned_date_range(self):
        for project in self:
            if (
                project.planned_start_date
                and project.planned_end_date
                and project.planned_end_date < project.planned_start_date
            ):
                raise ValidationError('Ngày dự kiến kết thúc phải sau ngày dự kiến bắt đầu.')
