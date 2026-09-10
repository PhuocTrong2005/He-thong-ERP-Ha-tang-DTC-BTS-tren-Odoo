from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


REQUESTER_GROUPS = (
    'base.group_system',
    'dtc_bts_base.group_dtc_bts_ksgs',
    'dtc_bts_base.group_dtc_bts_infrastructure',
)
PLANNING_GROUPS = (
    'base.group_system',
    'dtc_bts_base.group_dtc_bts_pkh',
)
WAREHOUSE_GROUPS = (
    'base.group_system',
    'dtc_bts_base.group_dtc_bts_warehouse',
)
MANAGER_GROUPS = (
    'base.group_system',
)


class BtsMaterialRequest(models.Model):
    _name = 'bts.material.request'
    _description = 'Yêu cầu cấp phát vật tư BTS'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc, id desc'

    name = fields.Char(
        string='Mã yêu cầu',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Mới'),
        tracking=True,
    )
    bts_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Dự án BTS',
        required=True,
        tracking=True,
        index=True,
        ondelete='restrict',
    )
    bts_project_code = fields.Char(
        string='Mã dự án',
        related='bts_project_id.project_code',
        store=True,
        readonly=True,
    )
    source = fields.Selection(
        selection=[
            ('project_construction', 'Dự án thi công'),
            ('maintenance', 'Bảo trì / sửa chữa'),
            ('manual', 'Khác'),
        ],
        string='Nguồn phát sinh',
        required=True,
        default='project_construction',
        tracking=True,
    )
    request_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Người yêu cầu',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    request_date = fields.Date(
        string='Ngày yêu cầu',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    vendor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Nhà cung cấp dự kiến',
        domain=[('partner_type', '=', 'supplier')],
        tracking=True,
    )
    line_ids = fields.One2many(
        comodel_name='bts.material.request.line',
        inverse_name='request_id',
        string='Dòng vật tư',
        copy=True,
    )
    purchase_order_ids = fields.One2many(
        comodel_name='purchase.order',
        inverse_name='bts_material_request_id',
        string='Đơn mua hàng',
        copy=False,
    )
    purchase_order_count = fields.Integer(
        string='Số đơn mua hàng',
        compute='_compute_document_counts',
    )
    picking_ids = fields.One2many(
        comodel_name='stock.picking',
        inverse_name='bts_material_request_id',
        string='Phiếu kho',
        copy=False,
    )
    picking_count = fields.Integer(
        string='Số phiếu kho',
        compute='_compute_document_counts',
    )
    notification_ids = fields.One2many(
        comodel_name='bts.material.notification',
        inverse_name='request_id',
        string='Thông báo',
        copy=False,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Nháp'),
            ('requested', 'Đã gửi'),
            ('approved', 'Đã duyệt'),
            ('waiting_purchase', 'Chờ mua hàng / bổ sung vật tư'),
            ('purchasing', 'Đang mua hàng'),
            ('ready', 'Sẵn sàng cấp phát'),
            ('partially_delivered', 'Cấp phát một phần'),
            ('issued', 'Hoàn tất yêu cầu'),
            ('postponed', 'Tạm hoãn'),
            ('rejected', 'Từ chối'),
            ('cancelled', 'Hủy'),
        ],
        string='Trạng thái',
        required=True,
        default='draft',
        tracking=True,
        index=True,
    )
    rejection_reason = fields.Text(string='Lý do từ chối', tracking=True)
    postponement_reason = fields.Text(string='Lý do tạm hoãn', tracking=True)
    note = fields.Text(string='Ghi chú')
    rejection_mail_sent_at = fields.Datetime(
        string='Email từ chối đã tạo lúc',
        readonly=True,
        copy=False,
    )
    ready_mail_sent_at = fields.Datetime(
        string='Email sẵn sàng cấp phát đã tạo lúc',
        readonly=True,
        copy=False,
    )
    submission_mail_sent_at = fields.Datetime(
        string='Email yêu cầu duyệt đã tạo lúc',
        readonly=True,
        copy=False,
    )
    decision_mail_sent_at = fields.Datetime(
        string='Email kết quả xử lý đã tạo lúc',
        readonly=True,
        copy=False,
    )
    issued_mail_sent_at = fields.Datetime(
        string='Email hoàn tất xuất kho đã tạo lúc',
        readonly=True,
        copy=False,
    )

    _sql_constraints = [
        (
            'material_request_name_unique',
            'unique(name)',
            'Mã yêu cầu cấp phát đã tồn tại.',
        ),
    ]

    @api.depends('purchase_order_ids', 'picking_ids')
    def _compute_document_counts(self):
        can_read_purchase_orders = self.env[
            'purchase.order'
        ].check_access_rights('read', raise_exception=False)
        can_read_pickings = self.env[
            'stock.picking'
        ].check_access_rights('read', raise_exception=False)
        for request in self:
            request.purchase_order_count = (
                len(request.purchase_order_ids)
                if can_read_purchase_orders
                else 0
            )
            request.picking_count = (
                len(request.picking_ids)
                if can_read_pickings
                else 0
            )

    @api.model_create_multi
    def create(self, vals_list):
        if not self._user_has_any_group(REQUESTER_GROUPS + PLANNING_GROUPS):
            raise AccessError(_('Bạn không có quyền tạo yêu cầu vật tư.'))
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('Mới'):
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code(
                        'dtc.bts.material.request'
                    )
                    or _('Mới')
                )
        return super().create(vals_list)

    def write(self, vals):
        if (
            'state' in vals
            and not self.env.context.get('bts_inventory_workflow')
            and not self._user_has_any_group(MANAGER_GROUPS)
        ):
            raise AccessError(_(
                'Không được thay đổi trực tiếp trạng thái yêu cầu vật tư.'
            ))
        return super().write(vals)

    @api.constrains('line_ids', 'state')
    def _check_request_lines(self):
        for request in self:
            if request.state != 'draft' and not request.line_ids:
                raise ValidationError(
                    'Yêu cầu vật tư phải có ít nhất một dòng vật tư.'
                )

    def action_submit(self):
        self._check_action_groups(REQUESTER_GROUPS, _(
            'Chỉ KSGS hoặc Tổ hạ tầng được gửi yêu cầu vật tư.'
        ))
        for request in self:
            if request.state != 'draft':
                raise UserError(_('Chỉ yêu cầu ở trạng thái Nháp mới được gửi.'))
            request._ensure_has_lines()
            request.with_context(bts_inventory_workflow=True).write({
                'state': 'requested',
                'rejection_reason': False,
                'postponement_reason': False,
                'rejection_mail_sent_at': False,
                'submission_mail_sent_at': False,
                'decision_mail_sent_at': False,
            })
            request._bts_close_activities(
                'dtc_bts_inventory.mail_activity_type_material_request_rejected',
                feedback=_('Yêu cầu vật tư đã được sửa và gửi lại.'),
            )
            request._bts_queue_workflow_email(
                'dtc_bts_inventory.mail_template_material_request_submitted',
                request._get_planning_users(),
                'material_request_submitted',
                marker_field='submission_mail_sent_at',
                extra_context=request._material_email_context(),
            )
            request._notify_material_users(
                'approval',
                request._get_planning_users(),
                _(
                    'Yêu cầu %(request)s của dự án %(project)s đang chờ '
                    'phê duyệt.',
                    request=request.name,
                    project=(
                        request.bts_project_code
                        or request.bts_project_id.display_name
                    ),
                ),
            )
        return True

    def action_approve(self):
        self._check_action_groups(PLANNING_GROUPS, _(
            'Chỉ Trưởng phòng Kế hoạch được duyệt yêu cầu vật tư.'
        ))
        for request in self:
            if request.state != 'requested':
                raise UserError(_('Chỉ yêu cầu Đã gửi mới được duyệt.'))
            request._ensure_has_lines()
            for line in request.line_ids:
                if line.quantity_approved <= 0:
                    line.quantity_approved = line.quantity_requested
            request.with_context(bts_inventory_workflow=True).state = (
                'waiting_purchase'
            )
            request._close_material_notifications(('approval',))
            request._bts_queue_workflow_email(
                'dtc_bts_inventory.mail_template_material_request_approved',
                request._get_requester_users(),
                'material_request_approved',
                marker_field='decision_mail_sent_at',
                extra_context=request._material_email_context(),
            )
        return True

    def action_reject(self):
        self._check_action_groups(PLANNING_GROUPS, _(
            'Chỉ Trưởng phòng Kế hoạch được từ chối yêu cầu vật tư.'
        ))
        for request in self:
            if request.state != 'requested':
                raise UserError(_('Chỉ yêu cầu Đã gửi mới được từ chối.'))
            if not request.rejection_reason:
                raise UserError(_('Vui lòng nhập lý do từ chối.'))
            request.with_context(bts_inventory_workflow=True).state = 'rejected'
            request._schedule_rejection_activity()
            request.message_post(body=_(
                'Yêu cầu vật tư bị từ chối. Lý do: %(reason)s',
                reason=request.rejection_reason,
            ))
            request._bts_queue_workflow_email(
                'dtc_bts_inventory.mail_template_material_request_rejected',
                request._get_requester_users(),
                'material_request_rejected',
                marker_field='rejection_mail_sent_at',
                extra_context=request._material_email_context(),
            )
        return True

    def action_postpone(self):
        self._check_action_groups(PLANNING_GROUPS, _(
            'Chỉ Trưởng phòng Kế hoạch được tạm hoãn yêu cầu vật tư.'
        ))
        for request in self:
            if request.state != 'requested':
                raise UserError(_('Chỉ yêu cầu Đã gửi mới được tạm hoãn.'))
            if not request.postponement_reason:
                raise UserError(_('Vui lòng nhập lý do tạm hoãn.'))
            request.with_context(bts_inventory_workflow=True).state = 'postponed'
            request.message_post(body=_(
                'Yêu cầu vật tư được tạm hoãn. Lý do: %(reason)s',
                reason=request.postponement_reason,
            ))
            request._bts_queue_workflow_email(
                'dtc_bts_inventory.mail_template_material_request_postponed',
                request._get_requester_users(),
                'material_request_postponed',
                marker_field='decision_mail_sent_at',
                extra_context=request._material_email_context(),
            )
        return True

    def _schedule_rejection_activity(self):
        self.ensure_one()
        candidates = (
            self.request_user_id | self.bts_project_id.project_manager_id
        ).filtered(lambda user: user.active)
        for user in candidates:
            activity = self._bts_schedule_activity_once(
                'dtc_bts_inventory.mail_activity_type_material_request_rejected',
                user=user,
                summary=_('Yêu cầu vật tư %(request)s bị từ chối') % {
                    'request': self.name,
                },
                deadline=fields.Date.context_today(self) + timedelta(days=2),
                note=_(
                    'Vui lòng sửa và gửi lại yêu cầu. Lý do từ chối: %(reason)s',
                    reason=self.rejection_reason,
                ),
            )
            if activity:
                break

    def action_cancel(self):
        for request in self:
            is_requester = (
                request.request_user_id == self.env.user
                and self._user_has_any_group(REQUESTER_GROUPS)
            )
            if not is_requester and not self._user_has_any_group(
                PLANNING_GROUPS + WAREHOUSE_GROUPS
            ):
                raise AccessError(_('Bạn không có quyền hủy yêu cầu vật tư.'))
            if request.picking_ids.filtered(
                lambda picking: (
                    picking.state == 'done'
                    and picking.picking_type_code == 'outgoing'
                )
            ):
                raise UserError(
                    _('Không thể hủy yêu cầu đã có phiếu xuất hoàn thành.')
                )
            request.with_context(bts_inventory_workflow=True).state = 'cancelled'
        return True

    def action_set_draft(self):
        self._check_action_groups(REQUESTER_GROUPS + MANAGER_GROUPS, _(
            'Bạn không có quyền đưa yêu cầu về Nháp.'
        ))
        for request in self:
            if request.state not in ('postponed', 'rejected', 'cancelled'):
                raise UserError(
                    _('Chỉ yêu cầu bị từ chối hoặc đã hủy mới về Nháp.')
                )
            request.with_context(bts_inventory_workflow=True).write({
                'state': 'draft',
                'rejection_reason': False,
                'postponement_reason': False,
                'rejection_mail_sent_at': False,
                'submission_mail_sent_at': False,
                'decision_mail_sent_at': False,
            })
        return True

    def action_create_purchase_order(self):
        self.ensure_one()
        self._check_action_groups(PLANNING_GROUPS, _(
            'Chỉ Trưởng phòng Kế hoạch được tạo đơn mua hàng.'
        ))
        if self.state not in (
            'approved', 'waiting_purchase', 'purchasing', 'partially_delivered'
        ):
            raise UserError(
                _('Yêu cầu chưa ở trạng thái cho phép tạo đơn mua hàng.')
            )
        if not self.vendor_id:
            raise UserError(_('Vui lòng chọn nhà cung cấp dự kiến.'))

        order_lines = []
        for line in self.line_ids:
            quantity = line._get_quantity_to_purchase()
            if quantity <= 0:
                continue
            order_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.product_id.display_name,
                'product_qty': quantity,
                'product_uom': line.product_uom_id.id,
                'price_unit': line.product_id.standard_price,
                'date_planned': fields.Datetime.now(),
                'bts_material_request_line_id': line.id,
            }))
        if not order_lines:
            raise UserError(
                _('Không còn số lượng thiếu cần tạo đơn mua hàng.')
            )

        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.vendor_id.id,
            'origin': self.name,
            'bts_project_id': self.bts_project_id.id,
            'bts_material_request_id': self.id,
            'order_line': order_lines,
        })
        self.with_context(bts_inventory_workflow=True).state = (
            'waiting_purchase'
        )
        return {
            'type': 'ir.actions.act_window',
            'name': _('Đơn mua hàng BTS'),
            'res_model': 'purchase.order',
            'res_id': purchase_order.id,
            'view_mode': 'form',
            'views': [(
                self.env.ref(
                    'dtc_bts_inventory.view_purchase_order_form_bts_inventory'
                ).id,
                'form',
            )],
            'target': 'current',
        }

    def action_create_delivery(self):
        self.ensure_one()
        self._check_action_groups(WAREHOUSE_GROUPS, _(
            'Chỉ Thủ kho được tạo phiếu xuất.'
        ))
        if self.state not in ('ready', 'partially_delivered'):
            raise UserError(
                _('Yêu cầu chưa ở trạng thái cho phép cấp phát vật tư.')
            )
        self._ensure_has_lines()
        warehouse = self._get_warehouse()
        picking_type = warehouse.out_type_id
        source_location = (
            picking_type.default_location_src_id
            or warehouse.lot_stock_id
        )
        destination_location = (
            picking_type.default_location_dest_id
            or self.env.ref('stock.stock_location_customers')
        )
        move_vals_list = []

        for line in self.line_ids:
            remaining_qty = max(
                line.quantity_approved - line.quantity_issued,
                0.0,
            )
            available_qty = line._get_available_quantity(warehouse)
            quantity = min(remaining_qty, available_qty)
            if quantity <= 0:
                continue
            move_vals_list.append({
                'name': line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': quantity,
                'product_uom': line.product_uom_id.id,
                'location_id': source_location.id,
                'location_dest_id': destination_location.id,
                'bts_material_request_line_id': line.id,
            })

        if not move_vals_list:
            raise UserError(
                _('Kho hiện không có số lượng khả dụng để cấp phát.')
            )

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': source_location.id,
            'location_dest_id': destination_location.id,
            'origin': self.name,
            'bts_project_id': self.bts_project_id.id,
            'bts_material_request_id': self.id,
            'move_ids_without_package': [
                (0, 0, vals) for vals in move_vals_list
            ],
        })
        picking.action_confirm()
        picking.action_assign()
        return self._action_open_picking(picking)

    def action_view_pickings(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'stock.action_picking_tree_all'
        )
        tree_view = self.env.ref(
            'dtc_bts_inventory.view_stock_picking_tree_bts_inventory'
        )
        form_view = self.env.ref(
            'dtc_bts_inventory.view_stock_picking_form_bts_inventory'
        )
        action['domain'] = [('id', 'in', self.picking_ids.ids)]
        action['views'] = [
            (tree_view.id, 'tree'),
            (form_view.id, 'form'),
        ]
        action['view_id'] = tree_view.id
        if len(self.picking_ids) == 1:
            action['views'] = [(form_view.id, 'form')]
            action['view_id'] = form_view.id
            action['res_id'] = self.picking_ids.id
        return action

    def action_view_purchase_orders(self):
        self.ensure_one()
        tree_view = self.env.ref(
            'dtc_bts_inventory.view_purchase_order_tree_bts_inventory'
        )
        form_view = self.env.ref(
            'dtc_bts_inventory.view_purchase_order_form_bts_inventory'
        )
        return {
            'type': 'ir.actions.act_window',
            'name': _('Đơn mua hàng BTS'),
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'views': [
                (tree_view.id, 'tree'),
                (form_view.id, 'form'),
            ],
            'domain': [('id', 'in', self.purchase_order_ids.ids)],
        }

    def _ensure_has_lines(self):
        for request in self:
            if not request.line_ids:
                raise UserError(
                    _('Yêu cầu vật tư phải có ít nhất một dòng vật tư.')
                )

    def _get_warehouse(self):
        warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if not warehouse:
            raise UserError(_('Chưa cấu hình kho cho công ty hiện tại.'))
        return warehouse

    def _refresh_supply_state(self):
        for request in self:
            if request.state in (
                'draft', 'requested', 'postponed', 'rejected', 'cancelled',
                'issued'
            ):
                continue
            request._update_issued_quantities(change_state=False)
            lines = request.line_ids
            if not lines:
                continue
            if all(
                line.quantity_issued >= line.quantity_approved
                for line in lines
            ):
                new_state = 'issued'
            elif any(line.quantity_issued > 0 for line in lines):
                new_state = 'partially_delivered'
            else:
                enough_received = all(
                    line._get_received_purchase_quantity()
                    >= line.quantity_approved
                    for line in lines
                )
                if enough_received:
                    new_state = 'ready'
                elif any(
                    line._get_confirmed_purchase_quantity() > 0
                    for line in lines
                ):
                    new_state = 'purchasing'
                else:
                    new_state = 'waiting_purchase'

            old_state = request.state
            request.with_context(bts_inventory_workflow=True).state = new_state
            if new_state == 'ready' and old_state != 'ready':
                request._close_material_notifications(('incoming',))
                request._notify_material_ready()
                request._bts_queue_workflow_email(
                    'dtc_bts_inventory.'
                    'mail_template_material_ready_for_issue',
                    request._get_ready_email_users(),
                    'material_ready_for_issue',
                    marker_field='ready_mail_sent_at',
                    extra_context=request._material_email_context(),
                )
            if new_state == 'issued' and old_state != 'issued':
                request._notify_material_users(
                    'lock_po',
                    request._get_planning_users(),
                    _(
                        'Yêu cầu %(request)s của dự án %(project)s đã xuất '
                        'kho hoàn tất. Vui lòng khóa PO.',
                        request=request.name,
                        project=(
                            request.bts_project_code
                            or request.bts_project_id.display_name
                        ),
                    ),
                )
                request._bts_queue_workflow_email(
                    'dtc_bts_inventory.'
                    'mail_template_material_request_issued',
                    request._get_planning_users(),
                    'material_request_issued',
                    marker_field='issued_mail_sent_at',
                    extra_context=request._material_email_context(),
                )
        return True

    def _update_issued_quantities(self, change_state=True):
        for request in self:
            for line in request.line_ids:
                done_moves = self.env['stock.move'].search([
                    ('bts_material_request_line_id', '=', line.id),
                    ('state', '=', 'done'),
                    ('picking_id.picking_type_code', '=', 'outgoing'),
                ])
                quantity = 0.0
                for move in done_moves:
                    quantity += move.product_uom._compute_quantity(
                        move.quantity,
                        line.product_uom_id,
                    )
                # System-owned value: always derived from completed deliveries.
                line.sudo().write({'quantity_issued': quantity})
            if change_state:
                request._refresh_supply_state()
        return True

    def _notify_material_ready(self):
        for request in self:
            candidates = (
                request.request_user_id
                | request.bts_project_id.project_manager_id
            ).filtered(lambda candidate: candidate.active)
            user = next(
                (
                    candidate
                    for candidate in candidates
                    if request._bts_user_can_read_activity_record(candidate)
                ),
                self.env['res.users'],
            )
            if not user:
                continue
            message = _(
                'Vật tư cho dự án %(project)s đã sẵn sàng cấp phát.',
                project=(
                    request.bts_project_code
                    or request.bts_project_id.display_name
                ),
            )
            request._notify_material_users('ready', user, message)

    def _notify_material_users(self, notification_type, users, message):
        notification_model = self.env['bts.material.notification'].sudo()
        for request in self:
            for user in (users or self.env['res.users']).filtered('active'):
                if not request._bts_user_can_read_activity_record(user):
                    continue
                notification = notification_model.search([
                    ('request_id', '=', request.id),
                    ('user_id', '=', user.id),
                    ('notification_type', '=', notification_type),
                ], limit=1)
                values = {
                    'message': message,
                    'is_seen': False,
                    'seen_date': False,
                }
                if notification:
                    notification.write(values)
                else:
                    values.update({
                        'request_id': request.id,
                        'user_id': user.id,
                        'notification_type': notification_type,
                    })
                    notification_model.create(values)
        return True

    def _close_material_notifications(self, notification_types):
        notifications = self.env['bts.material.notification'].sudo().search([
            ('request_id', 'in', self.ids),
            ('notification_type', 'in', tuple(notification_types)),
            ('is_seen', '=', False),
        ])
        if notifications:
            notifications.write({
                'is_seen': True,
                'seen_date': fields.Datetime.now(),
            })
        return True

    def _get_planning_users(self):
        group = self.env.ref(
            'dtc_bts_base.group_dtc_bts_pkh',
            raise_if_not_found=False,
        )
        return (
            group.users.filtered(lambda user: user.active)
            if group
            else self.env['res.users']
        )

    def _get_requester_users(self):
        self.ensure_one()
        return (
            self.request_user_id | self.bts_project_id.project_manager_id
        ).filtered(lambda user: user.active)

    def _get_warehouse_users(self):
        group = self.env.ref(
            'dtc_bts_base.group_dtc_bts_warehouse',
            raise_if_not_found=False,
        )
        return (
            group.users.filtered(lambda user: user.active)
            if group
            else self.env['res.users']
        )

    def _get_ready_email_users(self):
        self.ensure_one()
        if self.request_user_id and self.request_user_id.active:
            return self.request_user_id
        # Compatibility fallback for legacy rows created before requester was
        # required. New records always use request_user_id.
        return self.bts_project_id.project_manager_id.filtered(
            lambda user: user.active
        )

    def _material_email_context(self):
        self.ensure_one()
        warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        base_url = self.get_base_url()
        return {
            'state_label': dict(self._fields['state'].selection).get(
                self.state,
                self.state,
            ),
            'warehouse_name': warehouse.display_name if warehouse else '',
            'material_lines': [
                {
                    'product': line.product_id.display_name or '',
                    'quantity': line.quantity_approved,
                    'uom': line.product_uom_id.display_name or '',
                }
                for line in self.line_ids
            ],
            'approve_url': (
                '%s/dtc_bts_inventory/material_request/%s/approve'
                % (base_url.rstrip('/'), self.id)
                if base_url
                else False
            ),
            'reject_url': (
                '%s/dtc_bts_inventory/material_request/%s/reject'
                % (base_url.rstrip('/'), self.id)
                if base_url
                else False
            ),
            'postpone_url': (
                '%s/dtc_bts_inventory/material_request/%s/postpone'
                % (base_url.rstrip('/'), self.id)
                if base_url
                else False
            ),
        }

    def action_lock_purchase_orders(self):
        self._check_action_groups(PLANNING_GROUPS, _(
            'Chỉ Trưởng phòng Kế hoạch được khóa đơn mua hàng.'
        ))
        for request in self:
            if request.state != 'issued':
                raise UserError(_(
                    'Chỉ được khóa đơn mua sau khi vật tư đã xuất hoàn tất.'
                ))
            orders = request.purchase_order_ids.filtered(
                lambda order: order.state == 'purchase'
            )
            orders.button_done()
            request._close_material_notifications(('lock_po',))
            request.message_post(body=_(
                'Trưởng phòng Kế hoạch đã khóa %(count)s đơn mua hàng.',
                count=len(orders),
            ))
        return True

    def _action_open_picking(self, picking):
        form_view = self.env.ref(
            'dtc_bts_inventory.view_stock_picking_form_bts_inventory'
        )
        return {
            'type': 'ir.actions.act_window',
            'name': _('Phiếu xuất kho'),
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'views': [(form_view.id, 'form')],
            'res_id': picking.id,
            'target': 'current',
        }

    @api.model
    def _user_has_any_group(self, groups):
        return any(self.env.user.has_group(group) for group in groups)

    def _check_action_groups(self, groups, message):
        if not self._user_has_any_group(groups):
            raise AccessError(message)


