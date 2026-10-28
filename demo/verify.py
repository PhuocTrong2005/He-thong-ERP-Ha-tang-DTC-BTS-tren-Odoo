"""Integration demo through real HTTP sessions; OTPs read only from local Mailpit."""
import base64
import atexit
import json
import re
from datetime import date, timedelta
from pathlib import Path
import requests

BASE = 'http://127.0.0.1:8069'
MAIL = 'http://mailpit:8025'
secrets = json.loads(Path('/mnt/demo/.local/credentials.json').read_text(encoding='utf-8-sig'))
results = []
atexit.register(lambda: Path('/tmp/demo-verification-progress.json').write_text(
    json.dumps(results, ensure_ascii=False, indent=2)))

class Client:
    def __init__(self, role):
        self.role = role
        self.s = requests.Session()
        result = self.rpc('/web/session/authenticate', {'db': 'bts_contract_demo',
                          'login': role + '.demo', 'password': secrets[role]})
        assert result.get('uid'), result
        assert result.get('db') in (None, 'bts_contract_demo')
        self.uid = result['uid']
        results.append('HTTP login OK: ' + role)

    def rpc(self, path, params):
        r = self.s.post(BASE + path, json={'jsonrpc': '2.0', 'method': 'call',
                                         'params': params, 'id': 1}, timeout=90)
        r.raise_for_status()
        data = r.json()
        if data.get('error'):
            raise RuntimeError(data['error']['data'].get('message', str(data['error'])))
        return data.get('result')

    def call(self, model, method, args=None, **kwargs):
        kwargs.setdefault('context', {'tz': 'Asia/Ho_Chi_Minh', 'lang': 'en_US'})
        return self.rpc('/web/dataset/call_kw/' + model + '/' + method,
                        {'model': model, 'method': method, 'args': args or [], 'kwargs': kwargs})

    def read(self, model, ids, fields):
        return self.call(model, 'read', [ids], fields=fields)

    def find(self, model, domain, fields):
        return self.call(model, 'search_read', [domain], fields=fields)

    def write(self, model, ids, vals):
        return self.call(model, 'write', [ids, vals])

def blocked(label, fn):
    try:
        fn()
    except RuntimeError as e:
        results.append('BLOCKED as expected: ' + label + ': ' + str(e))
        return
    raise AssertionError('Expected rejection: ' + label)

ksgs, bgd, infra = (Client(r) for r in ('ksgs', 'bgd', 'infra'))
for client in (ksgs, bgd, infra):
    assert not client.call('res.users', 'has_group', ['base.group_system'])
    menus = client.s.get(BASE + '/web/webclient/load_menus/demo', timeout=60)
    menus.raise_for_status()
    tree = menus.json()
    names = [v.get('name') for k, v in tree.items() if isinstance(v, dict) and v.get('name')]
    results.append('Menus ' + client.role + ': ' + ', '.join(names))
    root = any('Quản lý hợp đồng BTS' == n for n in names)
    assert root == (client.role != 'ksgs')

project = ksgs.find('project.project', [('project_code', '=', 'DEMO-TESTED')], ['name'])[0]
station = ksgs.find('project.task', [('station_code', '=', 'DEMO-BTS-TESTED')],
                    ['land_contract_id', 'negotiation_minutes_id', 'station_lease_contract_id', 'station_state'])[0]
pid, sid = project['id'], station['id']
land = station['land_contract_id'][0]
batch_model = 'bts.contract.signature.batch'
line_model = batch_model + '.line'
document = base64.b64encode('TÀI LIỆU DEMO — xác nhận ký nội bộ; không có giá trị pháp lý.'.encode()).decode()
land_values = ksgs.read('bts.contract', [land], ['expiration_date', 'partner_id'])[0]
today = date.fromisoformat(land_values['expiration_date']) - timedelta(days=15)

