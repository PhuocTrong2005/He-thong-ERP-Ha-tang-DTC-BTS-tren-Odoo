from collections import defaultdict

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BtsMaintenanceBatch(models.Model):
    _name = 'bts.maintenance.batch'
    _description = 'Phiếu bảo trì dự án'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'maintenance_date desc, id desc'

    name = fields.Char(
        string='Mã phiếu bảo trì',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Mới'),
        tracking=True,
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Dự án BTS',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
    )
    station_type = fields.Selection(
        related='project_id.station_type',
        string='Loại trạm',
        store=True,
        readonly=True,
    )
    maintenance_date = fields.Date(
        string='Ngày bảo trì',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    effective_date = fields.Date(
        string='Ngày đưa vào vận hành',
        tracking=True,
    )
    maintenance_cycle_months = fields.Selection(
        selection=[
            ('1', 'Bảo trì tháng 1'),
            ('3', 'Bảo trì tháng 3'),
            ('6', 'Bảo trì tháng 6'),
        ],
        string='Chu kỳ bảo trì lần này',
        required=True,
        tracking=True,
    )
    technician_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Kỹ thuật viên phụ trách',
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Nháp'),
            ('generated', 'Đã sinh danh sách trạm'),
            ('in_progress', 'Đang kiểm tra'),
            ('submitted', 'Chờ tổ hạ tầng kiểm tra'),
            ('reviewed', 'Đã kiểm tra kết quả'),
            ('done', 'Hoàn tất'),
            ('cancelled', 'Đã hủy'),
        ],
        string='Trạng thái',
        required=True,
        default='draft',
        copy=False,
        tracking=True,
    )
    request_ids = fields.One2many(
        comodel_name='maintenance.request',
        inverse_name='maintenance_batch_id',
        string='Danh sách trạm kiểm tra',
        copy=False,
    )
    repair_proposal_ids = fields.One2many(
        comodel_name='bts.repair.proposal',
        inverse_name='maintenance_batch_id',
        string='Đề xuất sửa chữa',
        copy=False,
    )
    station_count = fields.Integer(
        string='Số trạm',
        compute='_compute_statistics',
        store=True,
    )
    completed_station_count = fields.Integer(
        string='Số trạm đã hoàn tất',
        compute='_compute_statistics',
        store=True,
    )
    failed_station_count = fields.Integer(
        string='Số trạm có lỗi',
        compute='_compute_statistics',
        store=True,
    )
    checklist_line_count = fields.Integer(
        string='Số dòng checklist',
        compute='_compute_statistics',
        store=True,
    )
    has_failure = fields.Boolean(
        string='Có hư hỏng',
        compute='_compute_statistics',
        store=True,
    )
    repair_proposal_count = fields.Integer(
        string='Số đề xuất sửa chữa',
        compute='_compute_statistics',
        store=True,
    )

    _sql_constraints = [
        (
            'repair_batch_name_unique',
            'unique(name)',
            'Mã phiếu bảo trì dự án đã tồn tại.',
        ),
    ]

    @api.depends(
        'request_ids.station_page_state',
        'request_ids.has_failure',
        'request_ids.checklist_result_ids',
        'repair_proposal_ids',
    )
    def _compute_statistics(self):
        for batch in self:
            requests = batch.request_ids
            batch.station_count = len(requests)
            batch.completed_station_count = len(
                requests.filtered(
                    lambda request: request.station_page_state in ('done', 'failed')
                )
            )
            batch.failed_station_count = len(requests.filtered('has_failure'))
            batch.checklist_line_count = sum(
                len(request.checklist_result_ids) for request in requests
            )
            batch.has_failure = any(request.has_failure for request in requests)
            batch.repair_proposal_count = len(batch.repair_proposal_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('Mới'):
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('bts.maintenance.batch')
                    or _('Mới')
                )
        return super().create(vals_list)

    @api.onchange('project_id')
    def _onchange_project_id(self):
        for batch in self:
            equipment = self.env['maintenance.equipment'].search([
                ('bts_project_id', '=', batch.project_id.id),
                ('active', '=', True),
                ('bts_state', '=', 'active'),
                ('station_id', '!=', False),
            ])
            effective_dates = equipment.mapped('effective_date')
            batch.effective_date = min(effective_dates) if effective_dates else False
            batch._suggest_maintenance_cycle()

    @api.onchange('effective_date', 'maintenance_date')
    def _onchange_maintenance_dates(self):
        self._suggest_maintenance_cycle()

    def _suggest_maintenance_cycle(self):
        for batch in self:
            if not batch.effective_date or not batch.maintenance_date:
                continue
            delta = relativedelta(batch.maintenance_date, batch.effective_date)
            elapsed_months = max(1, delta.years * 12 + delta.months)
            if elapsed_months % 6 == 0:
                batch.maintenance_cycle_months = '6'
            elif elapsed_months % 3 == 0:
                batch.maintenance_cycle_months = '3'
            else:
                batch.maintenance_cycle_months = '1'

    def action_generate_station_requests(self):
        self.ensure_one()
        if not self.project_id or not self.maintenance_date or not self.maintenance_cycle_months:
            raise UserError(_(
                'Vui lòng chọn dự án, ngày bảo trì và chu kỳ bảo trì trước khi sinh danh sách trạm.'
            ))
        if self.state in ('submitted', 'reviewed', 'done', 'cancelled'):
            raise UserError(_('Không thể sinh thêm trạm ở trạng thái hiện tại.'))

        equipment_records = self.env['maintenance.equipment'].search([
            ('station_id.project_id', '=', self.project_id.id),
            ('active', '=', True),
            ('bts_state', '=', 'active'),
            ('station_id', '!=', False),
        ], order='station_id, id')
        if not equipment_records:
            raise UserError(_(
                'Dự án chưa có hồ sơ thiết bị bảo trì cho các trạm.'
            ))

        existing_equipment_ids = set(self.request_ids.mapped('equipment_id').ids)
        sequence = max(self.request_ids.mapped('station_sequence') or [0])
        created_count = skipped_count = checklist_count = 0
        cycle = int(self.maintenance_cycle_months)
        result_model = self.env['bts.maintenance.checklist.result']

        for equipment in equipment_records:
            if equipment.id in existing_equipment_ids:
                skipped_count += 1
                continue
            sequence += 1
            request = self.env['maintenance.request'].create({
                'name': _(
                    '%(batch)s - %(station)s',
                    batch=self.name,
                    station=equipment.station_id.display_name,
                ),
                'maintenance_batch_id': self.id,
                'equipment_id': equipment.id,
                'user_id': self.technician_user_id.id or False,
                'station_sequence': sequence,
                'station_page_state': 'not_started',
                'maintenance_type': 'preventive',
                'request_date': self.maintenance_date,
                'schedule_date': fields.Datetime.to_datetime(self.maintenance_date),
            })
            checklist_items = self.env['bts.maintenance.checklist.item'].search([
                ('category_id', '=', equipment.category_id.id),
                ('active', '=', True),
                ('frequency_months', 'in', [frequency for frequency in (1, 3, 6)
                                             if cycle % frequency == 0]),
            ], order='sequence, id')
            if checklist_items:
                result_model.create([
                    {
                        'request_id': request.id,
                        'item_id': item.id,
                        'result_state': 'stable',
                    }
                    for item in checklist_items
                ])
                checklist_count += len(checklist_items)
            existing_equipment_ids.add(equipment.id)
            created_count += 1

        self.state = 'generated'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Đã sinh danh sách trạm và checklist'),
                'message': _(
                    'Đã tạo %(created)s phiếu trạm, bỏ qua %(skipped)s phiếu đã có, '
                    'và tạo %(lines)s dòng checklist.',
                    created=created_count,
                    skipped=skipped_count,
                    lines=checklist_count,
                ),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_submit(self):
        self.ensure_one()
        if not self.request_ids:
            raise UserError(_('Phiếu chưa có danh sách trạm kiểm tra.'))
        if any(
            request.station_page_state not in ('done', 'failed')
            for request in self.request_ids
        ):
            raise UserError(_('Chưa hoàn tất kiểm tra tất cả các trạm.'))
        self.state = 'submitted'
        self.message_post(body=_('Phiếu đã được gửi cho Tổ hạ tầng kiểm tra.'))
        return True

    def action_review(self):
        self.ensure_one()
        if self.state != 'submitted':
            raise UserError(_('Chỉ phiếu đang chờ kiểm tra mới có thể xác nhận kết quả.'))
        self.state = 'reviewed'
        self.message_post(body=_('Tổ hạ tầng đã xác nhận kết quả kiểm tra.'))
        return True

    def action_done(self):
        self.ensure_one()
        if self.state != 'reviewed':
            raise UserError(_('Vui lòng xác nhận kết quả trước khi hoàn tất phiếu.'))
        self.request_ids._check_repair_completion_allowed()
        next_action_date = (
            self.maintenance_date
            + relativedelta(months=int(self.maintenance_cycle_months))
        )
        self.request_ids.mapped('equipment_id').write({
            'next_action_date': next_action_date,
        })
        self.state = 'done'
        self.message_post(body=_('Phiếu bảo trì dự án đã hoàn tất.'))
        return True

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        return True

    def action_create_repair_proposal(self):
        self.ensure_one()
        existing = self.repair_proposal_ids[:1]
        if existing:
            return self._open_repair_proposal(existing)

        failed_results = self.request_ids.mapped('checklist_result_ids').filtered(
            lambda line: line.result_state in ('need_repair', 'need_replacement')
        )
        if not self.has_failure or not failed_results:
            raise UserError(_(
                'Không có hạng mục hư hỏng để tạo đề xuất sửa chữa.'
            ))

        labels = dict(
            self.env['bts.maintenance.checklist.result']._fields[
                'result_state'
            ]._description_selection(self.env)
        )
        grouped = defaultdict(list)
        for result in failed_results:
            grouped[result.request_id.station_id.display_name].append(
                '- %s: %s%s' % (
                    result.item_id.display_name,
                    labels.get(result.result_state, result.result_state),
                    (' — %s' % result.note) if result.note else '',
                )
            )
        summary = '\n'.join(
            '%s\n%s' % (station, '\n'.join(lines))
            for station, lines in grouped.items()
        )
        proposal = self.env['bts.repair.proposal'].create({
            'maintenance_batch_id': self.id,
            'issue_summary': summary,
            'proposal_line_ids': [
                (0, 0, {
                    'maintenance_request_id': result.request_id.id,
                    'checklist_result_id': result.id,
                    'station_id': result.request_id.station_id.id,
                    'item_id': result.item_id.id,
                    'result_state': result.result_state,
                    'technician_note': result.note,
                })
                for result in failed_results
            ],
        })
        return self._open_repair_proposal(proposal)

    def _open_repair_proposal(self, proposal):
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
