from odoo import api, fields, models
from odoo.exceptions import ValidationError


class BtsMaintenanceChecklistItem(models.Model):
    _name = 'bts.maintenance.checklist.item'
    _description = 'BTS Maintenance Checklist Item'
    _order = 'sequence, id'

    name = fields.Char(
        string='Hạng mục kiểm tra',
        required=True,
    )
    category_id = fields.Many2one(
        comodel_name='maintenance.equipment.category',
        string='Loại trạm',
        required=True,
        ondelete='restrict',
        index=True,
    )
    frequency_months = fields.Integer(
        string='Chu kỳ kiểm tra (tháng)',
        required=True,
    )
    is_external_required = fields.Boolean(
        string='Cần KTV thuê ngoài',
        default=False,
    )
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    @api.constrains('frequency_months')
    def _check_frequency_months(self):
        for item in self:
            if item.frequency_months not in (1, 3, 6):
                raise ValidationError(
                    'Chu kỳ kiểm tra chỉ được phép là 1, 3 hoặc 6 tháng.'
                )
