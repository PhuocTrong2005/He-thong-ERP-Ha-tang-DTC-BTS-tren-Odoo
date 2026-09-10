from collections import defaultdict

from markupsafe import escape

from odoo import fields, models


class DtcBtsDashboard(models.Model):
    _name = 'dtc.bts.dashboard'
    _description = 'Bảng tổng hợp dự án BTS'

    name = fields.Char(string='Tên bảng tổng hợp', required=True)
    dashboard_html = fields.Html(
        string='Bảng tổng hợp',
        compute='_compute_dashboard_html',
        sanitize=False,
    )

    def _compute_dashboard_html(self):
        for dashboard in self:
            dashboard.dashboard_html = dashboard._build_dashboard_html()

    def _build_dashboard_html(self):
        projects = self.env['project.project'].search(
            [('project_code', '!=', False)],
            order='project_code, name',
        )
        tasks = self.env['project.task'].search([
            ('station_code', '!=', False),
            ('project_id', 'in', projects.ids),
        ])
        today = fields.Date.context_today(self)
        delay_by_project = {
            project.id: self._get_project_delay_days(project, today)
            for project in projects
        }
        measured_delays = [
            delay
            for delay in delay_by_project.values()
            if delay is not None
        ]
        average_delay = (
            round(sum(measured_delays) / len(measured_delays))
            if measured_delays
            else None
        )

        status_chart_html = self._render_status_chart(projects)
        bucket_by_project = {
            project.id: self._get_progress_bucket(
                project,
                delay_by_project[project.id],
                today,
            )
            for project in projects
        }
        late_delays = [
            delay_by_project[project.id]
            for project in projects
            if bucket_by_project[project.id] == 'late'
        ]
        average_late = (
            round(sum(late_delays) / len(late_delays))
            if late_delays
            else 0
        )
        completed_measured = projects.filtered(
            lambda project: (
                project.state == 'done'
                and project.acceptance_date
                and project.planned_end_date
            )
        )
        completed_on_time = completed_measured.filtered(
            lambda project: delay_by_project[project.id] <= 0
        )
        on_time_rate = (
            round(len(completed_on_time) / len(completed_measured) * 100, 1)
            if completed_measured
            else 0
        )
        bucket_counts = {
            bucket: sum(
                bucket_by_project[project.id] == bucket
                for project in projects
            )
            for bucket in ('on_time', 'risk', 'late', 'missing')
        }
        intervention_html = self._render_intervention_table(
            projects,
            delay_by_project,
            bucket_by_project,
            today,
        )
        region_html = self._render_region_analysis(
            projects,
            delay_by_project,
            bucket_by_project,
        )
        manager_html = self._render_manager_analysis(
            projects,
            delay_by_project,
            bucket_by_project,
        )
        monthly_html = self._render_monthly_completion_trend(
            projects,
            delay_by_project,
        )
        province_chart_html = self._render_delay_bar_chart(
            title='Chênh lệch tiến độ trung bình theo khu vực',
            values=self._average_delays_by(
                projects,
                delay_by_project,
                lambda project: project.province or 'Chưa cập nhật',
            ),
            empty_label='Chưa có khu vực nào có dữ liệu tiến độ.',
        )
        notification_section_html = self._render_notification_section()
        return f"""
            <style>
                .dtc-analytics,
                .dtc-analytics * {{
                    box-sizing: border-box;
                    font-family: "Segoe UI", Roboto, Arial, sans-serif;
                }}
                .dtc-analytics {{
                    --navy: #172554;
                    --blue: #168de2;
                    --blue-dark: #1e40af;
                    --green: #22c55e;
                    --ink: #172033;
                    --muted: #667085;
                    --line: #dbe3ec;
                    padding: 18px;
                    color: var(--ink);
                    background: #f3f6fa;
                }}
                .dtc-analytics-header {{
                    display: flex;
                    align-items: flex-end;
                    justify-content: space-between;
                    gap: 16px;
                    margin-bottom: 14px;
                }}
                .dtc-analytics-title {{
                    margin: 0;
                    color: #0f172a;
                    font-size: 26px;
                    font-weight: 700;
                }}
                .dtc-analytics-subtitle {{
                    margin-top: 4px;
                    color: var(--muted);
                    font-size: 13px;
                }}
                .dtc-dashboard-grid {{
                    display: grid;
                    grid-template-columns: minmax(0, 2fr) minmax(320px, 1fr);
                    gap: 14px;
                }}
                .dtc-dashboard-left {{
                    display: grid;
                    gap: 14px;
                    min-width: 0;
                }}
                .dtc-kpis {{
                    display: grid;
                    grid-template-columns: repeat(6, minmax(0, 1fr));
                    gap: 8px;
                }}
                .dtc-kpi {{
                    min-height: 106px;
                    padding: 18px 16px;
                    background: #fff;
                    border: 1px solid var(--line);
                    border-top: 4px solid var(--navy);
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(15, 23, 42, .06);
                }}
                .dtc-kpi-value {{
                    color: #1f2937;
                    font-size: 34px;
                    font-weight: 650;
                    line-height: 1;
                }}
                .dtc-kpi-label {{
                    margin-top: 10px;
                    color: var(--muted);
                    font-size: 15px;
                }}
                .dtc-kpi--green {{ border-top-color: #16a34a; }}
                .dtc-kpi--yellow {{ border-top-color: #f59e0b; }}
                .dtc-kpi--red {{ border-top-color: #dc2626; }}
                .dtc-kpi--gray {{ border-top-color: #64748b; }}
                .dtc-panel {{
                    min-width: 0;
                    padding: 16px;
                    background: #fff;
                    border: 1px solid var(--line);
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(15, 23, 42, .05);
                }}
                .dtc-panel-title {{
                    margin: 0 0 14px;
                    color: #20232a;
                    font-size: 18px;
                    font-weight: 700;
                    text-align: center;
                }}
                .dtc-delay-table-wrap {{
                    overflow-x: auto;
                }}
                .dtc-delay-table {{
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 14px;
                }}
                .dtc-delay-table th {{
                    padding: 8px 10px;
                    border-bottom: 2px solid #8cc9dd;
                    color: #20232a;
                    font-weight: 700;
                    text-align: left;
                    white-space: nowrap;
                }}
                .dtc-delay-table td {{
                    padding: 7px 10px;
                    border-bottom: 1px solid #edf1f5;
                }}
                .dtc-delay-table tbody tr:nth-child(even) {{
                    background: #f3f4f6;
                }}
                .dtc-delay-table a {{
                    color: #1f4b7a;
                    font-weight: 600;
                    text-decoration: none;
                }}
                .dtc-delay-table a:hover {{
                    color: #0b72b9;
                    text-decoration: underline;
                }}
                .dtc-number {{
                    font-variant-numeric: tabular-nums;
                    text-align: right !important;
                }}
                .dtc-delay-positive {{
                    color: #be123c;
                    font-weight: 700;
                }}
                .dtc-delay-negative {{
                    color: #15803d;
                    font-weight: 700;
                }}
                .dtc-delay-summary td {{
                    border-top: 2px solid #8cc9dd;
                    border-bottom: 0;
                    background: #fff;
                    font-weight: 700;
                }}
                .dtc-progress-stack {{
                    display: flex;
                    width: 100%;
                    min-width: 150px;
                    height: 14px;
                    overflow: hidden;
                    background: #e5e7eb;
                    border-radius: 999px;
                }}
                .dtc-progress-stack span {{ min-width: 2px; }}
                .dtc-progress-on-time {{ background: #16a34a; }}
                .dtc-progress-risk {{ background: #f59e0b; }}
                .dtc-progress-late {{ background: #dc2626; }}
                .dtc-progress-missing {{ background: #94a3b8; }}
                .dtc-badge {{
                    display: inline-block;
                    padding: 3px 8px;
                    border-radius: 999px;
                    font-size: 11px;
                    font-weight: 700;
                    white-space: nowrap;
                }}
                .dtc-badge--green {{ color: #166534; background: #dcfce7; }}
                .dtc-badge--yellow {{ color: #92400e; background: #fef3c7; }}
                .dtc-badge--red {{ color: #991b1b; background: #fee2e2; }}
                .dtc-badge--gray {{ color: #475569; background: #e2e8f0; }}
                .dtc-score {{
                    display: inline-grid;
                    width: 38px;
                    height: 38px;
                    place-items: center;
                    border-radius: 50%;
                    color: #fff;
                    background: #2563eb;
                    font-weight: 750;
                }}
                .dtc-month-chart {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(58px, 1fr));
                    align-items: end;
                    gap: 8px;
                    min-height: 190px;
                }}
                .dtc-month-col {{
                    display: grid;
                    grid-template-rows: 145px auto;
                    gap: 7px;
                    text-align: center;
                }}
                .dtc-month-bars {{
                    display: flex;
                    align-items: flex-end;
                    justify-content: center;
                    gap: 3px;
                    border-bottom: 1px solid #cbd5e1;
                }}
                .dtc-month-bar {{
                    width: 17px;
                    min-height: 2px;
                    border-radius: 3px 3px 0 0;
                }}
                .dtc-month-label {{ color: #64748b; font-size: 10px; }}
                .dtc-inline-legend {{
                    display: flex;
                    justify-content: center;
                    gap: 16px;
                    margin-top: 10px;
                    color: #64748b;
                    font-size: 11px;
                }}
                .dtc-donut-layout {{
                    display: grid;
                    grid-template-columns: minmax(190px, 1fr) minmax(140px, auto);
                    align-items: center;
                    gap: 20px;
                    min-height: 270px;
                }}
                .dtc-donut {{
                    position: relative;
                    width: min(230px, 100%);
                    aspect-ratio: 1;
                    margin: auto;
                    border-radius: 50%;
                }}
                .dtc-donut::after {{
                    position: absolute;
                    inset: 27%;
                    display: grid;
                    place-items: center;
                    color: #334155;
                    background: #fff;
                    border-radius: 50%;
                    content: attr(data-total) "\\A dự án";
                    font-size: 18px;
                    font-weight: 700;
                    line-height: 1.25;
                    text-align: center;
                    white-space: pre;
                }}
                .dtc-legend {{
                    display: grid;
                    gap: 9px;
                }}
                .dtc-legend-row {{
                    display: grid;
                    grid-template-columns: 10px minmax(0, 1fr) auto;
                    align-items: center;
                    gap: 7px;
                    color: #475569;
                    font-size: 13px;
                }}
                .dtc-legend-dot {{
                    width: 9px;
                    height: 9px;
                    border-radius: 50%;
                }}
                .dtc-legend-value {{
                    color: #1f2937;
                    font-variant-numeric: tabular-nums;
                    font-weight: 650;
                }}
                .dtc-charts-grid {{
                    display: grid;
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                    gap: 14px;
                    margin-top: 14px;
                }}
                .dtc-bar-chart {{
                    display: grid;
                    gap: 8px;
                }}
                .dtc-bar-row {{
                    display: grid;
                    grid-template-columns: minmax(95px, 145px) minmax(200px, 1fr) 42px;
                    align-items: center;
                    gap: 9px;
                    min-height: 25px;
                }}
                .dtc-bar-label {{
                    overflow: hidden;
                    color: #4b5563;
                    font-size: 12px;
                    text-align: right;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                .dtc-bar-plot {{
                    position: relative;
                    height: 22px;
                    background:
                        linear-gradient(
                            to right,
                            transparent 49.8%,
                            #9ca3af 49.8%,
                            #9ca3af 50.2%,
                            transparent 50.2%
                        ),
                        repeating-linear-gradient(
                            to right,
                            transparent 0,
                            transparent calc(25% - 1px),
                            #eef2f7 calc(25% - 1px),
                            #eef2f7 25%
                        );
                }}
                .dtc-bar {{
                    position: absolute;
                    top: 2px;
                    height: 18px;
                    min-width: 2px;
                    border-radius: 2px;
                }}
                .dtc-bar--positive {{
                    left: 50%;
                    background: linear-gradient(90deg, #dc2626, #f87171);
                }}
                .dtc-bar--negative {{
                    right: 50%;
                    background: linear-gradient(90deg, #1d9f52, #36d879);
                }}
                .dtc-bar-value {{
                    color: #374151;
                    font-size: 12px;
                    font-variant-numeric: tabular-nums;
                    font-weight: 650;
                    text-align: right;
                }}
                .dtc-chart-axis {{
                    display: flex;
                    justify-content: space-between;
                    margin: 8px 51px 0 154px;
                    color: #94a3b8;
                    font-size: 11px;
                }}
                .dtc-empty {{
                    padding: 28px 12px;
                    color: #94a3b8;
                    font-style: italic;
                    text-align: center;
                }}
                .dtc-notifications {{
                    display: grid;
                    gap: 8px;
                }}
                .dtc-notification {{
                    display: grid;
                    grid-template-columns: 28px minmax(0, 1fr) auto;
                    align-items: center;
                    gap: 12px;
                    padding: 11px 13px;
                    border: 1px solid var(--line);
                    border-left: 4px solid #64748b;
                    border-radius: 5px;
                }}
                .dtc-notification--green {{ border-left-color: #059669; }}
                .dtc-notification--yellow {{ border-left-color: #d97706; }}
                .dtc-notification--red {{ border-left-color: #dc2626; }}
                .dtc-notification-icon {{
                    display: grid;
                    width: 24px;
                    height: 24px;
                    place-items: center;
                    color: #fff;
                    background: #64748b;
                    border-radius: 50%;
                    font-weight: 700;
                }}
                .dtc-notification--green .dtc-notification-icon {{ background: #059669; }}
                .dtc-notification--yellow .dtc-notification-icon {{ background: #d97706; }}
                .dtc-notification--red .dtc-notification-icon {{ background: #dc2626; }}
                .dtc-notification-title {{
                    color: #0f172a;
                    font-size: 13px;
                    font-weight: 700;
                }}
                .dtc-notification-description {{
                    margin-top: 2px;
                    color: var(--muted);
                    font-size: 12px;
                }}
                .dtc-notification-actions {{
                    display: flex;
                    gap: 6px;
                }}
                .dtc-notification-link {{
                    padding: 5px 8px;
                    color: #1d4ed8;
                    border: 1px solid #bfdbfe;
                    border-radius: 4px;
                    font-size: 12px;
                    text-decoration: none;
                    white-space: nowrap;
                }}
                @media (max-width: 1050px) {{
                    .dtc-dashboard-grid,
                    .dtc-charts-grid {{
                        grid-template-columns: 1fr;
                    }}
                    .dtc-kpis {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
                }}
                @media (max-width: 700px) {{
                    .dtc-analytics {{ padding: 10px; }}
                    .dtc-kpis {{ grid-template-columns: 1fr; }}
                    .dtc-kpi {{ min-height: 95px; }}
                    .dtc-donut-layout {{ grid-template-columns: 1fr; }}
                    .dtc-bar-row {{
                        grid-template-columns: minmax(80px, 105px) minmax(150px, 1fr) 38px;
                    }}
                    .dtc-chart-axis {{ margin-left: 114px; }}
                    .dtc-notification {{
                        grid-template-columns: 28px minmax(0, 1fr);
                    }}
                    .dtc-notification-actions {{ grid-column: 2; }}
                }}
            </style>
            <div class="dtc-analytics">
                <header class="dtc-analytics-header">
                    <div>
                        <h1 class="dtc-analytics-title">Phân tích tiến độ dự án BTS</h1>
                        <div class="dtc-analytics-subtitle">
                            Dữ liệu cập nhật trực tiếp từ hệ thống Odoo
                        </div>
                    </div>
                </header>
                <div class="dtc-dashboard-grid">
                    <div class="dtc-dashboard-left">
                        <div class="dtc-kpis">
                            {self._render_kpi('Tổng dự án', len(projects))}
                            {self._render_kpi('Sớm/đúng tiến độ', bucket_counts['on_time'], 'green')}
                            {self._render_kpi('Nguy cơ ≤ 30 ngày', bucket_counts['risk'], 'yellow')}
                            {self._render_kpi('Đã chậm', bucket_counts['late'], 'red')}
                            {self._render_kpi('Chậm TB (dự án chậm)', average_late, 'red')}
                            {self._render_kpi('Hoàn thành đúng hạn', f'{on_time_rate:g}%', 'green')}
                        </div>
                        {intervention_html}
                    </div>
                    {status_chart_html}
                </div>
                <div class="dtc-charts-grid">
                    {monthly_html}
                    {province_chart_html}
                </div>
                {region_html}
                {manager_html}
                {notification_section_html}
            </div>
        """

    @staticmethod
    def _get_project_delay_days(project, today):
        if not project.planned_end_date or project.state == 'cancelled':
            return None
        actual_date = (
            project.acceptance_date
            if project.state == 'done' and project.acceptance_date
            else today
        )
        return (actual_date - project.planned_end_date).days

    @staticmethod
    def _get_progress_bucket(project, delay, today):
        if project.state == 'cancelled':
            return 'missing'
        if not project.planned_end_date:
            return 'missing'
        if project.state == 'done':
            if not project.acceptance_date:
                return 'missing'
            return 'late' if delay > 0 else 'on_time'
        if delay > 0:
            return 'late'
        if 0 <= (project.planned_end_date - today).days <= 30:
            return 'risk'
        return 'on_time'

    @staticmethod
    def _render_kpi(label, value, tone='navy'):
        tone_class = (
            f' dtc-kpi--{tone}'
            if tone in ('green', 'yellow', 'red', 'gray')
            else ''
        )
        return f"""
            <article class="dtc-kpi{tone_class}">
                <div class="dtc-kpi-value">{escape(value)}</div>
                <div class="dtc-kpi-label">{escape(label)}</div>
            </article>
        """

    @staticmethod
    def _portfolio_metrics(
        projects,
        delay_by_project,
        bucket_by_project,
        key_getter,
    ):
        grouped = defaultdict(list)
        for project in projects:
            grouped[key_getter(project)].append(project)
        metrics = []
        for label, records in grouped.items():
            counts = {
                bucket: sum(
                    bucket_by_project[project.id] == bucket
                    for project in records
                )
                for bucket in ('on_time', 'risk', 'late', 'missing')
            }
            late_delays = [
                delay_by_project[project.id]
                for project in records
                if bucket_by_project[project.id] == 'late'
            ]
            total = len(records)
            metrics.append({
                'label': label,
                'total': total,
                **counts,
                'late_rate': round(counts['late'] / total * 100, 1)
                if total else 0,
                'average_late': round(
                    sum(late_delays) / len(late_delays),
                    1,
                ) if late_delays else 0,
                'max_late': max(late_delays) if late_delays else 0,
                'records': records,
            })
        return sorted(
            metrics,
            key=lambda item: (
                item['late_rate'],
                item['average_late'],
                item['total'],
            ),
            reverse=True,
        )

    @staticmethod
    def _render_progress_stack(item):
        total = item['total'] or 1
        segments = []
        for bucket in ('on_time', 'risk', 'late', 'missing'):
            count = item[bucket]
            if count:
                segments.append(
                    '<span class="dtc-progress-%s" style="width:%.2f%%" '
                    'title="%s: %s"></span>'
                    % (
                        bucket.replace('_', '-'),
                        count / total * 100,
                        {
                            'on_time': 'Đúng tiến độ',
                            'risk': 'Nguy cơ',
                            'late': 'Đã chậm',
                            'missing': 'Thiếu dữ liệu',
                        }[bucket],
                        count,
                    )
                )
        return (
            '<div class="dtc-progress-stack">%s</div>'
            % ''.join(segments)
        )

    def _render_region_analysis(
        self,
        projects,
        delay_by_project,
        bucket_by_project,
    ):
        metrics = self._portfolio_metrics(
            projects,
            delay_by_project,
            bucket_by_project,
            lambda project: project.province or 'Chưa cập nhật',
        )
        rows = []
        for item in metrics:
            rows.append(f"""
                <tr>
                    <td><strong>{escape(item['label'])}</strong></td>
                    <td class="dtc-number">{item['total']}</td>
                    <td>{self._render_progress_stack(item)}</td>
                    <td class="dtc-number dtc-delay-positive">{item['late']}</td>
                    <td class="dtc-number">{item['late_rate']:g}%</td>
                    <td class="dtc-number">{item['average_late']:g}</td>
                    <td class="dtc-number">{item['max_late']:g}</td>
                </tr>
            """)
        return f"""
            <section class="dtc-panel" style="margin-top:14px">
                <h2 class="dtc-panel-title">Phân tích hiệu quả tiến độ theo khu vực</h2>
                <div class="dtc-delay-table-wrap">
                    <table class="dtc-delay-table dtc-region-analysis">
                        <thead><tr>
                            <th>Tỉnh/Thành</th>
                            <th class="dtc-number">Dự án</th>
                            <th>Cơ cấu tiến độ</th>
                            <th class="dtc-number">Đã chậm</th>
                            <th class="dtc-number">Tỷ lệ chậm</th>
                            <th class="dtc-number">Chậm TB</th>
                            <th class="dtc-number">Chậm nhất</th>
                        </tr></thead>
                        <tbody>{''.join(rows)}</tbody>
                    </table>
                </div>
            </section>
        """

    def _render_manager_analysis(
        self,
        projects,
        delay_by_project,
        bucket_by_project,
    ):
        metrics = self._portfolio_metrics(
            projects,
            delay_by_project,
            bucket_by_project,
            lambda project: (
                project.project_manager_id.display_name or 'Chưa phân công'
            ),
        )
        rows = []
        for item in metrics:
            completed = [
                project
                for project in item['records']
                if (
                    project.state == 'done'
                    and project.acceptance_date
                    and project.planned_end_date
                )
            ]
            completed_on_time = sum(
                delay_by_project[project.id] <= 0
                for project in completed
            )
            completion_rate = (
                completed_on_time / len(completed) * 100
                if completed else 0
            )
            completeness = (
                (item['total'] - item['missing']) / item['total'] * 100
                if item['total'] else 0
            )
            non_late_rate = 100 - item['late_rate']
            score = round(
                non_late_rate * .45
                + completion_rate * .35
                + completeness * .20
            )
            rows.append(f"""
                <tr>
                    <td><strong>{escape(item['label'])}</strong></td>
                    <td class="dtc-number">{item['total']}</td>
                    <td class="dtc-number dtc-delay-positive">{item['late']}</td>
                    <td class="dtc-number">{item['late_rate']:g}%</td>
                    <td class="dtc-number">{completion_rate:.1f}%</td>
                    <td class="dtc-number">{completeness:.1f}%</td>
                    <td class="dtc-number"><span class="dtc-score">{score}</span></td>
                </tr>
            """)
        return f"""
            <section class="dtc-panel" style="margin-top:14px">
                <h2 class="dtc-panel-title">Chỉ số hiệu quả tiến độ theo KSGS</h2>
                <div class="dtc-delay-table-wrap">
                    <table class="dtc-delay-table dtc-manager-analysis">
                        <thead><tr>
                            <th>KSGS phụ trách</th>
                            <th class="dtc-number">Dự án</th>
                            <th class="dtc-number">Đã chậm</th>
                            <th class="dtc-number">Tỷ lệ chậm</th>
                            <th class="dtc-number">Hoàn thành đúng hạn</th>
                            <th class="dtc-number">Đủ dữ liệu</th>
                            <th class="dtc-number">Chỉ số</th>
                        </tr></thead>
                        <tbody>{''.join(rows)}</tbody>
                    </table>
                </div>
                <div class="dtc-analytics-subtitle" style="margin-top:10px">
                    Chỉ số tham khảo: 45% không chậm + 35% hoàn thành đúng hạn
                    + 20% đầy đủ dữ liệu; không dùng thay thế đánh giá nhân sự.
                </div>
            </section>
        """

    def _render_intervention_table(
        self,
        projects,
        delay_by_project,
        bucket_by_project,
        today,
    ):
        priority = {'late': 0, 'risk': 1, 'missing': 2, 'on_time': 3}
        candidates = sorted(
            projects,
            key=lambda project: (
                priority[bucket_by_project[project.id]],
                -(delay_by_project[project.id] or 0),
            ),
        )
        rows = []
        labels = {
            'late': ('Đã chậm', 'red'),
            'risk': ('Nguy cơ ≤ 30 ngày', 'yellow'),
            'missing': ('Thiếu dữ liệu', 'gray'),
            'on_time': ('Đúng tiến độ', 'green'),
        }
        for project in candidates[:12]:
            bucket = bucket_by_project[project.id]
            label, tone = labels[bucket]
            delay = delay_by_project[project.id]
            value = (
                f'{delay} ngày'
                if bucket == 'late'
                else f'Còn {abs(delay)} ngày'
                if bucket in ('risk', 'on_time') and delay is not None
                else '—'
            )
            rows.append(f"""
                <tr>
                    <td><a href="/web#id={project.id}&amp;model=project.project&amp;view_type=form"
                           target="_self">{escape(project.project_code or project.name)}</a></td>
                    <td>{escape(project.province or 'Chưa cập nhật')}</td>
                    <td>{escape(project.project_manager_id.display_name or 'Chưa phân công')}</td>
                    <td><span class="dtc-badge dtc-badge--{tone}">{label}</span></td>
                    <td class="dtc-number">{value}</td>
                </tr>
            """)
        return f"""
            <section class="dtc-panel">
                <h2 class="dtc-panel-title">Dự án cần ưu tiên can thiệp</h2>
                <div class="dtc-delay-table-wrap">
                    <table class="dtc-delay-table dtc-intervention-table">
                        <thead><tr>
                            <th>Mã dự án</th><th>Tỉnh/Thành</th><th>KSGS</th>
                            <th>Mức cảnh báo</th><th class="dtc-number">Tiến độ</th>
                        </tr></thead>
                        <tbody>{''.join(rows)}</tbody>
                    </table>
                </div>
            </section>
        """

    @staticmethod
    def _render_monthly_completion_trend(projects, delay_by_project):
        monthly = defaultdict(lambda: {'on_time': 0, 'late': 0})
        for project in projects:
            if not (
                project.state == 'done'
                and project.acceptance_date
                and project.planned_end_date
            ):
                continue
            month = project.acceptance_date.strftime('%m/%Y')
            key = (
                project.acceptance_date.year,
                project.acceptance_date.month,
                month,
            )
            monthly[key][
                'late' if delay_by_project[project.id] > 0 else 'on_time'
            ] += 1
        items = sorted(monthly.items())[-12:]
        if not items:
            body = '<div class="dtc-empty">Chưa có dự án hoàn thành.</div>'
        else:
            largest = max(
                max(values.values())
                for _key, values in items
            ) or 1
            columns = []
            for (_year, _month, label), values in items:
                on_time_height = max(values['on_time'] / largest * 135, 2)
                late_height = max(values['late'] / largest * 135, 2)
                columns.append(f"""
                    <div class="dtc-month-col">
                        <div class="dtc-month-bars">
                            <span class="dtc-month-bar dtc-progress-on-time"
                                  style="height:{on_time_height:.1f}px"
                                  title="Đúng hạn: {values['on_time']}"></span>
                            <span class="dtc-month-bar dtc-progress-late"
                                  style="height:{late_height:.1f}px"
                                  title="Chậm: {values['late']}"></span>
                        </div>
                        <div class="dtc-month-label">{label}</div>
                    </div>
                """)
            body = '<div class="dtc-month-chart">%s</div>' % ''.join(columns)
        return f"""
            <section class="dtc-panel">
                <h2 class="dtc-panel-title">Xu hướng hoàn thành theo tháng</h2>
                {body}
                <div class="dtc-inline-legend">
                    <span>🟢 Hoàn thành đúng hạn</span>
                    <span>🔴 Hoàn thành chậm</span>
                </div>
            </section>
        """

    def _render_delay_table(
        self,
        projects,
        delay_by_project,
        average_delay,
    ):
        measured_projects = [
            project
            for project in projects
            if delay_by_project[project.id] is not None
        ]
        measured_projects.sort(
            key=lambda project: delay_by_project[project.id],
            reverse=True,
        )
        rows = []
        for project in measured_projects[:10]:
            delay = delay_by_project[project.id]
            delay_class = (
                'dtc-delay-positive'
                if delay > 0
                else 'dtc-delay-negative'
                if delay < 0
                else ''
            )
            project_url = (
                f'/web#id={project.id}&model=project.project&view_type=form'
            )
            rows.append(f"""
                <tr>
                    <td>
                        <a href="{project_url}" target="_self">
                            {escape(project.project_code or project.name)}
                        </a>
                    </td>
                    <td>{escape(project.province or 'Chưa cập nhật')}</td>
                    <td>{escape(project.project_manager_id.display_name or 'Chưa phân công')}</td>
                    <td class="dtc-number {delay_class}">{delay}</td>
                </tr>
            """)
        if not rows:
            rows.append("""
                <tr>
                    <td colspan="4" class="dtc-empty">
                        Chưa có dự án được cấu hình ngày kết thúc kế hoạch.
                    </td>
                </tr>
            """)
        average_value = average_delay if average_delay is not None else '—'
        return f"""
            <section class="dtc-panel">
                <h2 class="dtc-panel-title">Tiến độ dự án</h2>
                <div class="dtc-delay-table-wrap">
                    <table class="dtc-delay-table">
                        <thead>
                            <tr>
                                <th>Mã dự án</th>
                                <th>Tỉnh/Thành</th>
                                <th>KSGS phụ trách</th>
                                <th class="dtc-number">Số ngày chậm</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(rows)}
                            <tr class="dtc-delay-summary">
                                <td colspan="3">Trung bình</td>
                                <td class="dtc-number">{average_value}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>
        """

    def _render_status_chart(self, projects):
        status_labels = dict(
            self.env['project.project']._fields['state'].selection
        )
        status_order = (
            'done',
            'handed_over',
            'approved',
            'in_progress',
            'survey',
            'draft',
            'cancelled',
        )
        status_colors = {
            'done': '#168de2',
            'handed_over': '#059669',
            'approved': '#1e40af',
            'in_progress': '#f97316',
            'survey': '#7e22ce',
            'draft': '#94a3b8',
            'cancelled': '#dc2626',
        }
        counts = {
            status: len(projects.filtered(
                lambda project, status=status: project.state == status
            ))
            for status in status_order
        }
        total = len(projects)
        stops = []
        cursor = 0.0
        legend_rows = []
        for status in status_order:
            count = counts[status]
            if not count:
                continue
            percentage = (count / total * 100) if total else 0
            next_cursor = cursor + percentage
            color = status_colors[status]
            stops.append(
                f'{color} {cursor:.2f}% {next_cursor:.2f}%'
            )
            legend_rows.append(f"""
                <div class="dtc-legend-row">
                    <span class="dtc-legend-dot" style="background:{color}"></span>
                    <span>{escape(status_labels.get(status, status))}</span>
                    <span class="dtc-legend-value">
                        {count} ({percentage:.1f}%)
                    </span>
                </div>
            """)
            cursor = next_cursor
        gradient = (
            ', '.join(stops)
            if stops
            else '#e2e8f0 0% 100%'
        )
        legend_html = (
            ''.join(legend_rows)
            if legend_rows
            else '<div class="dtc-empty">Chưa có dữ liệu dự án.</div>'
        )
        return f"""
            <section class="dtc-panel">
                <h2 class="dtc-panel-title">Tỷ lệ trạng thái dự án</h2>
                <div class="dtc-donut-layout">
                    <div
                        class="dtc-donut"
                        data-total="{total}"
                        style="background:conic-gradient({gradient})">
                    </div>
                    <div class="dtc-legend">{legend_html}</div>
                </div>
            </section>
        """

    @staticmethod
    def _average_delays_by(projects, delay_by_project, key_getter):
        grouped_delays = defaultdict(list)
        for project in projects:
            delay = delay_by_project[project.id]
            if delay is not None:
                grouped_delays[key_getter(project)].append(delay)
        averages = [
            (
                label,
                round(sum(delays) / len(delays), 1),
            )
            for label, delays in grouped_delays.items()
        ]
        return sorted(averages, key=lambda item: item[1], reverse=True)

    @staticmethod
    def _render_delay_bar_chart(title, values, empty_label):
        if not values:
            body_html = f'<div class="dtc-empty">{escape(empty_label)}</div>'
            axis_html = ''
        else:
            largest = max(abs(value) for _label, value in values) or 1
            rows = []
            for label, value in values[:10]:
                width = round(abs(value) / largest * 48, 2)
                direction = 'positive' if value >= 0 else 'negative'
                display_value = f'{value:g}'
                rows.append(f"""
                    <div class="dtc-bar-row" title="{escape(label)}: {display_value} ngày">
                        <div class="dtc-bar-label">{escape(label)}</div>
                        <div class="dtc-bar-plot">
                            <div
                                class="dtc-bar dtc-bar--{direction}"
                                style="width:{width}%">
                            </div>
                        </div>
                        <div class="dtc-bar-value">{display_value}</div>
                    </div>
                """)
            body_html = (
                '<div class="dtc-bar-chart">'
                + ''.join(rows)
                + '</div>'
            )
            axis_html = """
                <div class="dtc-chart-axis">
                    <span>Sớm tiến độ</span>
                    <span>0</span>
                    <span>Chậm tiến độ</span>
                </div>
            """
        return f"""
            <section class="dtc-panel">
                <h2 class="dtc-panel-title">{escape(title)}</h2>
                {body_html}
                {axis_html}
            </section>
        """

    def _render_notification_section(self):
        notifications = self._get_dashboard_notifications()
        if not notifications:
            return ''
        notification_html = ''.join(
            self._render_dashboard_notification(notification)
            for notification in notifications
        )
        return f"""
            <section class="dtc-panel" style="margin-top:14px">
                <h2 class="dtc-panel-title">Thông báo dự án</h2>
                <div class="dtc-notifications">{notification_html}</div>
            </section>
        """

    def _get_dashboard_notifications(self):
        """Extension hook for project-related notifications from other modules."""
        return []

    @staticmethod
    def _render_dashboard_notification(notification):
        priority = notification.get('priority', 'gray')
        if priority not in ('green', 'yellow', 'red', 'gray'):
            priority = 'gray'

        actions = []
        if notification.get('detail_url'):
            actions.append(
                '<a class="dtc-notification-link" href="%s" target="_self">%s</a>'
                % (
                    escape(notification['detail_url']),
                    escape(notification.get('detail_label', 'Xem chi tiết')),
                )
            )
        if notification.get('action_url'):
            actions.append(
                '<a class="dtc-notification-link" href="%s" target="_self">%s</a>'
                % (
                    escape(notification['action_url']),
                    escape(notification.get('action_label', 'Đã xem')),
                )
            )
        actions_html = (
            '<div class="dtc-notification-actions">%s</div>'
            % ''.join(actions)
            if actions
            else ''
        )
        return f"""
            <article class="dtc-notification dtc-notification--{priority}">
                <div class="dtc-notification-icon">
                    {escape(notification.get('icon', '!'))}
                </div>
                <div>
                    <div class="dtc-notification-title">
                        {escape(notification.get('title', 'Thông báo'))}
                    </div>
                    <div class="dtc-notification-description">
                        {escape(notification.get('description', ''))}
                    </div>
                </div>
                {actions_html}
            </article>
        """
