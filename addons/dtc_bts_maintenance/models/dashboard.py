from markupsafe import escape

from odoo import fields, models


class BtsMaintenanceDashboard(models.Model):
    _name = 'bts.maintenance.dashboard'
    _description = 'Dashboard bảo trì trạm BTS'

    name = fields.Char(string='Tên dashboard', required=True)
    dashboard_html = fields.Html(
        string='Dashboard bảo trì',
        compute='_compute_dashboard_html',
        sanitize=False,
    )

    def _compute_dashboard_html(self):
        for dashboard in self:
            dashboard.dashboard_html = dashboard._build_dashboard_html()

    def _get_dashboard_data(self):
        today = fields.Date.context_today(self)
        project_model = self.env['project.project'].sudo()

        equipment_model = (
            self.env['maintenance.equipment'].sudo()
            if 'maintenance.equipment' in self.env.registry.models
            else None
        )
        batch_model = (
            self.env['bts.maintenance.batch'].sudo()
            if 'bts.maintenance.batch' in self.env.registry.models
            else None
        )
        proposal_model = (
            self.env['bts.repair.proposal'].sudo()
            if 'bts.repair.proposal' in self.env.registry.models
            else None
        )

        equipment_domain = [
            ('active', '=', True),
            ('bts_state', '=', 'active'),
            ('station_id', '!=', False),
        ]
        total_equipment = (
            equipment_model.search_count(equipment_domain)
            if equipment_model is not None
            else 0
        )
        due_equipment = (
            equipment_model.search(equipment_domain + [
                ('next_action_date', '<=', today),
            ])
            if equipment_model is not None
            else []
        )

        due_by_project = {}
        for equipment in due_equipment or []:
            project = equipment.station_id.project_id
            if not project:
                continue
            project_data = due_by_project.setdefault(project.id, {
                'project': project,
                'equipment': [],
            })
            project_data['equipment'].append(equipment)

        open_batch_states = [
            'draft',
            'generated',
            'in_progress',
            'submitted',
            'reviewed',
        ]
        open_batches = (
            batch_model.search([('state', 'in', open_batch_states)])
            if batch_model is not None
            else []
        )
        open_batch_project_ids = set(open_batches.mapped('project_id').ids)

        pending_projects = (
            project_model.search([
                ('maintenance_handover_state', '=', 'pending'),
            ])
            if 'maintenance_handover_state' in project_model._fields
            else project_model.browse()
        )

        notifications = []
        notifications.extend(
            self._due_project_notifications(
                due_by_project,
                today,
                open_batch_project_ids,
            )
        )
        if batch_model is not None:
            notifications.extend(
                self._batch_notifications(open_batches, today)
            )
        if proposal_model is not None:
            notifications.extend(
                self._repair_notifications(
                    proposal_model.search([
                        ('state', 'in', [
                            'draft',
                            'confirmed',
                            'waiting_material',
                            'ready_to_repair',
                            'repairing',
                        ]),
                    ]),
                    today,
                )
            )
        notifications.extend(
            self._handover_notifications(pending_projects, today)
        )

        priority_order = {'red': 0, 'yellow': 1, 'gray': 2}
        notifications.sort(key=lambda item: (
            priority_order.get(item['priority'], 2),
            item['_sort_date'],
            item['title'],
        ))
        notifications = notifications[:15]

        if not notifications:
            notifications = [{
                'priority': 'gray',
                'icon': '✓',
                'title': 'Không có thông báo cần xử lý',
                'description': (
                    'Hiện chưa có dự án đến hạn, phiếu chờ xử lý hoặc '
                    'bàn giao cần tiếp nhận.'
                ),
                'date': '',
                'model': '',
                'res_id': False,
                'view_id': False,
            }]
        else:
            for notification in notifications:
                notification.pop('_sort_date', None)

        return {
            'kpis': {
                'total_equipment': total_equipment,
                'due_projects': len(due_by_project),
                'open_batches': len(open_batches),
                'pending_handover': len(pending_projects),
            },
            'notifications': notifications,
        }

    def _due_project_notifications(
        self,
        due_by_project,
        today,
        open_batch_project_ids=None,
    ):
        notifications = []
        open_batch_project_ids = open_batch_project_ids or set()
        view_id = self._view_id(
            'dtc_bts_maintenance.view_bts_due_project_form'
        )
        for project_data in due_by_project.values():
            project = project_data['project']
            if project.id in open_batch_project_ids:
                continue
            equipment = project_data['equipment']
            earliest_due = min(item.next_action_date for item in equipment)
            notifications.append({
                'priority': 'red' if earliest_due < today else 'yellow',
                'icon': '!',
                'title': 'Dự án đến hạn bảo trì',
                'description': (
                    f'Dự án {project.display_name} có {len(equipment)} trạm '
                    f'đến hạn bảo trì. Ngày đến hạn gần nhất: '
                    f'{self._format_date(earliest_due)}.'
                ),
                'date': self._format_date(earliest_due),
                'model': 'project.project',
                'res_id': project.id,
                'view_id': view_id,
                '_sort_date': earliest_due,
            })
        return notifications

    def _batch_notifications(self, batches, today):
        notifications = []
        view_id = self._view_id(
            'dtc_bts_maintenance.view_bts_maintenance_batch_form'
        )
        for batch in batches:
            project_name = batch.project_id.display_name or '-'
            if batch.state == 'submitted':
                title = 'Phiếu chờ Tổ hạ tầng kiểm tra'
                description = (
                    f'Phiếu {batch.name} của dự án {project_name} '
                    'đang chờ kiểm tra kết quả.'
                )
            elif batch.state == 'in_progress':
                title = 'Phiếu bảo trì đang thực hiện'
                description = (
                    f'Phiếu {batch.name} đang kiểm tra, đã hoàn tất '
                    f'{batch.completed_station_count}/{batch.station_count} '
                    'trạm.'
                )
            elif batch.state == 'reviewed':
                title = 'Phiếu bảo trì chờ hoàn tất'
                description = (
                    f'Phiếu {batch.name} của dự án {project_name} '
                    'đã kiểm tra kết quả và đang chờ hoàn tất.'
                )
            else:
                title = 'Phiếu bảo trì cần xử lý'
                description = (
                    f'Phiếu {batch.name} của dự án {project_name} '
                    'chưa hoàn tất quy trình bảo trì.'
                )
            notification_date = batch.maintenance_date or today
            notifications.append({
                'priority': 'yellow',
                'icon': '!',
                'title': title,
                'description': description,
                'date': self._format_date(notification_date),
                'model': 'bts.maintenance.batch',
                'res_id': batch.id,
                'view_id': view_id,
                '_sort_date': notification_date,
            })
        return notifications

    def _repair_notifications(self, proposals, today):
        notifications = []
        view_id = self._view_id(
            'dtc_bts_maintenance.view_bts_repair_proposal_form'
        )
        for proposal in proposals:
            project = proposal.project_id or proposal.bts_project_id
            project_name = project.display_name if project else '-'
            has_failure = bool(proposal.proposal_line_ids)
            if proposal.state == 'confirmed':
                title = 'Đề xuất đã xác nhận, cần tạo yêu cầu vật tư'
                description = (
                    f'Đề xuất {proposal.name} của dự án {project_name} '
                    'đã được Tổ hạ tầng xác nhận.'
                )
            elif proposal.state == 'waiting_material':
                title = 'Đề xuất sửa chữa đang chờ vật tư'
                description = (
                    f'Đề xuất {proposal.name} đang chờ kho cấp phát đủ vật tư.'
                )
            elif proposal.state == 'ready_to_repair':
                title = 'Đề xuất đã sẵn sàng sửa chữa'
                description = (
                    f'Đề xuất {proposal.name} đã đủ điều kiện để bắt đầu sửa.'
                )
            elif proposal.state == 'repairing':
                title = 'Đề xuất đang sửa chữa'
                description = (
                    f'Đề xuất {proposal.name} đang được Tổ hạ tầng xử lý.'
                )
            else:
                title = 'Hư hỏng mới cần Tổ hạ tầng xác nhận'
                description = (
                    f'Đề xuất {proposal.name} của dự án {project_name} '
                    'được tạo từ kết quả checklist lỗi.'
                )
            notification_date = (
                proposal.create_date.date()
                if proposal.create_date
                else today
            )
            notifications.append({
                'priority': 'red' if has_failure else 'yellow',
                'icon': '!',
                'title': title,
                'description': description,
                'date': self._format_date(notification_date),
                'model': 'bts.repair.proposal',
                'res_id': proposal.id,
                'view_id': view_id,
                '_sort_date': notification_date,
            })
        return notifications

    def _handover_notifications(self, projects, today):
        notifications = []
        view_id = self._view_id(
            'dtc_bts_maintenance.view_bts_maintenance_handover_project_form'
        )
        for project in projects:
            notification_date = project.maintenance_handover_date or today
            notifications.append({
                'priority': 'yellow',
                'icon': '!',
                'title': 'Dự án chờ tiếp nhận bàn giao',
                'description': (
                    f'Dự án {project.display_name} đang chờ Tổ hạ tầng '
                    'tiếp nhận bàn giao.'
                ),
                'date': self._format_date(notification_date),
                'model': 'project.project',
                'res_id': project.id,
                'view_id': view_id,
                '_sort_date': notification_date,
            })
        return notifications

    def _view_id(self, xml_id):
        view = self.env.ref(xml_id, raise_if_not_found=False)
        return view.id if view else False

    @staticmethod
    def _format_date(value):
        return value.strftime('%d/%m/%Y') if value else ''

    def _build_dashboard_html(self):
        data = self._get_dashboard_data()
        kpis = [
            ('Tổng hồ sơ bảo trì', data['kpis']['total_equipment']),
            ('Dự án đến hạn bảo trì', data['kpis']['due_projects']),
            (
                'Phiếu đang xử lý/chờ duyệt',
                data['kpis']['open_batches'],
            ),
            ('Chờ tiếp nhận bàn giao', data['kpis']['pending_handover']),
        ]
        kpi_html = ''.join(
            f"""
            <div class="bts-maintenance-kpi">
                <div class="bts-maintenance-kpi-label">{escape(label)}</div>
                <div class="bts-maintenance-kpi-value">{value}</div>
            </div>
            """
            for label, value in kpis
        )
        notification_html = ''.join(
            self._render_notification(notification)
            for notification in data['notifications']
        )

        return f"""
            <style>
                .bts-maintenance-dashboard,
                .bts-maintenance-dashboard * {{
                    font-family: "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    font-synthesis: none;
                    letter-spacing: 0;
                    text-shadow: none;
                }}
                .bts-maintenance-dashboard {{
                    padding: 20px 24px 28px;
                    color: #1f2937;
                    background: #f8f9fb;
                }}
                .bts-maintenance-title {{
                    margin: 0 0 18px;
                    color: #111827;
                    font-size: 30px;
                    font-weight: 600;
                    line-height: 1.25;
                }}
                .bts-maintenance-kpis {{
                    display: grid;
                    grid-template-columns: repeat(4, minmax(160px, 1fr));
                    gap: 12px;
                    margin-bottom: 20px;
                }}
                .bts-maintenance-kpi {{
                    min-height: 82px;
                    padding: 14px 16px;
                    background: #ffffff;
                    border: 1px solid #d9dee8;
                    border-left: 4px solid #0f766e;
                    border-radius: 10px;
                    box-shadow: none;
                }}
                .bts-maintenance-kpi-label {{
                    min-height: 32px;
                    color: #6b7280;
                    font-size: 13px;
                    font-weight: 500;
                    line-height: 1.3;
                }}
                .bts-maintenance-kpi-value {{
                    margin-top: 6px;
                    color: #111827;
                    font-size: 24px;
                    font-weight: 600;
                    line-height: 1;
                }}
                .bts-maintenance-feed {{
                    padding: 16px;
                    background: #ffffff;
                    border: 1px solid #d9dee8;
                    border-radius: 10px;
                }}
                .bts-maintenance-feed-title {{
                    margin: 0 0 14px;
                    color: #111827;
                    font-size: 16px;
                    font-weight: 600;
                    line-height: 1.4;
                }}
                .bts-maintenance-notifications {{
                    display: grid;
                    gap: 8px;
                }}
                .bts-maintenance-notification {{
                    display: grid;
                    grid-template-columns: 28px minmax(0, 1fr) auto;
                    align-items: center;
                    gap: 12px;
                    padding: 12px 14px;
                    background: #ffffff;
                    border: 1px solid #d9dee8;
                    border-left-width: 4px;
                    border-radius: 8px;
                }}
                .bts-maintenance-notification--red {{
                    border-left-color: #dc2626;
                }}
                .bts-maintenance-notification--yellow {{
                    border-left-color: #d97706;
                }}
                .bts-maintenance-notification--gray {{
                    border-left-color: #9ca3af;
                }}
                .bts-maintenance-notification-icon {{
                    display: flex;
                    width: 24px;
                    height: 24px;
                    align-items: center;
                    justify-content: center;
                    border-radius: 50%;
                    color: #ffffff;
                    font-size: 13px;
                    font-weight: 600;
                }}
                .bts-maintenance-notification--red
                .bts-maintenance-notification-icon {{
                    background: #dc2626;
                }}
                .bts-maintenance-notification--yellow
                .bts-maintenance-notification-icon {{
                    background: #d97706;
                }}
                .bts-maintenance-notification--gray
                .bts-maintenance-notification-icon {{
                    background: #6b7280;
                }}
                .bts-maintenance-notification-title {{
                    color: #111827;
                    font-size: 14px;
                    font-weight: 600;
                    line-height: 1.35;
                }}
                .bts-maintenance-notification-description {{
                    margin-top: 2px;
                    color: #4b5563;
                    font-size: 13px;
                    font-weight: 400;
                    line-height: 1.4;
                }}
                .bts-maintenance-notification-date {{
                    margin-top: 3px;
                    color: #9ca3af;
                    font-size: 12px;
                    font-weight: 400;
                }}
                .bts-maintenance-notification-link {{
                    padding: 6px 10px;
                    white-space: nowrap;
                    color: #0f766e;
                    background: #ffffff;
                    border: 1px solid #99d5cc;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 500;
                    text-decoration: none;
                }}
                .bts-maintenance-notification-link:hover {{
                    color: #115e59;
                    background: #f0fdfa;
                    text-decoration: none;
                }}
                @media (max-width: 1000px) {{
                    .bts-maintenance-kpis {{
                        grid-template-columns: repeat(2, minmax(160px, 1fr));
                    }}
                }}
                @media (max-width: 700px) {{
                    .bts-maintenance-dashboard {{
                        padding: 14px;
                    }}
                    .bts-maintenance-kpis {{
                        grid-template-columns: 1fr;
                    }}
                    .bts-maintenance-notification {{
                        grid-template-columns: 28px minmax(0, 1fr);
                    }}
                    .bts-maintenance-notification-link {{
                        grid-column: 2;
                        justify-self: start;
                    }}
                }}
            </style>
            <div class="bts-maintenance-dashboard">
                <h1 class="bts-maintenance-title">
                    BẢNG TỔNG HỢP BẢO TRÌ TRẠM BTS
                </h1>
                <div class="bts-maintenance-kpis">{kpi_html}</div>
                <section class="bts-maintenance-feed">
                    <h2 class="bts-maintenance-feed-title">
                        THÔNG BÁO CẦN XỬ LÝ
                    </h2>
                    <div class="bts-maintenance-notifications">
                        {notification_html}
                    </div>
                </section>
            </div>
        """

    def _render_notification(self, notification):
        priority = (
            notification['priority']
            if notification['priority'] in ('red', 'yellow', 'gray')
            else 'gray'
        )
        date_html = (
            '<div class="bts-maintenance-notification-date">%s</div>'
            % escape(notification['date'])
            if notification.get('date')
            else ''
        )
        link_html = ''
        if notification.get('model') and notification.get('res_id'):
            view_parameter = (
                f"&amp;view_id={int(notification['view_id'])}"
                if notification.get('view_id')
                else ''
            )
            link_html = (
                '<a class="bts-maintenance-notification-link" '
                'href="/web#id=%s&amp;model=%s&amp;view_type=form%s" '
                'target="_self">'
                'Xem chi tiết</a>'
            ) % (
                int(notification['res_id']),
                escape(notification['model']),
                view_parameter,
            )
        return f"""
            <article class="bts-maintenance-notification
                            bts-maintenance-notification--{priority}">
                <div class="bts-maintenance-notification-icon">
                    {escape(notification['icon'])}
                </div>
                <div class="bts-maintenance-notification-content">
                    <div class="bts-maintenance-notification-title">
                        {escape(notification['title'])}
                    </div>
                    <div class="bts-maintenance-notification-description">
                        {escape(notification['description'])}
                    </div>
                    {date_html}
                </div>
                {link_html}
            </article>
        """
