from collections import Counter, defaultdict

from markupsafe import escape

from odoo import api, fields, models


class DtcBtsInventoryDashboard(models.Model):
    _name = 'dtc.bts.inventory.dashboard'
    _description = 'Theo dõi cung ứng và cấp phát vật tư công trình'

    name = fields.Char(string='Tên bảng tổng hợp', required=True)
    dashboard_html = fields.Html(
        string='Theo dõi cung ứng vật tư',
        compute='_compute_dashboard_html',
        sanitize=False,
    )

    @api.depends_context('uid', 'lang', 'tz')
    def _compute_dashboard_html(self):
        for dashboard in self:
            dashboard.dashboard_html = dashboard._build_dashboard_html()

    def _build_dashboard_html(self):
        data = self._get_supply_analytics_data()
        return f"""
            <style>
                .dtc-supply-dashboard,
                .dtc-supply-dashboard * {{
                    box-sizing: border-box;
                    font-family: "Segoe UI", Roboto, Arial, sans-serif;
                }}
                .dtc-supply-dashboard {{
                    --ink: #202631;
                    --muted: #667085;
                    --line: #d9e1e8;
                    --blue: #168fe3;
                    --green: #20b26b;
                    --amber: #e59b24;
                    --red: #d94b4b;
                    padding: 18px 20px 28px;
                    color: var(--ink);
                    background: #fff;
                }}
                .dtc-supply-header {{
                    margin-bottom: 14px;
                }}
                .dtc-supply-title {{
                    margin: 0;
                    color: #1d2430;
                    font-size: 25px;
                    font-weight: 700;
                }}
                .dtc-supply-subtitle {{
                    margin-top: 4px;
                    color: var(--muted);
                    font-size: 12px;
                }}
                .dtc-supply-kpis {{
                    display: grid;
                    grid-template-columns: repeat(4, minmax(150px, 1fr));
                    gap: 8px;
                    margin-bottom: 12px;
                }}
                .dtc-supply-kpi {{
                    min-height: 108px;
                    padding: 16px;
                    border: 1px solid var(--line);
                    border-top: 4px solid var(--blue);
                    border-radius: 5px;
                    background: #fff;
                }}
                .dtc-supply-kpi--green {{ border-top-color: var(--green); }}
                .dtc-supply-kpi--amber {{ border-top-color: var(--amber); }}
                .dtc-supply-kpi--red {{ border-top-color: var(--red); }}
                .dtc-supply-kpi-value {{
                    color: #202631;
                    font-size: 31px;
                    font-weight: 600;
                    line-height: 1.1;
                }}
                .dtc-supply-kpi-label {{
                    margin-top: 7px;
                    color: var(--muted);
                    font-size: 12px;
                    line-height: 1.35;
                }}
                .dtc-supply-grid {{
                    display: grid;
                    grid-template-columns: minmax(0, 1.55fr) minmax(290px, .85fr);
                    gap: 12px;
                    margin-bottom: 12px;
                }}
                .dtc-supply-panel {{
                    min-width: 0;
                    padding: 13px 14px;
                    border: 1px solid var(--line);
                    border-radius: 5px;
                    background: #fff;
                }}
                .dtc-supply-panel-title {{
                    margin: 0 0 12px;
                    color: #242b36;
                    font-size: 16px;
                    font-weight: 700;
                    text-align: center;
                }}
                .dtc-project-progress {{
                    display: grid;
                    gap: 8px;
                }}
                .dtc-project-progress-row {{
                    display: grid;
                    grid-template-columns: minmax(125px, 190px) minmax(100px, 1fr) 45px;
                    align-items: center;
                    gap: 8px;
                }}
                .dtc-project-progress-name {{
                    overflow: hidden;
                    color: #475467;
                    font-size: 11px;
                    text-decoration: none;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                .dtc-project-progress-name:hover {{
                    color: #0b73b9;
                    text-decoration: underline;
                }}
                .dtc-progress-track {{
                    height: 14px;
                    overflow: hidden;
                    border-radius: 2px;
                    background: #edf1f5;
                }}
                .dtc-progress-fill {{
                    height: 100%;
                    min-width: 2px;
                    background: var(--blue);
                }}
                .dtc-progress-fill--done {{ background: var(--green); }}
                .dtc-progress-fill--risk {{ background: var(--amber); }}
                .dtc-project-progress-value {{
                    color: #475467;
                    font-size: 11px;
                    font-weight: 700;
                    text-align: right;
                }}
                .dtc-status-stack {{
                    display: flex;
                    height: 24px;
                    overflow: hidden;
                    margin: 17px 0 18px;
                    border-radius: 3px;
                    background: #edf1f5;
                }}
                .dtc-status-segment {{ min-width: 2px; }}
                .dtc-status-segment--approval {{ background: #a66bb5; }}
                .dtc-status-segment--supply {{ background: var(--amber); }}
                .dtc-status-segment--issue {{ background: var(--blue); }}
                .dtc-status-segment--done {{ background: var(--green); }}
                .dtc-status-legend {{
                    display: grid;
                    gap: 9px;
                }}
                .dtc-status-item {{
                    display: grid;
                    grid-template-columns: 11px minmax(0, 1fr) auto;
                    align-items: center;
                    gap: 8px;
                    color: #475467;
                    font-size: 12px;
                }}
                .dtc-status-dot {{
                    width: 10px;
                    height: 10px;
                    border-radius: 2px;
                }}
                .dtc-status-count {{
                    color: #202631;
                    font-weight: 700;
                }}
                .dtc-supply-table-wrap {{
                    overflow-x: auto;
                    border: 1px solid var(--line);
                    border-radius: 5px;
                    background: #fff;
                }}
                .dtc-supply-table-title {{
                    margin: 0;
                    padding: 13px 14px 10px;
                    color: #242b36;
                    font-size: 16px;
                    font-weight: 700;
                }}
                .dtc-supply-table {{
                    width: 100%;
                    min-width: 960px;
                    border-collapse: collapse;
                    font-size: 11px;
                }}
                .dtc-supply-table th {{
                    padding: 8px 7px;
                    color: #344054;
                    border-top: 1px solid var(--line);
                    border-bottom: 1px solid #b9d5df;
                    background: #f7fafb;
                    font-weight: 700;
                    text-align: right;
                    white-space: nowrap;
                }}
                .dtc-supply-table th:first-child,
                .dtc-supply-table th:nth-child(2),
                .dtc-supply-table th:nth-child(3),
                .dtc-supply-table th:last-child {{
                    text-align: left;
                }}
                .dtc-supply-table td {{
                    padding: 7px;
                    color: #475467;
                    border-bottom: 1px solid #edf0f2;
                    text-align: right;
                    white-space: nowrap;
                }}
                .dtc-supply-table td:first-child,
                .dtc-supply-table td:nth-child(2),
                .dtc-supply-table td:nth-child(3),
                .dtc-supply-table td:last-child {{
                    text-align: left;
                }}
                .dtc-supply-table tbody tr:nth-child(even) {{
                    background: #fafafa;
                }}
                .dtc-supply-table a {{
                    color: #1674b7;
                    text-decoration: none;
                }}
                .dtc-supply-table a:hover {{ text-decoration: underline; }}
                .dtc-supply-number--danger {{
                    color: var(--red) !important;
                    font-weight: 700;
                }}
                .dtc-supply-number--waiting {{
                    color: #b76e00 !important;
                    font-weight: 700;
                }}
                .dtc-supply-badge {{
                    display: inline-block;
                    padding: 3px 6px;
                    border-radius: 9px;
                    color: #475467;
                    background: #eef2f5;
                    font-size: 10px;
                    font-weight: 700;
                }}
                .dtc-supply-badge--danger {{
                    color: #a72e2e;
                    background: #fde8e8;
                }}
                .dtc-supply-badge--waiting {{
                    color: #966000;
                    background: #fff1d3;
                }}
                .dtc-supply-badge--ready {{
                    color: #116a45;
                    background: #dff6ea;
                }}
                .dtc-supply-badge--approval {{
                    color: #70417c;
                    background: #f0e4f3;
                }}
                .dtc-supply-empty {{
                    padding: 24px 12px;
                    color: #98a2b3;
                    font-size: 12px;
                    text-align: center;
                }}
                .dtc-supply-alerts {{
                    margin-top: 12px;
                }}
                .dtc-supply-alert-list {{
                    display: grid;
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                    gap: 7px;
                }}
                .dtc-supply-alert {{
                    display: grid;
                    grid-template-columns: 22px minmax(0, 1fr) auto;
                    align-items: center;
                    gap: 8px;
                    padding: 8px 10px;
                    border: 1px solid var(--line);
                    border-left: 4px solid var(--amber);
                    border-radius: 4px;
                }}
                .dtc-supply-alert--red {{ border-left-color: var(--red); }}
                .dtc-supply-alert-icon {{
                    display: grid;
                    width: 20px;
                    height: 20px;
                    place-items: center;
                    color: #fff;
                    border-radius: 50%;
                    background: var(--amber);
                    font-size: 11px;
                    font-weight: 700;
                }}
                .dtc-supply-alert--red .dtc-supply-alert-icon {{
                    background: var(--red);
                }}
                .dtc-supply-alert-title {{
                    color: #344054;
                    font-size: 11px;
                    font-weight: 700;
                }}
                .dtc-supply-alert-description {{
                    color: #667085;
                    font-size: 10px;
                }}
                .dtc-supply-alert-link {{
                    color: #0f766e;
                    font-size: 10px;
                    text-decoration: none;
                    white-space: nowrap;
                }}
                @media (max-width: 1050px) {{
                    .dtc-supply-grid {{ grid-template-columns: 1fr; }}
                    .dtc-supply-alert-list {{ grid-template-columns: 1fr; }}
                }}
                @media (max-width: 720px) {{
                    .dtc-supply-dashboard {{ padding: 10px; }}
                    .dtc-supply-kpis {{ grid-template-columns: repeat(2, 1fr); }}
                    .dtc-project-progress-row {{
                        grid-template-columns: 110px minmax(80px, 1fr) 40px;
                    }}
                }}
            </style>
            <div class="dtc-supply-dashboard">
                <header class="dtc-supply-header">
                    <h1 class="dtc-supply-title">
                        Theo dõi cung ứng và cấp phát vật tư công trình
                    </h1>
                    <div class="dtc-supply-subtitle">
                        Đối chiếu trực tiếp chuỗi Yêu cầu → Mua → Nhập → Xuất;
                        số lượng luôn giữ theo đúng đơn vị tính của từng vật tư
                    </div>
                </header>
                {self._render_workflow_notifications(data)}
                {self._render_kpis(data)}
                <div class="dtc-supply-grid">
                    {self._render_project_progress(data)}
                    {self._render_request_status(data)}
                </div>
                {self._render_supply_table(data)}
                {self._render_supply_alerts(data)}
            </div>
        """

    def _get_supply_analytics_data(self):
        requests = self._dashboard_model('bts.material.request').search(
            [('state', 'not in', ('cancelled', 'rejected'))],
            order='request_date desc, id desc',
        )
        lines = requests.mapped('line_ids').filtered('product_id')
        purchase_lines = self._search_if_readable(
            'purchase.order.line',
            [
                ('bts_material_request_line_id', 'in', lines.ids),
                ('order_id.state', '!=', 'cancel'),
            ],
        )
        purchase_by_line = defaultdict(
            lambda: self.env['purchase.order.line']
        )
        for purchase_line in purchase_lines:
            request_line = purchase_line.bts_material_request_line_id
            purchase_by_line[request_line.id] |= purchase_line

        rows = []
        approved_line_count = 0
        completed_line_count = 0
        shortage_line_count = 0
        waiting_issue_line_count = 0
        mismatch_line_count = 0
        project_data = defaultdict(lambda: {
            'project': self.env['project.project'],
            'ratios': [],
            'line_count': 0,
            'shortage_count': 0,
            'waiting_count': 0,
        })

        for line in lines:
            request = line.request_id
            demand = (
                line.quantity_approved
                if line.quantity_approved > 0
                else line.quantity_requested
            )
            ordered = received = 0.0
            for purchase_line in purchase_by_line[line.id]:
                ordered += purchase_line.product_uom._compute_quantity(
                    purchase_line.product_qty,
                    line.product_uom_id,
                )
                received += purchase_line.product_uom._compute_quantity(
                    purchase_line.qty_received,
                    line.product_uom_id,
                )
            issued = line.quantity_issued
            precision = line.product_uom_id.rounding or 0.01
            approved = line.quantity_approved > 0
            awaiting_approval = request.state in (
                'draft',
                'requested',
                'postponed',
            ) or not approved
            missing = (
                max(demand - received, 0.0)
                if not awaiting_approval
                else 0.0
            )
            waiting_issue = max(received - issued, 0.0)
            over_purchased = max(ordered - demand, 0.0)
            completed = approved and issued + precision >= demand
            hanging = (
                request.bts_project_id.state == 'done'
                and waiting_issue >= precision
            )

            if approved:
                approved_line_count += 1
            if completed:
                completed_line_count += 1
            if missing >= precision:
                shortage_line_count += 1
            if waiting_issue >= precision:
                waiting_issue_line_count += 1
            if over_purchased >= precision or hanging:
                mismatch_line_count += 1

            if awaiting_approval:
                status = 'approval'
                status_label = 'Chờ duyệt'
            elif completed:
                status = 'ready'
                status_label = 'Đã cấp đủ'
            elif waiting_issue >= precision:
                status = 'waiting'
                status_label = (
                    'Vật tư còn treo'
                    if hanging
                    else 'Chờ xuất'
                )
            elif missing >= precision:
                status = 'danger'
                status_label = 'Thiếu nhập'
            else:
                status = 'waiting'
                status_label = 'Đang xử lý'

            ratio = (
                min(max(issued / demand, 0.0), 1.0)
                if demand > 0 and approved
                else 0.0
            )
            summary = project_data[request.bts_project_id.id]
            summary['project'] = request.bts_project_id
            summary['ratios'].append(ratio)
            summary['line_count'] += 1
            summary['shortage_count'] += int(missing >= precision)
            summary['waiting_count'] += int(waiting_issue >= precision)

            rows.append({
                'line': line,
                'request': request,
                'project': request.bts_project_id,
                'product': line.product_id,
                'uom': line.product_uom_id,
                'demand': demand,
                'ordered': ordered,
                'received': received,
                'issued': issued,
                'missing': missing,
                'waiting_issue': waiting_issue,
                'over_purchased': over_purchased,
                'hanging': hanging,
                'status': status,
                'status_label': status_label,
            })

        project_summaries = []
        for summary in project_data.values():
            ratios = summary['ratios']
            summary['progress'] = (
                round(sum(ratios) / len(ratios) * 100)
                if ratios
                else 0
            )
            project_summaries.append(summary)
        project_summaries.sort(key=lambda item: (
            item['progress'],
            item['project'].project_code or '',
        ))

        request_status = {
            'approval': len(requests.filtered(
                lambda request: request.state in (
                    'draft',
                    'requested',
                    'postponed',
                )
            )),
            'supply': len(requests.filtered(
                lambda request: request.state in (
                    'approved',
                    'waiting_purchase',
                    'purchasing',
                )
            )),
            'issue': len(requests.filtered(
                lambda request: request.state in (
                    'ready',
                    'partially_delivered',
                )
            )),
            'done': len(requests.filtered(
                lambda request: request.state == 'issued'
            )),
        }
        fulfillment_rate = (
            completed_line_count / approved_line_count * 100
            if approved_line_count
            else 0.0
        )

        row_priority = {
            'danger': 0,
            'waiting': 1,
            'approval': 2,
            'ready': 3,
        }
        rows.sort(key=lambda row: (
            row_priority[row['status']],
            -(row['missing'] + row['waiting_issue']),
            row['project'].project_code or '',
            row['product'].display_name or '',
        ))

        alerts = self._get_supply_alerts(rows)
        return {
            'requests': requests,
            'rows': rows,
            'project_count': len(project_data),
            'project_summaries': project_summaries,
            'approved_line_count': approved_line_count,
            'completed_line_count': completed_line_count,
            'shortage_line_count': shortage_line_count,
            'waiting_issue_line_count': waiting_issue_line_count,
            'mismatch_line_count': mismatch_line_count,
            'fulfillment_rate': fulfillment_rate,
            'request_status': request_status,
            'alerts': alerts,
            'workflow_notifications': (
                self._get_workflow_notifications()
            ),
        }

    def _get_workflow_notifications(self):
        notification_types = []
        if (
            self.env.user.has_group('base.group_system')
            or self.env.user.has_group(
                'dtc_bts_base.group_dtc_bts_pkh'
            )
        ):
            notification_types.extend(('approval', 'lock_po'))
        if (
            self.env.user.has_group('base.group_system')
            or self.env.user.has_group(
                'dtc_bts_base.group_dtc_bts_warehouse'
            )
        ):
            notification_types.append('incoming')
        if not notification_types:
            return self.env['bts.material.notification']
        return self.env['bts.material.notification'].search([
            ('user_id', '=', self.env.user.id),
            ('notification_type', 'in', tuple(notification_types)),
            ('is_seen', '=', False),
        ], order='create_date desc, id desc', limit=20)

    @staticmethod
    def _render_workflow_notifications(data):
        notifications = data['workflow_notifications']
        if not notifications:
            return ''
        titles = {
            'approval': 'Yêu cầu vật tư chờ phê duyệt',
            'incoming': 'Đơn hàng chờ nhập kho',
            'lock_po': 'Yêu cầu hoàn tất chờ khóa PO',
        }
        content = ''.join(
            f"""
                <article class="dtc-supply-alert">
                    <div class="dtc-supply-alert-icon">!</div>
                    <div>
                        <div class="dtc-supply-alert-title">
                            {escape(titles.get(
                                notification.notification_type,
                                'Thông báo công việc',
                            ))}
                        </div>
                        <div class="dtc-supply-alert-description">
                            {escape(notification.message)}
                        </div>
                    </div>
                    <div>
                        <a class="dtc-supply-alert-link"
                           href="/web#id={notification.request_id.id}&amp;model=bts.material.request&amp;view_type=form">
                            Xem yêu cầu
                        </a>
                        <a class="dtc-supply-alert-link"
                           href="/dtc_bts_inventory/notification/{notification.id}/seen">
                            Đã xem
                        </a>
                    </div>
                </article>
            """
            for notification in notifications
        )
        return f"""
            <section class="dtc-supply-panel dtc-supply-alerts">
                <h2 class="dtc-supply-panel-title">
                    Thông báo công việc kho
                </h2>
                <div class="dtc-supply-alert-list">{content}</div>
            </section>
        """

    @staticmethod
    def _get_supply_alerts(rows):
        alerts = []
        for row in rows:
            if len(alerts) >= 10:
                break
            if row['missing'] > 0:
                alerts.append({
                    'priority': 'red',
                    'title': 'Công trình còn thiếu vật tư',
                    'description': (
                        f"{row['project'].project_code or '-'} · "
                        f"{row['product'].display_name}: thiếu "
                        f"{DtcBtsInventoryDashboard._format_quantity(row['missing'])} "
                        f"{row['uom'].display_name}"
                    ),
                    'request': row['request'],
                })
            elif row['hanging']:
                alerts.append({
                    'priority': 'red',
                    'title': 'Dự án hoàn thành còn vật tư treo',
                    'description': (
                        f"{row['project'].project_code or '-'} · "
                        f"{row['product'].display_name}: còn "
                        f"{DtcBtsInventoryDashboard._format_quantity(row['waiting_issue'])} "
                        f"{row['uom'].display_name} chưa xuất"
                    ),
                    'request': row['request'],
                })
            elif row['waiting_issue'] > 0:
                alerts.append({
                    'priority': 'yellow',
                    'title': 'Đã nhập nhưng chưa cấp đủ',
                    'description': (
                        f"{row['project'].project_code or '-'} · "
                        f"{row['product'].display_name}: chờ xuất "
                        f"{DtcBtsInventoryDashboard._format_quantity(row['waiting_issue'])} "
                        f"{row['uom'].display_name}"
                    ),
                    'request': row['request'],
                })
            elif row['over_purchased'] > 0:
                alerts.append({
                    'priority': 'yellow',
                    'title': 'Số mua vượt nhu cầu',
                    'description': (
                        f"{row['project'].project_code or '-'} · "
                        f"{row['product'].display_name}: vượt "
                        f"{DtcBtsInventoryDashboard._format_quantity(row['over_purchased'])} "
                        f"{row['uom'].display_name}"
                    ),
                    'request': row['request'],
                })
        return alerts

    def _render_kpis(self, data):
        kpis = (
            (
                'Dự án có nhu cầu vật tư',
                data['project_count'],
                '',
            ),
            (
                'Tỷ lệ dòng đã cấp đủ',
                f"{data['fulfillment_rate']:.1f}%",
                'green',
            ),
            (
                'Dòng vật tư còn thiếu nhập',
                data['shortage_line_count'],
                'red',
            ),
            (
                'Dòng đã nhập đang chờ xuất',
                data['waiting_issue_line_count'],
                'amber',
            ),
        )
        return '<div class="dtc-supply-kpis">%s</div>' % ''.join(
            f"""
                <div class="dtc-supply-kpi{
                    f' dtc-supply-kpi--{color}' if color else ''
                }">
                    <div class="dtc-supply-kpi-value">{escape(value)}</div>
                    <div class="dtc-supply-kpi-label">{escape(label)}</div>
                </div>
            """
            for label, value, color in kpis
        )

    @staticmethod
    def _render_project_progress(data):
        summaries = data['project_summaries'][:12]
        if not summaries:
            content = (
                '<div class="dtc-supply-empty">'
                'Chưa có yêu cầu vật tư để phân tích.'
                '</div>'
            )
        else:
            content = ''.join(
                f"""
                    <div class="dtc-project-progress-row">
                        <a class="dtc-project-progress-name"
                           href="/web#id={summary['project'].id}&amp;model=project.project&amp;view_type=form"
                           title="{escape(summary['project'].display_name)}">
                            {escape(summary['project'].project_code or summary['project'].display_name)}
                        </a>
                        <div class="dtc-progress-track">
                            <div class="dtc-progress-fill{
                                ' dtc-progress-fill--done'
                                if summary['progress'] >= 100
                                else ' dtc-progress-fill--risk'
                                if summary['shortage_count']
                                else ''
                            }" style="width:{summary['progress']}%"></div>
                        </div>
                        <div class="dtc-project-progress-value">
                            {summary['progress']}%
                        </div>
                    </div>
                """
                for summary in summaries
            )
        return f"""
            <section class="dtc-supply-panel">
                <h2 class="dtc-supply-panel-title">
                    Tiến độ cấp phát theo công trình
                </h2>
                <div class="dtc-project-progress">{content}</div>
            </section>
        """

    @staticmethod
    def _render_request_status(data):
        labels = (
            ('approval', 'Chờ duyệt', 'approval'),
            ('supply', 'Đang mua / chờ nhập', 'supply'),
            ('issue', 'Chờ xuất / cấp một phần', 'issue'),
            ('done', 'Đã cấp đủ', 'done'),
        )
        total = sum(data['request_status'].values())
        segments = ''.join(
            f"""
                <div class="dtc-status-segment dtc-status-segment--{css_class}"
                     style="width:{
                         data['request_status'][key] / total * 100
                         if total else 0
                     }%"></div>
            """
            for key, _label, css_class in labels
            if data['request_status'][key]
        )
        legend = ''.join(
            f"""
                <div class="dtc-status-item">
                    <span class="dtc-status-dot dtc-status-segment--{css_class}"></span>
                    <span>{escape(label)}</span>
                    <span class="dtc-status-count">
                        {data['request_status'][key]}
                    </span>
                </div>
            """
            for key, label, css_class in labels
        )
        return f"""
            <section class="dtc-supply-panel">
                <h2 class="dtc-supply-panel-title">
                    Trạng thái yêu cầu vật tư
                </h2>
                <div class="dtc-status-stack">{segments}</div>
                <div class="dtc-status-legend">{legend}</div>
            </section>
        """

    def _render_supply_table(self, data):
        table_rows = data['rows'][:24]
        if not table_rows:
            body = """
                <tr>
                    <td colspan="11" class="dtc-supply-empty">
                        Chưa có dữ liệu vật tư.
                    </td>
                </tr>
            """
        else:
            body = ''.join(
                f"""
                    <tr>
                        <td>
                            <a href="/web#id={row['project'].id}&amp;model=project.project&amp;view_type=form">
                                {escape(row['project'].project_code or '-')}
                            </a>
                        </td>
                        <td title="{escape(row['product'].display_name)}">
                            {escape(row['product'].display_name)}
                        </td>
                        <td>{escape(row['uom'].display_name)}</td>
                        <td>{self._format_quantity(row['demand'])}</td>
                        <td>{self._format_quantity(row['ordered'])}</td>
                        <td>{self._format_quantity(row['received'])}</td>
                        <td>{self._format_quantity(row['issued'])}</td>
                        <td class="{
                            'dtc-supply-number--danger' if row['missing'] else ''
                        }">{self._format_quantity(row['missing'])}</td>
                        <td class="{
                            'dtc-supply-number--waiting'
                            if row['waiting_issue'] else ''
                        }">{self._format_quantity(row['waiting_issue'])}</td>
                        <td>{self._format_quantity(row['over_purchased'])}</td>
                        <td>
                            <a href="/web#id={row['request'].id}&amp;model=bts.material.request&amp;view_type=form"
                               class="dtc-supply-badge dtc-supply-badge--{row['status']}">
                                {escape(row['status_label'])}
                            </a>
                        </td>
                    </tr>
                """
                for row in table_rows
            )
        return f"""
            <section class="dtc-supply-table-wrap">
                <h2 class="dtc-supply-table-title">
                    Đối chiếu nhu cầu – mua – nhập – xuất theo vật tư
                </h2>
                <table class="dtc-supply-table">
                    <thead>
                        <tr>
                            <th>Dự án</th>
                            <th>Vật tư</th>
                            <th>ĐVT</th>
                            <th>Nhu cầu</th>
                            <th>Đã mua</th>
                            <th>Đã nhập</th>
                            <th>Đã xuất</th>
                            <th>Còn thiếu</th>
                            <th>Chờ xuất</th>
                            <th>Mua vượt</th>
                            <th>Trạng thái</th>
                        </tr>
                    </thead>
                    <tbody>{body}</tbody>
                </table>
            </section>
        """

    @staticmethod
    def _render_supply_alerts(data):
        alerts = data['alerts']
        if not alerts:
            return """
                <section class="dtc-supply-panel dtc-supply-alerts">
                    <h2 class="dtc-supply-panel-title">
                        Cảnh báo lệch chuỗi cung ứng
                    </h2>
                    <div class="dtc-supply-empty">
                        Không có dòng vật tư thiếu, chờ xuất hoặc mua vượt.
                    </div>
                </section>
            """
        content = ''.join(
            f"""
                <article class="dtc-supply-alert{
                    ' dtc-supply-alert--red'
                    if alert['priority'] == 'red' else ''
                }">
                    <div class="dtc-supply-alert-icon">!</div>
                    <div>
                        <div class="dtc-supply-alert-title">
                            {escape(alert['title'])}
                        </div>
                        <div class="dtc-supply-alert-description">
                            {escape(alert['description'])}
                        </div>
                    </div>
                    <a class="dtc-supply-alert-link"
                       href="/web#id={alert['request'].id}&amp;model=bts.material.request&amp;view_type=form">
                        Xem yêu cầu
                    </a>
                </article>
            """
            for alert in alerts
        )
        return f"""
            <section class="dtc-supply-panel dtc-supply-alerts">
                <h2 class="dtc-supply-panel-title">
                    Cảnh báo lệch chuỗi cung ứng
                </h2>
                <div class="dtc-supply-alert-list">{content}</div>
            </section>
        """

    @staticmethod
    def _format_quantity(value):
        if abs(value - round(value)) < 0.00001:
            return f'{int(round(value)):,}'.replace(',', '.')
        return (
            f'{value:,.2f}'
            .replace(',', '_')
            .replace('.', ',')
            .replace('_', '.')
            .rstrip('0')
            .rstrip(',')
        )

    def _search_if_readable(self, model_name, domain):
        model = self._dashboard_model(model_name)
        if model.env.su:
            return model.search(domain)
        if not model.check_access_rights('read', raise_exception=False):
            return model.browse()
        return model.search(domain)

    def _dashboard_model(self, model_name):
        model = self.env[model_name]
        dashboard_groups = (
            self.env.ref(
                'dtc_bts_base.group_dtc_bts_pkh',
                raise_if_not_found=False,
            ),
            self.env.ref(
                'dtc_bts_base.group_dtc_bts_warehouse',
                raise_if_not_found=False,
            ),
            self.env.ref(
                'dtc_bts_base.group_dtc_bts_manager',
                raise_if_not_found=False,
            ),
            self.env.ref(
                'dtc_bts_base.group_bts_enterprise_director',
                raise_if_not_found=False,
            ),
            self.env.ref(
                'dtc_bts_contract.group_dtc_bts_contract_director',
                raise_if_not_found=False,
            ),
        )
        if any(
            group and group in self.env.user.groups_id
            for group in dashboard_groups
        ):
            return model.sudo()
        return model