def sign_batch(batch):
    if batch['state'] == 'done':
        signed = bgd.find(line_model, [('batch_id', '=', batch['id'])], ['state', 'otp_state', 'signature_valid'])
        assert signed and all(l['state'] == 'signed' and l['otp_state'] == 'used' and l['signature_valid'] for l in signed)
        results.append('Persisted completed batch and OTP signatures verified: ' + str(batch['id']))
        return
    lines = bgd.find(line_model, [('batch_id', '=', batch['id'])], ['state', 'otp_state'])
    for line in lines:
        if line['state'] == 'signed':
            continue
        lid = line['id']
        bgd.call(line_model, 'action_sign', [[lid]])
        bgd.call(line_model, 'action_send_signature_otp', [[lid]])
        # Read delivered email from Mailpit; never inspect the OTP hash or alter verification.
        messages = requests.get(MAIL + '/api/v1/messages', timeout=20).json()['messages']
        otp = None
        for msg in messages:
            if not any(x.get('Address') == 'bgd@demo.invalid' for x in msg.get('To', [])):
                continue
            detail = requests.get(MAIL + '/api/v1/message/' + msg['ID'], timeout=20).json()
            match = re.search(r'(?<!\d)(\d{6})(?!\d)', detail.get('Text', '') or detail.get('HTML', ''))
            if match:
                otp = match.group(1)
                break
        assert otp, 'No delivered OTP in Mailpit'
        # First submit an incorrect code and verify the attempt counter actually increases.
        wrong = '%06d' % ((int(otp) + 1) % 1000000)
        bgd.write(line_model, [lid], {'otp_code_input': wrong})
        assert bgd.read(line_model, [lid], ['otp_attempt_count'])[0]['otp_attempt_count'] == 1
        bgd.write(line_model, [lid], {'otp_code_input': otp})
        bgd.call(line_model, 'action_confirm_digital_signature', [[lid]])
        signed = bgd.read(line_model, [lid], ['state', 'otp_state', 'signature_valid', 'signed_by_id'])[0]
        assert signed['state'] == 'signed' and signed['otp_state'] == 'used' and signed['signature_valid'], signed
        assert signed['signed_by_id'][0] == bgd.uid
        results.append('OTP delivered, incorrect attempt counted, signature valid: line ' + str(lid))
    bgd.call(batch_model, 'action_complete', [[batch['id']]])
    assert bgd.read(batch_model, [batch['id']], ['state'])[0]['state'] == 'done'
    results.append('Batch completed: ' + str(batch['id']))

batches = ksgs.find(batch_model, [('project_id', '=', pid), ('phase', '=', 'phase_1')], ['state'])
if not batches:
    blocked('KSGS cannot activate individual contract', lambda: ksgs.call('bts.contract', 'action_activate', [[land]]))
    partner = land_values['partner_id'][0]
    try:
        ksgs.write('bts.contract', [land], {'partner_id': False})
        blocked('Missing dossier prevents batch submission',
                lambda: ksgs.call('project.project', 'action_send_contract_signature_batch', [[pid]]))
    finally:
        ksgs.write('bts.contract', [land], {'partner_id': partner})
    action = ksgs.call('project.project', 'action_send_contract_signature_batch', [[pid]])
    batches = ksgs.read(batch_model, [action['res_id']], ['state'])
sign_batch(batches[0])
assert ksgs.read('project.task', [sid], ['station_state'])[0]['station_state'] in ('contracted', 'station_lease_signed')

station = ksgs.read('project.task', [sid], ['station_lease_contract_id'])[0]
if not station['station_lease_contract_id']:
    blocked('Lease scan before acceptance', lambda: ksgs.write('project.task', [sid],
              {'station_lease_contract_scan': document, 'station_lease_contract_scan_filename': 'DEMO-lease.txt'}))
    ksgs.write('project.task', [sid], {'acceptance_date': str(today)})
    ksgs.write('project.task', [sid], {'station_lease_contract_scan': document,
                                   'station_lease_contract_scan_filename': 'DEMO-lease.txt'})
    lease = ksgs.read('project.task', [sid], ['station_lease_contract_id'])[0]['station_lease_contract_id'][0]
    ksgs.write('bts.contract', [lease], {'contract_code': 'DEMO-LEASE-TESTED', 'sign_date': str(today),
              'effective_date': str(today), 'expiration_date': str(today + timedelta(days=10)),
              'term_years': 1, 'rental_price': 24000000, 'payment_cycle': 'yearly'})
