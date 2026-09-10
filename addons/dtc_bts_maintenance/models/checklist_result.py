from odoo import fields, models


class BtsMaintenanceChecklistResult(models.Model):
    _name = 'bts.maintenance.checklist.result'
    _description = 'BTS Maintenance Checklist Result'
    _order = 'request_id, id'

    request_id = fields.Many2one(
        comodel_name='maintenance.request',
        string='Phiếu bảo trì',
        required=True,
        ondelete='cascade',
        index=True,
    )
    item_id = fields.Many2one(
        comodel_name='bts.maintenance.checklist.item',
        string='Hạng mục kiểm tra',
        required=True,
        ondelete='restrict',
        index=True,
    )
    category_id = fields.Many2one(
        comodel_name='maintenance.equipment.category',
        string='Loại trạm',
        related='item_id.category_id',
        store=True,
        readonly=True,
    )
    frequency_months = fields.Integer(
        string='Chu kỳ (tháng)',
        related='item_id.frequency_months',
        store=True,
        readonly=True,
    )
    is_external_required = fields.Boolean(
        string='Cần KTV thuê ngoài',
        related='item_id.is_external_required',
        store=True,
        readonly=True,
    )
    result_state = fields.Selection(
        selection=[
            ('stable', 'Ổn định'),
            ('need_repair', 'Cần sửa chữa'),
            ('need_replacement', 'Cần thay thế'),
        ],
        string='Kết quả kiểm tra',
        required=True,
        default='stable',
    )
    measurement_value = fields.Char(string='Thông số đo')
    note = fields.Text(string='Ghi chú')
    is_resolved = fields.Boolean(
        string='Đã xử lý',
        default=False,
        copy=False,
        index=True,
    )
    resolved_date = fields.Datetime(
        string='Thời điểm xử lý',
        readonly=True,
        copy=False,
    )
    repair_proposal_id = fields.Many2one(
        comodel_name='bts.repair.proposal',
        string='Đề xuất đã xử lý',
        readonly=True,
        copy=False,
        ondelete='set null',
    )

    _sql_constraints = [
        (
            'request_item_unique',
            'unique(request_id, item_id)',
            'Mỗi hạng mục kiểm tra chỉ được xuất hiện một lần trên phiếu bảo trì.',
        ),
    ]
