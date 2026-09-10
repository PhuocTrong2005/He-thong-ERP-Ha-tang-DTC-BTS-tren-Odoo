import hashlib
import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


_logger = logging.getLogger(__name__)


class BtsContract(models.Model):
    _name = 'bts.contract'
    _description = 'Hợp đồng trạm BTS'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expiration_date asc, contract_code asc'

    # -------------------------------------------------------------------------
    # Fields định danh
    # -------------------------------------------------------------------------
    contract_code = fields.Char(
        string='Mã hợp đồng',
        required=True,
        copy=False,
        index=True,
        default=lambda self: _('Mới'),
    )
    contract_type = fields.Selection(
        selection=[
            ('land_lease', 'Thuê đất'),
            ('infrastructure_lease', 'Cho thuê trạm'),
        ],
        string='Loại hợp đồng',
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Dự thảo'),
            ('submitted', 'Chờ ký duyệt'),
            ('active', 'Hiệu lực'),
            ('renewal_agreed', 'Đã thống nhất gia hạn'),
            ('liquidated', 'Đã thanh lý'),
            ('expired', 'Hết hạn'),
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
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Đối tác',
        index=True,
        ondelete='restrict',
    )
    # BGĐ phê duyệt/ký hợp đồng
    approved_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người ký duyệt (BGĐ)',
        ondelete='set null',
        tracking=True,
    )
    signed_date = fields.Date(string='Ngày ký duyệt', tracking=True)

    # KSGS tạo hợp đồng
    created_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người lập hợp đồng',
        default=lambda self: self.env.uid,
        ondelete='set null',
    )
    related_land_contract_id = fields.Many2one(
        comodel_name='bts.contract',
        string='Hợp đồng thuê đất liên quan',
        ondelete='restrict',
        domain="[('contract_type', '=', 'land_lease'), ('station_id', '=', station_id)]",
        help='Bắt buộc đối với hợp đồng thuê hạ tầng.',
    )

    # -------------------------------------------------------------------------
    # Thông tin hợp đồng
    # -------------------------------------------------------------------------
    sign_date = fields.Date(string='Ngày ký hợp đồng')
    effective_date = fields.Date(string='Ngày hiệu lực', tracking=True)
    expiration_date = fields.Date(string='Ngày hết hạn', tracking=True, index=True)
    term_years = fields.Integer(string='Thời hạn (năm)')
    rental_price = fields.Monetary(
        string='Giá thuê',
        currency_field='currency_id',
    )
    payment_cycle = fields.Selection(
        selection=[
            ('monthly', 'Hàng tháng'),
            ('quarterly', 'Hàng quý'),
            ('biannual', 'Nửa năm'),
            ('yearly', 'Hàng năm'),
        ],
        string='Chu kỳ thanh toán',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Tiền tệ',
        default=lambda self: self.env.company.currency_id,
    )
    alert_before_days = fields.Integer(
        string='Nhắc trước (ngày)',
        default=30,
        help='Số ngày trước khi hết hạn sẽ tạo nhắc nhở.',
    )
    notes = fields.Text(string='Ghi chú')
    initial_document = fields.Binary(
        string='Hợp đồng ban đầu',
        attachment=True,
    )
    initial_document_filename = fields.Char(string='Tên tệp hợp đồng ban đầu')
    signed_document = fields.Binary(
        string='Hợp đồng đã ký số',
        attachment=True,
    )
    signed_document_filename = fields.Char(string='Tên tệp hợp đồng đã ký số')
    digital_signature_state = fields.Selection(
        selection=[
            ('not_signed', 'Chưa ký số'),
            ('waiting', 'Chờ ký số'),
            ('signed', 'Đã ký số'),
        ],
        string='Trạng thái ký số',
        compute='_compute_digital_signature_state',
        store=True,
    )
    signature_line_ids = fields.One2many(
        comodel_name='bts.contract.signature.batch.line',
        inverse_name='contract_id',
        string='Lịch sử ký số',
        readonly=True,
    )

    # Tab gia hạn
    renewal_ids = fields.One2many(
        comodel_name='bts.contract.renewal',
        inverse_name='contract_id',
        string='Lịch sử gia hạn',
    )
    renewal_count = fields.Integer(
        string='Số lần gia hạn',
        compute='_compute_renewal_count',
    )

    # -------------------------------------------------------------------------
    # Fields tính toán
    # -------------------------------------------------------------------------
    days_to_expiration = fields.Integer(
        string='Số ngày còn lại',
        compute='_compute_days_to_expiration',
    )
    is_expiring_soon = fields.Boolean(
        string='Sắp hết hạn',
        compute='_compute_days_to_expiration',
    )
    is_expiring_within_30_days = fields.Boolean(
        string='Còn không quá 30 ngày',
        compute='_compute_is_expiring_within_30_days',
        search='_search_is_expiring_within_30_days',
    )

    # -------------------------------------------------------------------------
    # Constraints SQL
    # -------------------------------------------------------------------------
    _sql_constraints = [
        (
            'contract_code_unique',
            'unique(contract_code)',
            'Mã hợp đồng đã tồn tại. Vui lòng dùng mã khác.',
        ),
        (
            'term_years_positive',
            'CHECK(term_years IS NULL OR term_years > 0)',
            'Thời hạn hợp đồng phải lớn hơn 0.',
        ),
        (
            'alert_before_days_positive',
            'CHECK(alert_before_days > 0)',
            'Số ngày nhắc trước phải lớn hơn 0.',
        ),
    ]

    # -------------------------------------------------------------------------
    # Compute
    # -------------------------------------------------------------------------
    @api.depends('expiration_date', 'state')
    def _compute_days_to_expiration(self):
        today = date.today()
        for contract in self:
            if contract.expiration_date and contract.state == 'active':
                delta = (contract.expiration_date - today).days
                contract.days_to_expiration = delta
                contract.is_expiring_soon = 0 <= delta <= contract.alert_before_days
            else:
                contract.days_to_expiration = 0
                contract.is_expiring_soon = False

    def _compute_renewal_count(self):
        for contract in self:
            contract.renewal_count = len(contract.renewal_ids)

    @api.depends('state', 'signed_document', 'signature_line_ids.state')
    def _compute_digital_signature_state(self):
        for contract in self:
            if (
                contract.signature_line_ids.filtered(
                    lambda line: line.state == 'signed'
                )
                or contract.signed_document
            ):
                contract.digital_signature_state = 'signed'
            elif contract.state == 'submitted':
                contract.digital_signature_state = 'waiting'
            else:
                contract.digital_signature_state = 'not_signed'

    @api.depends('expiration_date', 'state')
    def _compute_is_expiring_within_30_days(self):
        today = fields.Date.context_today(self)
        deadline = today + timedelta(days=30)
        for contract in self:
            contract.is_expiring_within_30_days = bool(
                contract.state == 'active'
                and contract.expiration_date
                and today <= contract.expiration_date <= deadline
            )

    @api.model
    def _search_is_expiring_within_30_days(self, operator, value):
        today = fields.Date.context_today(self)
        deadline = today + timedelta(days=30)
        positive = (
            (operator in ('=', '==') and value)
            or (operator == '!=' and not value)
        )
        if positive:
            return [
                ('state', '=', 'active'),
                ('expiration_date', '>=', today),
                ('expiration_date', '<=', deadline),
            ]
        return [
            '|',
            ('state', '!=', 'active'),
            '|',
            ('expiration_date', '=', False),
            '|',
            ('expiration_date', '<', today),
            ('expiration_date', '>', deadline),
        ]

    @api.model
    def _get_contract_due_overview(self, contracts):
        """Return the contract expiry summary used by project/station views."""
        today = fields.Date.context_today(self)
        relevant = contracts.filtered(
            lambda contract: (
                contract.state in ('active', 'renewal_agreed')
                and contract.expiration_date
            )
        )
        overdue = relevant.filtered(
            lambda contract: contract.expiration_date < today
        )
        expiring = relevant.filtered(
            lambda contract: (
                0 <= (contract.expiration_date - today).days <= 30
            )
        )
        nearest_date = min(
            relevant.mapped('expiration_date'),
            default=False,
        )

        required_action = 'monitor'
        due_contracts = overdue | expiring
        if due_contracts.filtered(
            lambda contract: contract.contract_type == 'land_lease'
        ):
            required_action = 'renew_land_first'
        else:
            infrastructure_due = due_contracts.filtered(
                lambda contract: (
                    contract.contract_type == 'infrastructure_lease'
                )
            )
            for infrastructure_contract in infrastructure_due:
                renewal_years = infrastructure_contract.term_years or 1
                required_land_expiration = (
                    infrastructure_contract.expiration_date
                    + relativedelta(years=renewal_years)
                )
                sufficient_land_contract = relevant.filtered(
                    lambda contract: (
                        contract.station_id
                        == infrastructure_contract.station_id
                        and contract.contract_type == 'land_lease'
                        and contract.expiration_date
                        >= required_land_expiration
                    )
                )
                if not sufficient_land_contract:
                    required_action = 'renew_land_first'
                    break
                required_action = 'renew_infrastructure'

        if overdue:
            due_status = 'overdue'
            due_priority = 1
        elif expiring:
            due_status = 'expiring'
            due_priority = 2
        elif relevant:
            due_status = 'valid'
            due_priority = 3
        else:
            due_status = 'no_active'
            due_priority = 4

        return {
            'contract_count': len(contracts),
            'active_contract_count': len(relevant),
            'expiring_contract_count': len(expiring),
            'expiring_station_count': len(expiring.mapped('station_id')),
            'overdue_contract_count': len(overdue),
            'nearest_contract_expiration_date': nearest_date,
            'nearest_contract_days_left': (
                (nearest_date - today).days if nearest_date else 0
            ),
            'contract_due_status': due_status,
            'contract_due_priority': due_priority,
            'contract_action_required': required_action,
        }

    # -------------------------------------------------------------------------
    # Constrains Python
    # -------------------------------------------------------------------------
    @api.constrains('effective_date', 'expiration_date')
    def _check_date_range(self):
        for contract in self:
            if (
                contract.effective_date
                and contract.expiration_date
                and contract.expiration_date < contract.effective_date
            ):
                raise ValidationError('Ngày hết hạn phải sau ngày hiệu lực.')

    @api.constrains(
        'contract_type',
        'station_id',
        'related_land_contract_id',
        'state',
    )
    def _check_infrastructure_requires_land_contract(self):
        for contract in self:
            if contract.contract_type != 'infrastructure_lease':
                continue
            land_contract = contract.related_land_contract_id
            if not land_contract and contract.state != 'draft':
                raise ValidationError(
                    'Hợp đồng cho thuê trạm bắt buộc phải liên kết với hợp đồng thuê đất của trạm.'
                )
            if land_contract and (
                land_contract.contract_type != 'land_lease'
                or land_contract.station_id != contract.station_id
            ):
                raise ValidationError(
                    'Hợp đồng cho thuê trạm phải liên kết với hợp đồng thuê đất cùng trạm.'
                )

    @api.constrains('contract_type', 'partner_id')
    def _check_partner_type(self):
        for contract in self:
            pt = contract.partner_id.partner_type
            if contract.contract_type == 'land_lease' and pt and pt != 'landowner':
                raise ValidationError(
                    'Hợp đồng thuê đất phải chọn đối tác có loại là "Chủ đất".'
                )
            elif contract.contract_type == 'infrastructure_lease' and pt and pt != 'telecom_partner':
                raise ValidationError(
                    'Hợp đồng cho thuê trạm phải chọn đối tác có loại là "Đối tác viễn thông".'
                )

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        if (
            self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs')
            and not self.env.user.has_group('base.group_system')
        ):
            allowed_fields = {
                'contract_code',
                'contract_type',
                'station_id',
                'partner_id',
                'related_land_contract_id',
                'sign_date',
                'effective_date',
                'expiration_date',
                'term_years',
                'rental_price',
                'currency_id',
                'payment_cycle',
                'initial_document',
                'initial_document_filename',
                'notes',
                'state',
            }
            if any(
                set(vals) - allowed_fields
                or vals.get('state', 'draft') != 'draft'
                for vals in vals_list
            ):
                raise AccessError(
                    _('KSGS chỉ được tạo và nhập hồ sơ hợp đồng ban đầu theo trạm.')
                )
        for vals in vals_list:
            if (
                vals.get('contract_type') == 'infrastructure_lease'
                and vals.get('station_id')
                and not vals.get('related_land_contract_id')
            ):
                station = self.env['project.task'].browse(
                    vals['station_id']
                )
                land_contract = station._get_station_contract('land_lease')
                if land_contract:
                    vals['related_land_contract_id'] = land_contract.id
            if not vals.get('contract_code') or vals.get('contract_code') == _('Mới'):
                contract_type = vals.get('contract_type', 'land_lease')
                seq_code = (
                    'dtc.bts.contract.land'
                    if contract_type == 'land_lease'
                    else 'dtc.bts.contract.infra'
                )
                vals['contract_code'] = (
                    self.env['ir.sequence'].next_by_code(seq_code) or _('Mới')
                )
        return super().create(vals_list)

    def write(self, vals):
        must_reschedule_expiry = bool(
            {'expiration_date', 'alert_before_days', 'state'} & set(vals)
        )
        is_system = self.env.user.has_group('base.group_system')
        is_ksgs = self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs')
        is_infrastructure = self.env.user.has_group(
            'dtc_bts_base.group_dtc_bts_infrastructure'
        )
        is_director = self.env.user.has_group(
            'dtc_bts_contract.group_dtc_bts_contract_director'
        )
        if not is_system and is_ksgs:
            allowed_fields = {
                'contract_code',
                'contract_type',
                'station_id',
                'partner_id',
                'related_land_contract_id',
                'sign_date',
                'effective_date',
                'expiration_date',
                'term_years',
                'rental_price',
                'currency_id',
                'payment_cycle',
                'initial_document',
                'initial_document_filename',
                'notes',
            }
            if (
                self.env.context.get('signature_batch_submission')
                and vals.get('state') == 'submitted'
            ):
                allowed_fields.add('state')
            if set(vals) - allowed_fields:
                raise AccessError(
                    _('KSGS chỉ được cập nhật thông tin hồ sơ hợp đồng ban đầu theo trạm.')
                )
            if any(contract.state != 'draft' for contract in self):
                raise AccessError(
                    _('KSGS không thể sửa hồ sơ đã được gửi vào quy trình ký số.')
                )
        if not is_system and 'state' in vals and not is_ksgs:
            target_state = vals['state']
            if is_infrastructure:
                context_states = {
                    'contract_infrastructure_submit': 'submitted',
                    'contract_infrastructure_renewal': 'renewal_agreed',
                    'contract_infrastructure_cancel': 'cancelled',
                    'contract_infrastructure_reset': 'draft',
                }
            elif is_director:
                context_states = {
                    'contract_director_sign': 'active',
                    'contract_director_liquidate': 'liquidated',
                    'contract_director_reject': 'cancelled',
                    'director_renewal_signature': 'active',
                    'signature_line_sign': 'active',
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
                    _('Bạn không được phép chuyển hợp đồng sang trạng thái này.')
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
                _('Chỉ BGĐ hợp đồng được cập nhật thông tin ký số.')
            )
        if not is_system and is_director:
            allowed_fields = signed_fields | {'state'}
            if self.env.context.get('director_renewal_signature'):
                allowed_fields |= {
                    'sign_date',
                    'effective_date',
                    'expiration_date',
                    'rental_price',
                }
            if set(vals) - allowed_fields:
                raise AccessError(
                    _('BGĐ chỉ được cập nhật thông tin ký số và trạng thái phê duyệt.')
                )
        result = super().write(vals)
        if must_reschedule_expiry:
            self._clear_expiry_activities()
            active_contracts = self.filtered(
                lambda contract: contract.state == 'active'
            )
            active_contracts._schedule_expiry_activities()
        return result

    def _get_initial_dossier_missing_fields(self):
        """Return labels of data required before the initial batch is sent."""
        self.ensure_one()
        missing = []
        required_fields = (
            ('partner_id', 'Đối tác'),
            ('effective_date', 'Ngày hiệu lực'),
            ('expiration_date', 'Ngày hết hạn'),
            ('term_years', 'Thời hạn'),
            ('initial_document', 'File scan hợp đồng'),
        )
        for field_name, label in required_fields:
            if not self[field_name]:
                missing.append(label)
        if (
            self.contract_type == 'infrastructure_lease'
            and not self.related_land_contract_id
        ):
            missing.append('HĐ thuê đất liên quan')
        if self.state != 'draft':
            missing.append('Hồ sơ không ở trạng thái có thể gửi ký')
        return missing

    # -------------------------------------------------------------------------
    # Actions chuyển trạng thái theo UC
    # -------------------------------------------------------------------------
    def _check_contract_director(self):
        if (
            self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs')
            and not self.env.user.has_group('base.group_system')
        ):
            raise AccessError(
                _('KSGS không được ký hoặc từ chối từng hợp đồng riêng lẻ.')
            )
        if not (
            self.env.user.has_group(
                'dtc_bts_contract.group_dtc_bts_contract_director'
            )
            or self.env.user.has_group('base.group_system')
        ):
            raise AccessError(
                _('Chỉ Ban Giám đốc phụ trách hợp đồng mới được ký duyệt.')
            )

    def _check_contract_preparer(self):
        if (
            self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs')
            and not self.env.user.has_group('base.group_system')
        ):
            raise AccessError(
                _(
                    'KSGS không trình duyệt từng hợp đồng; '
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
                _('Chỉ Tổ quản lý hạ tầng được trình hồ sơ hợp đồng.')
            )

    def _check_contract_renewal_user(self):
        if not (
            self.env.user.has_group(
                'dtc_bts_base.group_dtc_bts_infrastructure'
            )
            or self.env.user.has_group('base.group_system')
        ):
            raise AccessError(
                _('Bạn không có quyền xử lý gia hạn hợp đồng.')
            )

    def action_submit(self):
        """Tổ hạ tầng trình duyệt hợp đồng lên BGĐ."""
        self._check_contract_preparer()
        for contract in self:
            if contract.state != 'draft':
                raise ValidationError('Chỉ có thể trình duyệt hợp đồng ở trạng thái Dự thảo.')
            if not contract.initial_document:
                raise ValidationError(
                    'Vui lòng tải lên hợp đồng ban đầu trước khi trình duyệt.'
                )
            if not contract.partner_id:
                raise ValidationError(
                    'Vui lòng chọn đối tác trước khi trình duyệt hợp đồng.'
                )
            if (
                contract.contract_type == 'infrastructure_lease'
                and not contract.related_land_contract_id
            ):
                raise ValidationError(
                    'Hợp đồng cho thuê trạm phải liên kết với hợp đồng thuê đất của trạm.'
                )
            contract.with_context(
                contract_infrastructure_submit=True
            ).state = 'submitted'

    def action_activate(self):
        """Open OTP signing for the pending batch document."""
        self._check_contract_director()
        self.ensure_one()
        pending_line = self.signature_line_ids.filtered(
            lambda line: (
                line.state == 'pending'
                and line.batch_id.state in ('submitted', 'partially_signed')
            )
        )[:1]
        if not pending_line:
            raise ValidationError(
                'Không tìm thấy hồ sơ chờ ký trong batch của dự án. '
                'KSGS cần gửi batch ký số trước khi Ban Giám đốc thực hiện ký.'
            )
        return pending_line.action_sign()

    def action_renewal_agreed(self):
        """Tổ hạ tầng đánh dấu đã thống nhất gia hạn."""
        self._check_contract_renewal_user()
        for contract in self:
            if contract.state != 'active':
                raise ValidationError('Chỉ có thể đánh dấu gia hạn khi hợp đồng đang hiệu lực.')
            contract.with_context(
                contract_infrastructure_renewal=True
            ).state = 'renewal_agreed'

    def action_liquidate(self):
        """BGĐ ký duyệt chấm dứt hợp đồng."""
        self._check_contract_director()
        for contract in self:
            if contract.state not in ('active', 'renewal_agreed', 'expired'):
                raise ValidationError('Không thể thanh lý hợp đồng ở trạng thái hiện tại.')
            contract.with_context(
                contract_director_liquidate=True
            ).state = 'liquidated'

    def action_cancel(self):
        for contract in self:
            if contract.state in ('liquidated', 'expired'):
                raise ValidationError('Không thể hủy hợp đồng đã thanh lý hoặc đã hết hạn.')
            if contract.state == 'submitted':
                contract._check_contract_director()
                contract = contract.with_context(contract_director_reject=True)
            else:
                contract._check_contract_preparer()
                contract = contract.with_context(
                    contract_infrastructure_cancel=True
                )
            contract.state = 'cancelled'

    def action_reset_to_draft(self):
        self._check_contract_preparer()
        for contract in self:
            if contract.state not in ('cancelled', 'submitted'):
                raise ValidationError('Chỉ có thể đặt lại về Dự thảo khi hợp đồng đã bị hủy hoặc từ chối.')
            contract.with_context(
                contract_infrastructure_reset=True
            ).state = 'draft'

    def action_create_renewal(self):
        """Tổ hạ tầng tạo bản ghi gia hạn."""
        self.ensure_one()
        self._check_contract_renewal_user()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tạo bản ghi gia hạn'),
            'res_model': 'bts.contract.renewal',
            'view_mode': 'form',
            'context': {
                'default_contract_id': self.id,
            },
            'target': 'new',
        }

    def action_report_renewal_failure(self):
        """Open or create the actionable renewal report for infrastructure."""
        self.ensure_one()
        self._check_contract_renewal_user()
        if self.state not in ('active', 'renewal_agreed', 'expired'):
            raise ValidationError(_(
                'Chỉ có thể báo gia hạn thất bại cho hợp đồng đang hiệu lực, '
                'đã thống nhất gia hạn hoặc đã hết hạn.'
            ))
        renewal = self.env['bts.contract.renewal'].search([
            ('contract_id', '=', self.id),
            ('state', 'in', ('draft', 'in_progress')),
            ('non_renewal_reported_at', '=', False),
        ], order='id desc', limit=1)
        if not renewal:
            renewal = self.env['bts.contract.renewal'].create({
                'contract_id': self.id,
                'renewal_date': fields.Date.context_today(self),
            })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Báo gia hạn thất bại'),
            'res_model': 'bts.contract.renewal',
            'res_id': renewal.id,
            'view_mode': 'form',
            'views': [(
                self.env.ref(
                    'dtc_bts_contract.view_bts_contract_renewal_form'
                ).id,
                'form',
            )],
            'target': 'current',
        }

    # -------------------------------------------------------------------------
    # Nhắc hạn hợp đồng
    # -------------------------------------------------------------------------
    def _clear_expiry_activities(self):
        return self._bts_close_activities(
            'dtc_bts_contract.mail_activity_type_contract_expiring',
            feedback=_('Cảnh báo hết hạn hợp đồng không còn cần xử lý.'),
        )

    def _schedule_expiry_activities(self):
        for contract in self:
            contract._schedule_expiry_activity()

    def _schedule_expiry_activity(self):
        self.ensure_one()
        if self.state != 'active' or not self.expiration_date:
            return
        today = fields.Date.context_today(self)
        alert_date = self.expiration_date - timedelta(
            days=self.alert_before_days
        )
        if alert_date > today:
            return
        alert_date = today
        infrastructure_group = self.env.ref(
            'dtc_bts_base.group_dtc_bts_infrastructure',
            raise_if_not_found=False,
        )
        responsible_users = (
            infrastructure_group.users.filtered(lambda user: user.active)
            if infrastructure_group
            else self.env['res.users']
        )
        if not responsible_users:
            responsible_users = self.approved_by_id.filtered(
                lambda user: user.active
            )
        for user in responsible_users:
            self._bts_schedule_activity_once(
                'dtc_bts_contract.mail_activity_type_contract_expiring',
                user=user,
                deadline=alert_date,
                summary=_('Hợp đồng %s sắp hết hạn vào %s') % (
                    self.contract_code,
                    self.expiration_date.strftime('%d/%m/%Y'),
                ),
                note=_(
                    'Kiểm tra phương án gia hạn, thanh lý hoặc kết thúc hợp đồng.'
                ),
            )

    @api.model
    def _cron_check_contract_expiry(self):
        today = fields.Date.context_today(self)
        expired = self.search([
            ('state', '=', 'active'),
            ('expiration_date', '<', today),
        ])
        expired.write({'state': 'expired'})
        expiring = self.search([
            ('state', '=', 'active'),
            ('expiration_date', '>=', today),
        ])
        for contract in expiring:
            if (
                0 <= (contract.expiration_date - today).days
                <= contract.alert_before_days
            ):
                contract._schedule_expiry_activity()
        self._queue_contract_renewal_due_digests()

    @api.model
    def _queue_contract_renewal_due_digests(self):
        """Queue one per-user, per-day digest using each contract alert window.

        Same-day list changes are intentionally included in the next daily
        digest instead of creating multiple operational emails in one day.
        """
        today = fields.Date.context_today(self)
        candidates = self.search([
            ('state', '=', 'active'),
            ('expiration_date', '>=', today),
            ('expiration_date', '!=', False),
        ])
        due_contracts = candidates.filtered(
            lambda contract: (
                0 <= (contract.expiration_date - today).days
                <= contract.alert_before_days
            )
        )
        if not due_contracts:
            return self.env['mail.mail']

        group = self.env.ref(
            'dtc_bts_base.group_dtc_bts_infrastructure',
            raise_if_not_found=False,
        )
        recipients = (
            group.users.filtered(lambda user: user.active)
            if group
            else self.env['res.users']
        )
        queued_mails = self.env['mail.mail']
        for user in recipients:
            if user.bts_contract_digest_last_date == today:
                continue
            readable = self.with_user(user).search([
                ('id', 'in', due_contracts.ids),
            ])
            if not readable:
                continue
            fingerprint_source = '|'.join(
                '%s:%s:%s' % (
                    contract.id,
                    contract.expiration_date,
                    contract.state,
                )
                for contract in readable.sorted('id')
            )
            fingerprint = hashlib.sha256(
                fingerprint_source.encode('utf-8')
            ).hexdigest()
            project_rows = []
            for project in readable.mapped('project_id').sorted(
                key=lambda item: (item.display_name or '', item.id)
            ):
                contracts = readable.filtered(
                    lambda contract: contract.project_id == project
                ).sorted(
                    key=lambda contract: (
                        contract.expiration_date,
                        contract.contract_code or '',
                    )
                )
                project_rows.append({
                    'name': project.display_name or '',
                    'code': project.project_code or '',
                    'responsible': (
                        project.project_manager_id.display_name or ''
                    ),
                    'contracts': [
                        {
                            'code': contract.contract_code or '',
                            'type': dict(
                                contract._fields['contract_type'].selection
                            ).get(
                                contract.contract_type,
                                contract.contract_type,
                            ),
                            'station': (
                                contract.station_id.display_name or ''
                            ),
                            'partner': (
                                contract.partner_id.display_name or ''
                            ),
                            'start_date': contract.effective_date or '',
                            'expiration_date': contract.expiration_date,
                            'days_left': (
                                contract.expiration_date - today
                            ).days,
                            'state': dict(
                                contract._fields['state'].selection
                            ).get(contract.state, contract.state),
                            'url': contract._bts_record_url(),
                            'priority': (
                                (contract.expiration_date - today).days
                                <= min(contract.alert_before_days, 7)
                            ),
                        }
                        for contract in contracts
                    ],
                })
            anchor = readable.sorted('id')[:1]
            mails = anchor._bts_queue_workflow_email(
                'dtc_bts_contract.'
                'mail_template_contract_renewal_due_digest',
                user,
                'contract_renewal_due_digest',
                extra_context={
                    'report_date': today,
                    'project_count': len(project_rows),
                    'contract_count': len(readable),
                    'digest_projects': project_rows,
                },
            )
            if mails:
                try:
                    with self.env.cr.savepoint():
                        user.write({
                            'bts_contract_digest_last_date': today,
                            'bts_contract_digest_fingerprint': fingerprint,
                        })
                except Exception:
                    _logger.warning(
                        'contract_digest_marker_write_failed user_id=%s date=%s',
                        user.id,
                        today,
                    )
                queued_mails |= mails
        return queued_mails

    def _bts_record_url(self):
        self.ensure_one()
        base_url = self.get_base_url()
        return (
            '%s/web#id=%s&model=%s&view_type=form'
            % (base_url.rstrip('/'), self.id, self._name)
            if base_url
            else False
        )
