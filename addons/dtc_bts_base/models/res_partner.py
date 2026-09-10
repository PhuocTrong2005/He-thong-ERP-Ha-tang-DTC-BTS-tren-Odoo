from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_type = fields.Selection(
        selection=[
            ('supplier', 'Nhà cung cấp'),
            ('landowner', 'Chủ đất'),
            ('telecom_partner', 'Đối tác viễn thông'),
            ('external_technician', 'Kỹ thuật viên thuê ngoài'),
            ('other', 'Khác'),
        ],
        string='Loại đối tác',
        required=True,
        default='other',
        index=True,
    )
