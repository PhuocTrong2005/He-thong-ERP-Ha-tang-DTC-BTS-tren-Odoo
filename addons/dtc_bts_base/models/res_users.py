from odoo import api, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _sync_dtc_demo_roles(self):
        """Keep demo accounts isolated to one explicit business role."""
        base_user = self.env.ref('base.group_user')
        demo_user_config = {
            'dtc_bts_base.user_dtc_ksgs_demo': (
                'dtc_bts_base.group_dtc_bts_ksgs',
                'vydtt4947@ut.edu.vn',
            ),
            'dtc_bts_base.user_dtc_ksgs_an_demo': (
                'dtc_bts_base.group_dtc_bts_ksgs',
                'ksgs.an.demo@example.invalid',
            ),
            'dtc_bts_base.user_dtc_ksgs_binh_demo': (
                'dtc_bts_base.group_dtc_bts_ksgs',
                'ksgs.binh.demo@example.invalid',
            ),
            'dtc_bts_base.user_dtc_ksgs_cuong_demo': (
                'dtc_bts_base.group_dtc_bts_ksgs',
                'ksgs.cuong.demo@example.invalid',
            ),
            'dtc_bts_base.user_dtc_ksgs_dung_demo': (
                'dtc_bts_base.group_dtc_bts_ksgs',
                'ksgs.dung.demo@example.invalid',
            ),
            'dtc_bts_base.user_bts_enterprise_director_demo': (
                'dtc_bts_base.group_bts_enterprise_director',
                'dthuyvy456@gmail.com',
            ),
            'dtc_bts_base.user_dtc_pkh_demo': (
                'dtc_bts_base.group_dtc_bts_pkh',
                'tpkh.dtc.demo@gmail.com',
            ),
            'dtc_bts_base.user_dtc_warehouse_demo': (
                'dtc_bts_base.group_dtc_bts_warehouse',
                'tk.dtc.demo@gmail.com',
            ),
            'dtc_bts_base.user_dtc_infrastructure_demo': (
                'dtc_bts_base.group_dtc_bts_infrastructure',
                'qltht.dtc.demo@gmail.com',
            ),
            'dtc_bts_base.user_dtc_admin_demo': (
                'dtc_bts_base.group_dtc_bts_admin',
                'admin.dtc.demo@gmail.com',
            ),
        }
        for user_xml_id, (role_xml_id, email) in demo_user_config.items():
            user = self.env.ref(user_xml_id, raise_if_not_found=False)
            role = self.env.ref(role_xml_id, raise_if_not_found=False)
            if user and role:
                user.sudo().write({
                    'active': True,
                    'email': email,
                    'groups_id': [(6, 0, [base_user.id, role.id])],
                })

        planning_user = self.env.ref(
            'dtc_bts_base.user_dtc_pkh_demo',
            raise_if_not_found=False,
        )
        if planning_user:
            planning_user.sudo().write({
                'name': 'Trưởng phòng Kế hoạch Demo',
                'login': 'tpkh.dtc.demo@gmail.com',
                'email': 'tpkh.dtc.demo@gmail.com',
            })

        legacy_planning_user = self.env.ref(
            'dtc_bts_base.user_dtc_pkh_manager_demo',
            raise_if_not_found=False,
        )
        if legacy_planning_user:
            legacy_planning_user.sudo().write({
                'active': False,
                'groups_id': [(6, 0, [base_user.id])],
            })

        manager_user = self.env.ref(
            'dtc_bts_base.user_dtc_manager_demo',
            raise_if_not_found=False,
        )
        if manager_user:
            manager_user.sudo().write({
                'name': 'Quản lý nghiệp vụ Demo',
                'login': 'manager.demo',
                'email': 'manager.dtc.demo@gmail.com',
                'active': False,
                'groups_id': [(6, 0, [base_user.id])],
            })
        return True
