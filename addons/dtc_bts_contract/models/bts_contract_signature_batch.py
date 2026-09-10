import base64
import hashlib
import hmac
import json
import logging
import secrets
from datetime import timedelta

from markupsafe import escape

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.tools import email_normalize


_logger = logging.getLogger(__name__)

OTP_VALIDITY_MINUTES = 5
OTP_MAX_ATTEMPTS = 5
OTP_HASH_ITERATIONS = 120000


class BtsContractSignatureBatch(models.Model):
    _name = 'bts.contract.signature.batch'
    _description = 'Batch ký số hợp đồng BTS theo dự án'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Mã batch',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Mới'),
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Dự án',
        required=True,
        index=True,
        ondelete='restrict',
        tracking=True,
    )
    phase = fields.Selection(
        selection=[
            ('phase_1', 'Giai đoạn 1 - HĐ thuê đất và BB đàm phán'),
            ('phase_2', 'Giai đoạn 2 - HĐ cho thuê trạm'),
        ],
        string='Giai đoạn ký số',
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Dự thảo'),
            ('submitted', 'Đã gửi BGĐ'),
            ('partially_signed', 'Đã ký một phần'),
            ('done', 'Hoàn tất'),
            ('rejected', 'Từ chối'),
        ],
        string='Trạng thái',
        required=True,
        default='draft',
        tracking=True,
    )
    line_ids = fields.One2many(
        comodel_name='bts.contract.signature.batch.line',
        inverse_name='batch_id',
        string='Hồ sơ ký số',
        copy=False,
    )
    line_count = fields.Integer(
        string='Tổng hồ sơ',
        compute='_compute_line_statistics',
    )
    signed_line_count = fields.Integer(
        string='Đã ký',
        compute='_compute_line_statistics',
    )
    created_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người tạo batch',
        default=lambda self: self.env.user,
        readonly=True,
    )
    submitted_date = fields.Datetime(
        string='Ngày gửi BGĐ',
        readonly=True,
        tracking=True,
    )
    completed_date = fields.Datetime(
        string='Ngày hoàn tất',
        readonly=True,
        tracking=True,
    )
    rejected_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người từ chối',
        readonly=True,
    )
    rejected_date = fields.Datetime(string='Ngày từ chối', readonly=True)
    rejection_reason = fields.Text(string='Lý do từ chối', tracking=True)
    notification_user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='bts_signature_batch_notification_user_rel',
        column1='batch_id',
        column2='user_id',
        string='KSGS nhận thông báo',
        readonly=True,
    )
    signature_request_mail_sent_at = fields.Datetime(
        string='Email yêu cầu ký GĐ1 đã tạo lúc',
        readonly=True,
        copy=False,
    )
    signature_rejected_mail_sent_at = fields.Datetime(
        string='Email từ chối GĐ1 đã tạo lúc',
        readonly=True,
        copy=False,
    )
    signature_completed_mail_sent_at = fields.Datetime(
        string='Email hoàn tất GĐ1 đã tạo lúc',
        readonly=True,
        copy=False,
    )

    _sql_constraints = [
        (
            'signature_batch_name_unique',
            'unique(name)',
            'Mã batch ký số đã tồn tại.',
        ),
    ]

    @api.depends('line_ids.state')
    def _compute_line_statistics(self):
        for batch in self:
            batch.line_count = len(batch.line_ids)
            batch.signed_line_count = len(
                batch.line_ids.filtered(lambda line: line.state == 'signed')
            )

    @api.model_create_multi
    def create(self, vals_list):
        if (
            self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs')
            and not self.env.user.has_group('base.group_system')
        ):
            allowed_fields = {'project_id', 'phase', 'line_ids'}
            if any(set(vals) - allowed_fields for vals in vals_list):
                raise AccessError(
                    _('KSGS chỉ được tạo batch dự thảo từ hồ sơ của dự án.')
                )
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('Mới'):
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code(
                        'dtc.bts.contract.signature.batch'
                    )
                    or _('Mới')
                )
        return super().create(vals_list)

    def write(self, vals):
        is_system = self.env.user.has_group('base.group_system')
        is_ksgs = self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs')
        is_director = self.env.user.has_group(
            'dtc_bts_contract.group_dtc_bts_contract_director'
        )
        if (
            is_ksgs
            and not is_system
        ):
            allowed_fields = {'state', 'submitted_date'}
            if (
                not self.env.context.get('signature_batch_submit')
                or set(vals) - allowed_fields
                or vals.get('state') != 'submitted'
            ):
                raise AccessError(
                    _('KSGS chỉ được gửi batch đã tạo sang trạng thái chờ BGĐ ký.')
                )
        if not is_system and is_director:
            allowed_fields = {
                'state',
                'rejection_reason',
                'rejected_by_id',
                'rejected_date',
                'completed_date',
                'notification_user_ids',
                'line_ids',
            }
            if set(vals) - allowed_fields:
                raise AccessError(
                    _('BGĐ chỉ được ký, từ chối hoặc hoàn thành batch.')
                )
            if 'line_ids' in vals:
                self._check_director_line_updates(vals['line_ids'])
            if 'state' in vals:
                context_states = {
                    'signature_batch_partial': 'partially_signed',
                    'signature_batch_complete': 'done',
                    'signature_batch_reject': 'rejected',
                }
                allowed = any(
                    self.env.context.get(context_key)
                    and vals['state'] == target_state
                    for context_key, target_state in context_states.items()
                )
                if not allowed:
                    raise AccessError(
                        _('Trạng thái batch chỉ được đổi qua nút workflow hợp lệ.')
                )
        return super().write(vals)

    def _check_director_line_updates(self, commands):
        """Allow inline upload only on existing lines of this batch."""
        allowed_line_fields = {
            'signed_document',
            'signed_document_filename',
        }
        batch_line_ids = set(self.line_ids.ids)
        for command in commands:
            valid_update = (
                isinstance(command, (list, tuple))
                and len(command) == 3
                and command[0] == 1
                and command[1] in batch_line_ids
                and isinstance(command[2], dict)
                and not set(command[2]) - allowed_line_fields
            )
            if not valid_update:
                raise AccessError(
                    _(
                        'BGĐ chỉ được tải file ký trên các dòng '
                        'đã có trong batch.'
                    )
                )

    def _check_submitter(self):
        if not (
            self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs')
            or self.env.user.has_group('base.group_system')
        ):
            raise AccessError(
                _('Chỉ KSGS được gửi batch hồ sơ hợp đồng cho BGĐ ký số.')
            )

    def _check_director(self):
        if not (
            self.env.user.has_group(
                'dtc_bts_contract.group_dtc_bts_contract_director'
            )
            or self.env.user.has_group('base.group_system')
        ):
            raise AccessError(
                _('Chỉ Ban Giám đốc phụ trách hợp đồng được ký hoặc từ chối batch.')
            )

    def _get_signature_director_users(self):
        director_group = self.env.ref(
            'dtc_bts_contract.group_dtc_bts_contract_director',
            raise_if_not_found=False,
        )
        return (
            director_group.users.filtered(lambda user: user.active)
            if director_group
            else self.env['res.users']
        )

    def _get_signature_owner_users(self):
        self.ensure_one()
        return (
            self.created_by_id | self.project_id.project_manager_id
        ).filtered(lambda user: user.active)

    def _get_signature_document_type_names(self):
        self.ensure_one()
        selection = dict(
            self.env['bts.contract.signature.batch.line']
            ._fields['document_type']
            .selection
        )
        return ', '.join(
            selection.get(document_type, document_type)
            for document_type in dict.fromkeys(
                self.line_ids.mapped('document_type')
            )
        )

    def _send_signature_workflow_email(
        self,
        template_xmlid,
        recipient_users=None,
        email_event=None,
        extra_context=None,
    ):
        """Send one workflow email per unique, authorized recipient email.

        Email rendering and delivery are isolated in savepoints because a
        missing/broken template or SMTP failure must not roll back the business
        transition. Configured HTML templates are sent immediately.
        """
        self.ensure_one()
        marker_by_event = {
            'request': 'signature_request_mail_sent_at',
            'rejected': 'signature_rejected_mail_sent_at',
            'completed': 'signature_completed_mail_sent_at',
        }
        marker_field = marker_by_event.get(email_event)
        if self.phase != 'phase_1' or not marker_field:
            return self.env['mail.mail']
        if self[marker_field]:
            return self.env['mail.mail']

        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if not template:
            _logger.warning(
                'signature_email_template_missing event=%s template=%s batch_id=%s',
                email_event,
                template_xmlid,
                self.id,
            )
            return self.env['mail.mail']

        recipients_by_email = {}
        for user in recipient_users or self.env['res.users']:
            partner = user.partner_id
            normalized_email = email_normalize(partner.email or '')
            if (
                not user.active
                or not partner.active
                or not normalized_email
                or not self._bts_user_can_read_activity_record(user)
            ):
                continue
            recipients_by_email.setdefault(normalized_email, user)

        queued_mails = self.env['mail.mail']
        base_url = self.get_base_url()
        base_context = {
            'record_url': (
                '%s/web#id=%s&model=%s&view_type=form'
                % (base_url.rstrip('/'), self.id, self._name)
                if base_url
                else False
            ),
            'reject_url': (
                '%s/dtc_bts_contract/signature_batch/%s/reject'
                % (base_url.rstrip('/'), self.id)
                if base_url
                else False
            ),
            'document_type_names': self._get_signature_document_type_names(),
            'state_label': dict(self._fields['state'].selection).get(
                self.state,
                self.state,
            ),
            'signature_deadline': (
                fields.Date.to_string(
                    fields.Date.context_today(self) + timedelta(days=3)
                )
                if email_event == 'request'
                else False
            ),
            'signer_names': ', '.join(
                self.line_ids.mapped('signed_by_id.name')
            ),
            'signed_file_names': ', '.join(
                filter(None, self.line_ids.mapped('signed_document_filename'))
            ),
        }
        base_context.update(extra_context or {})
        for user in recipients_by_email.values():
            try:
                with self.env.cr.savepoint():
                    mail_id = template.with_context(
                        **base_context,
                        recipient_name=user.name,
                    ).send_mail(
                        self.id,
                        force_send=True,
                        email_values={
                            'email_to': user.email_formatted,
                            'recipient_ids': [(6, 0, [user.partner_id.id])],
                        },
                    )
                    queued_mails |= self.env['mail.mail'].browse(mail_id)
            except Exception:
                # Mail rendering/queue errors are deliberately non-fatal for
                # the already-authorized business workflow. Do not include
                # exception text because renderer failures may contain body
                # fragments or other business data.
                _logger.warning(
                    'signature_email_send_failed '
                    'event=%s template=%s batch_id=%s recipient_user_id=%s',
                    email_event,
                    template_xmlid,
                    self.id,
                    user.id,
                )

        if queued_mails:
            # Bypass only this model's role-specific write whitelist. Normal
            # ACLs and record rules still apply; no sudo is used.
            super(BtsContractSignatureBatch, self).write({
                marker_field: fields.Datetime.now(),
            })
            recipient_names = ', '.join(
                recipients_by_email[email].name
                for email in recipients_by_email
                if queued_mails.filtered(
                    lambda mail: email_normalize(mail.email_to or '') == email
                )
            )
            self.message_post(body=_(
                'Đã tạo email %(event)s cho: %(recipients)s.',
                event={
                    'request': _('yêu cầu ký GĐ1'),
                    'rejected': _('thông báo từ chối GĐ1'),
                    'completed': _('thông báo hoàn tất GĐ1'),
                }[email_event],
                recipients=recipient_names,
            ))
        return queued_mails

    def action_submit(self):
        self._check_submitter()
        for batch in self:
            if batch.state != 'draft':
                raise ValidationError('Chỉ có thể gửi batch ở trạng thái Dự thảo.')
            if not batch.line_ids:
                raise ValidationError('Batch chưa có hồ sơ để gửi ký số.')
            stations = batch.project_id.task_ids.filtered(
                lambda station: station.station_code
            )
            expected_values = batch.project_id._prepare_signature_batch_lines(
                stations,
                batch.phase,
            )
            expected_documents = {
                (
                    values['station_id'],
                    values['document_type'],
                    values.get('contract_id'),
                    values.get('negotiation_minutes_id'),
                )
                for values in expected_values
            }
            actual_documents = {
                (
                    line.station_id.id,
                    line.document_type,
                    line.contract_id.id or None,
                    line.negotiation_minutes_id.id or None,
                )
                for line in batch.line_ids
            }
            if actual_documents != expected_documents:
                raise ValidationError(
                    'Batch không chứa đúng và đủ hồ sơ của tất cả trạm '
                    'trong dự án.'
                )
            active_batch = self.search([
                ('id', '!=', batch.id),
                ('project_id', '=', batch.project_id.id),
                ('phase', '=', batch.phase),
                ('state', 'in', ('submitted', 'partially_signed')),
            ], limit=1)
            if active_batch:
                raise ValidationError(
                    'Dự án đang có batch %s cùng giai đoạn chưa hoàn tất.'
                    % active_batch.name
                )
            batch._move_documents_to_signing()
            batch.with_context(signature_batch_submit=True).write({
                'state': 'submitted',
                'submitted_date': fields.Datetime.now(),
            })
            batch._schedule_signature_activities()
            batch.message_post(body=_(
                'Batch %(batch)s đã được gửi Ban Giám đốc chờ ký.',
                batch=batch.name,
            ))
            batch._send_signature_workflow_email(
                'dtc_bts_contract.mail_template_signature_stage1_request',
                recipient_users=batch._get_signature_director_users(),
                email_event='request',
            )

    def _schedule_signature_activities(self):
        users = self._get_signature_director_users()
        deadline = fields.Date.context_today(self) + timedelta(days=3)
        for batch in self:
            for user in users:
                batch._bts_schedule_activity_once(
                    'dtc_bts_contract.mail_activity_type_signature_batch_pending',
                    user=user,
                    deadline=deadline,
                    summary=_('Batch %(batch)s chờ ký') % {
                        'batch': batch.name,
                    },
                    note=_(
                        'Vui lòng kiểm tra và ký %(count)s hồ sơ của dự án %(project)s.',
                        count=batch.line_count,
                        project=batch.project_id.display_name,
                    ),
                )

    def _move_documents_to_signing(self):
        for line in self.line_ids:
            if line.contract_id and line.contract_id.state == 'draft':
                line.contract_id.with_context(
                    signature_batch_submission=True
                ).state = 'submitted'
            if (
                line.negotiation_minutes_id
                and line.negotiation_minutes_id.state == 'draft'
            ):
                line.negotiation_minutes_id.with_context(
                    signature_batch_submission=True
                ).state = 'pending_approval'

    def action_reject(self):
        self._check_director()
        for batch in self:
            if batch.state != 'submitted':
                raise ValidationError(
                    'Chỉ có thể từ chối batch chưa có hồ sơ nào được ký.'
                )
            if not batch.rejection_reason:
                raise ValidationError('Vui lòng nhập lý do từ chối batch.')
            batch.line_ids.with_context(
                signature_batch_reject=True
            ).write({'state': 'rejected'})
            batch._reset_unsigned_documents()
            batch.with_context(signature_batch_reject=True).write({
                'state': 'rejected',
                'rejected_by_id': self.env.user.id,
                'rejected_date': fields.Datetime.now(),
            })
            batch._bts_close_activities(
                'dtc_bts_contract.mail_activity_type_signature_batch_pending',
                feedback=_('Batch ký số đã bị từ chối.'),
            )
            batch._send_signature_workflow_email(
                'dtc_bts_contract.mail_template_signature_stage1_rejected',
                recipient_users=batch._get_signature_owner_users(),
                email_event='rejected',
            )

    def _reset_unsigned_documents(self):
        for line in self.line_ids:
            if line.contract_id and line.contract_id.state == 'submitted':
                line.contract_id.with_context(
                    signature_batch_rejection=True
                ).state = 'draft'
            if (
                line.negotiation_minutes_id
                and line.negotiation_minutes_id.state == 'pending_approval'
            ):
                line.negotiation_minutes_id.with_context(
                    signature_batch_rejection=True
                ).state = 'draft'

    def _refresh_signing_state(self):
        for batch in self:
            signed_lines = batch.line_ids.filtered(
                lambda line: line.state == 'signed'
            )
            if signed_lines:
                batch.with_context(
                    signature_batch_partial=True
                ).state = 'partially_signed'

    def action_complete(self):
        self._check_director()
        for batch in self:
            if batch.state not in ('submitted', 'partially_signed'):
                raise ValidationError(
                    'Chỉ có thể hoàn thành batch đang trong quá trình ký.'
                )
            if not batch.line_ids or any(
                line.state != 'signed' for line in batch.line_ids
            ):
                raise ValidationError(
                    'Chỉ được hoàn thành batch sau khi tất cả hồ sơ đã ký đủ.'
                )
            batch._complete_batch()

    def _complete_batch(self):
        self.ensure_one()
        target_station_state = (
            'contracted' if self.phase == 'phase_1' else 'station_lease_signed'
        )
        stations = self.line_ids.mapped('station_id')
        stations.sudo().write({'station_state': target_station_state})
        notification_candidates = (
            self.created_by_id
            | self.project_id.project_manager_id
            | stations.mapped('assigned_user_id')
        ).filtered(lambda user: user.active)
        notification_users = notification_candidates.filtered(
            lambda user: self._bts_user_can_read_activity_record(user)
        )
        self.with_context(signature_batch_complete=True).write({
            'state': 'done',
            'completed_date': fields.Datetime.now(),
            'notification_user_ids': [(6, 0, notification_users.ids)],
        })
        self._bts_close_activities(
            'dtc_bts_contract.mail_activity_type_signature_batch_pending',
            feedback=_('Batch ký số đã hoàn tất.'),
        )
        self._send_signature_workflow_email(
            'dtc_bts_contract.mail_template_signature_stage1_completed',
            recipient_users=self._get_signature_owner_users(),
            email_event='completed',
        )

    def action_mark_dashboard_notification_seen(self):
        user = self.env.user
        can_manage = (
            user.has_group('base.group_system')
            or user.has_group('dtc_bts_contract.group_dtc_bts_contract_director')
        )
        for batch in self:
            if user not in batch.notification_user_ids and not can_manage:
                raise AccessError(
                    _('Bạn không có quyền xử lý thông báo này.')
                )
            batch.sudo().write({
                'notification_user_ids': [(3, user.id)],
            })
        return True


