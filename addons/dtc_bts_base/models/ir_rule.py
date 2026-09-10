from odoo import api, models
from odoo.osv import expression


class IrRule(models.Model):
    _inherit = 'ir.rule'

    _BTS_PROJECT_SCOPE_DOMAINS = {
        'project.project': {
            'director': [('enterprise_director_id', '=', 'USER_ID')],
            'ksgs': [('project_manager_id', '=', 'USER_ID')],
        },
        'project.task': {
            'director': [('project_id.enterprise_director_id', '=', 'USER_ID')],
            'ksgs': [('project_id.project_manager_id', '=', 'USER_ID')],
        },
        'bts.material.request': {
            'director': [
                ('bts_project_id.enterprise_director_id', '=', 'USER_ID'),
            ],
            'ksgs': [('bts_project_id.project_manager_id', '=', 'USER_ID')],
        },
        'bts.material.request.line': {
            'director': [
                (
                    'request_id.bts_project_id.enterprise_director_id',
                    '=',
                    'USER_ID',
                ),
            ],
            'ksgs': [
                ('request_id.bts_project_id.project_manager_id', '=', 'USER_ID'),
            ],
        },
        'bts.contract': {
            'director': [('project_id.enterprise_director_id', '=', 'USER_ID')],
            'ksgs': [('project_id.project_manager_id', '=', 'USER_ID')],
        },
        'bts.contract.renewal': {
            'director': [('project_id.enterprise_director_id', '=', 'USER_ID')],
            'ksgs': [('project_id.project_manager_id', '=', 'USER_ID')],
        },
        'bts.negotiation.minutes': {
            'director': [('project_id.enterprise_director_id', '=', 'USER_ID')],
            'ksgs': [('project_id.project_manager_id', '=', 'USER_ID')],
        },
        'bts.contract.signature.batch': {
            'director': [('project_id.enterprise_director_id', '=', 'USER_ID')],
            'ksgs': [('project_id.project_manager_id', '=', 'USER_ID')],
        },
        'bts.contract.signature.batch.line': {
            'director': [
                ('batch_id.project_id.enterprise_director_id', '=', 'USER_ID'),
            ],
            'ksgs': [
                ('batch_id.project_id.project_manager_id', '=', 'USER_ID'),
            ],
        },
        'bts.maintenance.batch': {
            'director': [('project_id.enterprise_director_id', '=', 'USER_ID')],
            'ksgs': [('project_id.project_manager_id', '=', 'USER_ID')],
        },
        'maintenance.equipment': {
            'director': [
                ('bts_project_id.enterprise_director_id', '=', 'USER_ID'),
            ],
            'ksgs': [('bts_project_id.project_manager_id', '=', 'USER_ID')],
        },
        'maintenance.request': {
            'director': [
                ('bts_project_id.enterprise_director_id', '=', 'USER_ID'),
            ],
            'ksgs': [('bts_project_id.project_manager_id', '=', 'USER_ID')],
        },
        'bts.repair.proposal': {
            'director': [
                '|',
                ('project_id.enterprise_director_id', '=', 'USER_ID'),
                ('bts_project_id.enterprise_director_id', '=', 'USER_ID'),
            ],
            'ksgs': [
                '|',
                ('project_id.project_manager_id', '=', 'USER_ID'),
                ('bts_project_id.project_manager_id', '=', 'USER_ID'),
            ],
        },
    }

    @api.model
    def _compute_domain(self, model_name, mode='read'):
        """Add project scope only to the explicitly listed BTS models."""
        domain = super()._compute_domain(model_name, mode=mode)
        model_scopes = self._BTS_PROJECT_SCOPE_DOMAINS.get(model_name)
        if not model_scopes:
            return domain
        if self.env.user.has_group('base.group_system'):
            return []

        scope_domains = []
        if self.env.user.has_group(
            'dtc_bts_base.group_bts_enterprise_director'
        ):
            scope_domains.append(model_scopes['director'])
        if self.env.user.has_group('dtc_bts_base.group_dtc_bts_ksgs'):
            scope_domains.append(model_scopes['ksgs'])
        if not scope_domains:
            return domain

        user_id = self.env.uid
        scoped_domain = expression.OR(scope_domains)
        scoped_domain = [
            tuple(user_id if value == 'USER_ID' else value for value in item)
            if isinstance(item, tuple)
            else item
            for item in scoped_domain
        ]
        return expression.AND([domain, scoped_domain])
