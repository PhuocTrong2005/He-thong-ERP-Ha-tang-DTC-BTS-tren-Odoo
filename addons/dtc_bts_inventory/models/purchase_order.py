from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .constants import BTS_PURCHASE_CONFIRMATION_TOKEN


def _is_warehouse_readonly_user(env):
    return (
        not env.su
        and env.user.has_group('dtc_bts_base.group_dtc_bts_warehouse')
        and not env.user.has_group('dtc_bts_base.group_dtc_bts_pkh')
        and not env.user.has_group('base.group_system')
    )


def _check_warehouse_purchase_readonly(env):
    if _is_warehouse_readonly_user(env):
        raise AccessError(_(
            'Thủ kho chỉ được xem đơn mua hàng BTS.'
        ))


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    bts_material_request_id = fields.Many2one(
        comodel_name='bts.material.request',
        string='Yêu cầu vật tư',
        index=True,
        tracking=True,
        ondelete='set null',
        copy=False,
    )
    bts_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Dự án BTS',
        index=True,
        tracking=True,
        help='Dự án BTS mà đơn mua hàng phục vụ. Vật tư được quản lý theo gói dự án.',
    )
    bts_project_code = fields.Char(
        string='Mã dự án',
        related='bts_project_id.project_code',
        store=True,
        readonly=True,
    )

    bts_warehouse_mail_sent_at = fields.Datetime(
        string='Email thông báo Thủ kho đã tạo lúc',
        readonly=True,
        copy=False,
    )

    @api.onchange('bts_material_request_id')
    def _onchange_bts_material_request_id(self):
        if self.bts_material_request_id:
            self.bts_project_id = self.bts_material_request_id.bts_project_id

    @api.constrains('bts_material_request_id', 'bts_project_id')
    def _check_bts_request_project(self):
        for order in self:
            if (
                order.bts_material_request_id
                and order.bts_project_id
                != order.bts_material_request_id.bts_project_id
            ):
                raise ValidationError(_(
                    'Yêu cầu vật tư và đơn mua hàng phải thuộc cùng một dự án BTS.'
                ))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            request_id = vals.get('bts_material_request_id')
            if request_id and not vals.get('bts_project_id'):
                request = self.env['bts.material.request'].browse(request_id)
                vals['bts_project_id'] = request.bts_project_id.id
        allowed_groups = (
            'base.group_system',
            'dtc_bts_base.group_dtc_bts_pkh',
        )
        if (
            not self.env.su
            and not any(
                self.env.user.has_group(group) for group in allowed_groups
            )
        ):
            raise AccessError(_(
                'Chỉ Trưởng phòng Kế hoạch được tạo đơn mua hàng.'
            ))
        return super().create(vals_list)

    def write(self, vals):
        _check_warehouse_purchase_readonly(self.env)
        return super().write(vals)

    def unlink(self):
        _check_warehouse_purchase_readonly(self.env)
        return super().unlink()

    def _prepare_picking(self):
        res = super()._prepare_picking()
        if self.bts_project_id:
            res['bts_project_id'] = self.bts_project_id.id
        if self.bts_material_request_id:
            res['bts_material_request_id'] = self.bts_material_request_id.id
        return res

    def action_view_picking(self):
        result = super().action_view_picking()
        if len(self) == 1 and self.bts_project_id:
            form_view = self.env.ref(
                'dtc_bts_inventory.view_stock_picking_form_bts_inventory'
            )
            tree_view = self.env.ref(
                'dtc_bts_inventory.view_stock_picking_tree_bts_inventory'
            )
            if result.get('res_id'):
                result['views'] = [(form_view.id, 'form')]
                result['view_id'] = form_view.id
            else:
                result['views'] = [
                    (tree_view.id, 'tree'),
                    (form_view.id, 'form'),
                ]
                result['view_id'] = tree_view.id
        return result

    def button_confirm(self):
        orders_to_notify = self.filtered(
            lambda order: order.state not in ('purchase', 'done')
        )
        result = super(
            PurchaseOrder,
            self.with_context(
                bts_purchase_confirmation_token=(
                    BTS_PURCHASE_CONFIRMATION_TOKEN
                ),
            ),
        ).button_confirm()
        for order in self.filtered('bts_material_request_id'):
            request = order.bts_material_request_id
            if request.state not in ('cancelled', 'issued'):
                request.with_context(
                    bts_inventory_workflow=True
                ).state = 'purchasing'
            if order not in orders_to_notify:
                continue
            warehouse_users = request._get_warehouse_users()
            request._notify_material_users(
                'incoming',
                warehouse_users,
                _(
                    'Đơn mua %(order)s cho dự án %(project)s đã được đặt. '
                    'Vui lòng xác nhận phiếu nhập khi hàng về.',
                    order=order.name,
                    project=(
                        request.bts_project_code
                        or request.bts_project_id.display_name
                    ),
                ),
            )
            order._bts_queue_workflow_email(
                'dtc_bts_inventory.'
                'mail_template_purchase_order_confirmed_warehouse',
                warehouse_users,
                'purchase_order_confirmed_warehouse',
                marker_field='bts_warehouse_mail_sent_at',
                extra_context={
                    'material_request_name': request.name,
                    'project_code': request.bts_project_code,
                },
            )
        return result

    def button_cancel(self):
        result = super().button_cancel()
        self.mapped('bts_material_request_id')._refresh_supply_state()
        return result


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    bts_material_request_line_id = fields.Many2one(
        comodel_name='bts.material.request.line',
        string='Dòng yêu cầu vật tư',
        index=True,
        ondelete='set null',
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        _check_warehouse_purchase_readonly(self.env)
        return super().create(vals_list)

    def write(self, vals):
        _check_warehouse_purchase_readonly(self.env)
        return super().write(vals)

    def unlink(self):
        _check_warehouse_purchase_readonly(self.env)
        return super().unlink()
