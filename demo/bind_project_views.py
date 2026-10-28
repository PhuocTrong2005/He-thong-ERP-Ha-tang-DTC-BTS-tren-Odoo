"""Odoo shell: bind the existing BTS project form in the dedicated demo database.

The base action otherwise resolves its unspecified form to the contract due
overview. This changes view selection only, without modifying ACL or workflow.
"""
import json

if env.cr.dbname != 'bts_contract_demo':
    raise RuntimeError('Refuse any database other than bts_contract_demo')
action = env.ref('dtc_bts_base.action_dtc_bts_project')
before = action.views
for kind, xid, sequence in [
    ('tree', 'dtc_bts_base.view_dtc_bts_project_tree', 1),
    ('form', 'dtc_bts_base.view_dtc_bts_project_form', 2),
]:
    existing = action.view_ids.filtered(lambda view: view.view_mode == kind)
    if existing:
        if existing.view_id != env.ref(xid):
            raise RuntimeError('Preserve unexpected manual view binding')
        continue
    record = env['ir.actions.act_window.view'].create({
        'act_window_id': action.id, 'view_mode': kind,
        'view_id': env.ref(xid).id, 'sequence': sequence,
    })
    env['ir.model.data'].create({
        'module': 'bts_local_demo', 'name': 'project_action_' + kind,
        'model': 'ir.actions.act_window.view', 'res_id': record.id, 'noupdate': True,
    })
env.cr.commit()
print(json.dumps({'action': action.id, 'before': before, 'after': action.views}))
