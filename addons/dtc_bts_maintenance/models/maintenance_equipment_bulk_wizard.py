from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class BtsMaintenanceEquipmentBulkWizard(models.TransientModel):
    _name = 'bts.maintenance.equipment.bulk.wizard'
    _description = 'Bulk Create BTS Maintenance Equipment'

    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Dự án BTS',
        required=True,
        domain=[('maintenance_handover_state', '=', 'accepted')],
    )
    effective_date = fields.Date(
        string='Ngày nghiệm thu dự án',
        related='project_id.acceptance_date',
        readonly=True,
    )
    technician_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Người phụ trách bảo trì',
        domain=[('share', '=', False)],
    )
    category_id = fields.Many2one(
        comodel_name='maintenance.equipment.category',
        string='Loại trạm',
        required=True,
        default=lambda self: self._default_category_id(),
    )
    only_handed_over = fields.Boolean(
        string='Chỉ tạo cho trạm đã bàn giao',
        default=False,
    )

    def _category_for_project(self, project):
        category_xmlid = {
            'macro': 'dtc_bts_maintenance.category_bts_macro',
            'cell': 'dtc_bts_maintenance.category_bts_cell',
        }.get(project.station_type)
        if not category_xmlid:
            return self.env['maintenance.equipment.category']
        return self.env.ref(category_xmlid, raise_if_not_found=False)

    def _default_category_id(self):
        project_id = self.env.context.get('default_project_id')
        if not project_id:
            return False
        category = self._category_for_project(
            self.env['project.project'].browse(project_id)
        )
        return category.id if category else False

    @api.onchange('project_id')
    def _onchange_project_id(self):
        self.category_id = self._category_for_project(self.project_id)

    def action_create_equipment(self):
        self.ensure_one()
        if self.project_id.maintenance_handover_state != 'accepted':
            raise ValidationError(
                'Dự án phải được tiếp nhận bàn giao trước khi tạo hồ sơ bảo trì.'
            )
        expected_category = self._category_for_project(self.project_id)
        if not expected_category:
            raise ValidationError(
                'Không tìm thấy loại trạm bảo trì phù hợp với dự án BTS.'
            )
        if self.category_id != expected_category:
            raise ValidationError(
                'Loại trạm bảo trì phải khớp với loại trạm của dự án BTS.'
            )
        effective_date = self.project_id.acceptance_date
        if not effective_date:
            raise ValidationError(
                'Vui lòng nhập ngày nghiệm thu dự án trước khi tạo hồ sơ bảo trì.'
            )

        all_stations = self.env['project.task'].search([
            ('project_id', '=', self.project_id.id),
        ])
        stations = all_stations
        ignored_count = 0
        if self.only_handed_over:
            stations = all_stations.filtered(
                lambda station: station.station_state in ('handover', 'operating')
            )
            ignored_count = len(all_stations - stations)

        existing_station_ids = set(
            self.env['maintenance.equipment'].search([
                ('station_id', 'in', stations.ids),
            ]).mapped('station_id').ids
        )
        stations_to_create = stations.filtered(
            lambda station: station.id not in existing_station_ids
        )
        skipped_count = len(stations) - len(stations_to_create)

        checklist_items = self.env['bts.maintenance.checklist.item'].search([
            ('category_id', '=', self.category_id.id),
            ('active', '=', True),
        ])
        frequencies = [
            frequency
            for frequency in checklist_items.mapped('frequency_months')
            if frequency > 0
        ]
        next_action_date = (
            effective_date + relativedelta(months=min(frequencies))
            if frequencies
            else False
        )

        equipment_values = []
        for station in stations_to_create:
            name_parts = [
                'HSBT',
                station.station_code,
                station.name,
            ]
            equipment_values.append({
                'station_id': station.id,
                'name': ' - '.join(part for part in name_parts if part),
                'category_id': self.category_id.id,
                'technician_user_id': self.technician_user_id.id or False,
                'effective_date': effective_date,
                'next_action_date': next_action_date,
                'bts_state': 'active',
            })
        if equipment_values:
            self.env['maintenance.equipment'].create(equipment_values)

        created_count = len(equipment_values)
        if hasattr(self.project_id, 'message_post'):
            self.project_id.sudo().message_post(
                body=_(
                    'Đã tạo %(count)s hồ sơ thiết bị bảo trì cho dự án.',
                    count=created_count,
                )
            )
        message = _(
            'Đã tạo: %(created)s hồ sơ; bỏ qua do đã tồn tại: '
            '%(skipped)s trạm; không xử lý theo bộ lọc: %(ignored)s trạm.',
            created=created_count,
            skipped=skipped_count,
            ignored=ignored_count,
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Tạo hồ sơ bảo trì cho dự án'),
                'message': message,
                'type': 'success',
                'sticky': True,
                'created_count': created_count,
                'skipped_count': skipped_count,
                'ignored_count': ignored_count,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
