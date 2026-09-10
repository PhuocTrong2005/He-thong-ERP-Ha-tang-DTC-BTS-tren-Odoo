from collections import Counter
from datetime import date

from dateutil.relativedelta import relativedelta
from markupsafe import escape

from odoo import fields, models


class BtsMaintenanceDashboardAnalytics(models.Model):
    _inherit = 'bts.maintenance.dashboard'

    def _build_dashboard_html(self):
        data = self._get_maintenance_analytics_data()
        return f"""
            <style>
                .maintenance-analytics,
                .maintenance-analytics * {{
                    box-sizing: border-box;
                    font-family: "Segoe UI", Roboto, Arial, sans-serif;
                }}
                .maintenance-analytics {{
                    --ink: #222936;
                    --muted: #667085;
                    --line: #d9e1e8;
                    --blue: #3f9ee8;
                    padding: 16px;
                    color: var(--ink);
                    background: #f3f6fa;
                }}
                .maintenance-title {{
                    margin: 0 0 4px;
                    color: #0f172a;
                    font-size: 26px;
                    font-weight: 700;
                }}
                .maintenance-subtitle {{
                    margin-bottom: 14px;
                    color: var(--muted);
                    font-size: 13px;
                }}
                .maintenance-top-grid {{
                    display: grid;
                    grid-template-columns: minmax(0, 2fr) minmax(330px, 1fr);
                    gap: 14px;
                }}
                .maintenance-left {{
                    display: grid;
                    gap: 14px;
                    min-width: 0;
                }}
                .maintenance-kpis {{
                    display: grid;
                    grid-template-columns: repeat(3, minmax(0, 1fr));
                    gap: 8px;
                }}
                .maintenance-kpi {{
                    min-height: 126px;
                    padding: 24px;
                    background: #fff;
                    border: 1px solid var(--line);
                    border-top: 4px solid #172554;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(15, 23, 42, .05);
                }}
                .maintenance-kpi-value {{
                    color: #20252d;
                    font-size: 34px;
                    font-variant-numeric: tabular-nums;
                    font-weight: 650;
                    line-height: 1;
                }}
                .maintenance-kpi-label {{
                    margin-top: 11px;
                    color: var(--muted);
                    font-size: 15px;
                }}
                .maintenance-panel {{
                    min-width: 0;
                    padding: 16px;
                    background: #fff;
                    border: 1px solid var(--line);
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(15, 23, 42, .05);
                }}
                .maintenance-panel-title {{
                    margin: 0 0 14px;
                    color: #252a31;
                    font-size: 18px;
                    font-weight: 700;
                    text-align: center;
                }}
                .maintenance-trend {{
                    width: 100%;
                    min-height: 255px;
                }}
                .maintenance-trend svg {{
                    display: block;
                    width: 100%;
                    height: 255px;
                    overflow: visible;
                }}
                .maintenance-trend-grid {{
                    stroke: #e4e8ed;
                    stroke-dasharray: 3 4;
                    stroke-width: 1;
                }}
                .maintenance-trend-axis {{
                    fill: #737d8a;
                    font-size: 11px;
                }}
                .maintenance-trend-line {{
                    fill: none;
                    stroke: #c2414d;
                    stroke-linecap: round;
                    stroke-linejoin: round;
                    stroke-width: 3;
                }}
                .maintenance-trend-point {{
                    fill: #fff;
                    stroke: #c2414d;
                    stroke-width: 2;
                }}
                .maintenance-bars {{
                    display: grid;
                    gap: 11px;
                    padding-top: 7px;
                }}
                .maintenance-bar-row {{
                    display: grid;
                    grid-template-columns: 112px minmax(180px, 1fr) 34px;
                    align-items: center;
                    gap: 9px;
                }}
                .maintenance-bar-label {{
                    overflow: hidden;
                    color: #5e6874;
                    font-size: 12px;
                    text-align: right;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                .maintenance-bar-track {{
                    height: 31px;
                    background:
                        repeating-linear-gradient(
                            to right,
                            #f6f7f9 0,
                            #f6f7f9 calc(25% - 1px),
                            #dfe5eb calc(25% - 1px),
                            #dfe5eb 25%
                        );
                }}
                .maintenance-bar-fill {{
                    height: 100%;
                    min-width: 3px;
                    background: linear-gradient(90deg, #3699e6, #51acf0);
                }}
                .maintenance-bar-value {{
                    color: #374151;
                    font-size: 12px;
                    font-variant-numeric: tabular-nums;
                    font-weight: 700;
                    text-align: right;
                }}
                .maintenance-axis {{
                    display: flex;
                    justify-content: space-between;
                    margin: 10px 43px 0 121px;
                    color: #8a94a1;
                    font-size: 11px;
                }}
                .maintenance-axis-title {{
                    margin-top: 5px;
                    color: #59636f;
                    font-size: 12px;
                    text-align: center;
                }}
                .maintenance-items {{
                    margin-top: 14px;
                }}
                .maintenance-item-bars {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    align-items: end;
                    gap: 18px;
                    min-height: 280px;
                    padding: 18px 25px 0;
                    border-bottom: 1px solid #cfd6de;
                    background:
                        repeating-linear-gradient(
                            to top,
                            transparent 0,
                            transparent calc(25% - 1px),
                            #e4e8ed calc(25% - 1px),
                            #e4e8ed 25%
                        );
                }}
                .maintenance-item-column {{
                    display: grid;
                    grid-template-rows: 225px minmax(44px, auto);
                    align-items: end;
                    gap: 8px;
                    height: 100%;
                }}
                .maintenance-item-plot {{
                    display: flex;
                    height: 225px;
                    align-items: flex-end;
                    justify-content: center;
                }}
                .maintenance-item-bar {{
                    position: relative;
                    width: min(88%, 180px);
                    min-height: 3px;
                    background: linear-gradient(180deg, #717bc8, #616dbf);
                    border-radius: 3px 3px 0 0;
                }}
                .maintenance-item-value {{
                    position: absolute;
                    top: -22px;
                    left: 50%;
                    color: #4b5563;
                    font-size: 12px;
                    font-weight: 700;
                    transform: translateX(-50%);
                }}
                .maintenance-item-label {{
                    overflow: hidden;
                    color: #56606c;
                    font-size: 11px;
                    line-height: 1.25;
                    text-align: center;
                    text-overflow: ellipsis;
                }}
                .maintenance-empty {{
                    padding: 36px 14px;
                    color: #94a3b8;
                    font-size: 13px;
                    font-style: italic;
                    text-align: center;
                }}
                .maintenance-notification-panel {{
                    margin-top: 14px;
                }}
                .maintenance-notifications {{
                    display: grid;
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                    gap: 8px;
                }}
                .maintenance-notification {{
                    display: grid;
                    grid-template-columns: 25px minmax(0, 1fr) auto;
                    align-items: center;
                    gap: 9px;
                    padding: 9px 11px;
                    border: 1px solid var(--line);
                    border-left: 4px solid #9ca3af;
                    border-radius: 5px;
                }}
                .maintenance-notification--red {{
                    border-left-color: #dc2626;
                }}
                .maintenance-notification--yellow {{
                    border-left-color: #d97706;
                }}
                .maintenance-notification-icon {{
                    display: grid;
                    width: 22px;
                    height: 22px;
                    place-items: center;
                    color: #fff;
                    background: #64748b;
                    border-radius: 50%;
                    font-size: 12px;
                    font-weight: 700;
                }}
                .maintenance-notification--red
                .maintenance-notification-icon {{
                    background: #dc2626;
                }}
                .maintenance-notification--yellow
                .maintenance-notification-icon {{
                    background: #d97706;
                }}
                .maintenance-notification-title {{
                    color: #1f2937;
                    font-size: 12px;
                    font-weight: 700;
                }}
                .maintenance-notification-description,
                .maintenance-notification-date {{
                    color: #6b7280;
                    font-size: 11px;
                }}
                .maintenance-notification-link {{
                    padding: 4px 7px;
                    color: #0f766e;
                    border: 1px solid #99d5cc;
                    border-radius: 4px;
                    font-size: 11px;
                    text-decoration: none;
                    white-space: nowrap;
                }}
                @media (max-width: 1050px) {{
                    .maintenance-top-grid {{
                        grid-template-columns: 1fr;
                    }}
                }}
                @media (max-width: 720px) {{
                    .maintenance-analytics {{ padding: 10px; }}
                    .maintenance-kpis {{ grid-template-columns: 1fr; }}
                    .maintenance-kpi {{ min-height: 96px; }}
                    .maintenance-notifications {{
                        grid-template-columns: 1fr;
                    }}
                    .maintenance-item-bars {{
                        overflow-x: auto;
                        grid-template-columns: repeat(5, minmax(120px, 1fr));
                    }}
                }}
            </style>
            <div class="maintenance-analytics">
                <h1 class="maintenance-title">Phân tích hư hỏng và bảo trì BTS</h1>
                <div class="maintenance-subtitle">
                    Dữ liệu cập nhật trực tiếp từ phiếu bảo trì và checklist Odoo
                </div>
                <div class="maintenance-top-grid">
                    <div class="maintenance-left">
                        <div class="maintenance-kpis">
                            {self._render_analytics_kpi(
                                'Tổng vụ hư hỏng',
                                data['total_failures'],
                            )}
                            {self._render_analytics_kpi(
                                'Chi phí sửa dự kiến',
                                self._format_compact_cost(data['estimated_cost']),
                            )}
                            {self._render_analytics_kpi(
                                'Tỷ lệ phiếu có hư hỏng',
                                f"{data['failure_rate']:.2f}%",
                            )}
                        </div>
                        {self._render_failure_trend(data)}
                    </div>
                    {self._render_ranked_bars(
                        'Các tỉnh hay hư hỏng nhất',
                        data['province_counts'],
                        'Số vụ hư hỏng',
                    )}
                </div>
                {self._render_failure_items(data)}
                {self._render_maintenance_notification_feed(data)}
            </div>
        """

    def _get_maintenance_analytics_data(self):
        result_model = self.env[
            'bts.maintenance.checklist.result'
        ].sudo()
        request_model = self.env['maintenance.request'].sudo()
        proposal_model = self.env['bts.repair.proposal'].sudo()
        failure_results = result_model.search([
            ('result_state', 'in', (
                'need_repair',
                'need_replacement',
            )),
        ])
        inspected_requests = request_model.search([
            ('checklist_result_ids', '!=', False),
        ])
        failed_request_ids = set(failure_results.mapped('request_id').ids)
        failure_rate = (
            len(failed_request_ids) / len(inspected_requests) * 100
            if inspected_requests
            else 0.0
        )

        proposals = proposal_model.search([
            ('state', '!=', 'cancelled'),
        ])
        estimated_cost = sum(
            proposal.estimated_cost
            or sum(proposal.proposal_line_ids.mapped('estimated_cost'))
            for proposal in proposals
        )

        trend_counts = Counter()
        province_counts = Counter()
        item_counts = Counter()
        for result in failure_results:
            request = result.request_id
            failure_date = self._get_failure_date(request)
            if failure_date:
                trend_counts[(failure_date.year, failure_date.month)] += 1
            province = (
                request.bts_project_id.province
                or 'Chưa cập nhật'
            )
            province_counts[province] += 1
            item_counts[
                result.item_id.display_name or 'Chưa xác định'
            ] += 1

        today = fields.Date.context_today(self)
        month_start = date(today.year, today.month, 1)
        months = [
            month_start - relativedelta(months=offset)
            for offset in reversed(range(12))
        ]
        trend = [
            {
                'date': month,
                'label': f'T{month.month}/{str(month.year)[2:]}',
                'value': trend_counts[(month.year, month.month)],
            }
            for month in months
        ]
        dashboard_data = self._get_dashboard_data()
        return {
            'total_failures': len(failure_results),
            'estimated_cost': estimated_cost,
            'failure_rate': failure_rate,
            'trend': trend,
            'province_counts': province_counts,
            'item_counts': item_counts,
            'notifications': dashboard_data['notifications'],
        }

    @staticmethod
    def _get_failure_date(request):
        value = (
            request.actual_date
            or request.maintenance_batch_id.maintenance_date
            or request.request_date
        )
        return fields.Date.to_date(value) if value else None

    @staticmethod
    def _format_compact_cost(value):
        if value >= 1_000_000_000:
            return f'{value / 1_000_000_000:.2f} tỷ'
        if value >= 1_000_000:
            return f'{value / 1_000_000:.2f} tr'
        return f'{value:,.0f}'

    @staticmethod
    def _render_analytics_kpi(label, value):
        return f"""
            <article class="maintenance-kpi">
                <div class="maintenance-kpi-value">{escape(value)}</div>
                <div class="maintenance-kpi-label">{escape(label)}</div>
            </article>
        """

    def _render_failure_trend(self, data):
        trend = data['trend']
        chart_width = 900
        chart_height = 220
        left = 38
        right = 18
        top = 16
        bottom = 34
        plot_width = chart_width - left - right
        plot_height = chart_height - top - bottom
        largest = max(
            (point['value'] for point in trend),
            default=0,
        ) or 1
        coordinates = []
        labels = []
        circles = []
        count = len(trend)
        for index, point in enumerate(trend):
            x = (
                left + index * plot_width / (count - 1)
                if count > 1
                else left + plot_width / 2
            )
            y = top + plot_height - point['value'] / largest * plot_height
            coordinates.append(f'{x:.1f},{y:.1f}')
            labels.append(f"""
                <text
                    class="maintenance-trend-axis"
                    x="{x:.1f}"
                    y="{chart_height - 9}"
                    text-anchor="middle">
                    {escape(point['label'])}
                </text>
            """)
            circles.append(f"""
                <circle
                    class="maintenance-trend-point"
                    cx="{x:.1f}"
                    cy="{y:.1f}"
                    r="3">
                    <title>{point['value']} vụ</title>
                </circle>
            """)
        grid_lines = []
        for index in range(5):
            y = top + index * plot_height / 4
            value = round(largest * (4 - index) / 4)
            grid_lines.append(f"""
                <line
                    class="maintenance-trend-grid"
                    x1="{left}"
                    y1="{y:.1f}"
                    x2="{chart_width - right}"
                    y2="{y:.1f}">
                </line>
                <text
                    class="maintenance-trend-axis"
                    x="{left - 7}"
                    y="{y + 4:.1f}"
                    text-anchor="end">
                    {value}
                </text>
            """)
        return f"""
            <section class="maintenance-panel">
                <h2 class="maintenance-panel-title">
                    Xu hướng hư hỏng theo tháng
                </h2>
                <div class="maintenance-trend">
                    <svg
                        viewBox="0 0 {chart_width} {chart_height}"
                        role="img"
                        aria-label="Xu hướng số vụ hư hỏng trong 12 tháng">
                        {''.join(grid_lines)}
                        <polyline
                            class="maintenance-trend-line"
                            points="{' '.join(coordinates)}">
                        </polyline>
                        {''.join(circles)}
                        {''.join(labels)}
                    </svg>
                </div>
            </section>
        """

    @staticmethod
    def _render_ranked_bars(title, counts, axis_title):
        values = sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[:10]
        largest = max((count for _label, count in values), default=0)
        if not values:
            content = """
                <div class="maintenance-empty">
                    Chưa có dữ liệu hư hỏng theo tỉnh/thành.
                </div>
            """
        else:
            rows = []
            for label, count in values:
                width = round(count / largest * 100, 2) if largest else 0
                rows.append(f"""
                    <div class="maintenance-bar-row" title="{escape(label)}">
                        <div class="maintenance-bar-label">{escape(label)}</div>
                        <div class="maintenance-bar-track">
                            <div
                                class="maintenance-bar-fill"
                                style="width:{width}%">
                            </div>
                        </div>
                        <div class="maintenance-bar-value">{count}</div>
                    </div>
                """)
            content = (
                '<div class="maintenance-bars">'
                + ''.join(rows)
                + '</div>'
                + f"""
                    <div class="maintenance-axis">
                        <span>0</span>
                        <span>{largest}</span>
                    </div>
                    <div class="maintenance-axis-title">
                        {escape(axis_title)}
                    </div>
                """
            )
        return f"""
            <section class="maintenance-panel">
                <h2 class="maintenance-panel-title">{escape(title)}</h2>
                {content}
            </section>
        """

    def _render_failure_items(self, data):
        values = sorted(
            data['item_counts'].items(),
            key=lambda item: (-item[1], item[0]),
        )[:8]
        largest = max((count for _label, count in values), default=0)
        if not values:
            content = """
                <div class="maintenance-empty">
                    Chưa có hạng mục checklist ghi nhận hư hỏng.
                </div>
            """
        else:
            columns = []
            for label, count in values:
                height = round(count / largest * 100, 2) if largest else 0
                columns.append(f"""
                    <div class="maintenance-item-column" title="{escape(label)}">
                        <div class="maintenance-item-plot">
                            <div
                                class="maintenance-item-bar"
                                style="height:{height}%">
                                <span class="maintenance-item-value">{count}</span>
                            </div>
                        </div>
                        <div class="maintenance-item-label">
                            {escape(label)}
                        </div>
                    </div>
                """)
            content = (
                '<div class="maintenance-item-bars">'
                + ''.join(columns)
                + '</div>'
                + """
                    <div class="maintenance-axis-title">
                        Hạng mục checklist
                    </div>
                """
            )
        return f"""
            <section class="maintenance-panel maintenance-items">
                <h2 class="maintenance-panel-title">
                    Hạng mục hay hư hỏng nhất
                </h2>
                {content}
            </section>
        """

    def _render_maintenance_notification_feed(self, data):
        notifications = data['notifications'][:8]
        if not notifications:
            return ''
        items = ''.join(
            self._render_analytics_notification(notification)
            for notification in notifications
        )
        return f"""
            <section class="maintenance-panel maintenance-notification-panel">
                <h2 class="maintenance-panel-title">
                    Cảnh báo và công việc bảo trì
                </h2>
                <div class="maintenance-notifications">{items}</div>
            </section>
        """

    @staticmethod
    def _render_analytics_notification(notification):
        href = ''
        if notification.get('model') and notification.get('res_id'):
            href = (
                f"/web#id={notification['res_id']}"
                f"&model={notification['model']}&view_type=form"
            )
            if notification.get('view_id'):
                href += f"&view_id={notification['view_id']}"
        link_html = (
            f'<a class="maintenance-notification-link" '
            f'href="{href}" target="_self">Mở chi tiết</a>'
            if href
            else ''
        )
        priority = notification.get('priority', 'gray')
        return f"""
            <article
                class="maintenance-notification
                       maintenance-notification--{priority}">
                <div class="maintenance-notification-icon">
                    {escape(notification.get('icon', '!'))}
                </div>
                <div>
                    <div class="maintenance-notification-title">
                        {escape(notification.get('title', 'Thông báo'))}
                    </div>
                    <div class="maintenance-notification-description">
                        {escape(notification.get('description', ''))}
                    </div>
                    <div class="maintenance-notification-date">
                        {escape(notification.get('date', ''))}
                    </div>
                </div>
                {link_html}
            </article>
        """
