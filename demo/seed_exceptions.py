"""Odoo shell: add fictional exception starters without resetting existing records."""
import base64
import json
from pathlib import Path
from odoo import fields

if env.cr.dbname != 'bts_contract_demo':
    raise RuntimeError('Refuse any database other than bts_contract_demo')
env = env(context=dict(env.context, tz='Asia/Ho_Chi_Minh', no_reset_password=True))
ksgs = env.ref('bts_local_demo.user_ksgs')
director = env.ref('dtc_bts_base.user_bts_enterprise_director_demo')
telecom = env.ref('bts_local_demo.telecom')
landowner = env.ref('bts_local_demo.landowner')
template = env.ref('bts_local_demo.station_live').land_contract_id
today = fields.Date.context_today(env.user)
document = base64.b64encode(Path('/mnt/demo/DEMO-document.txt').read_bytes())
results = []
for key, label in [('EXCEPTION', 'NGOẠI LỆ'), ('REJECT', 'TỪ CHỐI')]:
    code = 'DEMO-' + key
    project = env['project.project'].search([('project_code', '=', code)])
    if project:
        if not project.name.startswith('DEMO '):
            raise RuntimeError('Unexpected record at demo code; preserve it')
        results.append({'project': code, 'id': project.id, 'status': 'preserved'})
        continue
    project = env['project.project'].with_user(director).create({
        'name': 'DEMO ' + label + ' - Dữ liệu kiểm tra riêng', 'project_code': code,
        'project_manager_id': ksgs.id, 'privacy_visibility': 'employees',
        'telecom_partner_id': telecom.id,
    })
    station = env['project.task'].with_user(ksgs).create({
        'name': 'DEMO Trạm ' + label, 'station_code': 'DEMO-BTS-' + key,
        'project_id': project.id, 'assigned_user_id': ksgs.id,
    })
    if key == 'REJECT':
        station.with_user(ksgs).write({
            'land_contract_scan': document, 'land_contract_scan_filename': 'DEMO-document.txt',
            'negotiation_minutes_scan': document, 'negotiation_minutes_scan_filename': 'DEMO-document.txt',
        })
        station.land_contract_id.with_user(ksgs).write({
            'contract_code': 'DEMO-LAND-REJECT', 'partner_id': landowner.id,
            'sign_date': template.sign_date, 'effective_date': template.effective_date,
            'expiration_date': template.expiration_date, 'term_years': 1,
            'rental_price': 12000000, 'payment_cycle': 'yearly',
        })
        station.negotiation_minutes_id.with_user(ksgs).write({
            'memo_code': 'DEMO-MEMO-REJECT', 'partner_id': landowner.id, 'memo_date': today,
        })
        project.with_user(ksgs).action_send_contract_signature_batch()
    results.append({'project': code, 'id': project.id, 'status': 'created'})
env.cr.commit()
print(json.dumps(results, ensure_ascii=False))
