from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    maintenance_batch_id = fields.Many2one(
        comodel_name='bts.maintenance.batch',
        string='Phiếu bảo trì dự án',
        ondelete='cascade',
        index=True,
        copy=False,
    )
    station_sequence = fields.Integer(string='STT trạm', default=10)
    station_page_state = fields.Selection(
        selection=[
            ('not_started', 'Chưa kiểm tra'),
            ('in_progress', 'Đang kiểm tra'),
            ('done', 'Đã hoàn tất'),
            ('failed', 'Có lỗi'),
        ],
        string='Trạng thái kiểm tra trạm',
        required=True,
        default='not_started',
        copy=False,
    )
    station_id = fields.Many2one(
        comodel_name='project.task',
        string='Trạm BTS',
        related='equipment_id.station_id',
        store=True,
        readonly=True,
    )
    bts_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Dự án BTS',
        related='equipment_id.bts_project_id',
        store=True,
        readonly=True,
    )
    executor_type = fields.Selection(
        selection=[
            ('internal', 'Nội bộ'),
            ('external', 'KTV thuê ngoài'),
        ],
        string='Người thực hiện',
        required=True,
        default='internal',
    )
    external_technician_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='KTV thuê ngoài',
        domain=[('partner_type', '=', 'external_technician')],
        ondelete='set null',
    )
    actual_date = fields.Date(string='Ngày thực hiện thực tế')
    repair_completed_date = fields.Datetime(
        string='Thời điểm hoàn tất sửa chữa',
        readonly=True,
        copy=False,
    )
    repair_result_summary = fields.Text(
        string='Kết quả sửa chữa',
        readonly=True,
        copy=False,
    )
    has_failure = fields.Boolean(
        string='Có lỗi',
        compute='_compute_has_failure',
        store=True,
    )
    checklist_result_ids = fields.One2many(
        comodel_name='bts.maintenance.checklist.result',
        inverse_name='request_id',
        string='Kết quả checklist',
        copy=False,
    )
    checklist_result_count = fields.Integer(
        string='Số dòng checklist',
        compute='_compute_checklist_result_count',
        store=True,
    )
    repair_proposal_ids = fields.One2many(
        comodel_name='bts.repair.proposal',
        inverse_name='maintenance_request_id',
        string='Đề xuất sửa chữa',
        copy=False,
    )

    _sql_constraints = [
        (
            'maintenance_batch_equipment_unique',
            'unique(maintenance_batch_id, equipment_id)',
            'Mỗi trạm chỉ được xuất hiện một lần trong một phiếu bảo trì dự án.',
        ),
    ]

    @api.depends(
        'checklist_result_ids.result_state',
        'checklist_result_ids.is_resolved',
    )
    def _compute_has_failure(self):
        failure_states = ('need_repair', 'need_replacement')
        for request in self:
            request.has_failure = any(
                line.result_state in failure_states and not line.is_resolved
                for line in request.checklist_result_ids
            )

    def _get_all_repair_proposals(self):
        self.ensure_one()
        line_proposals = self.env['bts.repair.proposal'].search([
            ('proposal_line_ids.maintenance_request_id', '=', self.id),
        ])
        return self.repair_proposal_ids | line_proposals

    def _check_repair_completion_allowed(self):
        for request in self:
            unresolved_results = request.checklist_result_ids.filtered(
                lambda line: (
                    line.result_state in ('need_repair', 'need_replacement')
                    and not line.is_resolved
                )
            )
            if not unresolved_results:
                continue
            proposals = request._get_all_repair_proposals()
            if not proposals:
                raise UserError(_(
                    'Phiếu %(request)s còn checklist lỗi nhưng chưa có đề xuất '
                    'sửa chữa.',
                    request=request.display_name,
                ))
            pending = proposals.filtered(
                lambda proposal: proposal.state not in ('done', 'cancelled')
            )
            if pending:
                raise UserError(_(
                    'Phiếu %(request)s còn đề xuất sửa chữa chưa hoàn tất: '
                    '%(proposals)s.',
                    request=request.display_name,
                    proposals=', '.join(pending.mapped('name')),
                ))
        return True

    def write(self, vals):
        if (
            'stage_id' in vals
            and not self.env.context.get('bts_skip_repair_completion_check')
        ):
            stage = self.env['maintenance.stage'].browse(
                vals['stage_id']
            )
            if stage.done:
                self._check_repair_completion_allowed()
        return super().write(vals)

    @api.depends('checklist_result_ids')
    def _compute_checklist_result_count(self):
        for request in self:
            request.checklist_result_count = len(request.checklist_result_ids)

    def action_generate_bts_checklist(self):
        self.ensure_one()
        if not self.equipment_id:
            raise UserError(_('Vui lòng chọn thiết bị BTS trước khi sinh checklist.'))
        if not self.equipment_id.category_id:
            raise UserError(_('Thiết bị BTS chưa có loại trạm để sinh checklist.'))
        if self.checklist_result_ids:
            raise UserError(_('Phiếu này đã có checklist.'))

        domain = [
            ('category_id', '=', self.equipment_id.category_id.id),
            ('active', '=', True),
        ]
        if self.maintenance_batch_id:
            cycle = int(self.maintenance_batch_id.maintenance_cycle_months)
            domain.append(('frequency_months', 'in', [
                frequency for frequency in (1, 3, 6) if cycle % frequency == 0
            ]))
        checklist_items = self.env['bts.maintenance.checklist.item'].search(domain)
        if not checklist_items:
            raise UserError(_(
                'Không tìm thấy checklist mẫu đang hoạt động cho loại trạm %(category)s.',
                category=self.equipment_id.category_id.display_name,
            ))

        self.env['bts.maintenance.checklist.result'].create([
            {
                'request_id': self.id,
                'item_id': item.id,
                'result_state': 'stable',
            }
            for item in checklist_items
        ])
        return True

    def action_create_repair_proposal(self):
        self.ensure_one()
        if self.maintenance_batch_id:
            return self.maintenance_batch_id.action_create_repair_proposal()
        existing_proposal = self.repair_proposal_ids[:1]
        if existing_proposal:
            proposal = existing_proposal
        else:
            if not self.has_failure:
                raise UserError(_(
                    'Phiếu bảo trì chưa có hạng mục cần sửa chữa hoặc thay thế.'
                ))

            failure_labels = {
                'need_repair': _('Cần sửa chữa'),
                'need_replacement': _('Cần thay thế'),
            }
            failed_lines = self.checklist_result_ids.filtered(
                lambda line: line.result_state in failure_labels
            )
            summary_lines = []
            for line in failed_lines:
                summary = '- %(item)s: %(result)s' % {
                    'item': line.item_id.display_name,
                    'result': failure_labels[line.result_state],
                }
                details = [
                    detail
                    for detail in (line.measurement_value, line.note)
                    if detail
                ]
                if details:
                    summary += ' — %s' % '; '.join(details)
                summary_lines.append(summary)

            proposal = self.env['bts.repair.proposal'].create({
                'maintenance_request_id': self.id,
                'issue_summary': '\n'.join(summary_lines),
                'proposal_line_ids': [
                    (0, 0, {
                        'maintenance_request_id': self.id,
                        'checklist_result_id': line.id,
                        'station_id': self.station_id.id,
                        'item_id': line.item_id.id,
                        'result_state': line.result_state,
                        'technician_note': line.note,
                    })
                    for line in failed_lines
                ],
            })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Đề xuất sửa chữa'),
            'res_model': 'bts.repair.proposal',
            'res_id': proposal.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'dtc_bts_maintenance.view_bts_repair_proposal_form'
            ).id,
            'target': 'current',
        }

    def action_start_station_inspection(self):
        self.ensure_one()
        self.station_page_state = 'in_progress'
        if (
            self.maintenance_batch_id
            and self.maintenance_batch_id.state == 'generated'
        ):
            self.maintenance_batch_id.state = 'in_progress'
        return True

    def action_complete_station_inspection(self):
        self.ensure_one()
        self.write({
            'station_page_state': 'failed' if self.has_failure else 'done',
            'actual_date': self.actual_date or fields.Date.context_today(self),
        })
        return True

    def action_next_station(self):
        self.ensure_one()
        if self.station_page_state not in ('done', 'failed'):
            self.action_complete_station_inspection()
        next_request = self.search([
            ('maintenance_batch_id', '=', self.maintenance_batch_id.id),
            ('station_sequence', '>', self.station_sequence),
        ], order='station_sequence, id', limit=1)
        if not next_request:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Đã đến trạm cuối cùng'),
                    'message': _(
                        'Đã kiểm tra đến trạm cuối cùng. Vui lòng gửi phiếu cho Tổ hạ tầng.'
                    ),
                    'type': 'info',
                    'sticky': True,
                },
            }
        return {
            'type': 'ir.actions.act_window',
            'name': _('Phiếu kiểm tra trạm'),
            'res_model': 'maintenance.request',
            'res_id': next_request.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'dtc_bts_maintenance.view_dtc_bts_maintenance_request_form'
            ).id,
            'target': 'current',
        }
