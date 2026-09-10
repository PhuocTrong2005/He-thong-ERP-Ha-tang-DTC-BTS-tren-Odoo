from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class BtsNegotiationMinutes(models.Model):
    _name = 'bts.negotiation.minutes'
    _description = 'Biên bản đàm phán trạm BTS'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'memo_date desc, memo_code asc'

    # -------------------------------------------------------------------------
    # Fields định danh
    # -------------------------------------------------------------------------
    memo_code = fields.Char(
        string='Mã biên bản',
        required=True,
        copy=False,
        index=True,
        default=lambda self: _('Mới'),
    )
    memo_type = fields.Selection(
        selection=[
            ('land_lease', 'Đàm phán thuê đất'),
            ('infrastructure_lease', 'Đàm phán thuê hạ tầng'),
        ],
        string='Loại biên bản',
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Dự thảo'),
            ('pending_approval', 'Chờ phê duyệt'),
            ('confirmed', 'Đã xác nhận'),
            ('converted', 'Legacy - Đã chuyển thành hợp đồng'),
            ('rejected', 'Từ chối'),
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
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Đối tác đàm phán',
        ondelete='restrict',
    )
    converted_to_contract_id = fields.Many2one(
        comodel_name='bts.contract',
        string='Hợp đồng đã tạo',
        readonly=True,
        ondelete='set null',
        help='Chỉ lưu tham chiếu lịch sử từ luồng convert cũ đã ngừng sử dụng.',
    )

    # -------------------------------------------------------------------------
    # Thông tin đàm phán
    # -------------------------------------------------------------------------
    memo_date = fields.Date(
        string='Ngày đàm phán',
        required=True,
        default=fields.Date.today,
    )
    agreed_rental_price = fields.Monetary(
        string='Giá thuê thống nhất',
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Tiền tệ',
        default=lambda self: self.env.company.currency_id,
    )
    discussed_terms = fields.Text(string='Nội dung đàm phán / Điều khoản đã thảo luận')
    notes = fields.Text(string='Ghi chú')
    initial_document = fields.Binary(
        string='Biên bản ban đầu',
        attachment=True,
    )
    initial_document_filename = fields.Char(string='Tên tệp biên bản')
    signed_document = fields.Binary(
        string='Biên bản đã ký số',
        attachment=True,
    )
    signed_document_filename = fields.Char(string='Tên tệp biên bản đã ký số')
    approved_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người ký duyệt (BGĐ)',
        readonly=True,
        ondelete='set null',
    )
    signed_date = fields.Date(string='Ngày ký duyệt', readonly=True)
    land_negotiation_failed = fields.Boolean(
        string='Không thương lượng được thuê đất',
        readonly=True,
        copy=False,
        tracking=True,
    )
    land_negotiation_failed_reason = fields.Text(
        string='Lý do không thương lượng được',
        copy=False,
        tracking=True,
    )
    land_negotiation_failed_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người báo thất bại đàm phán',
        readonly=True,
        copy=False,
    )
    land_negotiation_failed_at = fields.Datetime(
        string='Thời gian báo thất bại đàm phán',
        readonly=True,
        copy=False,
    )
    land_negotiation_failed_mail_sent_at = fields.Datetime(
        string='Email báo thất bại đã tạo lúc',
        readonly=True,
        copy=False,
    )
    failure_review_state = fields.Selection(
        selection=[
            ('enterprise_pending', 'Chờ Giám đốc Xí nghiệp xử lý'),
            ('director_pending', 'Đã trình Ban Giám đốc'),
            ('cancelled', 'Giám đốc Xí nghiệp đã hủy dự án'),
            ('accepted', 'Ban Giám đốc đã chấp thuận'),
        ],
        string='Xử lý thương lượng thất bại',
        readonly=True,
        copy=False,
        tracking=True,
    )
    failure_escalated_by_id = fields.Many2one(
        'res.users',
        string='Người trình Ban Giám đốc',
        readonly=True,
        copy=False,
    )
    failure_escalated_at = fields.Datetime(
        string='Thời gian trình Ban Giám đốc',
        readonly=True,
        copy=False,
    )
    failure_escalation_mail_sent_at = fields.Datetime(
        string='Email trình Ban Giám đốc đã tạo lúc',
        readonly=True,
        copy=False,
    )
    decision_type = fields.Selection(
        selection=[
            ('remove_station', 'Hủy trạm'),
            ('cancel_project', 'Hủy dự án'),
        ],
        string='Quyết định BGĐ',
        readonly=True,
        copy=False,
        tracking=True,
    )
    decision_reason = fields.Text(
        string='Lý do quyết định',
        copy=False,
        tracking=True,
    )
    decision_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người quyết định',
        readonly=True,
        copy=False,
    )
    decision_at = fields.Datetime(
        string='Thời gian quyết định',
        readonly=True,
        copy=False,
    )
    decision_mail_sent_at = fields.Datetime(
        string='Email quyết định đã tạo lúc',
        readonly=True,
        copy=False,
    )

    # -------------------------------------------------------------------------
    # SQL Constraints
    # -------------------------------------------------------------------------
    _sql_constraints = [
        (
            'memo_code_unique',
            'unique(memo_code)',
            'Mã biên bản đã tồn tại. Vui lòng dùng mã khác.',
        ),
        (
            'uq_negotiation_station_type',
            'unique(station_id, memo_type)',
            'Mỗi trạm chỉ được có một biên bản đàm phán cho mỗi loại (đất / hạ tầng).',
        ),
    ]

    # -------------------------------------------------------------------------
    # Constrains Python
    # -------------------------------------------------------------------------
    @api.constrains('memo_type', 'partner_id')
    def _check_partner_type(self):
        for memo in self:
            pt = memo.partner_id.partner_type
            if memo.memo_type == 'land_lease' and pt and pt != 'landowner':
                raise ValidationError(
                    'Biên bản đàm phán thuê đất phải chọn đối tác có loại là "Chủ đất".'
                )
            elif memo.memo_type == 'infrastructure_lease' and pt and pt != 'telecom_partner':
                raise ValidationError(
                    'Biên bản đàm phán thuê hạ tầng phải chọn đối tác có loại là "Đối tác viễn thông".'
                )

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        technical_fields = {
            'land_negotiation_failed',
            'land_negotiation_failed_by_id',
            'land_negotiation_failed_at',
            'land_negotiation_failed_mail_sent_at',
            'failure_review_state',
            'failure_escalated_by_id',
            'failure_escalated_at',
            'failure_escalation_mail_sent_at',
            'decision_type',
            'decision_by_id',
            'decision_at',
            'decision_mail_sent_at',
        }
        if (
            not self.env.su
            and any(technical_fields.intersection(vals) for vals in vals_list)
        ):
            raise AccessError(
                _('Marker workflow chỉ được tạo bởi workflow máy chủ.')
            )
        if (
            self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs')
            and not self.env.user.has_group('base.group_system')
        ):
            allowed_fields = {
                'memo_code',
                'memo_type',
                'station_id',
                'partner_id',
                'memo_date',
                'agreed_rental_price',
                'currency_id',
                'discussed_terms',
                'notes',
                'initial_document',
                'initial_document_filename',
                'state',
            }
            if any(
                set(vals) - allowed_fields
                or vals.get('state', 'draft') != 'draft'
                for vals in vals_list
            ):
                raise AccessError(
                    _('KSGS chỉ được tạo và nhập biên bản ban đầu theo trạm.')
                )
        for vals in vals_list:
            if not vals.get('memo_code') or vals.get('memo_code') == _('Mới'):
                vals['memo_code'] = (
                    self.env['ir.sequence'].next_by_code('dtc.bts.negotiation.minutes') or _('Mới')
                )
        return super().create(vals_list)

    def write(self, vals):
        is_system = self.env.user.has_group('base.group_system')
        is_ksgs = self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs')
        is_infrastructure = self.env.user.has_group(
            'dtc_bts_base.group_dtc_bts_infrastructure'
        )
        is_director = self.env.user.has_group(
            'dtc_bts_contract.group_dtc_bts_contract_director'
        )
        email_marker_fields = {
            'land_negotiation_failed_mail_sent_at',
            'failure_escalation_mail_sent_at',
            'decision_mail_sent_at',
        }
        if (
            not is_system
            and self.env.context.get('bts_email_marker_write')
            and set(vals).issubset(email_marker_fields)
        ):
            return super().write(vals)
        failure_action_fields = {
            'land_negotiation_failed',
            'land_negotiation_failed_by_id',
            'land_negotiation_failed_at',
            'failure_review_state',
            'failure_escalated_by_id',
            'failure_escalated_at',
        }
        decision_action_fields = {
            'decision_type',
            'decision_by_id',
            'decision_at',
        }
        if failure_action_fields.intersection(vals) and not self.env.su:
            raise AccessError(
                _('Marker thất bại đàm phán chỉ được ghi bởi workflow máy chủ.')
            )
        if decision_action_fields.intersection(vals) and not self.env.su:
            raise AccessError(
                _('Marker quyết định BGĐ chỉ được ghi bởi workflow máy chủ.')
            )
        if (
            not self.env.su
            and 'land_negotiation_failed_reason' in vals
            and any(
                minutes.land_negotiation_failed
                or minutes.land_negotiation_failed_at
                for minutes in self
            )
        ):
            raise AccessError(
                _('Không được sửa lý do sau khi đã báo thất bại đàm phán.')
            )
        if (
            not self.env.su
            and 'decision_reason' in vals
            and any(minutes.decision_at for minutes in self)
        ):
            raise AccessError(_('Không được sửa lý do sau khi BGĐ đã quyết định.'))
        if not is_system and not self.env.su and is_ksgs:
            allowed_fields = {
                'memo_code',
                'memo_type',
                'station_id',
                'partner_id',
                'memo_date',
                'agreed_rental_price',
                'currency_id',
                'discussed_terms',
                'notes',
                'initial_document',
                'initial_document_filename',
                'land_negotiation_failed',
                'land_negotiation_failed_reason',
                'land_negotiation_failed_by_id',
                'land_negotiation_failed_at',
            }
            allowed_fields |= email_marker_fields
            if (
                self.env.context.get('signature_batch_submission')
                and vals.get('state') == 'pending_approval'
            ):
                allowed_fields.add('state')
            if set(vals) - allowed_fields:
                raise AccessError(
                    _('KSGS chỉ được cập nhật thông tin biên bản ban đầu theo trạm.')
                )
            if any(minutes.state != 'draft' for minutes in self):
                raise AccessError(
                    _('KSGS không thể sửa biên bản đã gửi vào quy trình ký số.')
                )
        if not is_system and 'state' in vals and not is_ksgs:
            target_state = vals['state']
            if is_infrastructure:
                context_states = {
                    'minutes_infrastructure_submit': 'pending_approval',
                    'minutes_infrastructure_reset': 'draft',
                }
            elif is_director:
                context_states = {
                    'minutes_director_confirm': 'confirmed',
                    'minutes_director_reject': 'rejected',
                    'signature_line_sign': 'confirmed',
                    'signature_batch_rejection': 'draft',
                }
            else:
                context_states = {}
            allowed = any(
                self.env.context.get(context_key)
                and target_state == allowed_state
                for context_key, allowed_state in context_states.items()
            )
            if not allowed:
                raise AccessError(
                    _('Bạn không được phép chuyển biên bản sang trạng thái này.')
                )
        signed_fields = {
            'signed_document',
            'signed_document_filename',
            'approved_by_id',
            'signed_date',
        }
        if (
            not is_system
            and signed_fields.intersection(vals)
            and not is_director
        ):
            raise AccessError(
                _('Chỉ BGĐ hợp đồng được cập nhật thông tin ký số biên bản.')
            )
        if (
            not is_system
            and is_director
            and set(vals) - (
                signed_fields
                | {
                    'state',
                    'decision_type',
                    'decision_reason',
                    'decision_by_id',
                    'decision_at',
                }
                | email_marker_fields
            )
        ):
            raise AccessError(
                _('BGĐ chỉ được cập nhật thông tin ký số và trạng thái biên bản.')
            )
        return super().write(vals)

    def _get_initial_dossier_missing_fields(self):
        self.ensure_one()
        missing = []
        required_fields = (
            ('partner_id', 'Đối tác đàm phán'),
            ('memo_date', 'Ngày đàm phán'),
            ('initial_document', 'File scan biên bản'),
        )
        for field_name, label in required_fields:
            if not self[field_name]:
                missing.append(label)
        if self.state != 'draft':
            missing.append('Hồ sơ không ở trạng thái có thể gửi ký')
        return missing

    # -------------------------------------------------------------------------
    # Actions chuyển trạng thái
    # -------------------------------------------------------------------------
    def _check_contract_director(self):
        if (
            self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs')
            and not self.env.user.has_group('base.group_system')
        ):
            raise AccessError(
                _('KSGS không được phê duyệt hoặc từ chối từng biên bản.')
            )
        if not (
            self.env.user.has_group(
                'dtc_bts_contract.group_dtc_bts_contract_director'
            )
            or self.env.user.has_group('base.group_system')
        ):
            raise AccessError(
                _('Chỉ Ban Giám đốc phụ trách hợp đồng mới được phê duyệt.')
            )

    def _check_contract_preparer(self):
        if (
            self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs')
            and not self.env.user.has_group('base.group_system')
        ):
            raise AccessError(
                _(
                    'KSGS không nộp riêng từng biên bản; '
                    'hãy dùng nút Gửi BGĐ ký số trên Dự án.'
                )
            )
        if not (
            self.env.user.has_group(
                'dtc_bts_base.group_dtc_bts_infrastructure'
            )
            or self.env.user.has_group('base.group_system')
        ):
            raise AccessError(
                _('Chỉ Tổ quản lý hạ tầng được chuẩn bị hồ sơ hợp đồng.')
            )

    def action_submit(self):
        self._check_contract_preparer()
        for memo in self:
            if memo.state != 'draft':
                raise ValidationError('Chỉ có thể nộp biên bản ở trạng thái Dự thảo.')
            if not memo.initial_document:
                raise ValidationError(
                    'Vui lòng tải lên biên bản ban đầu trước khi nộp phê duyệt.'
                )
            if not memo.partner_id:
                raise ValidationError(
                    'Vui lòng chọn đối tác đàm phán trước khi nộp phê duyệt.'
                )
            memo.with_context(
                minutes_infrastructure_submit=True
            ).state = 'pending_approval'

    def action_confirm(self):
        self._check_contract_director()
        for memo in self:
            if memo.state != 'pending_approval':
                raise ValidationError('Chỉ có thể xác nhận biên bản đang chờ phê duyệt.')
            memo.with_context(minutes_director_confirm=True).state = 'confirmed'

    def action_reject(self):
        self._check_contract_director()
        for memo in self:
            if memo.state not in ('pending_approval', 'confirmed'):
                raise ValidationError('Không thể từ chối biên bản ở trạng thái hiện tại.')
            memo.with_context(minutes_director_reject=True).state = 'rejected'

    def action_reset_to_draft(self):
        self._check_contract_preparer()
        for memo in self:
            if memo.state not in ('rejected',):
                raise ValidationError('Chỉ có thể đặt lại về Dự thảo khi biên bản đã bị từ chối.')
            memo.with_context(
                minutes_infrastructure_reset=True
            ).state = 'draft'

    def _get_contract_director_users(self):
        group = self.env.ref(
            'dtc_bts_contract.group_dtc_bts_contract_director',
            raise_if_not_found=False,
        )
        return (
            group.users.filtered(lambda user: user.active)
            if group
            else self.env['res.users']
        )

    def _initial_failure_email_context(self):
        self.ensure_one()
        return {
            'decision_label': dict(self._fields['decision_type'].selection).get(
                self.decision_type,
                '',
            ),
            'station_state_label': dict(
                self.station_id._fields['station_state'].selection
            ).get(self.station_id.station_state, self.station_id.station_state),
            'project_state_label': dict(
                self.project_id._fields['state'].selection
            ).get(self.project_id.state, self.project_id.state),
        }

    def action_mark_land_negotiation_failed(self):
        for minutes in self:
            is_admin = self.env.user.has_group('base.group_system')
            is_assigned_ksgs = (
                self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs')
                and minutes.project_id.project_manager_id == self.env.user
            )
            if not (is_admin or is_assigned_ksgs):
                raise AccessError(
                    _('Chỉ KSGS phụ trách Project được báo thất bại đàm phán.')
                )
            if minutes.state != 'draft':
                raise ValidationError(
                    _('Chỉ được báo thất bại khi biên bản đang ở trạng thái Dự thảo.')
                )
            if minutes.memo_type != 'land_lease':
                raise ValidationError(
                    _('Chỉ biên bản đàm phán thuê đất được dùng workflow này.')
                )
            if minutes.land_negotiation_failed:
                raise ValidationError(
                    _('Biên bản đã được xác nhận không thương lượng được.')
                )
            if not minutes.land_negotiation_failed_reason:
                raise ValidationError(
                    _('Vui lòng nhập lý do không thương lượng được.')
                )
            minutes._record_land_negotiation_failure()
            minutes.message_post(body=_(
                'KSGS đã báo không thương lượng được hợp đồng thuê đất. '
                'Lý do: %(reason)s',
                reason=minutes.land_negotiation_failed_reason,
            ))
            minutes._bts_queue_workflow_email(
                'dtc_bts_contract.'
                'mail_template_initial_land_negotiation_failed',
                minutes.project_id.enterprise_director_id.filtered(
                    lambda user: user.active
                ),
                'initial_land_negotiation_failed',
                marker_field='land_negotiation_failed_mail_sent_at',
                extra_context=minutes._initial_failure_email_context(),
            )
        return True

    def _record_land_negotiation_failure(self):
        self.ensure_one()
        is_admin = self.env.user.has_group('base.group_system')
        is_assigned_ksgs = (
            self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs')
            and self.project_id.project_manager_id == self.env.user
        )
        if not (is_admin or is_assigned_ksgs):
            raise AccessError(
                _('Chỉ KSGS phụ trách Project được báo thất bại đàm phán.')
            )
        if self.state != 'draft' or self.memo_type != 'land_lease':
            raise ValidationError(_('Biên bản không hợp lệ để báo thất bại.'))
        if self.land_negotiation_failed or self.land_negotiation_failed_at:
            raise ValidationError(
                _('Biên bản đã được xác nhận không thương lượng được.')
            )
        if not self.land_negotiation_failed_reason:
            raise ValidationError(_('Vui lòng nhập lý do không thương lượng được.'))
        self.sudo().write({
            'land_negotiation_failed': True,
            'land_negotiation_failed_by_id': self.env.user.id,
            'land_negotiation_failed_at': fields.Datetime.now(),
            'failure_review_state': 'enterprise_pending',
        })

    def _check_enterprise_director(self):
        self.ensure_one()
        is_owner = (
            self.env.user.has_group(
                'dtc_bts_base.group_bts_enterprise_director'
            )
            and self.project_id.enterprise_director_id == self.env.user
        )
        if not (
            is_owner or self.env.user.has_group('base.group_system')
        ):
            raise AccessError(_(
                'Chỉ Giám đốc Xí nghiệp phụ trách dự án được xử lý báo cáo này.'
            ))

    def action_escalate_failure_to_director(self):
        for minutes in self:
            minutes._check_enterprise_director()
            if minutes.failure_review_state != 'enterprise_pending':
                raise ValidationError(_(
                    'Báo cáo không ở trạng thái chờ Giám đốc Xí nghiệp xử lý.'
                ))
            minutes.sudo().write({
                'failure_review_state': 'director_pending',
                'failure_escalated_by_id': self.env.user.id,
                'failure_escalated_at': fields.Datetime.now(),
            })
            minutes._bts_queue_workflow_email(
                'dtc_bts_contract.'
                'mail_template_initial_failure_escalated',
                minutes._get_contract_director_users(),
                'initial_failure_escalated',
                marker_field='failure_escalation_mail_sent_at',
                extra_context=minutes._initial_failure_email_context(),
            )
        return True

    def action_enterprise_cancel_project(self):
        for minutes in self:
            minutes._check_enterprise_director()
            if minutes.failure_review_state != 'enterprise_pending':
                raise ValidationError(_(
                    'Báo cáo không ở trạng thái chờ Giám đốc Xí nghiệp xử lý.'
                ))
            if minutes.project_id.state == 'cancelled':
                raise ValidationError(_('Dự án đã bị hủy.'))
            reason = (
                minutes.decision_reason
                or minutes.land_negotiation_failed_reason
            )
            now = fields.Datetime.now()
            minutes.sudo().write({
                'failure_review_state': 'cancelled',
                'decision_type': 'cancel_project',
                'decision_reason': reason,
                'decision_by_id': self.env.user.id,
                'decision_at': now,
            })
            minutes.project_id.sudo().write({
                'state': 'cancelled',
                'contract_cancel_decision_by_id': self.env.user.id,
                'contract_cancel_decision_at': now,
                'contract_cancel_reason': reason,
                'contract_cancel_source_model': minutes._name,
                'contract_cancel_source_id': minutes.id,
            })
            minutes._notify_failure_decision()
        return True

    def _notify_failure_decision(self):
        self.ensure_one()
        recipients = (
            self.project_id.enterprise_director_id
            | self.land_negotiation_failed_by_id
            | self.project_id.project_manager_id
        )
        return self._bts_queue_workflow_email(
            'dtc_bts_contract.'
            'mail_template_initial_project_station_cancelled',
            recipients,
            'initial_project_station_cancelled',
            marker_field='decision_mail_sent_at',
            extra_context=self._initial_failure_email_context(),
        )

    def _record_director_decision(self, decision_type):
        self.ensure_one()
        self._check_contract_director()
        if decision_type not in ('remove_station', 'cancel_project'):
            raise ValidationError(_('Loại quyết định BGĐ không hợp lệ.'))
        if not (
            self.land_negotiation_failed
            and self.land_negotiation_failed_by_id
            and self.land_negotiation_failed_at
        ):
            raise ValidationError(
                _('Chỉ được ra quyết định sau khi KSGS báo đàm phán thất bại.')
            )
        if self.decision_at or self.decision_type or self.decision_by_id:
            raise ValidationError(_('Biên bản đã có quyết định của BGĐ.'))
        if not self.decision_reason:
            raise ValidationError(_('Vui lòng nhập lý do quyết định.'))
        self.sudo().write({
            'decision_type': decision_type,
            'decision_by_id': self.env.user.id,
            'decision_at': fields.Datetime.now(),
        })

    def _action_director_decision(self, decision_type):
        self._check_contract_director()
        for minutes in self:
            if not (
                minutes.land_negotiation_failed
                and minutes.land_negotiation_failed_by_id
                and minutes.land_negotiation_failed_at
            ):
                raise ValidationError(
                    _('Chỉ được ra quyết định sau khi KSGS báo đàm phán thất bại.')
                )
            if minutes.decision_at:
                raise ValidationError(_('Biên bản đã có quyết định của BGĐ.'))
            if not minutes.decision_reason:
                raise ValidationError(_('Vui lòng nhập lý do quyết định.'))
            if decision_type == 'remove_station':
                if not minutes.station_id or minutes.station_id.project_id != minutes.project_id:
                    raise ValidationError(_('Trạm nguồn không thuộc đúng Project.'))
                if minutes.station_id.station_state == 'cancelled':
                    raise ValidationError(_('Trạm đã bị hủy.'))
            else:
                if not minutes.project_id:
                    raise ValidationError(_('Biên bản không có Project nguồn hợp lệ.'))
                if minutes.project_id.state == 'cancelled':
                    raise ValidationError(_('Project đã bị hủy.'))
            minutes._record_director_decision(decision_type)
            if decision_type == 'remove_station':
                minutes.station_id._apply_contract_director_station_cancel(minutes)
            else:
                minutes.project_id._apply_contract_director_cancel(minutes)
            minutes.sudo().write({'failure_review_state': 'accepted'})
            minutes.message_post(body=_(
                'BGĐ đã quyết định %(decision)s. Lý do: %(reason)s',
                decision=dict(minutes._fields['decision_type'].selection)[
                    decision_type
                ],
                reason=minutes.decision_reason,
            ))
            recipients = (
                minutes.land_negotiation_failed_by_id
                | minutes.project_id.project_manager_id
                | minutes.station_id.assigned_user_id
                | minutes.project_id.enterprise_director_id
            )
            minutes._bts_queue_workflow_email(
                'dtc_bts_contract.'
                'mail_template_initial_project_station_cancelled',
                recipients,
                'initial_project_station_cancelled',
                marker_field='decision_mail_sent_at',
                extra_context=minutes._initial_failure_email_context(),
            )
        return True

    def action_director_cancel_station(self):
        return self._action_director_decision('remove_station')

    def action_director_cancel_project(self):
        return self._action_director_decision('cancel_project')
