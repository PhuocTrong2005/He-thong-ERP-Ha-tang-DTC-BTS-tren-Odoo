from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class BtsContractRenewal(models.Model):
    _name = 'bts.contract.renewal'
    _description = 'Bản ghi gia hạn hợp đồng BTS'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'renewal_date desc'

    renewal_code = fields.Char(
        string='Mã gia hạn',
        required=True,
        copy=False,
        index=True,
        default=lambda self: _('Mới'),
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Dự thảo'),
            ('in_progress', 'Đang thực hiện'),
            ('pending_signature', 'Chờ BGĐ ký số'),
            ('completed', 'Hoàn thành'),
            ('rejected', 'BGĐ từ chối'),
            ('cancelled', 'Đã hủy'),
        ],
        string='Trạng thái',
        required=True,
        default='draft',
        tracking=True,
    )
    contract_id = fields.Many2one(
        comodel_name='bts.contract',
        string='Hợp đồng',
        required=True,
        ondelete='cascade',
        index=True,
    )
    station_id = fields.Many2one(
        comodel_name='project.task',
        string='Trạm BTS',
        related='contract_id.station_id',
        store=True,
        readonly=True,
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Dự án',
        related='contract_id.project_id',
        store=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Đối tác',
        related='contract_id.partner_id',
        store=True,
        readonly=True,
    )
    contract_type = fields.Selection(
        related='contract_id.contract_type',
        string='Loại hợp đồng',
        store=True,
        readonly=True,
    )
    renewal_date = fields.Date(
        string='Ngày thực hiện gia hạn',
        required=True,
        default=fields.Date.today,
        tracking=True,
    )
    new_expiration_date = fields.Date(
        string='Ngày hết hạn mới',
        tracking=True,
    )
    new_sign_date = fields.Date(
        string='Ngày ký mới',
        tracking=True,
    )
    new_effective_date = fields.Date(
        string='Ngày hiệu lực mới',
        tracking=True,
    )
    new_rental_price = fields.Monetary(
        string='Giá thuê mới',
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='contract_id.currency_id',
        readonly=True,
    )
    performed_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người thực hiện',
        default=lambda self: self.env.uid,
        ondelete='restrict',
    )
    result = fields.Text(string='Kết quả gia hạn')
    notes = fields.Text(string='Ghi chú')
    renewal_scan = fields.Binary(
        string='File scan gia hạn từ Tổ hạ tầng',
        attachment=True,
    )
    renewal_scan_filename = fields.Char(string='Tên file scan gia hạn')
    signed_document = fields.Binary(
        string='Hồ sơ gia hạn đã ký số',
        attachment=True,
    )
    signed_document_filename = fields.Char(string='Tên file gia hạn đã ký số')
    signed_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người ký (BGĐ)',
        readonly=True,
        ondelete='set null',
    )
    signed_date = fields.Datetime(string='Ngày ký', readonly=True)
    rejection_reason = fields.Text(string='Lý do từ chối', tracking=True)
    rejected_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người từ chối',
        readonly=True,
        ondelete='set null',
    )
    rejected_date = fields.Datetime(string='Ngày từ chối', readonly=True)
    signature_request_mail_sent_at = fields.Datetime(
        string='Email yêu cầu ký đã tạo lúc',
        readonly=True,
        copy=False,
    )
    signature_completed_mail_sent_at = fields.Datetime(
        string='Email hoàn tất ký đã tạo lúc',
        readonly=True,
        copy=False,
    )
    signature_rejected_mail_sent_at = fields.Datetime(
        string='Email từ chối ký đã tạo lúc',
        readonly=True,
        copy=False,
    )
    non_renewal_type = fields.Selection(
        selection=[
            ('land', 'Không gia hạn được hợp đồng thuê đất'),
            ('station', 'Không gia hạn được hợp đồng thuê trạm'),
        ],
        string='Loại báo cáo không gia hạn',
        readonly=True,
        copy=False,
        tracking=True,
    )
    non_renewal_reason = fields.Text(
        string='Lý do không gia hạn được',
        copy=False,
        tracking=True,
    )
    non_renewal_reported_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người báo cáo không gia hạn',
        readonly=True,
        copy=False,
    )
    non_renewal_reported_at = fields.Datetime(
        string='Thời gian báo cáo không gia hạn',
        readonly=True,
        copy=False,
    )
    non_renewal_mail_sent_at = fields.Datetime(
        string='Email báo không gia hạn đã tạo lúc',
        readonly=True,
        copy=False,
    )
    non_renewal_review_state = fields.Selection(
        selection=[
            ('enterprise_pending', 'Chờ Giám đốc Xí nghiệp xử lý'),
            ('director_pending', 'Đã trình Ban Giám đốc'),
            ('cancelled', 'Giám đốc Xí nghiệp đã hủy dự án'),
            ('accepted', 'Ban Giám đốc đã chấp thuận'),
        ],
        string='Xử lý không gia hạn được',
        readonly=True,
        copy=False,
        tracking=True,
    )
    non_renewal_escalated_by_id = fields.Many2one(
        'res.users',
        string='Người trình Ban Giám đốc',
        readonly=True,
        copy=False,
    )
    non_renewal_escalated_at = fields.Datetime(
        string='Thời gian trình Ban Giám đốc',
        readonly=True,
        copy=False,
    )
    non_renewal_escalation_mail_sent_at = fields.Datetime(
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
    can_edit_negotiation = fields.Boolean(
        compute='_compute_can_edit_negotiation',
    )

    _sql_constraints = [
        (
            'renewal_code_unique',
            'unique(renewal_code)',
            'Mã gia hạn đã tồn tại.',
        ),
    ]

    @api.depends_context('uid')
    def _compute_can_edit_negotiation(self):
        allowed = (
            self.env.user.has_group(
                'dtc_bts_base.group_dtc_bts_infrastructure'
            )
            or self.env.user.has_group('base.group_system')
        )
        for rec in self:
            rec.can_edit_negotiation = allowed

    @api.constrains(
        'renewal_date',
        'new_sign_date',
        'new_effective_date',
        'new_expiration_date',
    )
    def _check_dates(self):
        for rec in self:
            if rec.new_expiration_date and rec.renewal_date:
                if rec.new_expiration_date <= rec.renewal_date:
                    raise ValidationError('Ngày hết hạn mới phải sau ngày thực hiện gia hạn.')
            if (
                rec.new_effective_date
                and rec.new_expiration_date
                and rec.new_expiration_date <= rec.new_effective_date
            ):
                raise ValidationError(
                    'Ngày hết hạn mới phải sau ngày hiệu lực mới.'
                )
            if (
                rec.new_sign_date
                and rec.new_expiration_date
                and rec.new_expiration_date <= rec.new_sign_date
            ):
                raise ValidationError('Ngày hết hạn mới phải sau ngày ký mới.')

    def _check_renewal_user(self):
        if not (
            self.env.user.has_group(
                'dtc_bts_base.group_dtc_bts_infrastructure'
            )
            or self.env.user.has_group('base.group_system')
        ):
            raise AccessError(
                _('Bạn không có quyền xử lý gia hạn hợp đồng.')
            )

    def _check_contract_director(self):
        if not (
            self.env.user.has_group(
                'dtc_bts_contract.group_dtc_bts_contract_director'
            )
            or self.env.user.has_group('base.group_system')
        ):
            raise AccessError(
                _('Chỉ Ban Giám đốc phụ trách hợp đồng được ký hoặc từ chối gia hạn.')
            )

    def _check_infrastructure_user(self):
        if not (
            self.env.user.has_group(
                'dtc_bts_base.group_dtc_bts_infrastructure'
            )
            or self.env.user.has_group('base.group_system')
        ):
            raise AccessError(
                _(
                    'Chỉ Tổ quản lý hạ tầng được xử lý, tải scan '
                    'và gửi hồ sơ gia hạn ký số.'
                )
            )

    def _check_land_contract_coverage(self):
        for rec in self:
            if not rec.new_expiration_date:
                raise ValidationError('Vui lòng nhập ngày hết hạn mới.')
            if rec.contract_type != 'infrastructure_lease':
                continue
            land_contract = rec.contract_id.related_land_contract_id
            if (
                not land_contract
                or land_contract.state not in ('active', 'renewal_agreed')
                or not land_contract.expiration_date
                or land_contract.expiration_date < rec.new_expiration_date
            ):
                raise ValidationError(
                    'Không thể gia hạn HĐ cho thuê trạm %s đến ngày %s: '
                    'HĐ thuê đất cùng trạm phải đang hiệu lực và có ngày hết hạn '
                    'không sớm hơn ngày hết hạn mới.'
                    % (
                        rec.contract_id.contract_code,
                        rec.new_expiration_date.strftime('%d/%m/%Y'),
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        technical_fields = {
            'non_renewal_type',
            'non_renewal_reported_by_id',
            'non_renewal_reported_at',
            'non_renewal_mail_sent_at',
            'non_renewal_review_state',
            'non_renewal_escalated_by_id',
            'non_renewal_escalated_at',
            'non_renewal_escalation_mail_sent_at',
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
        self._check_infrastructure_sensitive_values(vals_list)
        for vals in vals_list:
            if not vals.get('renewal_code') or vals.get('renewal_code') == _('Mới'):
                vals['renewal_code'] = (
                    self.env['ir.sequence'].next_by_code('dtc.bts.contract.renewal') or _('Mới')
                )
        return super().create(vals_list)

    def write(self, vals):
        self._check_infrastructure_sensitive_values([vals])
        is_system = self.env.user.has_group('base.group_system')
        is_infrastructure = self.env.user.has_group(
            'dtc_bts_base.group_dtc_bts_infrastructure'
        )
        is_director = self.env.user.has_group(
            'dtc_bts_contract.group_dtc_bts_contract_director'
        )
        email_marker_fields = {
            'signature_request_mail_sent_at',
            'signature_completed_mail_sent_at',
            'signature_rejected_mail_sent_at',
            'non_renewal_mail_sent_at',
            'non_renewal_escalation_mail_sent_at',
            'decision_mail_sent_at',
        }
        if (
            not is_system
            and self.env.context.get('bts_email_marker_write')
            and set(vals).issubset(email_marker_fields)
        ):
            return super().write(vals)
        non_renewal_action_fields = {
            'non_renewal_type',
            'non_renewal_reported_by_id',
            'non_renewal_reported_at',
            'non_renewal_review_state',
            'non_renewal_escalated_by_id',
            'non_renewal_escalated_at',
        }
        decision_action_fields = {
            'decision_type',
            'decision_by_id',
            'decision_at',
        }
        if non_renewal_action_fields.intersection(vals) and not self.env.su:
            raise AccessError(
                _('Marker không gia hạn chỉ được ghi bởi workflow máy chủ.')
            )
        if decision_action_fields.intersection(vals) and not self.env.su:
            raise AccessError(
                _('Marker quyết định BGĐ chỉ được ghi bởi workflow máy chủ.')
            )
        if (
            not self.env.su
            and 'non_renewal_reason' in vals
            and any(rec.non_renewal_reported_at for rec in self)
        ):
            raise AccessError(
                _('Không được sửa lý do sau khi đã báo không gia hạn.')
            )
        if (
            not self.env.su
            and 'decision_reason' in vals
            and any(rec.decision_at for rec in self)
        ):
            raise AccessError(_('Không được sửa lý do sau khi BGĐ đã quyết định.'))
        if not is_system and 'state' in vals:
            if is_infrastructure:
                context_states = {
                    'renewal_infrastructure_start': 'in_progress',
                    'renewal_infrastructure_submit': 'pending_signature',
                    'renewal_user_cancel': 'cancelled',
                    'renewal_reset': 'draft',
                }
            elif is_director:
                context_states = {
                    'renewal_director_sign': 'completed',
                    'renewal_director_reject': 'rejected',
                }
            else:
                context_states = {}
            allowed = any(
                self.env.context.get(context_key)
                and vals['state'] == target_state
                for context_key, target_state in context_states.items()
            )
            if not allowed:
                raise AccessError(
                    _('Bạn không được phép chuyển hồ sơ gia hạn sang trạng thái này.')
                )
        signed_fields = {
            'signed_document',
            'signed_document_filename',
            'signed_by_id',
            'signed_date',
        }
        if (
            not is_system
            and signed_fields.intersection(vals)
            and not is_director
            and not self.env.context.get('renewal_reset')
        ):
            raise AccessError(
                _('Chỉ BGĐ hợp đồng được cập nhật hồ sơ gia hạn đã ký số.')
            )
        if not is_system and not self.env.su and is_director:
            allowed_fields = signed_fields | {
                'state',
                'rejection_reason',
                'rejected_by_id',
                'rejected_date',
                'decision_type',
                'decision_reason',
                'decision_by_id',
                'decision_at',
            }
            allowed_fields |= email_marker_fields
            if set(vals) - allowed_fields:
                raise AccessError(
                    _('BGĐ chỉ được ký hoặc từ chối hồ sơ gia hạn.')
                )
        if not is_system and not self.env.su and is_infrastructure:
            allowed_fields = {
                'state',
                'renewal_date',
                'new_sign_date',
                'new_effective_date',
                'new_expiration_date',
                'new_rental_price',
                'renewal_scan',
                'renewal_scan_filename',
                'performed_by_id',
                'result',
                'notes',
                'rejection_reason',
                'rejected_by_id',
                'rejected_date',
                'non_renewal_type',
                'non_renewal_reason',
                'non_renewal_reported_by_id',
                'non_renewal_reported_at',
            }
            allowed_fields |= email_marker_fields
            if self.env.context.get('renewal_reset'):
                allowed_fields |= signed_fields
            if set(vals) - allowed_fields:
                raise AccessError(
                    _(
                        'Tổ hạ tầng chỉ được cập nhật nội dung '
                        'xử lý gia hạn.'
                    )
                )
        return super().write(vals)

    def _check_infrastructure_sensitive_values(self, vals_list):
        sensitive_fields = {
            'new_sign_date',
            'new_effective_date',
            'new_expiration_date',
            'new_rental_price',
            'renewal_scan',
            'renewal_scan_filename',
            'result',
        }
        if not any(sensitive_fields.intersection(vals) for vals in vals_list):
            return
        if (
            self.env.user.has_group(
                'dtc_bts_base.group_dtc_bts_infrastructure'
            )
            or self.env.user.has_group('base.group_system')
        ):
            return
        raise AccessError(
            _(
                'Chỉ Tổ quản lý hạ tầng được cập nhật nội dung '
                'và file scan gia hạn.'
            )
        )

    def action_start(self):
        self._check_infrastructure_user()
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError('Chỉ có thể bắt đầu từ trạng thái Dự thảo.')
            rec.with_context(renewal_infrastructure_start=True).write({
                'performed_by_id': self.env.user.id,
                'state': 'in_progress',
            })

    def action_complete(self):
        self._check_infrastructure_user()
        for rec in self:
            if rec.state != 'in_progress':
                raise ValidationError(
                    'Chỉ có thể gửi ký số khi hồ sơ đang thực hiện.'
                )
            if not rec.renewal_scan:
                raise ValidationError(
                    'Tổ hạ tầng phải tải file scan gia hạn '
                    'trước khi gửi BGĐ ký số.'
                )
            if (
                not rec.new_sign_date
                or not rec.new_effective_date
                or not rec.new_expiration_date
            ):
                raise ValidationError(
                    'Vui lòng nhập ngày ký mới, ngày hiệu lực mới và ngày hết hạn mới.'
                )
            rec._check_land_contract_coverage()
            rec.with_context(
                renewal_infrastructure_submit=True
            ).state = 'pending_signature'
            rec._bts_queue_workflow_email(
                'dtc_bts_contract.mail_template_renewal_signature_request',
                rec._get_contract_director_users(),
                'renewal_signature_request',
                marker_field='signature_request_mail_sent_at',
                extra_context=rec._renewal_email_context(),
            )

    def action_sign_signature(self):
        self._check_contract_director()
        for rec in self:
            if rec.state != 'pending_signature':
                raise ValidationError('Hồ sơ gia hạn không ở trạng thái chờ ký.')
            if not rec.signed_document:
                raise ValidationError(
                    'Vui lòng tải hồ sơ gia hạn đã ký số trước khi xác nhận.'
                )
            rec._check_land_contract_coverage()
            contract_values = {
                'sign_date': rec.new_sign_date,
                'effective_date': rec.new_effective_date,
                'expiration_date': rec.new_expiration_date,
                'state': 'active',
            }
            if rec.new_rental_price:
                contract_values['rental_price'] = rec.new_rental_price
            rec.contract_id.with_context(
                director_renewal_signature=True
            ).write(contract_values)
            rec.contract_id._clear_expiry_activities()
            rec.contract_id._schedule_expiry_activity()
            rec.with_context(renewal_director_sign=True).write({
                'state': 'completed',
                'signed_by_id': self.env.user.id,
                'signed_date': fields.Datetime.now(),
            })
            rec._bts_queue_workflow_email(
                'dtc_bts_contract.mail_template_renewal_signature_completed',
                rec._get_infrastructure_recipient_users(),
                'renewal_signature_completed',
                marker_field='signature_completed_mail_sent_at',
                extra_context=rec._renewal_email_context(),
            )

    def action_reject_signature(self):
        self._check_contract_director()
        for rec in self:
            if rec.state != 'pending_signature':
                raise ValidationError('Chỉ có thể từ chối hồ sơ đang chờ ký.')
            if not rec.rejection_reason:
                raise ValidationError('Vui lòng nhập lý do từ chối hồ sơ gia hạn.')
            rec.with_context(renewal_director_reject=True).write({
                'state': 'rejected',
                'rejected_by_id': self.env.user.id,
                'rejected_date': fields.Datetime.now(),
            })
            rec._bts_queue_workflow_email(
                'dtc_bts_contract.mail_template_renewal_signature_rejected',
                (
                    rec.project_id.project_manager_id
                    | rec._get_infrastructure_recipient_users()
                ),
                'renewal_signature_rejected',
                marker_field='signature_rejected_mail_sent_at',
                extra_context=rec._renewal_email_context(),
            )

    def action_cancel(self):
        self._check_renewal_user()
        for rec in self:
            if rec.state in ('pending_signature', 'completed'):
                raise ValidationError(
                    'Không thể hủy hồ sơ đang chờ ký hoặc đã hoàn thành.'
                )
            rec.with_context(renewal_user_cancel=True).state = 'cancelled'

    def action_reset_to_draft(self):
        self._check_renewal_user()
        for rec in self:
            if rec.state not in ('cancelled', 'rejected'):
                raise ValidationError(
                    'Chỉ có thể đặt lại về Dự thảo khi đã hủy hoặc bị từ chối.'
                )
            rec.with_context(renewal_reset=True).write({
                'state': 'draft',
                'rejection_reason': False,
                'rejected_by_id': False,
                'rejected_date': False,
                'signed_document': False,
                'signed_document_filename': False,
                'signed_by_id': False,
                'signed_date': False,
                'signature_request_mail_sent_at': False,
                'signature_completed_mail_sent_at': False,
                'signature_rejected_mail_sent_at': False,
            })

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

    def _get_infrastructure_recipient_users(self):
        self.ensure_one()
        if self.performed_by_id and self.performed_by_id.active:
            return self.performed_by_id
        group = self.env.ref(
            'dtc_bts_base.group_dtc_bts_infrastructure',
            raise_if_not_found=False,
        )
        return (
            group.users.filtered(lambda user: user.active)
            if group
            else self.env['res.users']
        )

    def _renewal_email_context(self):
        self.ensure_one()
        base_url = self.get_base_url()
        return {
            'state_label': dict(self._fields['state'].selection).get(
                self.state,
                self.state,
            ),
            'contract_type_label': dict(
                self.env['bts.contract']._fields['contract_type'].selection
            ).get(self.contract_type, self.contract_type),
            'decision_label': dict(self._fields['decision_type'].selection).get(
                self.decision_type,
                '',
            ),
            'reject_url': (
                '%s/dtc_bts_contract/renewal/%s/reject'
                % (base_url.rstrip('/'), self.id)
                if base_url
                else False
            ),
        }

    def _action_mark_not_renewable(self, non_renewal_type):
        self._check_infrastructure_user()
        template_by_type = {
            'land': (
                'dtc_bts_contract.mail_template_renewal_land_not_renewable'
            ),
            'station': (
                'dtc_bts_contract.mail_template_renewal_station_not_renewable'
            ),
        }
        for rec in self:
            if rec.state not in ('draft', 'in_progress'):
                raise ValidationError(
                    _('Chỉ được báo không gia hạn ở trạng thái Dự thảo hoặc Đang thực hiện.')
                )
            if rec.non_renewal_reported_at:
                raise ValidationError(
                    _('Hồ sơ đã được xác nhận không gia hạn được.')
                )
            if not rec.non_renewal_reason:
                raise ValidationError(_('Vui lòng nhập lý do không gia hạn được.'))
            rec._record_non_renewal_report(non_renewal_type)
            rec.message_post(body=_(
                'Tổ hạ tầng đã báo %(kind)s. Lý do: %(reason)s',
                kind=dict(rec._fields['non_renewal_type'].selection)[
                    non_renewal_type
                ],
                reason=rec.non_renewal_reason,
            ))
            rec._bts_queue_workflow_email(
                template_by_type[non_renewal_type],
                rec.project_id.enterprise_director_id.filtered(
                    lambda user: user.active
                ),
                'renewal_%s_not_renewable' % non_renewal_type,
                marker_field='non_renewal_mail_sent_at',
                extra_context=rec._renewal_email_context(),
            )
        return True

    def _record_non_renewal_report(self, non_renewal_type):
        self.ensure_one()
        self._check_infrastructure_user()
        if non_renewal_type not in ('land', 'station'):
            raise ValidationError(_('Loại báo cáo không gia hạn không hợp lệ.'))
        if self.state not in ('draft', 'in_progress'):
            raise ValidationError(
                _('Hồ sơ không ở trạng thái có thể báo không gia hạn.')
            )
        if (
            self.non_renewal_type
            or self.non_renewal_reported_by_id
            or self.non_renewal_reported_at
        ):
            raise ValidationError(
                _('Hồ sơ đã được xác nhận không gia hạn được.')
            )
        if not self.non_renewal_reason:
            raise ValidationError(_('Vui lòng nhập lý do không gia hạn được.'))
        self.sudo().write({
            'non_renewal_type': non_renewal_type,
            'non_renewal_reported_by_id': self.env.user.id,
            'non_renewal_reported_at': fields.Datetime.now(),
            'non_renewal_review_state': 'enterprise_pending',
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

    def action_escalate_non_renewal_to_director(self):
        for rec in self:
            rec._check_enterprise_director()
            if rec.non_renewal_review_state != 'enterprise_pending':
                raise ValidationError(_(
                    'Báo cáo không ở trạng thái chờ Giám đốc Xí nghiệp xử lý.'
                ))
            rec.sudo().write({
                'non_renewal_review_state': 'director_pending',
                'non_renewal_escalated_by_id': self.env.user.id,
                'non_renewal_escalated_at': fields.Datetime.now(),
            })
            rec._bts_queue_workflow_email(
                'dtc_bts_contract.mail_template_renewal_failure_escalated',
                rec._get_contract_director_users(),
                'renewal_failure_escalated',
                marker_field='non_renewal_escalation_mail_sent_at',
                extra_context=rec._renewal_email_context(),
            )
        return True

    def action_enterprise_cancel_project(self):
        for rec in self:
            rec._check_enterprise_director()
            if rec.non_renewal_review_state != 'enterprise_pending':
                raise ValidationError(_(
                    'Báo cáo không ở trạng thái chờ Giám đốc Xí nghiệp xử lý.'
                ))
            if rec.project_id.state == 'cancelled':
                raise ValidationError(_('Dự án đã bị hủy.'))
            reason = rec.decision_reason or rec.non_renewal_reason
            now = fields.Datetime.now()
            rec.sudo().write({
                'non_renewal_review_state': 'cancelled',
                'decision_type': 'cancel_project',
                'decision_reason': reason,
                'decision_by_id': self.env.user.id,
                'decision_at': now,
            })
            rec.project_id.sudo().write({
                'state': 'cancelled',
                'contract_cancel_decision_by_id': self.env.user.id,
                'contract_cancel_decision_at': now,
                'contract_cancel_reason': reason,
                'contract_cancel_source_model': rec._name,
                'contract_cancel_source_id': rec.id,
            })
            rec._notify_non_renewal_decision()
        return True

    def _notify_non_renewal_decision(self):
        self.ensure_one()
        recipients = (
            self.project_id.enterprise_director_id
            | self.non_renewal_reported_by_id
            | self._get_infrastructure_recipient_users()
        )
        return self._bts_queue_workflow_email(
            'dtc_bts_contract.'
            'mail_template_renewal_project_station_cancelled',
            recipients,
            'renewal_project_station_cancelled',
            marker_field='decision_mail_sent_at',
            extra_context=self._renewal_email_context(),
        )

    def _record_director_decision(self, decision_type):
        self.ensure_one()
        self._check_contract_director()
        if decision_type not in ('remove_station', 'cancel_project'):
            raise ValidationError(_('Loại quyết định BGĐ không hợp lệ.'))
        if not (
            self.non_renewal_type
            and self.non_renewal_reported_by_id
            and self.non_renewal_reported_at
        ):
            raise ValidationError(
                _('Chỉ được ra quyết định sau khi có báo cáo không gia hạn.')
            )
        if self.decision_at or self.decision_type or self.decision_by_id:
            raise ValidationError(_('Hồ sơ đã có quyết định của BGĐ.'))
        if not self.decision_reason:
            raise ValidationError(_('Vui lòng nhập lý do quyết định.'))
        self.sudo().write({
            'decision_type': decision_type,
            'decision_by_id': self.env.user.id,
            'decision_at': fields.Datetime.now(),
        })

    def action_mark_land_not_renewable(self):
        return self._action_mark_not_renewable('land')

    def action_mark_station_not_renewable(self):
        return self._action_mark_not_renewable('station')

    def _action_director_decision(self, decision_type):
        self._check_contract_director()
        for rec in self:
            if not (
                rec.non_renewal_type
                and rec.non_renewal_reported_by_id
                and rec.non_renewal_reported_at
            ):
                raise ValidationError(
                    _('Chỉ được ra quyết định sau khi có báo cáo không gia hạn.')
                )
            if rec.decision_at:
                raise ValidationError(_('Hồ sơ đã có quyết định của BGĐ.'))
            if not rec.decision_reason:
                raise ValidationError(_('Vui lòng nhập lý do quyết định.'))
            if decision_type == 'remove_station':
                if not rec.station_id or rec.station_id.project_id != rec.project_id:
                    raise ValidationError(_('Trạm nguồn không thuộc đúng Project.'))
                if rec.station_id.station_state == 'cancelled':
                    raise ValidationError(_('Trạm đã bị hủy.'))
            else:
                if not rec.project_id:
                    raise ValidationError(_('Hồ sơ không có Project nguồn hợp lệ.'))
                if rec.project_id.state == 'cancelled':
                    raise ValidationError(_('Project đã bị hủy.'))
            rec._record_director_decision(decision_type)
            if decision_type == 'remove_station':
                rec.station_id._apply_contract_director_station_cancel(rec)
            else:
                rec.project_id._apply_contract_director_cancel(rec)
            rec.sudo().write({'non_renewal_review_state': 'accepted'})
            rec.message_post(body=_(
                'BGĐ đã quyết định %(decision)s. Lý do: %(reason)s',
                decision=dict(rec._fields['decision_type'].selection)[
                    decision_type
                ],
                reason=rec.decision_reason,
            ))
            recipients = (
                rec.non_renewal_reported_by_id
                | rec._get_infrastructure_recipient_users()
                | rec.project_id.enterprise_director_id
            )
            rec._bts_queue_workflow_email(
                'dtc_bts_contract.'
                'mail_template_renewal_project_station_cancelled',
                recipients,
                'renewal_project_station_cancelled',
                marker_field='decision_mail_sent_at',
                extra_context=rec._renewal_email_context(),
            )
        return True

    def action_director_cancel_station(self):
        return self._action_director_decision('remove_station')

    def action_director_cancel_project(self):
        return self._action_director_decision('cancel_project')
