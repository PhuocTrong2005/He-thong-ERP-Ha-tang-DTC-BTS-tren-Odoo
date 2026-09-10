from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    bts_contract_digest_last_date = fields.Date(
        string='Ngày gửi digest gia hạn gần nhất',
        readonly=True,
        copy=False,
    )
    bts_contract_digest_fingerprint = fields.Char(
        string='Fingerprint digest gia hạn gần nhất',
        readonly=True,
        copy=False,
    )

    @api.model
    def _sync_contract_director_demo_role(self):
        user = self.env.ref(
            'dtc_bts_contract.user_dtc_contract_director_demo',
            raise_if_not_found=False,
        )
        role = self.env.ref(
            'dtc_bts_contract.group_dtc_bts_contract_director',
            raise_if_not_found=False,
        )
        base_user = self.env.ref('base.group_user')
        if user and role:
            user.sudo().write({
                'active': True,
                'login': 'vyhocthcb@gmail.com',
                'email': 'vyhocthcb@gmail.com',
                'groups_id': [(6, 0, [base_user.id, role.id])],
            })
        return True
