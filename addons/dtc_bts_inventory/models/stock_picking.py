from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools.float_utils import float_compare

from .constants import BTS_PURCHASE_CONFIRMATION_TOKEN


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    bts_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Dự án BTS',
        index=True,
        tracking=True,
    )
    bts_project_code = fields.Char(
        string='Mã dự án',
        related='bts_project_id.project_code',
        store=True,
        readonly=True,
    )
    bts_material_request_id = fields.Many2one(
        comodel_name='bts.material.request',
        string='Yêu cầu cấp phát',
        index=True,
        ondelete='set null',
        copy=False,
    )
    bts_material_request_name = fields.Char(
        string='Mã yêu cầu',
        related='bts_material_request_id.name',
        store=True,
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        planning_only = (
            not self.env.su
            and self.env.user.has_group(
                'dtc_bts_base.group_dtc_bts_pkh'
            )
            and not self.env.user.has_group(
                'dtc_bts_base.group_dtc_bts_warehouse'
            )
            and not self.env.user.has_group('base.group_system')
        )
        purchase_confirmation = (
            self.env.context.get('bts_purchase_confirmation_token')
            is BTS_PURCHASE_CONFIRMATION_TOKEN
        )
        if planning_only and not purchase_confirmation:
            raise AccessError(_(
                'Trưởng phòng Kế hoạch chỉ được xem phiếu nhập, phiếu xuất; '
                'không được tạo phiếu kho trực tiếp.'
            ))

        requester_groups = (
            'dtc_bts_base.group_dtc_bts_ksgs',
            'dtc_bts_base.group_dtc_bts_infrastructure',
        )
        operational_groups = (
            'base.group_system',
            'dtc_bts_base.group_dtc_bts_pkh',
            'dtc_bts_base.group_dtc_bts_warehouse',
        )
        requester_only = (
            any(self.env.user.has_group(group) for group in requester_groups)
            and not any(
                self.env.user.has_group(group)
                for group in operational_groups
            )
        )
        if requester_only:
            raise AccessError(_(
                'KSGS và Tổ hạ tầng không được tạo phiếu kho trực tiếp.'
            ))
        return super().create(vals_list)

    def _action_done(self):
        res = super()._action_done()
        for picking in self.filtered('bts_material_request_id'):
            request = picking.bts_material_request_id
            if picking.picking_type_code == 'outgoing':
                request._update_issued_quantities()
            elif picking.picking_type_code == 'incoming':
                request._refresh_supply_state()
        return res

    def button_validate(self):
        bts_pickings = self.filtered('bts_project_id')
        if bts_pickings and not (
            self.env.user.has_group('base.group_system')
            or self.env.user.has_group(
                'dtc_bts_base.group_dtc_bts_warehouse'
            )
        ):
            raise AccessError(_(
                'Chỉ Thủ kho được xác nhận nhập hoặc xuất kho BTS.'
            ))
        self.filtered(
            lambda picking: (
                picking.picking_type_code == 'outgoing'
                and picking.bts_material_request_id
            )
        )._check_bts_delivery_workflow()
        self.filtered(
            lambda picking: (
                picking.picking_type_code == 'incoming'
                and picking.bts_material_request_id
            )
        )._check_bts_receipt_workflow()
        return super().button_validate()

    def _check_bts_receipt_workflow(self):
        for picking in self:
            request = picking.bts_material_request_id
            if request.state != 'purchasing':
                raise UserError(_(
                    'Chỉ được xác nhận nhập kho khi yêu cầu vật tư đang ở '
                    'trạng thái Đang mua hàng.'
                ))
            linked_orders = request.purchase_order_ids.filtered(
                lambda order: (
                    order.state in ('purchase', 'done')
                    and picking in order.picking_ids
                )
            )
            if not linked_orders:
                raise UserError(_(
                    'Phiếu nhập phải được sinh từ đơn mua đã xác nhận của '
                    'đúng yêu cầu vật tư.'
                ))

    def _check_bts_delivery_workflow(self):
        for picking in self:
            request = picking.bts_material_request_id
            if request.state not in ('ready', 'partially_delivered'):
                raise UserError(_(
                    'Chỉ được xác nhận xuất kho sau khi phiếu nhập của đơn '
                    'mua đã hoàn tất và yêu cầu ở trạng thái Sẵn sàng cấp phát.'
                ))
            request_moves = picking.move_ids.filtered(
                lambda move: move.state != 'cancel'
            )
            if (
                not request_moves
                or any(
                    not move.bts_material_request_line_id
                    or move.bts_material_request_line_id.request_id != request
                    for move in request_moves
                )
            ):
                raise UserError(_(
                    'Phiếu xuất phải được tạo từ nút Tạo phiếu xuất trên '
                    'đúng yêu cầu vật tư.'
                ))
        self._check_bts_approved_delivery_quantities()

    def _check_bts_approved_delivery_quantities(self):
        moves = self.mapped('move_ids').filtered(
            lambda item: (
                item.state != 'cancel'
                and item.bts_material_request_line_id
            )
        )
        request_lines = moves.mapped('bts_material_request_line_id')
        if request_lines:
            self.env.cr.execute(
                """
                    SELECT id
                      FROM bts_material_request_line
                     WHERE id IN %s
                     FOR UPDATE
                """,
                [tuple(request_lines.ids)],
            )
            request_lines.invalidate_recordset(['quantity_issued'])

        quantities_by_line = {}
        for move in moves:
            request_line = move.bts_material_request_line_id
            quantity = move.product_uom._compute_quantity(
                move.quantity,
                request_line.product_uom_id,
            )
            quantities_by_line[request_line] = (
                quantities_by_line.get(request_line, 0.0) + quantity
            )

        for request_line, delivery_quantity in quantities_by_line.items():
            remaining_quantity = max(
                request_line.quantity_approved
                - request_line.quantity_issued,
                0.0,
            )
            if float_compare(
                delivery_quantity,
                remaining_quantity,
                precision_rounding=request_line.product_uom_id.rounding,
            ) > 0:
                raise UserError(_(
                    'Không thể xuất %(delivery)s %(uom)s của '
                    '%(product)s: số lượng được duyệt còn lại chỉ là '
                    '%(remaining)s %(uom)s.',
                    delivery=delivery_quantity,
                    remaining=remaining_quantity,
                    uom=request_line.product_uom_id.display_name,
                    product=request_line.product_id.display_name,
                ))

    @api.onchange('bts_material_request_id')
    def _onchange_bts_material_request_id(self):
        if self.bts_material_request_id:
            request = self.bts_material_request_id
            self.bts_project_id = request.bts_project_id
            self.origin = request.name
