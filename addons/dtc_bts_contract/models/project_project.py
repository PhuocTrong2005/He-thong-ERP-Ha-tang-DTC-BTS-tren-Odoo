from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    _contract_cancel_audit_fields = {
        'contract_cancel_decision_by_id',
        'contract_cancel_decision_at',
        'contract_cancel_reason',
        'contract_cancel_source_model',
        'contract_cancel_source_id',
    }

    contract_cancel_decision_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người quyết định hủy hợp đồng',
        readonly=True,
        copy=False,
    )
    contract_cancel_decision_at = fields.Datetime(
        string='Thời gian quyết định hủy hợp đồng',
        readonly=True,
        copy=False,
    )
    contract_cancel_reason = fields.Text(
        string='Lý do quyết định hủy hợp đồng',
        readonly=True,
        copy=False,
    )
    contract_cancel_source_model = fields.Char(
        string='Model nguồn quyết định hủy',
        readonly=True,
        copy=False,
    )
    contract_cancel_source_id = fields.Integer(
        string='ID nguồn quyết định hủy',
        readonly=True,
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        if (
            not self.env.su
            and any(
                self._contract_cancel_audit_fields.intersection(vals)
                for vals in vals_list
            )
        ):
            raise AccessError(
                _('Audit quyết định hủy Project chỉ được ghi bởi workflow máy chủ.')
            )
        return super().create(vals_list)

    def write(self, vals):
        user = self.env.user
        if (
            not self.env.su
            and self._contract_cancel_audit_fields.intersection(vals)
        ):
            raise AccessError(
                _('Audit quyết định hủy Project chỉ được ghi bởi workflow máy chủ.')
            )
        if (
            user.has_group(
                'dtc_bts_contract.group_dtc_bts_contract_director'
            )
            and not self.env.su
            and not user.has_group('base.group_system')
        ):
            raise AccessError(
                _('BGĐ hợp đồng không được ghi trực tiếp Project.')
            )
        return super().write(vals)

    def _apply_contract_director_cancel(self, source):
        self.ensure_one()
        source.ensure_one()
        if not (
            self.env.user.has_group(
                'dtc_bts_contract.group_dtc_bts_contract_director'
            )
            or self.env.user.has_group('base.group_system')
        ):
            raise AccessError(_('Chỉ BGĐ hợp đồng được quyết định hủy Project.'))
        if source._name == 'bts.negotiation.minutes':
            report_exists = bool(
                source.land_negotiation_failed
                and source.land_negotiation_failed_by_id
                and source.land_negotiation_failed_at
            )
        elif source._name == 'bts.contract.renewal':
            report_exists = bool(
                source.non_renewal_type
                and source.non_renewal_reported_by_id
                and source.non_renewal_reported_at
            )
        else:
            raise ValidationError(_('Nguồn quyết định hủy Project không hợp lệ.'))
        if source.project_id != self:
            raise ValidationError(_('Nguồn quyết định không thuộc Project này.'))
        if not report_exists:
            raise ValidationError(_('Nguồn quyết định chưa có báo cáo thất bại hợp lệ.'))
        if (
            source.decision_type != 'cancel_project'
            or not source.decision_at
            or source.decision_by_id != self.env.user
            or not source.decision_reason
        ):
            raise ValidationError(_('Quyết định hủy Project chưa hợp lệ.'))
        if self.state == 'cancelled':
            raise ValidationError(_('Project đã bị hủy.'))
        decision_at = source.decision_at
        reason = source.decision_reason
        self.sudo().write({
            'state': 'cancelled',
            'contract_cancel_decision_by_id': self.env.user.id,
            'contract_cancel_decision_at': decision_at,
            'contract_cancel_reason': reason,
            'contract_cancel_source_model': source._name,
            'contract_cancel_source_id': source.id,
        })
        self.sudo().message_post(body=_(
            'BGĐ %(director)s đã hủy Project từ %(source_label)s #%(source_id)s. '
            'Lý do: %(reason)s',
            director=self.env.user.display_name,
            source_label=source._description,
            source_id=source.id,
            reason=reason,
        ))
        return True

    contract_count = fields.Integer(
        string='Tổng hợp đồng',
        compute='_compute_contract_overview',
        store=True,
    )
    active_contract_count = fields.Integer(
        string='Hợp đồng còn hiệu lực nghiệp vụ',
        compute='_compute_contract_overview',
        store=True,
    )
    expiring_contract_count = fields.Integer(
        string='Hợp đồng sắp hết hạn',
        compute='_compute_contract_overview',
        store=True,
    )
    expiring_station_count = fields.Integer(
        string='Trạm có HĐ sắp hết hạn',
        compute='_compute_contract_overview',
        store=True,
    )
    overdue_contract_count = fields.Integer(
        string='HĐ quá hạn',
        compute='_compute_contract_overview',
        store=True,
    )
    nearest_contract_expiration_date = fields.Date(
        string='Ngày hết hạn gần nhất',
        compute='_compute_contract_overview',
        store=True,
    )
    nearest_contract_days_left = fields.Integer(
        string='Còn lại (ngày)',
        compute='_compute_contract_overview',
        store=True,
    )
    contract_due_status = fields.Selection(
        selection=[
            ('overdue', 'Quá hạn'),
            ('expiring', 'Sắp hết hạn'),
            ('valid', 'Còn hạn'),
            ('no_active', 'Chưa có HĐ hiệu lực'),
        ],
        string='Trạng thái hợp đồng',
        compute='_compute_contract_overview',
        store=True,
    )
    contract_action_required = fields.Selection(
        selection=[
            ('renew_land_first', 'Gia hạn HĐ thuê đất trước'),
            ('renew_infrastructure', 'Gia hạn HĐ cho thuê trạm'),
            ('monitor', 'Theo dõi'),
        ],
        string='Cần xử lý',
        compute='_compute_contract_overview',
        store=True,
    )
    contract_due_priority = fields.Integer(
        compute='_compute_contract_overview',
        store=True,
    )

    signature_batch_ids = fields.One2many(
        comodel_name='bts.contract.signature.batch',
        inverse_name='project_id',
        string='Batch ký số hợp đồng',
    )

    @api.depends(
        'task_ids.contract_ids.state',
        'task_ids.contract_ids.contract_type',
        'task_ids.contract_ids.expiration_date',
        'task_ids.contract_ids.term_years',
        'task_ids.contract_ids.station_id',
    )
    def _compute_contract_overview(self):
        contract_model = self.env['bts.contract']
        for project in self:
            overview = contract_model._get_contract_due_overview(
                project.task_ids.contract_ids
            )
            for field_name, value in overview.items():
                project[field_name] = value

    @api.model
    def _cron_refresh_contract_overview(self):
        projects = self.search([])
        projects._compute_contract_overview()
        projects.task_ids._compute_contract_due_overview()

    def action_send_contract_signature_batch(self):
        self.ensure_one()
        if not (
            self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs')
            or self.env.user.has_group('base.group_system')
        ):
            raise AccessError(
                _('Chỉ KSGS được gửi batch hợp đồng từ form Dự án.')
            )
        stations = self.task_ids.filtered(lambda task: task.station_code)
        if not stations:
            raise ValidationError('Dự án chưa có trạm BTS để gửi ký số.')

        phase = self._get_next_signature_phase()
        line_values = self._prepare_signature_batch_lines(stations, phase)
        batch = self.env['bts.contract.signature.batch'].create({
            'project_id': self.id,
            'phase': phase,
            'line_ids': [(0, 0, values) for values in line_values],
        })
        batch.action_submit()
        action = self.env['ir.actions.actions']._for_xml_id(
            'dtc_bts_contract.action_bts_contract_signature_batch'
        )
        action.update({
            'res_id': batch.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'current',
        })
        return action

    def _get_next_signature_phase(self):
        batches = self.env['bts.contract.signature.batch'].search([
            ('project_id', '=', self.id),
        ])
        active_batch = batches.filtered(
            lambda batch: batch.state in (
                'draft',
                'submitted',
                'partially_signed',
            )
        )[:1]
        if active_batch:
            raise ValidationError(
                'Dự án đang có batch %s chưa hoàn tất.' % active_batch.name
            )
        phase_1_done = batches.filtered(
            lambda batch: batch.phase == 'phase_1' and batch.state == 'done'
        )
        phase_2_done = batches.filtered(
            lambda batch: batch.phase == 'phase_2' and batch.state == 'done'
        )
        if not phase_1_done:
            return 'phase_1'
        if not phase_2_done:
            return 'phase_2'
        raise ValidationError('Dự án đã hoàn tất ký số cả hai giai đoạn.')

    def _prepare_signature_batch_lines(self, stations, phase):
        lines = []
        missing = []
        for station in stations:
            if phase == 'phase_1':
                land_contract = station._get_station_contract('land_lease')
                minutes = (
                    station.negotiation_minutes_id
                    or station.negotiation_minute_ids[:1]
                )
                station_missing = []
                if not land_contract:
                    station_missing.append('thiếu HĐ thuê đất')
                else:
                    contract_missing = (
                        land_contract._get_initial_dossier_missing_fields()
                    )
                    if contract_missing:
                        station_missing.append(
                            'HĐ thuê đất thiếu %s'
                            % ', '.join(contract_missing)
                        )
                if not minutes:
                    station_missing.append('thiếu BB đàm phán')
                else:
                    minutes_missing = (
                        minutes._get_initial_dossier_missing_fields()
                    )
                    if minutes_missing:
                        station_missing.append(
                            'BB đàm phán thiếu %s'
                            % ', '.join(minutes_missing)
                        )
                if station_missing:
                    missing.append(
                        '%s: %s'
                        % (station.display_name, '; '.join(station_missing))
                    )
                    continue
                lines.extend([
                    {
                        'station_id': station.id,
                        'document_type': 'land_contract',
                        'contract_id': land_contract.id,
                    },
                    {
                        'station_id': station.id,
                        'document_type': 'negotiation_minutes',
                        'negotiation_minutes_id': minutes.id,
                    },
                ])
            else:
                station_contract = station._get_station_contract(
                    'infrastructure_lease'
                )
                station_missing = []
                if not station.acceptance_date:
                    station_missing.append('chưa nghiệm thu')
                if not station_contract:
                    station_missing.append('thiếu HĐ cho thuê trạm')
                else:
                    contract_missing = (
                        station_contract._get_initial_dossier_missing_fields()
                    )
                    if contract_missing:
                        station_missing.append(
                            'HĐ cho thuê trạm thiếu %s'
                            % ', '.join(contract_missing)
                        )
                if station_missing:
                    missing.append(
                        '%s: %s'
                        % (station.display_name, '; '.join(station_missing))
                    )
                    continue
                lines.append({
                    'station_id': station.id,
                    'document_type': 'station_lease_contract',
                    'contract_id': station_contract.id,
                })
        if missing:
            message = (
                'Chưa đủ HĐ thuê đất/BB đàm phán cho tất cả trạm.'
                if phase == 'phase_1'
                else 'Chưa đủ HĐ cho thuê trạm cho tất cả trạm.'
            )
            raise ValidationError(
                '%s\n- %s' % (message, '\n- '.join(missing))
            )
        return lines
