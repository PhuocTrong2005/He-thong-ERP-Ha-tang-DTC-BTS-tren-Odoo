from collections import Counter, defaultdict

from markupsafe import escape

from odoo import fields, models


class BtsContractDashboardAnalytics(models.Model):
    _inherit = 'bts.contract.dashboard'

    def _build_dashboard_html(self):
        data = self._get_contract_analytics_data()
        return f"""
            <style>
                .contract-analytics,
                .contract-analytics * {{
                    box-sizing: border-box;
                    font-family: "Segoe UI", Roboto, Arial, sans-serif;
                }}
                .contract-analytics {{
                    --ink: #222936;
                    --muted: #667085;
                    --line: #d9e1e8;
                    --purple: #a45fb2;
                    --blue: #168fe3;
                    padding: 16px;
                    color: var(--ink);
                    background: #f3f6fa;
                }}
                .contract-analytics-title {{
                    margin: 0 0 14px;
                    color: #0f172a;
                    font-size: 26px;
                    font-weight: 700;
                }}
                .contract-analytics-subtitle {{
                    margin: -8px 0 16px;
                    color: var(--muted);
                    font-size: 13px;
                }}
                .contract-analytics-grid {{
                    display: grid;
                    grid-template-columns: minmax(360px, 1fr) minmax(500px, 1.25fr);
                    gap: 14px;
                }}
                .contract-panel {{
                    min-width: 0;
                    padding: 16px;
                    background: #fff;
                    border: 1px solid var(--line);
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(15, 23, 42, .05);
                }}
                .contract-panel-title {{
                    margin: 0 0 15px;
                    color: #24272d;
                    font-size: 18px;
                    font-weight: 700;
                    text-align: center;
                }}
                .contract-panel-title--alert {{
                    color: #b33d49;
                }}
                .contract-expiry-bars {{
                    display: grid;
                    gap: 14px;
                    padding: 8px 4px 0;
                }}
                .contract-expiry-row {{
                    display: grid;
                    grid-template-columns: 125px minmax(180px, 1fr) 36px;
                    align-items: center;
                    gap: 10px;
                }}
                .contract-expiry-label {{
                    color: #56606d;
                    font-size: 13px;
                    text-align: right;
                }}
                .contract-expiry-track {{
                    height: 42px;
                    background:
                        repeating-linear-gradient(
                            to right,
                            #f4f5f7 0,
                            #f4f5f7 calc(25% - 1px),
                            #dfe3e8 calc(25% - 1px),
                            #dfe3e8 25%
                        );
                }}
                .contract-expiry-bar {{
                    height: 100%;
                    min-width: 3px;
                    background: linear-gradient(90deg, #a45fb2, #b36fc0);
                }}
                .contract-expiry-value {{
                    color: #374151;
                    font-size: 13px;
                    font-variant-numeric: tabular-nums;
                    font-weight: 700;
                    text-align: right;
                }}
                .contract-axis {{
                    display: flex;
                    justify-content: space-between;
                    margin: 10px 46px 0 139px;
                    color: #87909d;
                    font-size: 11px;
                }}
                .contract-axis-title {{
                    margin-top: 4px;
                    color: #56606d;
                    font-size: 12px;
                    text-align: center;
                }}
                .contract-heatmap-wrap,
                .contract-alert-table-wrap {{
                    overflow-x: auto;
                }}
                .contract-heatmap,
                .contract-alert-table {{
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 13px;
                }}
                .contract-heatmap th,
                .contract-heatmap td,
                .contract-alert-table th,
                .contract-alert-table td {{
                    padding: 7px 9px;
                    border-bottom: 1px solid #edf0f3;
                }}
                .contract-heatmap th,
                .contract-alert-table th {{
                    border-bottom: 2px solid #8cc9dd;
                    color: #2f343c;
                    font-weight: 700;
                    text-align: left;
                    white-space: nowrap;
                }}
                .contract-heatmap td {{
                    min-width: 80px;
                    font-variant-numeric: tabular-nums;
                    text-align: right;
                }}
                .contract-heatmap tbody tr:nth-child(even),
                .contract-alert-table tbody tr:nth-child(even) {{
                    background: #f1f2f4;
                }}
                .contract-heatmap-cell {{
                    background-clip: padding-box !important;
                    font-weight: 650;
                }}
                .contract-total {{
                    font-weight: 750;
                }}
                .contract-priority-bars {{
                    display: grid;
                    gap: 13px;
                    padding-top: 6px;
                }}
                .contract-priority-row {{
                    display: grid;
                    grid-template-columns: 110px minmax(180px, 1fr) 35px;
                    align-items: center;
                    gap: 10px;
                }}
                .contract-priority-label {{
                    overflow: hidden;
                    color: #5a6471;
                    font-size: 13px;
                    text-align: right;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                .contract-priority-track {{
                    height: 42px;
                    background:
                        repeating-linear-gradient(
                            to right,
                            #f5f7f9 0,
                            #f5f7f9 calc(25% - 1px),
                            #dde4eb calc(25% - 1px),
                            #dde4eb 25%
                        );
                }}
                .contract-priority-bar {{
                    height: 100%;
                    min-width: 3px;
                    background: linear-gradient(90deg, #0b8ee8, #30a7f2);
                }}
                .contract-priority-value {{
                    font-size: 13px;
                    font-variant-numeric: tabular-nums;
                    font-weight: 700;
                    text-align: right;
                }}
                .contract-alert-table a {{
                    color: #28577f;
                    font-weight: 650;
                    text-decoration: none;
                    white-space: nowrap;
                }}
                .contract-alert-table a:hover {{
                    color: #0877bd;
                    text-decoration: underline;
                }}
                .contract-alert-table td {{
                    color: #4b5563;
                    white-space: nowrap;
                }}
                .contract-empty {{
                    padding: 36px 14px;
                    color: #94a3b8;
                    font-size: 13px;
                    font-style: italic;
                    text-align: center;
                }}
                .contract-notification-panel {{
                    margin-top: 14px;
                }}
                .contract-notifications {{
                    display: grid;
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                    gap: 8px;
                }}
                .contract-notification {{
                    display: grid;
                    grid-template-columns: 25px minmax(0, 1fr) auto;
                    align-items: center;
                    gap: 9px;
                    padding: 9px 11px;
                    border: 1px solid var(--line);
                    border-left: 4px solid #9ca3af;
                    border-radius: 5px;
                }}
                .contract-notification--red {{ border-left-color: #dc2626; }}
                .contract-notification--yellow {{ border-left-color: #d97706; }}
                .contract-notification-icon {{
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
                .contract-notification--red .contract-notification-icon {{
                    background: #dc2626;
                }}
                .contract-notification--yellow .contract-notification-icon {{
                    background: #d97706;
                }}
                .contract-notification-title {{
                    color: #1f2937;
                    font-size: 12px;
                    font-weight: 700;
                }}
                .contract-notification-description,
                .contract-notification-date {{
                    color: #6b7280;
                    font-size: 11px;
                }}
                .contract-notification-link {{
                    padding: 4px 7px;
                    color: #0f766e;
                    border: 1px solid #99d5cc;
                    border-radius: 4px;
                    font-size: 11px;
                    text-decoration: none;
                    white-space: nowrap;
                }}
                @media (max-width: 1080px) {{
                    .contract-analytics-grid {{
                        grid-template-columns: 1fr;
                    }}
                }}
                @media (max-width: 720px) {{
                    .contract-analytics {{ padding: 10px; }}
                    .contract-expiry-row {{
                        grid-template-columns: 95px minmax(150px, 1fr) 30px;
                    }}
                    .contract-priority-row {{
                        grid-template-columns: 90px minmax(150px, 1fr) 30px;
                    }}
                    .contract-axis {{ margin-left: 109px; }}
                    .contract-notifications {{
                        grid-template-columns: 1fr;
                    }}
                }}
            </style>
            <div class="contract-analytics">
                <h1 class="contract-analytics-title">
                    Phân tích thời hạn hợp đồng BTS
                </h1>
                <div class="contract-analytics-subtitle">
                    Dữ liệu cập nhật trực tiếp từ hệ thống Odoo
                </div>
                <div class="contract-analytics-grid">
                    {self._render_expiry_bucket_chart(data)}
                    {self._render_expiry_heatmap(data)}
                    {self._render_partner_priority_chart(data)}
                    {self._render_land_expiry_alerts(data)}
                </div>
                {self._render_notification_feed(data)}
            </div>
        """

    def _get_contract_analytics_data(self):
        today = fields.Date.context_today(self)
        contracts = self._dashboard_model('bts.contract').search(
            [],
            order='expiration_date asc, contract_code asc',
        )
        dated_contracts = contracts.filtered(
            lambda contract: (
                contract.expiration_date
                and contract.state in (
                    'active',
                    'renewal_agreed',
                    'expired',
                )
            )
        )
        bucket_order = (
            'over_90',
            '60_90',
            'under_60',
            'overdue',
        )
        bucket_labels = {
            'over_90': 'Trên 90 ngày',
            '60_90': '60–90 ngày',
            'under_60': 'Dưới 60 ngày',
            'overdue': 'Quá hạn',
        }
        bucket_by_contract = {
            contract.id: self._get_expiry_bucket(contract, today)
            for contract in dated_contracts
        }
        bucket_counts = Counter(bucket_by_contract.values())
        visible_buckets = tuple(
            bucket
            for bucket in bucket_order
            if bucket_counts[bucket]
        )

        heatmap = defaultdict(Counter)
        for contract in dated_contracts:
            province = (
                contract.project_id.province
                or 'Chưa cập nhật'
            )
            heatmap[province][bucket_by_contract[contract.id]] += 1

        priority_counts = Counter()
        for contract in dated_contracts:
            bucket = bucket_by_contract[contract.id]
            if bucket != 'over_90':
                partner = (
                    contract.partner_id.display_name
                    or 'Chưa xác định'
                )
                priority_counts[partner] += 1

        mismatch_contracts = contracts.filtered(
            lambda contract: (
                contract.contract_type == 'infrastructure_lease'
                and contract.expiration_date
                and contract.related_land_contract_id.expiration_date
                and (
                    contract.related_land_contract_id.expiration_date
                    < contract.expiration_date
                )
                and contract.state not in ('cancelled', 'liquidated')
            )
        ).sorted(
            key=lambda contract: (
                contract.related_land_contract_id.expiration_date,
                contract.contract_code,
            )
        )
        dashboard_data = self._get_dashboard_data()
        return {
            'today': today,
            'dated_contracts': dated_contracts,
            'bucket_order': visible_buckets,
            'bucket_labels': bucket_labels,
            'bucket_counts': bucket_counts,
            'heatmap': heatmap,
            'priority_counts': priority_counts,
            'mismatch_contracts': mismatch_contracts,
            'notifications': dashboard_data['notifications'],
        }

    @staticmethod
    def _get_expiry_bucket(contract, today):
        days_left = (contract.expiration_date - today).days
        if days_left < 0:
            return 'overdue'
        if days_left <= 59:
            return 'under_60'
        if days_left <= 90:
            return '60_90'
        return 'over_90'

    def _render_expiry_bucket_chart(self, data):
        buckets = data['bucket_order']
        counts = data['bucket_counts']
        largest = max(
            (counts[bucket] for bucket in buckets),
            default=0,
        )
        if not buckets:
            chart_html = """
                <div class="contract-empty">
                    Chưa có hợp đồng hiệu lực được cấu hình ngày hết hạn.
                </div>
            """
            axis_html = ''
        else:
            rows = []
            for bucket in buckets:
                count = counts[bucket]
                width = round(count / largest * 100, 2) if largest else 0
                rows.append(f"""
                    <div class="contract-expiry-row">
                        <div class="contract-expiry-label">
                            {escape(data['bucket_labels'][bucket])}
                        </div>
                        <div class="contract-expiry-track">
                            <div
                                class="contract-expiry-bar"
                                style="width:{width}%">
                            </div>
                        </div>
                        <div class="contract-expiry-value">{count}</div>
                    </div>
                """)
            chart_html = (
                '<div class="contract-expiry-bars">'
                + ''.join(rows)
                + '</div>'
            )
            axis_html = f"""
                <div class="contract-axis">
                    <span>0</span>
                    <span>{largest}</span>
                </div>
                <div class="contract-axis-title">Số hợp đồng</div>
            """
        return f"""
            <section class="contract-panel">
                <h2 class="contract-panel-title">
                    Số hợp đồng theo mốc hạn
                </h2>
                {chart_html}
                {axis_html}
            </section>
        """

    def _render_expiry_heatmap(self, data):
        buckets = data['bucket_order']
        heatmap = data['heatmap']
        if not buckets or not heatmap:
            body_html = """
                <div class="contract-empty">
                    Chưa có dữ liệu tỉnh và thời hạn hợp đồng.
                </div>
            """
        else:
            largest_cell = max(
                (
                    counts[bucket]
                    for counts in heatmap.values()
                    for bucket in buckets
                ),
                default=1,
            ) or 1
            header_cells = ''.join(
                f'<th>{escape(data["bucket_labels"][bucket])}</th>'
                for bucket in buckets
            )
            rows = []
            column_totals = Counter()
            for province in sorted(heatmap):
                counts = heatmap[province]
                cells = []
                for bucket in buckets:
                    count = counts[bucket]
                    column_totals[bucket] += count
                    alpha = 0.12 + (count / largest_cell * 0.65) if count else 0
                    value = count or ''
                    cells.append(f"""
                        <td
                            class="contract-heatmap-cell"
                            style="background:rgba(22,143,227,{alpha:.2f})">
                            {value}
                        </td>
                    """)
                rows.append(f"""
                    <tr>
                        <td>{escape(province)}</td>
                        {''.join(cells)}
                        <td class="contract-total">
                            {sum(counts.values())}
                        </td>
                    </tr>
                """)
            total_cells = ''.join(
                f'<td class="contract-total">{column_totals[bucket]}</td>'
                for bucket in buckets
            )
            body_html = f"""
                <div class="contract-heatmap-wrap">
                    <table class="contract-heatmap">
                        <thead>
                            <tr>
                                <th>Tỉnh/Thành</th>
                                {header_cells}
                                <th>Tổng</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(rows)}
                            <tr class="contract-total">
                                <td>Tổng</td>
                                {total_cells}
                                <td>{len(data['dated_contracts'])}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            """
        return f"""
            <section class="contract-panel">
                <h2 class="contract-panel-title">
                    Bản đồ nhiệt hợp đồng theo tỉnh × hạn
                </h2>
                {body_html}
            </section>
        """

    def _render_partner_priority_chart(self, data):
        partners = sorted(
            data['priority_counts'].items(),
            key=lambda item: (-item[1], item[0]),
        )[:10]
        largest = max((count for _partner, count in partners), default=0)
        if not partners:
            body_html = """
                <div class="contract-empty">
                    Chưa có đối tác với hợp đồng cần ưu tiên gia hạn.
                </div>
            """
        else:
            rows = []
            for partner, count in partners:
                width = round(count / largest * 100, 2) if largest else 0
                rows.append(f"""
                    <div class="contract-priority-row" title="{escape(partner)}">
                        <div class="contract-priority-label">
                            {escape(partner)}
                        </div>
                        <div class="contract-priority-track">
                            <div
                                class="contract-priority-bar"
                                style="width:{width}%">
                            </div>
                        </div>
                        <div class="contract-priority-value">{count}</div>
                    </div>
                """)
            body_html = (
                '<div class="contract-priority-bars">'
                + ''.join(rows)
                + '</div>'
                + '<div class="contract-axis-title">Số lượng</div>'
            )
        return f"""
            <section class="contract-panel">
                <h2 class="contract-panel-title">
                    Đối tác cần ưu tiên gia hạn
                </h2>
                {body_html}
            </section>
        """

    def _render_land_expiry_alerts(self, data):
        contracts = data['mismatch_contracts']
        if not contracts:
            rows_html = """
                <tr>
                    <td colspan="6" class="contract-empty">
                        Không có hợp đồng đất hết hạn sớm hơn hợp đồng hạ tầng.
                    </td>
                </tr>
            """
        else:
            rows = []
            for contract in contracts[:20]:
                land_contract = contract.related_land_contract_id
                land_expiry = land_contract.expiration_date
                infrastructure_url = (
                    f'/web#id={contract.id}&model=bts.contract'
                    '&view_type=form'
                )
                land_url = (
                    f'/web#id={land_contract.id}&model=bts.contract'
                    '&view_type=form'
                )
                rows.append(f"""
                    <tr>
                        <td>
                            <a href="{infrastructure_url}" target="_self">
                                {escape(contract.contract_code)}
                            </a>
                        </td>
                        <td>{escape(contract.partner_id.display_name or '-')}</td>
                        <td>{land_expiry.year}</td>
                        <td>{land_expiry.month:02d}</td>
                        <td>{land_expiry.day:02d}</td>
                        <td>
                            <a href="{land_url}" target="_self">
                                {escape(land_contract.contract_code)}
                            </a>
                        </td>
                    </tr>
                """)
            rows_html = ''.join(rows)
        return f"""
            <section class="contract-panel">
                <h2 class="contract-panel-title contract-panel-title--alert">
                    Cảnh báo: đất hết hạn sớm hơn hạ tầng
                </h2>
                <div class="contract-alert-table-wrap">
                    <table class="contract-alert-table">
                        <thead>
                            <tr>
                                <th>Hợp đồng hạ tầng</th>
                                <th>Đối tác</th>
                                <th>Năm</th>
                                <th>Tháng</th>
                                <th>Ngày</th>
                                <th>Hợp đồng đất</th>
                            </tr>
                        </thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                </div>
            </section>
        """

    def _render_notification_feed(self, data):
        notifications = data['notifications'][:8]
        if not notifications:
            return ''
        notification_html = ''.join(
            self._render_analytics_notification(notification)
            for notification in notifications
        )
        return f"""
            <section class="contract-panel contract-notification-panel">
                <h2 class="contract-panel-title">
                    Cảnh báo và công việc hợp đồng
                </h2>
                <div class="contract-notifications">
                    {notification_html}
                </div>
            </section>
        """

    @staticmethod
    def _render_analytics_notification(notification):
        notification_date = notification.get('date')
        date_text = (
            notification_date.strftime('%d/%m/%Y')
            if notification_date
            else '-'
        )
        href = (
            f"/web#id={notification['res_id']}"
            f"&model={notification['model']}&view_type=form"
        )
        tone = notification.get('tone', 'gray')
        return f"""
            <article class="contract-notification contract-notification--{tone}">
                <div class="contract-notification-icon">
                    {escape(notification.get('icon', '!'))}
                </div>
                <div>
                    <div class="contract-notification-title">
                        {escape(notification.get('title', 'Thông báo'))}
                    </div>
                    <div class="contract-notification-description">
                        {escape(notification.get('description', ''))}
                    </div>
                    <div class="contract-notification-date">{date_text}</div>
                </div>
                <a class="contract-notification-link" href="{href}" target="_self">
                    Mở chi tiết
                </a>
            </article>
        """
