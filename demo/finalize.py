"""Finish demo configuration and inspect persisted workflow evidence via ORM."""
import json
from odoo import fields
assert env.cr.dbname == 'bts_contract_demo'
env = env(context=dict(env.context, tz='Asia/Ho_Chi_Minh'))
lang = env['res.lang'].with_context(active_test=False).search([('code', '=', 'vi_VN')], limit=1)
if not lang.active:
    env['base.language.install'].create({'lang_ids': [(6, 0, lang.ids)]}).lang_install()
users = env['res.users'].search([('login', 'in', ['admin.demo', 'ksgs.demo', 'bgd.demo', 'infra.demo'])])
users.write({'lang': 'vi_VN', 'tz': 'Asia/Ho_Chi_Minh'})
for user in users.filtered(lambda u: u.login != 'admin.demo'):
    action = ('dtc_bts_base.action_dtc_bts_dashboard' if user.login == 'ksgs.demo'
              else 'dtc_bts_contract.action_bts_contract_dashboard')
    user.write({'action_id': env.ref(action).id})
land = env['bts.contract'].search([('contract_code', '=', 'DEMO-LAND-TESTED')])
if not env['bts.contract.renewal'].search_count([('renewal_code', '=', 'DEMO-RENEWAL-PRACTICE')]):
    infra = users.filtered(lambda u: u.login == 'infra.demo')
    env['bts.contract.renewal'].with_user(infra).create({'contract_id': land.id,
        'renewal_code': 'DEMO-RENEWAL-PRACTICE', 'notes': 'DEMO hồ sơ để thực hành gia hạn thuê đất'})
env['bts.contract']._cron_check_contract_expiry()
pending = env.ref('bts_local_demo.project_pending')
if not pending.signature_batch_ids:
    pending.with_user(users.filtered(lambda u: u.login == 'ksgs.demo')).action_send_contract_signature_batch()
batches = env['bts.contract.signature.batch'].search([('project_id.project_code', '=', 'DEMO-TESTED')])
assert len(batches) == 2 and all(b.state == 'done' for b in batches)
assert len(batches.line_ids) == 3
assert all(line.state == 'signed' and line.otp_state == 'used' and line.signature_valid for line in batches.line_ids)
modules = env['ir.module.module'].search([('state', '=', 'installed')]).mapped('name')
assert 'dtc_bts_inventory' not in modules and 'dtc_bts_maintenance' not in modules
assert all(not u.has_group('base.group_system') for u in users if u.login != 'admin.demo')
env.cr.commit()
print('DEMO_FINAL_EVIDENCE', json.dumps({'modules': sorted(modules),
    'batch_states': [(b.name, b.phase, b.state) for b in batches],
    'signatures': [{'line': l.id, 'otp': l.otp_state, 'attempts': l.otp_attempt_count,
                    'valid': l.signature_valid, 'signer': l.signed_by_id.login} for l in batches.line_ids],
    'contracts': env['bts.contract'].search([('contract_code', '=like', 'DEMO-%')]).read(
        ['contract_code', 'state', 'expiration_date']),
    'cron_executed': 'bts.contract._cron_check_contract_expiry',
    'date': str(fields.Date.context_today(users.filtered(lambda u: u.login == 'ksgs.demo')))
}, ensure_ascii=False, default=str))