class BtsMaterialRequestLine(models.Model):
    _name = 'bts.material.request.line'
    _description = 'Dòng yêu cầu cấp phát vật tư BTS'
    _order = 'id'

    request_id = fields.Many2one(
        comodel_name='bts.material.request',
        string='Yêu cầu vật tư',
        required=True,
        ondelete='cascade',
        index=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Vật tư',
        required=True,
        domain="[('is_bts_material', '=', True)]",
    )
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Đơn vị tính',
        required=True,
    )
    quantity_requested = fields.Float(
        string='Số lượng yêu cầu',
        required=True,
        digits='Product Unit of Measure',
    )
    quantity_approved = fields.Float(
        string='Số lượng duyệt',
        digits='Product Unit of Measure',
        default=0.0,
    )
    quantity_issued = fields.Float(
        string='Số lượng đã cấp',
        digits='Product Unit of Measure',
        readonly=True,
        default=0.0,
    )
    quantity_available = fields.Float(
        string='Tồn khả dụng',
        compute='_compute_supply_quantities',
        digits='Product Unit of Measure',
    )
    quantity_to_purchase = fields.Float(
        string='Cần mua',
        compute='_compute_supply_quantities',
        digits='Product Unit of Measure',
    )
    purchase_line_ids = fields.One2many(
        comodel_name='purchase.order.line',
        inverse_name='bts_material_request_line_id',
        string='Dòng mua hàng',
    )
    state = fields.Selection(
        related='request_id.state',
        store=True,
        readonly=True,
    )

    @api.depends(
        'product_id',
        'product_uom_id',
        'quantity_approved',
        'quantity_issued',
        'purchase_line_ids.product_qty',
        'purchase_line_ids.qty_received',
        'purchase_line_ids.order_id.state',
    )
    def _compute_supply_quantities(self):
        for line in self:
            if not line.product_id or not line.product_uom_id:
                line.quantity_available = 0.0
                line.quantity_to_purchase = 0.0
                continue
            # These are derived summary values. Requesters may see the totals
            # without receiving access to purchase or stock documents.
            line_sudo = line.sudo()
            warehouse = self.env['stock.warehouse'].sudo().search([
                ('company_id', '=', self.env.company.id),
            ], limit=1)
            line.quantity_available = (
                line_sudo._get_available_quantity(warehouse)
                if warehouse
                else 0.0
            )
            line.quantity_to_purchase = (
                line_sudo._get_quantity_to_purchase()
            )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id

    def write(self, vals):
        if self.env.su and set(vals) <= {'quantity_issued'}:
            return super().write(vals)
        if any(self.env.user.has_group(group) for group in MANAGER_GROUPS):
            return super().write(vals)

        allowed_fields = set()
        if any(self.env.user.has_group(group) for group in REQUESTER_GROUPS):
            if all(line.request_id.state == 'draft' for line in self):
                allowed_fields.update({
                    'product_id',
                    'product_uom_id',
                    'quantity_requested',
                })
        if any(self.env.user.has_group(group) for group in PLANNING_GROUPS):
            allowed_fields.add('quantity_approved')
        if set(vals) - allowed_fields:
            raise AccessError(_(
                'Bạn không có quyền sửa các trường này trên dòng yêu cầu vật tư.'
            ))
        return super().write(vals)

    def unlink(self):
        if any(self.env.user.has_group(group) for group in MANAGER_GROUPS):
            return super().unlink()
        allowed = (
            any(self.env.user.has_group(group) for group in REQUESTER_GROUPS)
            and all(line.request_id.state == 'draft' for line in self)
        )
        if not allowed:
            raise AccessError(_(
                'Chỉ được xóa dòng vật tư khi yêu cầu còn ở trạng thái Nháp.'
            ))
        return super().unlink()

    @api.constrains('quantity_requested', 'quantity_approved')
    def _check_quantities(self):
        for line in self:
            if line.quantity_requested <= 0:
                raise ValidationError(
                    'Số lượng yêu cầu phải lớn hơn 0.'
                )
            if line.quantity_approved < 0:
                raise ValidationError(
                    'Số lượng duyệt không được nhỏ hơn 0.'
                )
            if line.quantity_approved > line.quantity_requested:
                raise ValidationError(
                    'Số lượng duyệt không được vượt số lượng yêu cầu.'
                )

    def _get_available_quantity(self, warehouse):
        self.ensure_one()
        if not warehouse or not self.product_id:
            return 0.0
        quantity = self.env['stock.quant']._get_available_quantity(
            self.product_id,
            warehouse.lot_stock_id,
            strict=False,
        )
        return self.product_id.uom_id._compute_quantity(
            quantity,
            self.product_uom_id,
        )

    def _get_outstanding_purchase_quantity(self):
        self.ensure_one()
        quantity = 0.0
        for purchase_line in self.purchase_line_ids.filtered(
            lambda line: line.order_id.state != 'cancel'
        ):
            outstanding = max(
                purchase_line.product_qty - purchase_line.qty_received,
                0.0,
            )
            quantity += purchase_line.product_uom._compute_quantity(
                outstanding,
                self.product_uom_id,
            )
        return quantity

    def _get_confirmed_purchase_quantity(self):
        self.ensure_one()
        quantity = 0.0
        for purchase_line in self.purchase_line_ids.filtered(
            lambda line: line.order_id.state in ('purchase', 'done')
        ):
            quantity += purchase_line.product_uom._compute_quantity(
                purchase_line.product_qty,
                self.product_uom_id,
            )
        return quantity

    def _get_received_purchase_quantity(self):
        self.ensure_one()
        quantity = 0.0
        for purchase_line in self.purchase_line_ids.filtered(
            lambda line: line.order_id.state in ('purchase', 'done')
        ):
            quantity += purchase_line.product_uom._compute_quantity(
                purchase_line.qty_received,
                self.product_uom_id,
            )
        return quantity

    def _get_ordered_purchase_quantity(self):
        self.ensure_one()
        quantity = 0.0
        for purchase_line in self.purchase_line_ids.filtered(
            lambda line: line.order_id.state != 'cancel'
        ):
            quantity += purchase_line.product_uom._compute_quantity(
                purchase_line.product_qty,
                self.product_uom_id,
            )
        return quantity

    def _get_quantity_to_purchase(self):
        self.ensure_one()
        if not self.product_id or not self.product_uom_id:
            return 0.0
        return max(
            self.quantity_approved - self._get_ordered_purchase_quantity(),
            0.0,
        )
