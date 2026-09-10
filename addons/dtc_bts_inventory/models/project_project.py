from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    bts_material_request_ids = fields.One2many(
        comodel_name='bts.material.request',
        inverse_name='bts_project_id',
        string='Yêu cầu vật tư',
    )
    bts_material_request_count = fields.Integer(
        string='Số yêu cầu vật tư',
        compute='_compute_bts_material_request_count',
    )

    def _compute_bts_material_request_count(self):
        for project in self:
            project.bts_material_request_count = len(
                project.bts_material_request_ids
            )

    def action_create_bts_material_request(self):
        self.ensure_one()
        allowed_groups = (
            'base.group_system',
            'dtc_bts_base.group_dtc_bts_ksgs',
        )
        if not any(self.env.user.has_group(group) for group in allowed_groups):
            raise AccessError(_('Bạn không có quyền tạo yêu cầu vật tư từ dự án.'))
        if self.state != 'approved':
            raise UserError(_(
                'Chỉ có thể tạo yêu cầu vật tư khi dự án đã được phê duyệt.'
            ))

        request = self.env['bts.material.request'].create({
            'bts_project_id': self.id,
            'request_user_id': self.env.user.id,
            'source': 'project_construction',
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Yêu cầu vật tư dự án'),
            'res_model': 'bts.material.request',
            'res_id': request.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_bts_material_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Yêu cầu vật tư'),
            'res_model': 'bts.material.request',
            'view_mode': 'tree,form',
            'domain': [('bts_project_id', '=', self.id)],
            'context': {'default_bts_project_id': self.id},
        }
