from odoo import fields, models


class BtsMaterialRequest(models.Model):
    _inherit = 'bts.material.request'

    repair_proposal_id = fields.Many2one(
        comodel_name='bts.repair.proposal',
        string='Đề xuất sửa chữa',
        index=True,
        ondelete='set null',
        copy=False,
    )
    station_id = fields.Many2one(
        comodel_name='project.task',
        string='Trạm BTS sửa chữa',
        index=True,
        ondelete='set null',
        copy=False,
    )

    def write(self, vals):
        result = super().write(vals)
        if 'state' in vals:
            # The request state is managed by PKH/warehouse users, while the
            # linked repair proposal is intentionally restricted to the
            # infrastructure team. Synchronize this derived state as the
            # system without granting those users access to repair proposals.
            self.sudo().mapped(
                'repair_proposal_id'
            )._sync_material_state()
        return result
