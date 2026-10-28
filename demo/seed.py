"""Run in odoo shell. Only targets the dedicated demo database and owned XML IDs."""
import base64
import json
from datetime import timedelta
from pathlib import Path
from odoo import fields

assert env.cr.dbname == 'bts_contract_demo', 'Refuse any other database'
secrets = json.loads(Path('/mnt/demo/.local/credentials.json').read_text(encoding='utf-8-sig'))
ctx = dict(tracking_disable=True, mail_create_nosubscribe=True, no_reset_password=True, tz='Asia/Ho_Chi_Minh')
env = env(context=dict(env.context, **ctx))

def owned(key, model, vals):
    xid = 'bts_local_demo.' + key
    record = env.ref(xid, raise_if_not_found=False)
    if record:
        return record
    record = env[model].create(vals)
    env['ir.model.data'].create({'module': 'bts_local_demo', 'name': key,
                               'model': model, 'res_id': record.id, 'noupdate': True})
    return record

# These are configuration changes solely in the newly created demo database.
env.ref('base.user_admin').write({'login': 'admin.demo', 'password': secrets['admin'],
                                'email': 'admin@demo.invalid', 'tz': 'Asia/Ho_Chi_Minh'})
env.company.write({'name': 'DEMO DTC BTS', 'email': 'odoo@demo.invalid'})
env['ir.config_parameter'].sudo().set_param('web.base.url', 'http://127.0.0.1:8079')
env['ir.config_parameter'].sudo().set_param('web.base.url.freeze', 'True')
owned('smtp', 'ir.mail_server', {'name': 'DEMO Mailpit ONLY', 'smtp_host': 'mailpit',
      'smtp_port': 1025, 'smtp_encryption': 'none', 'sequence': 1, 'from_filter': False})
assert all(s.smtp_host == 'mailpit' for s in env['ir.mail_server'].search([]))

actors = {}
for role, group in [('ksgs', 'dtc_bts_base.group_dtc_bts_ksgs'),
                    ('bgd', 'dtc_bts_contract.group_dtc_bts_contract_director'),
                    ('infra', 'dtc_bts_base.group_dtc_bts_infrastructure')]:
    actors[role] = owned('user_' + role, 'res.users', {
        'name': 'DEMO ' + role.upper(), 'login': role + '.demo',
        'email': role + '@demo.invalid', 'password': secrets[role],
        'tz': 'Asia/Ho_Chi_Minh', 'notification_type': 'inbox',
        'groups_id': [(6, 0, [env.ref('base.group_user').id, env.ref(group).id])]})
    assert not actors[role].has_group('base.group_system')

landowner = owned('landowner', 'res.partner', {'name': 'DEMO Chủ đất Nguyễn An',
                  'partner_type': 'landowner', 'email': 'landowner@demo.invalid'})
telecom = owned('telecom', 'res.partner', {'name': 'DEMO Viễn thông Sao Việt',
                'partner_type': 'telecom_partner', 'email': 'telecom@demo.invalid', 'is_company': True})
today = fields.Date.context_today(actors['ksgs'])
document = base64.b64encode(('TÀI LIỆU DEMO\nHồ sơ giả phục vụ phỏng vấn BA/ERP.\n'
                            'Không có giá trị pháp lý. Xác nhận ký nội bộ Odoo.\n').encode())
Path('/tmp/demo-document.txt').write_bytes(base64.b64decode(document))
for key, label in [('live', '01 - Thực hành dự thảo'), ('tested', '02 - Kiểm thử thực tế'),
                   ('pending', '03 - Chờ BGĐ ký')]:
    project = owned('project_' + key, 'project.project', {
        'name': 'DEMO ' + label, 'project_code': 'DEMO-' + key.upper(),
        'project_manager_id': actors['ksgs'].id, 'telecom_partner_id': telecom.id,
        'privacy_visibility': 'employees', 'province': 'TP. Hồ Chí Minh'})
    station = owned('station_' + key, 'project.task', {
        'name': 'DEMO Trạm ' + key.upper(), 'station_code': 'DEMO-BTS-' + key.upper(),
        'project_id': project.id, 'assigned_user_id': actors['ksgs'].id,
        'user_ids': [(6, 0, [actors['ksgs'].id])], 'site_address': 'Địa chỉ giả DEMO'})
    if not station.land_contract_id:
        station.with_user(actors['ksgs']).write({
            'land_contract_scan': document, 'land_contract_scan_filename': 'DEMO-thue-dat.txt',
            'negotiation_minutes_scan': document, 'negotiation_minutes_scan_filename': 'DEMO-dam-phan.txt'})
        station.land_contract_id.with_user(actors['ksgs']).write({
            'contract_code': 'DEMO-LAND-' + key.upper(), 'partner_id': landowner.id,
            'sign_date': today - timedelta(days=350), 'effective_date': today - timedelta(days=350),
            'expiration_date': today + timedelta(days=15), 'term_years': 1,
            'rental_price': 12000000, 'payment_cycle': 'yearly'})
        station.negotiation_minutes_id.with_user(actors['ksgs']).write({
            'memo_code': 'DEMO-MEMO-' + key.upper(), 'partner_id': landowner.id,
            'memo_date': today, 'agreed_rental_price': 12000000})

env.cr.commit()
print('DEMO_SEED_OK', json.dumps({'date': str(today), 'users': {k: v.login for k, v in actors.items()},
      'owned_records': env['ir.model.data'].search_count([('module', '=', 'bts_local_demo')])}))
