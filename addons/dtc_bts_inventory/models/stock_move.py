from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    bts_material_request_line_id = fields.Many2one(
        comodel_name='bts.material.request.line',
        string='Dòng yêu cầu cấp phát',
        index=True,
        ondelete='set null',
        copy=False,
    )
