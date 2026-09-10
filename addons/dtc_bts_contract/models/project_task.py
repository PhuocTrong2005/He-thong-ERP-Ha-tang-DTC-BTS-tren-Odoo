from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    _contract_cancel_audit_fields = {
        'contract_cancel_decision_by_id',
        'contract_cancel_decision_at',
        'contract_cancel_reason',
        'contract_cancel_source_model',
        'contract_cancel_source_id',
    }

    def action_report_land_negotiation_failure(self):
        """Open the KSGS failure report at the station entry point."""
        self.ensure_one()
        is_admin = self.env.user.has_group('base.group_system')
        is_assigned_ksgs = (
            self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs')
            and self.project_id.project_manager_id == self.env.user
        )
        if not (is_admin or is_assigned_ksgs):
            raise AccessError(_(
                'Chỉ KSGS phụ trách dự án được báo đàm phán thuê đất thất bại.'
            ))
        minutes = self.env['bts.negotiation.minutes'].search([
            ('station_id', '=', self.id),
            ('memo_type', '=', 'land_lease'),
            ('state', '=', 'draft'),
            ('land_negotiation_failed', '=', False),
        ], order='id desc', limit=1)
        if not minutes:
            minutes = self.env['bts.negotiation.minutes'].create({
                'station_id': self.id,
                'memo_type': 'land_lease',
                'memo_date': fields.Date.context_today(self),
            })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Báo đàm phán thuê đất thất bại'),
            'res_model': 'bts.negotiation.minutes',
            'res_id': minutes.id,
            'view_mode': 'form',
            'views': [(
                self.env.ref(
                    'dtc_bts_contract.view_bts_negotiation_minutes_form'
                ).id,
                'form',
            )],
            'target': 'current',
        }

    contract_cancel_decision_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người quyết định loại trạm',
        readonly=True,
        copy=False,
    )
    contract_cancel_decision_at = fields.Datetime(
        string='Thời gian quyết định loại trạm',
        readonly=True,
        copy=False,
    )
    contract_cancel_reason = fields.Text(
        string='Lý do quyết định loại trạm',
        readonly=True,
        copy=False,
    )
    contract_cancel_source_model = fields.Char(
        string='Model nguồn quyết định loại trạm',
        readonly=True,
        copy=False,
    )
    contract_cancel_source_id = fields.Integer(
        string='ID nguồn quyết định loại trạm',
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
                _('Audit quyết định loại trạm chỉ được ghi bởi workflow máy chủ.')
            )
        return super().create(vals_list)

    contract_ids = fields.One2many(
        comodel_name='bts.contract',
        inverse_name='station_id',
        string='Hợp đồng trạm',
    )
    negotiation_minute_ids = fields.One2many(
        comodel_name='bts.negotiation.minutes',
        inverse_name='station_id',
        string='Biên bản ban đầu',
    )
    contract_count = fields.Integer(
        string='Số hợp đồng',
        compute='_compute_contract_document_counts',
    )
    negotiation_minute_count = fields.Integer(
        string='Số biên bản',
        compute='_compute_contract_document_counts',
    )
    land_contract_id = fields.Many2one(
        comodel_name='bts.contract',
        string='Hồ sơ HĐ thuê đất',
        copy=False,
        readonly=True,
        ondelete='set null',
    )
    negotiation_minutes_id = fields.Many2one(
        comodel_name='bts.negotiation.minutes',
        string='Hồ sơ biên bản đàm phán',
        copy=False,
        readonly=True,
        ondelete='set null',
    )
    station_lease_contract_id = fields.Many2one(
        comodel_name='bts.contract',
        string='Hồ sơ HĐ cho thuê trạm',
        copy=False,
        readonly=True,
        ondelete='set null',
    )

    land_contract_scan = fields.Binary(
        string='Scan HĐ thuê đất',
        attachment=True,
        copy=False,
    )
    land_contract_scan_filename = fields.Char(
        string='Tên file HĐ thuê đất',
        copy=False,
    )
    negotiation_minutes_scan = fields.Binary(
        string='Scan BB đàm phán',
        attachment=True,
        copy=False,
    )
    negotiation_minutes_scan_filename = fields.Char(
        string='Tên file BB đàm phán',
        copy=False,
    )
    station_lease_contract_scan = fields.Binary(
        string='Scan HĐ cho thuê trạm',
        attachment=True,
        copy=False,
    )
    station_lease_contract_scan_filename = fields.Char(
        string='Tên file HĐ cho thuê trạm',
        copy=False,
    )

    land_contract_dossier_state = fields.Selection(
        selection=[
            ('missing', 'Chưa có'),
            ('uploaded', 'Đã tải scan'),
            ('submitted', 'Chờ ký số'),
            ('signed', 'Đã ký số'),
            ('active', 'Đang hiệu lực'),
            ('closed', 'Đã kết thúc'),
        ],
        string='Hợp đồng thuê đất',
        compute='_compute_contract_dossier_states',
    )
    negotiation_dossier_state = fields.Selection(
        selection=[
            ('missing', 'Chưa có'),
            ('uploaded', 'Đã tải scan'),
            ('pending_approval', 'Chờ phê duyệt'),
            ('confirmed', 'Đã xác nhận'),
            ('converted', 'Đã chuyển HĐ'),
            ('rejected', 'Từ chối'),
        ],
        string='Biên bản đàm phán',
        compute='_compute_contract_dossier_states',
    )
    station_lease_dossier_state = fields.Selection(
        selection=[
            ('not_ready', 'Chưa nghiệm thu'),
            ('missing', 'Chưa có'),
            ('uploaded', 'Đã tải scan'),
            ('submitted', 'Chờ ký số'),
            ('signed', 'Đã ký số'),
            ('active', 'Đang hiệu lực'),
            ('closed', 'Đã kết thúc'),
        ],
        string='Hợp đồng cho thuê trạm',
        compute='_compute_contract_dossier_states',
    )
    digital_signature_state = fields.Selection(
        selection=[
            ('not_ready', 'Chưa có hồ sơ'),
            ('pending', 'Chờ ký số'),
            ('partial', 'Ký số một phần'),
            ('completed', 'Đã ký số'),
        ],
        string='Trạng thái ký số',
        compute='_compute_contract_dossier_states',
    )
    overview_land_contract_id = fields.Many2one(
        comodel_name='bts.contract',
        string='HĐ thuê đất',
        compute='_compute_contract_due_overview',
        store=True,
    )
    overview_infrastructure_contract_id = fields.Many2one(
        comodel_name='bts.contract',
        string='HĐ cho thuê trạm',
        compute='_compute_contract_due_overview',
        store=True,
    )
    nearest_contract_expiration_date = fields.Date(
        string='Ngày hết hạn gần nhất',
        compute='_compute_contract_due_overview',
        store=True,
    )
    nearest_contract_days_left = fields.Integer(
        string='Còn lại (ngày)',
        compute='_compute_contract_due_overview',
        store=True,
    )
    contract_action_required = fields.Selection(
        selection=[
            ('renew_land_first', 'Gia hạn HĐ thuê đất trước'),
            ('renew_infrastructure', 'Gia hạn HĐ cho thuê trạm'),
            ('monitor', 'Theo dõi'),
        ],
        string='Cần xử lý',
        compute='_compute_contract_due_overview',
        store=True,
    )

    @api.depends(
        'contract_ids.state',
        'contract_ids.contract_type',
        'contract_ids.expiration_date',
        'contract_ids.term_years',
    )
    def _compute_contract_due_overview(self):
        contract_model = self.env['bts.contract']
        for station in self:
            land_contracts = station.contract_ids.filtered(
                lambda contract: contract.contract_type == 'land_lease'
            ).sorted(
                key=lambda contract: (
                    contract.state in ('active', 'renewal_agreed'),
                    contract.expiration_date or fields.Date.from_string(
                        '1900-01-01'
                    ),
                    contract.id,
                ),
                reverse=True,
            )
            infrastructure_contracts = station.contract_ids.filtered(
                lambda contract: (
                    contract.contract_type == 'infrastructure_lease'
                )
            ).sorted(
                key=lambda contract: (
                    contract.state in ('active', 'renewal_agreed'),
                    contract.expiration_date or fields.Date.from_string(
                        '1900-01-01'
                    ),
                    contract.id,
                ),
                reverse=True,
            )
            overview = contract_model._get_contract_due_overview(
                station.contract_ids
            )
            station.overview_land_contract_id = land_contracts[:1]
            station.overview_infrastructure_contract_id = (
                infrastructure_contracts[:1]
            )
            station.nearest_contract_expiration_date = overview[
                'nearest_contract_expiration_date'
            ]
            station.nearest_contract_days_left = overview[
                'nearest_contract_days_left'
            ]
            station.contract_action_required = overview[
                'contract_action_required'
            ]

    def _compute_contract_document_counts(self):
        contract_groups = self.env['bts.contract'].read_group(
            [('station_id', 'in', self.ids)],
            ['station_id'],
            ['station_id'],
        )
        minute_groups = self.env['bts.negotiation.minutes'].read_group(
            [('station_id', 'in', self.ids)],
            ['station_id'],
            ['station_id'],
        )
        contract_counts = {
            group['station_id'][0]: group['station_id_count']
            for group in contract_groups
        }
        minute_counts = {
            group['station_id'][0]: group['station_id_count']
            for group in minute_groups
        }
        for station in self:
            station.contract_count = contract_counts.get(station.id, 0)
            station.negotiation_minute_count = minute_counts.get(station.id, 0)

    @api.depends(
        'acceptance_date',
        'land_contract_scan',
        'negotiation_minutes_scan',
        'station_lease_contract_scan',
        'contract_ids.state',
        'contract_ids.initial_document',
        'contract_ids.signed_document',
        'negotiation_minute_ids.state',
        'negotiation_minute_ids.initial_document',
        'land_contract_id.state',
        'land_contract_id.initial_document',
        'land_contract_id.signed_document',
        'negotiation_minutes_id.state',
        'negotiation_minutes_id.initial_document',
        'station_lease_contract_id.state',
        'station_lease_contract_id.initial_document',
        'station_lease_contract_id.signed_document',
    )
    def _compute_contract_dossier_states(self):
        for station in self:
            land_contract = station._get_station_contract('land_lease')
            station_lease_contract = station._get_station_contract(
                'infrastructure_lease'
            )
            negotiation_minutes = (
                station.negotiation_minutes_id
                or station.negotiation_minute_ids[:1]
            )
            station.land_contract_dossier_state = station._contract_state_for_dashboard(
                land_contract,
                station.land_contract_scan,
            )
            station.negotiation_dossier_state = (
                (
                    'uploaded'
                    if negotiation_minutes.initial_document
                    or station.negotiation_minutes_scan
                    else 'missing'
                )
                if negotiation_minutes and negotiation_minutes.state == 'draft'
                else (
                    negotiation_minutes.state
                    if negotiation_minutes
                    else (
                        'uploaded'
                        if station.negotiation_minutes_scan
                        else 'missing'
                    )
                )
            )
            if (
                not station.acceptance_date
                and not station.station_lease_contract_scan
                and not station_lease_contract
            ):
                station.station_lease_dossier_state = 'not_ready'
            else:
                station.station_lease_dossier_state = (
                    station._contract_state_for_dashboard(
                        station_lease_contract,
                        station.station_lease_contract_scan,
                    )
                )

            contracts = (land_contract | station_lease_contract).filtered(
                lambda contract: contract.initial_document
                or contract.state != 'draft'
            )
            if not contracts:
                station.digital_signature_state = (
                    'pending'
                    if station.land_contract_scan or station.station_lease_contract_scan
                    else 'not_ready'
                )
                continue
            signed_contracts = contracts.filtered(
                lambda contract: contract.signed_document
                or contract.state in ('active', 'renewal_agreed', 'liquidated', 'expired')
            )
            if len(signed_contracts) == len(contracts):
                station.digital_signature_state = 'completed'
            elif signed_contracts:
                station.digital_signature_state = 'partial'
            else:
                station.digital_signature_state = 'pending'

    def _contract_state_for_dashboard(self, contract, scan):
        if not contract:
            return 'uploaded' if scan else 'missing'
        if contract.state == 'submitted':
            return 'signed' if contract.signed_document else 'submitted'
        if contract.state in ('active', 'renewal_agreed'):
            return 'active'
        if contract.state in ('liquidated', 'expired', 'cancelled'):
            return 'closed'
        return 'uploaded' if contract.initial_document or scan else 'missing'

    def _get_station_contract(self, contract_type):
        self.ensure_one()
        linked_contract = (
            self.land_contract_id
            if contract_type == 'land_lease'
            else self.station_lease_contract_id
        )
        contracts = self.contract_ids.filtered(
            lambda contract: contract.contract_type == contract_type
        ).sorted(key=lambda contract: contract.id, reverse=True)
        return linked_contract or contracts[:1]

    @api.constrains('station_lease_contract_scan', 'acceptance_date')
    def _check_station_lease_scan_after_acceptance(self):
        for station in self:
            if station.station_lease_contract_scan and not station.acceptance_date:
                raise ValidationError(
                    'Chỉ được tải HĐ cho thuê trạm sau khi trạm đã có ngày nghiệm thu.'
                )

    def write(self, vals):
        user = self.env.user
        if (
            not self.env.su
            and self._contract_cancel_audit_fields.intersection(vals)
        ):
            raise AccessError(
                _('Audit quyết định loại trạm chỉ được ghi bởi workflow máy chủ.')
            )
        if (
            user.has_group(
                'dtc_bts_contract.group_dtc_bts_contract_director'
            )
            and not self.env.su
            and not user.has_group('base.group_system')
        ):
            raise AccessError(
                _('BGĐ hợp đồng không được ghi trực tiếp trạm.')
            )
        self._check_scanned_dossiers_mutable(vals)
        result = super().write(vals)
        scan_fields = {
            'land_contract_scan',
            'land_contract_scan_filename',
            'negotiation_minutes_scan',
            'negotiation_minutes_scan_filename',
            'station_lease_contract_scan',
            'station_lease_contract_scan_filename',
        }
        if scan_fields.intersection(vals):
            self._sync_scanned_contract_dossiers()
        return result

    def _apply_contract_director_station_cancel(self, source):
        self.ensure_one()
        source.ensure_one()
        if not (
            self.env.user.has_group(
                'dtc_bts_contract.group_dtc_bts_contract_director'
            )
            or self.env.user.has_group('base.group_system')
        ):
            raise AccessError(_('Chỉ BGĐ hợp đồng được quyết định hủy trạm.'))
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
            raise ValidationError(_('Nguồn quyết định loại trạm không hợp lệ.'))
        if source.station_id != self or source.project_id != self.project_id:
            raise ValidationError(_('Nguồn quyết định không thuộc trạm này.'))
        if not report_exists:
            raise ValidationError(_('Nguồn quyết định chưa có báo cáo thất bại hợp lệ.'))
        if (
            source.decision_type != 'remove_station'
            or not source.decision_at
            or source.decision_by_id != self.env.user
            or not source.decision_reason
        ):
            raise ValidationError(_('Quyết định loại trạm chưa hợp lệ.'))
        if self.station_state == 'cancelled':
            raise ValidationError(_('Trạm đã bị hủy.'))
        decision_at = source.decision_at
        reason = source.decision_reason
        self.sudo().with_context(
            bts_skip_project_summary_sync=True,
        ).write({
            'station_state': 'cancelled',
            'contract_cancel_decision_by_id': self.env.user.id,
            'contract_cancel_decision_at': decision_at,
            'contract_cancel_reason': reason,
            'contract_cancel_source_model': source._name,
            'contract_cancel_source_id': source.id,
        })
        self.sudo().message_post(body=_(
            'BGĐ %(director)s đã loại trạm từ %(source_label)s #%(source_id)s. '
            'Lý do: %(reason)s',
            director=self.env.user.display_name,
            source_label=source._description,
            source_id=source.id,
            reason=reason,
        ))
        return True

    def _check_scanned_dossiers_mutable(self, vals):
        field_groups = (
            (
                {'land_contract_scan', 'land_contract_scan_filename'},
                lambda station: station._get_station_contract('land_lease'),
                'HĐ thuê đất',
            ),
            (
                {
                    'negotiation_minutes_scan',
                    'negotiation_minutes_scan_filename',
                },
                lambda station: (
                    station.negotiation_minutes_id
                    or station.negotiation_minute_ids[:1]
                ),
                'BB đàm phán',
            ),
            (
                {
                    'station_lease_contract_scan',
                    'station_lease_contract_scan_filename',
                },
                lambda station: station._get_station_contract(
                    'infrastructure_lease'
                ),
                'HĐ cho thuê trạm',
            ),
        )
        for fields_to_check, get_document, label in field_groups:
            if not fields_to_check.intersection(vals):
                continue
            for station in self:
                document = get_document(station)
                if document and document.state != 'draft':
                    raise ValidationError(
                        '%s đã được đưa vào quy trình xử lý; '
                        'KSGS không thể thay file scan từ form Dự án.' % label
                    )

    def _sync_scanned_contract_dossiers(self):
        for station in self:
            station._sync_contract_scan(
                link_field='land_contract_id',
                scan_field='land_contract_scan',
                filename_field='land_contract_scan_filename',
                contract_type='land_lease',
            )
            station._sync_negotiation_scan()
            station._sync_contract_scan(
                link_field='station_lease_contract_id',
                scan_field='station_lease_contract_scan',
                filename_field='station_lease_contract_scan_filename',
                contract_type='infrastructure_lease',
            )

    def _sync_contract_scan(
        self,
        link_field,
        scan_field,
        filename_field,
        contract_type,
    ):
        self.ensure_one()
        scan = self[scan_field]
        contract = self[link_field] or self._get_station_contract(contract_type)
        values = {
            'initial_document': scan,
            'initial_document_filename': self[filename_field],
        }
        if contract and contract.state == 'draft':
            contract.write(values)
            if not self[link_field]:
                super(ProjectTask, self).write({link_field: contract.id})
        elif scan and not contract:
            values.update({
                'station_id': self.id,
                'contract_type': contract_type,
            })
            if contract_type == 'infrastructure_lease':
                values.update({
                    'partner_id': self.project_id.telecom_partner_id.id,
                    'related_land_contract_id': self._get_station_contract(
                        'land_lease'
                    ).id,
                })
            contract = self.env['bts.contract'].create(values)
            super(ProjectTask, self).write({link_field: contract.id})

    def _sync_negotiation_scan(self):
        self.ensure_one()
        scan = self.negotiation_minutes_scan
        minutes = self.negotiation_minutes_id or self.negotiation_minute_ids[:1]
        values = {
            'initial_document': scan,
            'initial_document_filename': self.negotiation_minutes_scan_filename,
        }
        if minutes and minutes.state == 'draft':
            minutes.write(values)
            if not self.negotiation_minutes_id:
                super(ProjectTask, self).write({
                    'negotiation_minutes_id': minutes.id,
                })
        elif scan and not minutes:
            values.update({
                'station_id': self.id,
                'memo_type': 'land_lease',
            })
            minutes = self.env['bts.negotiation.minutes'].create(values)
            super(ProjectTask, self).write({
                'negotiation_minutes_id': minutes.id,
            })

    def action_open_station_contracts(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'dtc_bts_contract.action_bts_contract'
        )
        action.update({
            'name': _('Hợp đồng trạm %s') % self.display_name,
            'domain': [('station_id', '=', self.id)],
            'context': {
                'default_station_id': self.id,
                'search_default_station_id': self.id,
            },
        })
        return action

    def action_open_station_contract_dossiers(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'dtc_bts_contract.action_bts_contract'
        )
        tree_view = self.env.ref(
            'dtc_bts_contract.view_bts_contract_project_dossier_tree'
        )
        form_view = self.env.ref(
            'dtc_bts_contract.view_bts_contract_project_dossier_form'
        )
        contracts = self.contract_ids.sorted('id', reverse=True)
        if len(contracts) <= 1:
            action.update({
                'name': _('Hồ sơ hợp đồng trạm %s') % self.display_name,
                'view_id': form_view.id,
                'view_mode': 'form',
                'views': [(form_view.id, 'form')],
                'res_id': contracts.id or False,
                'target': 'current',
                'context': {
                    'default_station_id': self.id,
                    'from_project_contract_tab': True,
                    'create': True,
                },
            })
            return action
        action.update({
            'name': _('Hồ sơ hợp đồng trạm %s') % self.display_name,
            'domain': [('station_id', '=', self.id)],
            'view_id': tree_view.id,
            'view_mode': 'tree,form',
            'views': [
                (tree_view.id, 'tree'),
                (form_view.id, 'form'),
            ],
            'context': {
                'default_station_id': self.id,
                'search_default_station_id': self.id,
                'from_project_contract_tab': True,
                'create': True,
            },
        })
        return action

    def action_open_station_negotiation_minutes(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'dtc_bts_contract.action_bts_negotiation_minutes'
        )
        action.update({
            'name': _('Biên bản trạm %s') % self.display_name,
            'domain': [('station_id', '=', self.id)],
            'context': {
                'default_station_id': self.id,
                'search_default_station_id': self.id,
            },
        })
        return action

    def action_open_station_negotiation_dossiers(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'dtc_bts_contract.action_bts_negotiation_minutes'
        )
        tree_view = self.env.ref(
            'dtc_bts_contract.view_bts_negotiation_minutes_project_tree'
        )
        form_view = self.env.ref(
            'dtc_bts_contract.view_bts_negotiation_minutes_project_form'
        )
        minutes = self.negotiation_minute_ids.sorted('id', reverse=True)
        if len(minutes) <= 1:
            action.update({
                'name': _('Hồ sơ biên bản trạm %s') % self.display_name,
                'view_id': form_view.id,
                'view_mode': 'form',
                'views': [(form_view.id, 'form')],
                'res_id': minutes.id or False,
                'target': 'current',
                'context': {
                    'default_station_id': self.id,
                    'default_memo_type': 'land_lease',
                    'from_project_contract_tab': True,
                    'create': True,
                },
            })
            return action
        action.update({
            'name': _('Hồ sơ biên bản trạm %s') % self.display_name,
            'domain': [('station_id', '=', self.id)],
            'view_id': tree_view.id,
            'view_mode': 'tree,form',
            'views': [
                (tree_view.id, 'tree'),
                (form_view.id, 'form'),
            ],
            'context': {
                'default_station_id': self.id,
                'default_memo_type': 'land_lease',
                'search_default_station_id': self.id,
                'from_project_contract_tab': True,
                'create': True,
            },
        })
        return action
