from html import escape

from odoo import api, fields, models


class BtsContractDashboard(models.Model):
    _name = 'bts.contract.dashboard'
    _description = 'Dashboard hợp đồng BTS'

    name = fields.Char(string='Tên dashboard', required=True)
    dashboard_html = fields.Html(
        string='Dashboard',
        compute='_compute_dashboard_html',
        sanitize=False,
    )

    @api.depends_context('uid', 'lang', 'tz')
    def _compute_dashboard_html(self):
        for dashboard in self:
            dashboard.dashboard_html = dashboard._build_dashboard_html()

    def _get_dashboard_data(self):
        today = fields.Date.context_today(self)
        contracts = self._dashboard_model('bts.contract').search(
            [],
            order='expiration_date asc, contract_code asc',
        )
        pending_memos = self._dashboard_model(
            'bts.negotiation.minutes'
        ).search(
            [('state', '=', 'pending_approval')],
            order='memo_date asc, id asc',
        )
        can_sign_renewals = (
            self.env.user.has_group(
                'dtc_bts_contract.group_dtc_bts_contract_director'
            )
            or self.env.user.has_group('base.group_system')
        )
        renewal_states = ['in_progress']
        if can_sign_renewals:
            renewal_states.append('pending_signature')
        renewals = self._dashboard_model('bts.contract.renewal').search(
            [('state', 'in', renewal_states)],
            order='renewal_date asc, id asc',
        )

        expiring_contracts = contracts.filtered(
            lambda contract: (
                contract.state == 'active'
                and contract.expiration_date
                and 0 <= (contract.expiration_date - today).days <= 30
            )
        )
        notifications = []

        for contract in contracts:
            station_name = contract.station_id.display_name or '-'
            if contract.state == 'submitted':
                notifications.append({
                    'tone': 'gray',
                    'icon': '✓',
                    'title': 'Hợp đồng chờ ký duyệt',
                    'description': (
                        f'{contract.contract_code} · {station_name} đang chờ '
                        'Ban Giám đốc ký duyệt.'
                    ),
                    'date': contract.write_date.date() if contract.write_date else today,
                    'model': contract._name,
                    'res_id': contract.id,
                    'sort': 30,
                })
            elif contract.state == 'renewal_agreed':
                notifications.append({
                    'tone': 'yellow',
                    'icon': '↻',
                    'title': 'Hợp đồng chờ gia hạn',
                    'description': (
                        f'{contract.contract_code} · {station_name} đã thống nhất '
                        'gia hạn và cần lập bản ghi gia hạn.'
                    ),
                    'date': contract.expiration_date or today,
                    'model': contract._name,
                    'res_id': contract.id,
                    'sort': 10,
                })

            if contract.state == 'active' and contract.expiration_date:
                days_left = (contract.expiration_date - today).days
                if days_left < 0:
                    notifications.append({
                        'tone': 'red',
                        'icon': '!',
                        'title': 'Hợp đồng đã quá hạn',
                        'description': (
                            f'{contract.contract_code} · {station_name} đã quá hạn '
                            f'{abs(days_left)} ngày.'
                        ),
                        'date': contract.expiration_date,
                        'model': contract._name,
                        'res_id': contract.id,
                        'sort': 0,
                    })
                elif days_left <= 30:
                    notifications.append({
                        'tone': 'yellow',
                        'icon': '!',
                        'title': 'Hợp đồng sắp hết hạn',
                        'description': (
                            f'{contract.contract_code} · {station_name} còn '
                            f'{days_left} ngày hiệu lực.'
                        ),
                        'date': contract.expiration_date,
                        'model': contract._name,
                        'res_id': contract.id,
                        'sort': 5,
                    })

        for memo in pending_memos:
            notifications.append({
                'tone': 'gray',
                'icon': '✓',
                'title': 'Biên bản đàm phán chờ phê duyệt',
                'description': (
                    f'{memo.memo_code} · {memo.station_id.display_name or "-"} '
                    'đang chờ xác nhận.'
                ),
                'date': memo.memo_date or today,
                'model': memo._name,
                'res_id': memo.id,
                'sort': 20,
            })

        for renewal in renewals:
            if renewal.state == 'pending_signature':
                notifications.append({
                    'tone': 'yellow',
                    'icon': '✓',
                    'title': 'Hồ sơ gia hạn chờ BGĐ ký số',
                    'description': (
                        f'{renewal.renewal_code} · '
                        f'{renewal.station_id.display_name or "-"} đang chờ '
                        'ký số hoặc từ chối.'
                    ),
                    'date': renewal.write_date.date()
                    if renewal.write_date else today,
                    'model': renewal._name,
                    'res_id': renewal.id,
                    'sort': -10,
                })
            else:
                notifications.append({
                    'tone': 'gray',
                    'icon': '↻',
                    'title': 'Đang thực hiện gia hạn',
                    'description': (
                        f'{renewal.renewal_code} · '
                        f'{renewal.station_id.display_name or "-"} chưa hoàn thành.'
                    ),
                    'date': renewal.renewal_date or today,
                    'model': renewal._name,
                    'res_id': renewal.id,
                    'sort': 15,
                })

        notifications.sort(
            key=lambda item: (item['sort'], item['date'], item['title'])
        )
        return {
            'kpis': [
                ('Tổng hợp đồng', len(contracts)),
                ('Đang hiệu lực', len(contracts.filtered(
                    lambda contract: contract.state == 'active'
                ))),
                ('Sắp hết hạn', len(expiring_contracts)),
                ('Chờ phê duyệt', len(contracts.filtered(
                    lambda contract: contract.state == 'submitted'
                )) + len(pending_memos) + len(renewals.filtered(
                    lambda renewal: renewal.state == 'pending_signature'
                ))),
            ],
            'notifications': notifications[:20],
        }

    def _dashboard_model(self, model_name):
        model = self.env[model_name]
        if (
            self.env.user.has_group('dtc_bts_base.group_dtc_bts_pkh')
            or self.env.user.has_group(
                'dtc_bts_contract.group_dtc_bts_contract_director'
            )
        ):
            return model.sudo()
        return model

    def _build_dashboard_html(self):
        data = self._get_dashboard_data()
        kpi_html = ''.join(
            f"""
                <div class="bts-contract-kpi">
                    <div class="bts-contract-kpi-label">{escape(label)}</div>
                    <div class="bts-contract-kpi-value">{value}</div>
                </div>
            """
            for label, value in data['kpis']
        )
        notification_html = ''.join(
            self._render_notification(notification)
            for notification in data['notifications']
        )
        if not notification_html:
            notification_html = """
                <div class="bts-contract-empty">
                    Chưa có cảnh báo hoặc công việc hợp đồng cần xử lý.
                </div>
            """

        return f"""
            <style>
                .bts-contract-dashboard,
                .bts-contract-dashboard * {{
                    font-family: "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    font-synthesis: none;
                    letter-spacing: 0;
                    text-shadow: none;
                }}
                .bts-contract-dashboard {{
                    padding: 20px 24px 28px;
                    color: #1f2937;
                    background: #f8f9fb;
                }}
                .bts-contract-title {{
                    margin: 0 0 18px;
                    color: #111827;
                    font-size: 30px;
                    font-weight: 600;
                    line-height: 1.25;
                }}
                .bts-contract-kpis {{
                    display: grid;
                    grid-template-columns: repeat(4, minmax(160px, 1fr));
                    gap: 12px;
                    margin-bottom: 20px;
                }}
                .bts-contract-kpi {{
                    min-height: 82px;
                    padding: 14px 16px;
                    background: #ffffff;
                    border: 1px solid #d9dee8;
                    border-left: 4px solid #0f766e;
                    border-radius: 10px;
                    box-shadow: none;
                }}
                .bts-contract-kpi-label {{
                    min-height: 32px;
                    color: #6b7280;
                    font-size: 13px;
                    font-weight: 500;
                    line-height: 1.3;
                }}
                .bts-contract-kpi-value {{
                    margin-top: 6px;
                    color: #111827;
                    font-size: 24px;
                    font-weight: 600;
                    line-height: 1;
                }}
                .bts-contract-feed {{
                    padding: 16px;
                    background: #ffffff;
                    border: 1px solid #d9dee8;
                    border-radius: 10px;
                }}
                .bts-contract-feed-title {{
                    margin: 0 0 14px;
                    color: #111827;
                    font-size: 16px;
                    font-weight: 600;
                    line-height: 1.4;
                }}
                .bts-contract-notifications {{
                    display: grid;
                    gap: 8px;
                }}
                .bts-contract-notification {{
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
                .bts-contract-notification--red {{ border-left-color: #dc2626; }}
                .bts-contract-notification--yellow {{ border-left-color: #d97706; }}
                .bts-contract-notification--gray {{ border-left-color: #9ca3af; }}
                .bts-contract-notification-icon {{
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
                .bts-contract-notification--red .bts-contract-notification-icon {{
                    background: #dc2626;
                }}
                .bts-contract-notification--yellow .bts-contract-notification-icon {{
                    background: #d97706;
                }}
                .bts-contract-notification--gray .bts-contract-notification-icon {{
                    background: #6b7280;
                }}
                .bts-contract-notification-title {{
                    color: #111827;
                    font-size: 14px;
                    font-weight: 600;
                    line-height: 1.35;
                }}
                .bts-contract-notification-description {{
                    margin-top: 2px;
                    color: #4b5563;
                    font-size: 13px;
                    font-weight: 400;
                    line-height: 1.4;
                }}
                .bts-contract-notification-date {{
                    margin-top: 3px;
                    color: #9ca3af;
                    font-size: 12px;
                    font-weight: 400;
                }}
                .bts-contract-notification-link {{
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
                .bts-contract-notification-link:hover {{
                    color: #115e59;
                    background: #f0fdfa;
                    text-decoration: none;
                }}
                .bts-contract-empty {{
                    padding: 24px;
                    color: #6b7280;
                    font-size: 13px;
                    text-align: center;
                }}
                @media (max-width: 1000px) {{
                    .bts-contract-kpis {{
                        grid-template-columns: repeat(2, minmax(160px, 1fr));
                    }}
                }}
                @media (max-width: 700px) {{
                    .bts-contract-dashboard {{ padding: 14px; }}
                    .bts-contract-kpis {{ grid-template-columns: 1fr; }}
                    .bts-contract-notification {{
                        grid-template-columns: 28px minmax(0, 1fr);
                    }}
                    .bts-contract-notification-link {{
                        grid-column: 2;
                        justify-self: start;
                    }}
                }}
            </style>
            <div class="bts-contract-dashboard">
                <h1 class="bts-contract-title">
                    BẢNG TỔNG HỢP HỢP ĐỒNG BTS
                </h1>
                <div class="bts-contract-kpis">{kpi_html}</div>
                <section class="bts-contract-feed">
                    <h2 class="bts-contract-feed-title">
                        CẢNH BÁO VÀ CÔNG VIỆC HỢP ĐỒNG
                    </h2>
                    <div class="bts-contract-notifications">
                        {notification_html}
                    </div>
                </section>
            </div>
        """

    @staticmethod
    def _render_notification(notification):
        notification_date = notification['date']
        date_text = (
            notification_date.strftime('%d/%m/%Y')
            if notification_date
            else '-'
        )
        href = (
            f"/web#id={notification['res_id']}"
            f"&model={notification['model']}&view_type=form"
        )
        return f"""
            <article class="bts-contract-notification
                            bts-contract-notification--{notification['tone']}">
                <div class="bts-contract-notification-icon">
                    {escape(notification['icon'])}
                </div>
                <div class="bts-contract-notification-content">
                    <div class="bts-contract-notification-title">
                        {escape(notification['title'])}
                    </div>
                    <div class="bts-contract-notification-description">
                        {escape(notification['description'])}
                    </div>
                    <div class="bts-contract-notification-date">{date_text}</div>
                </div>
                <a class="bts-contract-notification-link" href="{href}" target="_self">
                    Mở chi tiết
                </a>
            </article>
        """
