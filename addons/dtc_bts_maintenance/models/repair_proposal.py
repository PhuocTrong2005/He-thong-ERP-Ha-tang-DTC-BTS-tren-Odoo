from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class BtsRepairProposal(models.Model):
    _name = 'bts.repair.proposal'
    _description = 'Đề xuất sửa chữa BTS'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Mã đề xuất',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Mới'),
        tracking=True,
    )
    maintenance_request_id = fields.Many2one(
        comodel_name='maintenance.request',
        string='Phiếu bảo trì',
        ondelete='restrict',
        index=True,
        copy=False,
    )
    maintenance_batch_id = fields.Many2one(
        comodel_name='bts.maintenance.batch',
        string='Phiếu bảo trì dự án',
        ondelete='restrict',
        index=True,
        copy=False,
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Dự án phiếu bảo trì',
        related='maintenance_batch_id.project_id',
        store=True,
        readonly=True,
    )
    proposal_line_ids = fields.One2many(
        comodel_name='bts.repair.proposal.line',
        inverse_name='proposal_id',
        string='Chi tiết hư hỏng',
        copy=True,
    )
    material_line_ids = fields.One2many(
        comodel_name='bts.repair.proposal.material.line',
        inverse_name='proposal_id',
        string='Vật tư cần cấp',
        copy=True,
    )
    material_request_ids = fields.One2many(
        comodel_name='bts.material.request',
        inverse_name='repair_proposal_id',
        string='Yêu cầu vật tư',
        copy=False,
    )
    material_request_count = fields.Integer(
        string='Số yêu cầu vật tư',
        compute='_compute_material_request_count',
    )
    equipment_id = fields.Many2one(
        comodel_name='maintenance.equipment',
        string='Hồ sơ thiết bị',
        related='maintenance_request_id.equipment_id',
        store=True,
        readonly=True,
    )
    station_id = fields.Many2one(
        comodel_name='project.task',
        string='Trạm BTS',
        related='maintenance_request_id.station_id',
        store=True,
        readonly=True,
    )
    bts_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Dự án yêu cầu bảo trì',
        related='maintenance_request_id.bts_project_id',
        store=True,
        readonly=True,
    )
    proposed_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Người lập đề xuất',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    issue_summary = fields.Text(
        string='Tóm tắt hư hỏng',
        required=True,
        tracking=True,
    )
    material_note = fields.Text(string='Ghi chú vật tư')
    estimated_cost = fields.Float(string='Chi phí dự kiến')
    priority = fields.Selection(
        selection=[
            ('low', 'Thấp'),
            ('normal', 'Bình thường'),
            ('high', 'Cao'),
            ('urgent', 'Khẩn cấp'),
        ],
        string='Mức độ ưu tiên',
        required=True,
        default='normal',
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Nháp'),
            ('confirmed', 'Đã xác nhận'),
            ('waiting_material', 'Chờ vật tư'),
            ('ready_to_repair', 'Sẵn sàng sửa chữa'),
            ('repairing', 'Đang sửa chữa'),
            ('done', 'Hoàn tất'),
            ('cancelled', 'Hủy'),
        ],
        string='Trạng thái',
        required=True,
        default='draft',
        copy=False,
        tracking=True,
        index=True,
    )
    repair_result = fields.Text(
        string='Kết quả sửa chữa',
        tracking=True,
    )
    repair_started_date = fields.Datetime(
        string='Bắt đầu sửa chữa',
        readonly=True,
        copy=False,
    )
    repair_completed_date = fields.Datetime(
        string='Hoàn tất sửa chữa',
        readonly=True,
        copy=False,
    )
    note = fields.Text(string='Ghi chú xử lý')

    _sql_constraints = [
        (
            'maintenance_request_unique',
            'unique(maintenance_request_id)',
            'Mỗi phiếu bảo trì chỉ được có một đề xuất sửa chữa.',
        ),
        (
            'maintenance_batch_unique',
            'unique(maintenance_batch_id)',
            'Mỗi phiếu bảo trì dự án chỉ được có một đề xuất sửa chữa.',
        ),
        (
            'estimated_cost_non_negative',
            'CHECK(estimated_cost >= 0)',
            'Chi phí dự kiến phải lớn hơn hoặc bằng 0.',
        ),
    ]

    def init(self):
        """Map legacy approval states to the infrastructure-owned workflow."""
        self.env.cr.execute("""
            UPDATE bts_repair_proposal
               SET state = CASE state
                   WHEN 'submitted' THEN 'confirmed'
                   WHEN 'approved' THEN 'ready_to_repair'
                   WHEN 'rejected' THEN 'cancelled'
                   ELSE state
               END
             WHERE state IN ('submitted', 'approved', 'rejected')
        """)

    @api.depends('material_request_ids')
    def _compute_material_request_count(self):
        for proposal in self:
            proposal.material_request_count = len(proposal.material_request_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('Mới'):
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('bts.repair.proposal')
                    or _('Mới')
                )
        return super().create(vals_list)

    def write(self, vals):
        if 'state' in vals:
            if not self.env.context.get('bts_repair_material_sync'):
                self._check_infrastructure_user()
            allowed_transitions = {
                'draft': {'draft', 'confirmed', 'ready_to_repair', 'cancelled'},
                'confirmed': {
                    'confirmed',
                    'waiting_material',
                    'ready_to_repair',
                    'cancelled',
                },
                'waiting_material': {
                    'waiting_material',
                    'ready_to_repair',
                    'cancelled',
                },
                'ready_to_repair': {
                    'ready_to_repair',
                    'repairing',
                    'done',
                    'cancelled',
                },
                'repairing': {'repairing', 'done', 'cancelled'},
                'done': {'done'},
                'cancelled': {'cancelled', 'draft'},
            }
            target_state = vals['state']
            for proposal in self:
                if target_state not in allowed_transitions.get(
                    proposal.state, set()
                ):
                    raise UserError(_(
                        'Không thể chuyển đề xuất sửa chữa từ trạng thái '
                        '%(from_state)s sang %(target)s.',
                        from_state=proposal.state,
                        target=target_state,
                    ))
        return super().write(vals)

    @api.constrains('estimated_cost')
    def _check_estimated_cost(self):
        for proposal in self:
            if proposal.estimated_cost < 0:
                raise ValidationError(
                    _('Chi phí dự kiến phải lớn hơn hoặc bằng 0.')
                )

    def _get_project(self):
        self.ensure_one()
        return self.project_id or self.bts_project_id

    def _get_station(self):
        self.ensure_one()
        return self.station_id or self.proposal_line_ids.mapped('station_id')[:1]

    def _check_state(self, allowed_states, message):
        for proposal in self:
            if proposal.state not in allowed_states:
                raise UserError(message)

    def _check_infrastructure_user(self):
        if not (
            self.env.user.has_group(
                'dtc_bts_base.group_dtc_bts_infrastructure'
            )
            or self.env.user.has_group('base.group_system')
        ):
            raise AccessError(_(
                'Chỉ Tổ quản lý hạ tầng được xử lý đề xuất sửa chữa.'
            ))

    def action_confirm(self):
        self._check_infrastructure_user()
        self._check_state(
            {'draft'},
            _('Chỉ đề xuất ở trạng thái Nháp mới được xác nhận.'),
        )
        for proposal in self:
            next_state = (
                'confirmed'
                if proposal.material_line_ids
                else 'ready_to_repair'
            )
            proposal.write({'state': next_state})
            proposal.message_post(body=_(
                'Tổ hạ tầng đã xác nhận đề xuất sửa chữa.'
            ))
        return True

    def action_create_material_request(self):
        self.ensure_one()
        self._check_infrastructure_user()
        self._check_state(
            {'confirmed', 'waiting_material'},
            _(
                'Chỉ đề xuất đã xác nhận hoặc đang chờ vật tư mới được tạo '
                'yêu cầu vật tư.'
            ),
        )
        if not self.material_line_ids:
            raise UserError(_(
                'Đề xuất không có dòng vật tư. Hãy xác nhận đề xuất để chuyển '
                'thẳng sang Sẵn sàng sửa chữa.'
            ))

        active_requests = self.material_request_ids.filtered(
            lambda request: request.state not in ('cancelled', 'rejected')
        )
        if active_requests:
            return self._open_material_requests(active_requests)

        project = self._get_project()
        if not project:
            raise UserError(_(
                'Không xác định được dự án BTS cho đề xuất sửa chữa.'
            ))
        station = self._get_station()
        material_request = self.env['bts.material.request'].create({
            'bts_project_id': project.id,
            'station_id': station.id if station else False,
            'repair_proposal_id': self.id,
            'source': 'maintenance',
            'request_user_id': self.env.user.id,
            'request_date': fields.Date.context_today(self),
            'note': _(
                'Yêu cầu vật tư được tạo từ đề xuất sửa chữa %s.'
            ) % self.name,
            'line_ids': [
                (0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'quantity_requested': line.product_uom_qty,
                })
                for line in self.material_line_ids
            ],
        })
        self.write({'state': 'waiting_material'})
        self.message_post(body=_(
            'Đã tạo yêu cầu vật tư %(request)s.',
            request=material_request.name,
        ))
        return self._open_material_requests(material_request)

    def action_view_material_requests(self):
        self.ensure_one()
        return self._open_material_requests(self.material_request_ids)

    def _open_material_requests(self, requests):
        action = self.env['ir.actions.actions']._for_xml_id(
            'dtc_bts_inventory.action_bts_material_request'
        )
        action['domain'] = [('id', 'in', requests.ids)]
        if len(requests) == 1:
            action.update({
                'view_mode': 'form',
                'views': [(
                    self.env.ref(
                        'dtc_bts_inventory.view_bts_material_request_form'
                    ).id,
                    'form',
                )],
                'res_id': requests.id,
            })
        return action

    def _sync_material_state(self):
        for proposal in self:
            if proposal.state in ('done', 'cancelled', 'repairing'):
                continue
            if not proposal.material_line_ids:
                if proposal.state == 'confirmed':
                    proposal.with_context(
                        bts_repair_material_sync=True
                    ).state = 'ready_to_repair'
                continue
            active_requests = proposal.material_request_ids.filtered(
                lambda request: request.state not in ('cancelled', 'rejected')
            )
            if active_requests and all(
                request.state == 'issued' for request in active_requests
            ):
                if proposal.state != 'ready_to_repair':
                    proposal.with_context(
                        bts_repair_material_sync=True
                    ).state = 'ready_to_repair'
                    proposal.message_post(body=_(
                        'Vật tư đã được cấp phát đủ. Đề xuất sẵn sàng sửa chữa.'
                    ))
            elif proposal.state != 'waiting_material':
                proposal.with_context(
                    bts_repair_material_sync=True
                ).state = 'waiting_material'
        return True

    def action_start_repair(self):
        self._check_infrastructure_user()
        self._check_state(
            {'ready_to_repair'},
            _(
                'Chỉ đề xuất ở trạng thái Sẵn sàng sửa chữa mới được bắt đầu.'
            ),
        )
        self.write({
            'state': 'repairing',
            'repair_started_date': fields.Datetime.now(),
        })
        self.message_post(body=_('Tổ hạ tầng đã bắt đầu sửa chữa.'))
        return True

    def action_done(self):
        self._check_infrastructure_user()
        self._check_state(
            {'ready_to_repair', 'repairing'},
            _(
                'Chỉ đề xuất đang sửa chữa hoặc sẵn sàng sửa chữa mới được '
                'hoàn tất.'
            ),
        )
        for proposal in self:
            if not proposal.repair_result:
                raise UserError(_(
                    'Vui lòng nhập kết quả sửa chữa trước khi hoàn tất.'
                ))

            completion_date = fields.Datetime.now()
            checklist_results = proposal.proposal_line_ids.mapped(
                'checklist_result_id'
            )
            checklist_results.write({
                'is_resolved': True,
                'resolved_date': completion_date,
                'repair_proposal_id': proposal.id,
            })

            requests = (
                proposal.maintenance_request_id
                | proposal.proposal_line_ids.mapped('maintenance_request_id')
            )
            requests.write({
                'repair_completed_date': completion_date,
                'repair_result_summary': proposal.repair_result,
                'station_page_state': 'done',
            })
            for maintenance_request in requests:
                maintenance_request.message_post(body=_(
                    'Đã hoàn tất sửa chữa theo đề xuất %(proposal)s: '
                    '%(result)s',
                    proposal=proposal.name,
                    result=proposal.repair_result,
                ))

            equipment = requests.mapped('equipment_id')
            equipment.write({
                'last_repair_date': fields.Date.context_today(proposal),
                'last_repair_note': proposal.repair_result,
            })

            proposal.write({
                'state': 'done',
                'repair_completed_date': completion_date,
            })
            proposal.message_post(body=_(
                'Đề xuất sửa chữa đã hoàn tất: %s'
            ) % proposal.repair_result)
        return True

    def action_cancel(self):
        self._check_state(
            {
                'draft',
                'confirmed',
                'waiting_material',
                'ready_to_repair',
                'repairing',
            },
            _('Không thể hủy đề xuất ở trạng thái hiện tại.'),
        )
        self.write({'state': 'cancelled'})
        self.message_post(body=_('Đề xuất sửa chữa đã được hủy.'))
        return True

    def action_reset_to_draft(self):
        self._check_state(
            {'cancelled'},
            _('Chỉ đề xuất đã hủy mới được đưa về Nháp.'),
        )
        if self.mapped('material_request_ids').filtered(
            lambda request: request.state not in ('cancelled', 'rejected')
        ):
            raise UserError(_(
                'Vui lòng hủy yêu cầu vật tư đang xử lý trước khi đưa đề xuất '
                'về Nháp.'
            ))
        self.write({
            'state': 'draft',
            'repair_started_date': False,
            'repair_completed_date': False,
        })
        return True