else:
    lease = station['station_lease_contract_id'][0]
batches = ksgs.find(batch_model, [('project_id', '=', pid), ('phase', '=', 'phase_2')], ['state'])
if not batches:
    action = ksgs.call('project.project', 'action_send_contract_signature_batch', [[pid]])
    batches = ksgs.read(batch_model, [action['res_id']], ['state'])
sign_batch(batches[0])
assert ksgs.read('project.task', [sid], ['station_state'])[0]['station_state'] == 'station_lease_signed'

renewals = infra.find('bts.contract.renewal', [('renewal_code', '=', 'DEMO-RENEWAL-TESTED')], ['state'])
if not renewals:
    rid = infra.call('bts.contract.renewal', 'create', [{'contract_id': lease,
                     'renewal_code': 'DEMO-RENEWAL-TESTED', 'notes': 'DEMO kiểm thử gia hạn'}])
    renewals = [{'id': rid, 'state': 'draft'}]
rid = renewals[0]['id']
if renewals[0]['state'] == 'draft':
    infra.call('bts.contract.renewal', 'action_start', [[rid]])
if renewals[0]['state'] in ('draft', 'in_progress'):
    infra.write('bts.contract.renewal', [rid], {'new_sign_date': str(today),
        'new_effective_date': str(today), 'new_expiration_date': str(today + timedelta(days=20)),
        'renewal_scan': document, 'renewal_scan_filename': 'DEMO-renewal.txt'})
    blocked('Renewal exceeds land coverage', lambda: infra.call('bts.contract.renewal', 'action_complete', [[rid]]))
    infra.write('bts.contract.renewal', [rid], {'new_expiration_date': str(today + timedelta(days=14))})
    infra.call('bts.contract.renewal', 'action_complete', [[rid]])
if renewals[0]['state'] != 'completed':
    bgd.write('bts.contract.renewal', [rid], {'signed_document': document,
                                         'signed_document_filename': 'DEMO-renewal-confirmed.txt'})
    bgd.call('bts.contract.renewal', 'action_sign_signature', [[rid]])
assert infra.read('bts.contract.renewal', [rid], ['state'])[0]['state'] == 'completed'
assert infra.read('bts.contract', [lease], ['expiration_date'])[0]['expiration_date'] == str(today + timedelta(days=14))
results.append('Renewal completed with BGĐ file confirmation (this source uses no renewal OTP)')
dash = infra.find('bts.contract.dashboard', [], ['dashboard_html'])
assert dash and dash[0]['dashboard_html']
activities = infra.find('mail.activity', [('res_model', '=', 'bts.contract'), ('res_id', 'in', [land, lease])],
                        ['date_deadline', 'user_id'])
assert any(a['user_id'][0] == infra.uid for a in activities), activities
results.append('Dashboard rendered; expiry activities assigned to infrastructure user')
blocked('BGĐ cannot edit project', lambda: bgd.write('project.project', [pid], {'name': 'FORBIDDEN'}))
blocked('Infrastructure cannot edit station', lambda: infra.write('project.task', [sid], {'name': 'FORBIDDEN'}))
live = ksgs.find('bts.contract', [('contract_code', '=', 'DEMO-LAND-LIVE')], ['state'])
assert live[0]['state'] == 'draft'
results.append('Live practice project remains draft')
Path('/tmp/demo-verification.json').write_text(json.dumps({'date': str(today), 'results': results}, ensure_ascii=False, indent=2))
print(json.dumps({'date': str(today), 'results': results}, ensure_ascii=False, indent=2))
