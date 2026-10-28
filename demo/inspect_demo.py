"""Read-only Odoo shell inventory and checks; never applies workflow transitions.

Run after bind_project_views.py. IDs/URLs are resolved from the current database,
so users need not rely on the historical IDs in the interview runbook.
"""
import json
from odoo import fields

if env.cr.dbname != 'bts_contract_demo':
    raise RuntimeError('Refuse any database other than bts_contract_demo')
env = env(context=dict(env.context, tz='Asia/Ho_Chi_Minh', lang='vi_VN'))
action = env.ref('dtc_bts_base.action_dtc_bts_project')
bindings = {view.view_mode: view.view_id for view in action.view_ids}
assert bindings.get('form') == env.ref('dtc_bts_base.view_dtc_bts_project_form')
assert bindings.get('tree') == env.ref('dtc_bts_base.view_dtc_bts_project_tree')
servers = env['ir.mail_server'].search([])
assert servers and all(server.smtp_host == 'mailpit' and server.smtp_port == 1025 for server in servers)
users = env['res.users'].search([('login', 'in', ['ksgs.demo', 'bgd.demo', 'infra.demo'])])
assert len(users) == 3 and all(not user.has_group('base.group_system') for user in users)
actions = {
    'project.project': action.id,
    'project.task': env.ref('dtc_bts_base.action_dtc_bts_station').id,
    'bts.contract': env.ref('dtc_bts_contract.action_bts_contract').id,
    'bts.negotiation.minutes': None,
    'bts.contract.signature.batch': env.ref('dtc_bts_contract.action_bts_contract_signature_batch').id,
    'bts.contract.renewal': env.ref('dtc_bts_contract.action_bts_contract_renewal').id,
}
codes = {'project.project': 'project_code', 'project.task': 'station_code',
         'bts.contract': 'contract_code', 'bts.negotiation.minutes': 'memo_code',
         'bts.contract.signature.batch': 'name', 'bts.contract.renewal': 'renewal_code'}
result = {'date': str(fields.Date.context_today(env.user)), 'view_binding': 'OK',
          'smtp': 'Mailpit only', 'business_users_without_system': True, 'records': {}}
for model, action_id in actions.items():
    code = codes[model]
    domain = [('project_id.project_code', '=like', 'DEMO-%')] if model == 'bts.contract.signature.batch' else [(code, '=like', 'DEMO-%')]
    rows = []
    for record in env[model].search(domain):
        row = {'id': record.id, 'code': record[code],
               'state': record.station_state if model == 'project.task' else record.state}
        if model == 'project.project':
            row['name'] = record.name
        if model == 'bts.contract':
            row['expiration_date'] = str(record.expiration_date)
        if model == 'bts.contract.signature.batch':
            row.update(project_code=record.project_id.project_code, phase=record.phase,
                       signed_lines=record.signed_line_count, total_lines=record.line_count)
        if action_id:
            row['url'] = 'http://127.0.0.1:8079/web#id=%s&model=%s&view_type=form&action=%s' % (record.id, model, action_id)
        rows.append(row)
    result['records'][model] = rows
print(json.dumps(result, ensure_ascii=False, indent=2))
env.cr.rollback()