class BtsContractSignatureBatchLine(models.Model):
    _name = 'bts.contract.signature.batch.line'
    _description = 'Dòng hồ sơ trong batch ký số hợp đồng BTS'
    _order = 'station_id, document_type, id'

    batch_id = fields.Many2one(
        comodel_name='bts.contract.signature.batch',
        string='Batch ký số',
        required=True,
        ondelete='cascade',
        index=True,
    )
    station_id = fields.Many2one(
        comodel_name='project.task',
        string='Trạm BTS',
        required=True,
        ondelete='restrict',
        index=True,
    )
    document_type = fields.Selection(
        selection=[
            ('land_contract', 'Hợp đồng thuê đất'),
            ('negotiation_minutes', 'Biên bản đàm phán'),
            ('station_lease_contract', 'Hợp đồng cho thuê trạm'),
        ],
        string='Loại hồ sơ',
        required=True,
    )
    contract_id = fields.Many2one(
        comodel_name='bts.contract',
        string='Hợp đồng',
        ondelete='restrict',
    )
    negotiation_minutes_id = fields.Many2one(
        comodel_name='bts.negotiation.minutes',
        string='Biên bản đàm phán',
        ondelete='restrict',
    )
    state = fields.Selection(
        selection=[
            ('pending', 'Chờ ký'),
            ('signed', 'Đã ký'),
            ('rejected', 'Từ chối'),
        ],
        string='Trạng thái',
        required=True,
        default='pending',
    )
    source_document = fields.Binary(
        string='File scan KSGS',
        compute='_compute_source_document',
    )
    source_document_filename = fields.Char(
        string='Tên file scan',
        compute='_compute_source_document',
    )
    signed_document = fields.Binary(
        string='File đã ký số',
        attachment=True,
    )
    signed_document_filename = fields.Char(string='Tên file đã ký số')
    signed_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người ký',
        readonly=True,
    )
    signed_date = fields.Datetime(string='Ngày ký', readonly=True)
    otp_channel = fields.Selection(
        selection=[
            ('email', 'Email'),
            ('sms', 'SMS'),
        ],
        string='Kênh nhận OTP',
        required=True,
        default='email',
    )
    otp_state = fields.Selection(
        selection=[
            ('none', 'Chưa gửi'),
            ('sent', 'Đã gửi'),
            ('verified', 'Đã xác thực'),
            ('used', 'Đã sử dụng'),
            ('expired', 'Đã hết hạn'),
            ('locked', 'Đã khóa'),
        ],
        string='Trạng thái OTP',
        required=True,
        default='none',
        readonly=True,
        copy=False,
    )
    otp_hash = fields.Char(readonly=True, copy=False)
    otp_salt = fields.Char(readonly=True, copy=False)
    otp_expires_at = fields.Datetime(
        string='OTP hết hạn lúc',
        readonly=True,
        copy=False,
    )
    otp_sent_at = fields.Datetime(
        string='Gửi OTP lúc',
        readonly=True,
        copy=False,
    )
    otp_used_at = fields.Datetime(
        string='Dùng OTP lúc',
        readonly=True,
        copy=False,
    )
    otp_attempt_count = fields.Integer(
        string='Số lần nhập sai',
        readonly=True,
        default=0,
        copy=False,
    )
    otp_max_attempts = fields.Integer(
        string='Số lần nhập tối đa',
        readonly=True,
        default=OTP_MAX_ATTEMPTS,
        copy=False,
    )
    otp_destination = fields.Char(
        string='Nơi nhận OTP',
        readonly=True,
        copy=False,
    )
    otp_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Người nhận OTP',
        readonly=True,
        copy=False,
        ondelete='set null',
    )
    otp_code_input = fields.Char(
        string='Mã OTP',
        store=False,
        copy=False,
    )
    otp_feedback = fields.Char(readonly=True, copy=False)
    signature_hash = fields.Char(
        string='Mã băm chữ ký',
        readonly=True,
        copy=False,
        index=True,
    )
    document_hash = fields.Char(
        string='Mã băm tài liệu',
        readonly=True,
        copy=False,
    )
    certificate_serial = fields.Char(
        string='Mã chứng thư nội bộ',
        readonly=True,
        copy=False,
    )
    signature_ip = fields.Char(
        string='Địa chỉ IP',
        readonly=True,
        copy=False,
    )
    signature_device = fields.Char(
        string='Thiết bị',
        readonly=True,
        copy=False,
    )
    signature_payload = fields.Text(readonly=True, copy=False)
    signature_nonce = fields.Char(readonly=True, copy=False)
    signature_valid = fields.Boolean(
        string='Chữ ký hợp lệ',
        compute='_compute_signature_valid',
    )

    _sql_constraints = [
        (
            'signature_batch_station_document_unique',
            'unique(batch_id, station_id, document_type)',
            'Mỗi trạm chỉ có một hồ sơ cùng loại trong một batch.',
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        if (
            self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs')
            and not self.env.user.has_group('base.group_system')
        ):
            for vals in vals_list:
                allowed_fields = {
                    'batch_id',
                    'station_id',
                    'document_type',
                    'contract_id',
                    'negotiation_minutes_id',
                }
                if set(vals) - allowed_fields:
                    raise AccessError(
                        _('KSGS không được đặt trạng thái hoặc file ký trên dòng batch.')
                    )
                batch = self.env['bts.contract.signature.batch'].browse(
                    vals.get('batch_id')
                )
                station = self.env['project.task'].browse(vals.get('station_id'))
                if (
                    not batch
                    or batch.state != 'draft'
                    or batch.created_by_id != self.env.user
                    or station.project_id != batch.project_id
                ):
                    raise AccessError(
                        _('KSGS chỉ được thêm hồ sơ của đúng dự án vào batch dự thảo do mình tạo.')
                    )
                allowed_types = (
                    {'land_contract', 'negotiation_minutes'}
                    if batch.phase == 'phase_1'
                    else {'station_lease_contract'}
                )
                if vals.get('document_type') not in allowed_types:
                    raise AccessError(
                        _('Loại hồ sơ không phù hợp với giai đoạn ký số.')
                    )
        return super().create(vals_list)

    def write(self, vals):
        otp_code = vals.pop('otp_code_input', False)
        is_system = self.env.user.has_group('base.group_system')
        is_director = self.env.user.has_group(
            'dtc_bts_contract.group_dtc_bts_contract_director'
        )
        if not is_system and is_director:
            allowed_fields = {
                'signed_document',
                'signed_document_filename',
                'state',
                'signed_by_id',
                'signed_date',
                'otp_channel',
            }
            if self.env.context.get('digital_signature_otp'):
                allowed_fields |= {
                    'otp_state',
                    'otp_hash',
                    'otp_salt',
                    'otp_expires_at',
                    'otp_sent_at',
                    'otp_used_at',
                    'otp_attempt_count',
                    'otp_max_attempts',
                    'otp_destination',
                    'otp_user_id',
                    'otp_feedback',
                }
            if self.env.context.get('digital_signature_sign'):
                allowed_fields |= {
                    'signature_hash',
                    'document_hash',
                    'certificate_serial',
                    'signature_ip',
                    'signature_device',
                    'signature_payload',
                    'signature_nonce',
                    'otp_state',
                    'otp_hash',
                    'otp_salt',
                    'otp_used_at',
                    'otp_feedback',
                }
            if set(vals) - allowed_fields:
                raise AccessError(
                    _('BGĐ chỉ được tải file ký và xác nhận dòng batch.')
                )
            workflow_fields = {'state', 'signed_by_id', 'signed_date'}
            if (
                workflow_fields.intersection(vals)
                and not (
                    self.env.context.get('signature_line_sign')
                    or self.env.context.get('signature_batch_reject')
                    or self.env.context.get('digital_signature_sign')
                )
            ):
                raise AccessError(
                    _('Dòng batch chỉ được xác nhận qua nút Ký số / xác nhận ký.')
                )
            if 'state' in vals:
                valid_state = (
                    (
                        self.env.context.get('signature_line_sign')
                        or self.env.context.get('digital_signature_sign')
                    )
                    and vals['state'] == 'signed'
                ) or (
                    self.env.context.get('signature_batch_reject')
                    and vals['state'] == 'rejected'
                )
                if not valid_state:
                    raise AccessError(
                        _('Trạng thái dòng batch không phù hợp thao tác hiện tại.')
                    )
        result = super().write(vals)
        if otp_code:
            self._process_otp_input(otp_code)
        return result

    @api.depends(
        'contract_id.initial_document',
        'contract_id.initial_document_filename',
        'negotiation_minutes_id.initial_document',
        'negotiation_minutes_id.initial_document_filename',
    )
    def _compute_source_document(self):
        for line in self:
            document = line.contract_id or line.negotiation_minutes_id
            line.source_document = document.initial_document
            line.source_document_filename = document.initial_document_filename

    @api.constrains(
        'document_type',
        'contract_id',
        'negotiation_minutes_id',
    )
    def _check_document_reference(self):
        for line in self:
            if line.document_type == 'negotiation_minutes':
                valid = line.negotiation_minutes_id and not line.contract_id
            else:
                valid = line.contract_id and not line.negotiation_minutes_id
            if not valid:
                raise ValidationError(
                    'Dòng batch phải liên kết đúng một hồ sơ theo loại đã chọn.'
                )
            document_station = (
                line.contract_id.station_id
                if line.contract_id
                else line.negotiation_minutes_id.station_id
            )
            if document_station != line.station_id:
                raise ValidationError(
                    'Hồ sơ trong dòng batch không thuộc đúng trạm đã chọn.'
                )

    def action_sign(self):
        """Open the OTP signing dialog for one pending document."""
        self.mapped('batch_id')._check_director()
        self.ensure_one()
        self._check_can_digitally_sign()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Ký số hồ sơ'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'dtc_bts_contract.view_bts_contract_signature_otp_form'
            ).id,
            'target': 'new',
        }

    def _check_can_digitally_sign(self):
        self.ensure_one()
        if self.batch_id.state not in ('submitted', 'partially_signed'):
            raise ValidationError(
                'Chỉ có thể ký hồ sơ trong batch đang chờ ký.'
            )
        if self.state != 'pending':
            raise ValidationError('Hồ sơ này không còn ở trạng thái Chờ ký.')
        if not self.source_document:
            raise ValidationError('Hồ sơ chưa có tài liệu nguồn để ký số.')

    def action_send_signature_otp(self):
        self.mapped('batch_id')._check_director()
        for line in self:
            line._check_can_digitally_sign()
            code = '%06d' % secrets.randbelow(1000000)
            salt = secrets.token_hex(16)
            now = fields.Datetime.now()
            destination = line._get_otp_destination()
            line.with_context(digital_signature_otp=True).write({
                'otp_state': 'sent',
                'otp_hash': line._hash_otp(code, salt),
                'otp_salt': salt,
                'otp_expires_at': (
                    now + timedelta(minutes=OTP_VALIDITY_MINUTES)
                ),
                'otp_sent_at': now,
                'otp_used_at': False,
                'otp_attempt_count': 0,
                'otp_max_attempts': OTP_MAX_ATTEMPTS,
                'otp_destination': line._mask_destination(destination),
                'otp_user_id': self.env.user.id,
                'otp_feedback': False,
            })
            if line.otp_channel == 'email':
                line._send_otp_email(destination, code)
            else:
                line._send_otp_sms(destination, code)
            line.batch_id.message_post(body=_(
                'Đã gửi OTP ký số hồ sơ %(document)s qua %(channel)s '
                'tới %(destination)s.',
                document=escape(line.display_name),
                channel=dict(
                    line._fields['otp_channel'].selection
                ).get(line.otp_channel),
                destination=escape(line.otp_destination),
            ))
        return self.ensure_one().action_sign()

    def _get_otp_destination(self):
        self.ensure_one()
        partner = self.env.user.partner_id
        if self.otp_channel == 'email':
            destination = self.env.user.email or partner.email
            label = 'email'
        else:
            destination = partner.mobile or partner.phone
            label = 'số điện thoại'
        if not destination:
            raise ValidationError(
                _('Tài khoản người ký chưa được cấu hình %s.') % label
            )
        return destination.strip()

    @staticmethod
    def _hash_otp(code, salt):
        return hashlib.pbkdf2_hmac(
            'sha256',
            code.encode('utf-8'),
            salt.encode('utf-8'),
            OTP_HASH_ITERATIONS,
        ).hex()

    @staticmethod
    def _mask_destination(destination):
        if '@' in destination:
            local, domain = destination.split('@', 1)
            return '%s***@%s' % (local[:2], domain)
        return '%s***%s' % (destination[:3], destination[-3:])

    def _send_otp_email(self, destination, code):
        self.ensure_one()
        template = self.env.ref(
            'dtc_bts_contract.mail_template_signature_otp',
            raise_if_not_found=False,
        )
        if not template:
            raise ValidationError(
                _('Không tìm thấy template email OTP ký số.')
            )
        try:
            template.sudo().with_context(
                otp_code=code,
                otp_validity_minutes=OTP_VALIDITY_MINUTES,
                recipient_name=self.env.user.display_name,
            ).send_mail(
                self.id,
                force_send=True,
                raise_exception=True,
                email_values={'email_to': destination},
            )
        except Exception as error:
            raise ValidationError(_(
                'Không thể gửi OTP qua email. Vui lòng kiểm tra cấu hình '
                'Outgoing Mail Server. Chi tiết: %(error)s',
                error=str(error),
            )) from error

    def _send_otp_sms(self, destination, code):
        """Integration hook for the SMS provider."""
        self.ensure_one()
        _logger.info(
            'Mock SMS signature OTP to %s for batch line %s: %s',
            destination,
            self.id,
            code,
        )

    def _process_otp_input(self, code):
        for line in self:
            line._check_can_digitally_sign()
            if line.otp_user_id != self.env.user:
                raise AccessError(
                    _('OTP này được cấp cho người ký khác. Vui lòng gửi mã mới.')
                )
            now = fields.Datetime.now()
            feedback = False
            if line.otp_state in ('used', 'verified'):
                feedback = _('OTP đã được sử dụng và không thể dùng lại.')
            elif line.otp_state == 'locked':
                feedback = _(
                    'OTP đã bị khóa do nhập sai quá số lần cho phép.'
                )
            elif (
                line.otp_state != 'sent'
                or not line.otp_expires_at
                or line.otp_expires_at <= now
            ):
                line.with_context(digital_signature_otp=True).write({
                    'otp_state': 'expired',
                    'otp_feedback': _(
                        'OTP đã hết hạn. Vui lòng gửi mã mới.'
                    ),
                })
                continue
            else:
                candidate = line._hash_otp(
                    (code or '').strip(),
                    line.otp_salt,
                )
                if hmac.compare_digest(candidate, line.otp_hash or ''):
                    line.with_context(digital_signature_otp=True).write({
                        'otp_state': 'verified',
                        'otp_feedback': False,
                    })
                    line._perform_internal_signature()
                    continue
                attempts = line.otp_attempt_count + 1
                locked = attempts >= line.otp_max_attempts
                feedback = (
                    _('OTP đã bị khóa do nhập sai quá số lần cho phép.')
                    if locked
                    else _(
                        'OTP không đúng. Bạn còn %(count)s lần thử.',
                        count=line.otp_max_attempts - attempts,
                    )
                )
                line.with_context(digital_signature_otp=True).write({
                    'otp_attempt_count': attempts,
                    'otp_state': 'locked' if locked else 'sent',
                    'otp_feedback': feedback,
                })
                continue
            line.with_context(digital_signature_otp=True).write({
                'otp_feedback': feedback,
            })

    def action_confirm_digital_signature(self):
        self.ensure_one()
        if self.state == 'signed':
            return {'type': 'ir.actions.act_window_close'}
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Chưa thể ký số'),
                'message': self.otp_feedback or _(
                    'Vui lòng nhập OTP hợp lệ trước khi ký số.'
                ),
                'type': 'warning',
                'sticky': True,
                'next': self.action_sign(),
            },
        }

    def _perform_internal_signature(self):
        self.ensure_one()
        self._check_can_digitally_sign()
        now = fields.Datetime.now()
        document_hash = self._get_source_document_hash()
        nonce = secrets.token_hex(16)
        certificate_serial = 'INTERNAL-%s-%s' % (
            self.env.company.id,
            self.env.user.id,
        )
        ip_address, device = self._get_request_metadata()
        payload_values = {
            'batch_id': self.batch_id.id,
            'line_id': self.id,
            'document_type': self.document_type,
            'document_id': (
                self.contract_id.id or self.negotiation_minutes_id.id
            ),
            'document_hash': document_hash,
            'signer_id': self.env.user.id,
            'signed_at': fields.Datetime.to_string(now),
            'certificate_serial': certificate_serial,
            'nonce': nonce,
        }
        payload = json.dumps(
            payload_values,
            ensure_ascii=False,
            sort_keys=True,
            separators=(',', ':'),
        )
        signature_hash = hmac.new(
            self._get_internal_signing_secret().encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()
        self._apply_signed_document()
        self.with_context(digital_signature_sign=True).write({
            'signed_document': self.source_document,
            'signed_document_filename': self.source_document_filename,
            'state': 'signed',
            'signed_by_id': self.env.user.id,
            'signed_date': now,
            'otp_state': 'used',
            'otp_hash': False,
            'otp_salt': False,
            'otp_used_at': now,
            'otp_feedback': False,
            'document_hash': document_hash,
            'signature_hash': signature_hash,
            'certificate_serial': certificate_serial,
            'signature_ip': ip_address,
            'signature_device': device,
            'signature_payload': payload,
            'signature_nonce': nonce,
        })
        self.batch_id.message_post(body=_(
            'Hồ sơ %(document)s đã được %(signer)s ký số nội bộ. '
            'Mã băm chữ ký: %(signature_hash)s',
            document=escape(self.display_name),
            signer=escape(self.env.user.display_name),
            signature_hash=escape(signature_hash),
        ))
        self.batch_id._refresh_signing_state()

    def _get_source_document_hash(self):
        self.ensure_one()
        document = self.source_document or b''
        if isinstance(document, str):
            document = document.encode('ascii')
        try:
            content = base64.b64decode(document, validate=True)
        except (ValueError, TypeError):
            content = document
        return hashlib.sha256(content).hexdigest()

    def _get_internal_signing_secret(self):
        parameters = self.env['ir.config_parameter'].sudo()
        key = 'dtc_bts_contract.internal_signing_secret'
        secret = parameters.get_param(key)
        if not secret:
            secret = secrets.token_hex(32)
            parameters.set_param(key, secret)
        return secret

    @api.depends(
        'signature_hash',
        'signature_payload',
        'document_hash',
        'contract_id.initial_document',
        'negotiation_minutes_id.initial_document',
    )
    def _compute_signature_valid(self):
        for line in self:
            if not line.signature_hash or not line.signature_payload:
                line.signature_valid = False
                continue
            expected_hash = hmac.new(
                line._get_internal_signing_secret().encode('utf-8'),
                line.signature_payload.encode('utf-8'),
                hashlib.sha256,
            ).hexdigest()
            line.signature_valid = bool(
                hmac.compare_digest(expected_hash, line.signature_hash)
                and line.document_hash == line._get_source_document_hash()
            )

    @staticmethod
    def _get_request_metadata():
        try:
            from odoo.http import request

            http_request = request.httprequest
            forwarded_for = http_request.headers.get('X-Forwarded-For', '')
            ip_address = (
                forwarded_for.split(',')[0].strip()
                if forwarded_for
                else http_request.remote_addr
            )
            return ip_address, http_request.headers.get('User-Agent')
        except (AttributeError, RuntimeError):
            return False, False

    @api.model
    def _cron_expire_signature_otps(self):
        expired_lines = self.search([
            ('otp_state', '=', 'sent'),
            ('otp_expires_at', '!=', False),
            ('otp_expires_at', '<=', fields.Datetime.now()),
        ])
        expired_lines.with_context(digital_signature_otp=True).write({
            'otp_state': 'expired',
            'otp_feedback': _('OTP đã tự động hết hạn.'),
        })

    def _apply_signed_document(self):
        self.ensure_one()
        signed_date = fields.Date.context_today(self)
        if self.contract_id:
            self.contract_id.with_context(signature_line_sign=True).write({
                'signed_document': self.source_document,
                'signed_document_filename': self.source_document_filename,
                'approved_by_id': self.env.user.id,
                'signed_date': signed_date,
                'state': 'active',
            })
            self.contract_id._schedule_expiry_activity()
        else:
            self.negotiation_minutes_id.with_context(
                signature_line_sign=True
            ).write({
                'signed_document': self.source_document,
                'signed_document_filename': self.source_document_filename,
                'approved_by_id': self.env.user.id,
                'signed_date': signed_date,
                'state': 'confirmed',
            })