class BtsRepairProposalLine(models.Model):
    _name = 'bts.repair.proposal.line'
    _description = 'Chi tiết đề xuất sửa chữa BTS'
    _order = 'station_id, id'

    proposal_id = fields.Many2one(
        comodel_name='bts.repair.proposal',
        string='Đề xuất sửa chữa',
        required=True,
        ondelete='cascade',
        index=True,
    )
    maintenance_request_id = fields.Many2one(
        comodel_name='maintenance.request',
        string='Phiếu kiểm tra trạm',
        ondelete='set null',
    )
    station_id = fields.Many2one(
        comodel_name='project.task',
        string='Trạm BTS',
        ondelete='set null',
    )
    checklist_result_id = fields.Many2one(
        comodel_name='bts.maintenance.checklist.result',
        string='Dòng checklist lỗi',
        ondelete='set null',
    )
    item_id = fields.Many2one(
        comodel_name='bts.maintenance.checklist.item',
        string='Hạng mục lỗi',
        ondelete='restrict',
    )
    result_state = fields.Selection(
        selection=[
            ('need_repair', 'Cần sửa chữa'),
            ('need_replacement', 'Cần thay thế'),
        ],
        string='Kết quả lỗi',
        required=True,
    )
    technician_note = fields.Text(string='Ghi chú KTV')
    material_note = fields.Text(string='Vật tư cần sửa/thay')
    estimated_cost = fields.Float(string='Chi phí dự kiến')

    _sql_constraints = [
        (
            'proposal_checklist_result_unique',
            'unique(proposal_id, checklist_result_id)',
            'Mỗi dòng checklist lỗi chỉ được thêm một lần vào đề xuất.',
        ),
        (
            'line_estimated_cost_non_negative',
            'CHECK(estimated_cost >= 0)',
            'Chi phí dự kiến phải lớn hơn hoặc bằng 0.',
        ),
    ]

    @api.constrains('estimated_cost')
    def _check_line_estimated_cost(self):
        for line in self:
            if line.estimated_cost < 0:
                raise ValidationError(
                    _('Chi phí dự kiến phải lớn hơn hoặc bằng 0.')
                )


class BtsRepairProposalMaterialLine(models.Model):
    _name = 'bts.repair.proposal.material.line'
    _description = 'Vật tư cho đề xuất sửa chữa BTS'
    _order = 'id'

    proposal_id = fields.Many2one(
        comodel_name='bts.repair.proposal',
        string='Đề xuất sửa chữa',
        required=True,
        ondelete='cascade',
        index=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Vật tư',
        required=True,
        domain=[('is_bts_material', '=', True)],
        ondelete='restrict',
    )
    product_uom_qty = fields.Float(
        string='Số lượng',
        required=True,
        default=1.0,
        digits='Product Unit of Measure',
    )
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Đơn vị tính',
        required=True,
    )
    note = fields.Char(string='Ghi chú')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id

    @api.constrains('product_uom_qty')
    def _check_product_uom_qty(self):
        for line in self:
            if line.product_uom_qty <= 0:
                raise ValidationError(_('Số lượng vật tư phải lớn hơn 0.'))
