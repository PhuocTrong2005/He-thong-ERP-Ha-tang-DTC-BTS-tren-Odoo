from odoo import models


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def _visible_menu_ids(self, debug=False):
        visible_ids = super()._visible_menu_ids(debug=debug)
        user = self.env.user
        if user.has_group('base.group_system'):
            return visible_ids

        if user.has_group('dtc_bts_base.group_dtc_bts_pkh'):
            other_dashboard_menu_xmlids = (
                'dtc_bts_base.menu_dtc_bts_root',
                'dtc_bts_base.menu_dtc_bts_dashboard',
                'dtc_bts_maintenance.menu_dtc_bts_maintenance_root',
                'dtc_bts_maintenance.menu_dtc_bts_maintenance_dashboard',
                'dtc_bts_contract.menu_dtc_bts_contract_root',
                'dtc_bts_contract.menu_bts_contract_dashboard',
            )
            allowed_menu_ids = {
                menu.id
                for xmlid in other_dashboard_menu_xmlids
                if (menu := self.env.ref(xmlid, raise_if_not_found=False))
            }
            inventory_root = self.env.ref(
                'dtc_bts_inventory.menu_dtc_bts_inventory_root',
                raise_if_not_found=False,
            )
            if inventory_root:
                inventory_root_path = inventory_root.sudo().parent_path
                allowed_menu_ids.update(
                    menu.id
                    for menu in self.sudo().browse(visible_ids)
                    if (
                        menu.parent_path
                        and menu.parent_path.startswith(inventory_root_path)
                    )
                )
            return set(visible_ids) & allowed_menu_ids

        if user.has_group(
            'dtc_bts_contract.group_dtc_bts_contract_director'
        ):
            other_app_dashboard_xmlids = (
                'dtc_bts_base.menu_dtc_bts_root',
                'dtc_bts_base.menu_dtc_bts_dashboard',
                'dtc_bts_inventory.menu_dtc_bts_inventory_root',
                'dtc_bts_inventory.menu_dtc_bts_inventory_dashboard',
                'dtc_bts_maintenance.menu_dtc_bts_maintenance_root',
                'dtc_bts_maintenance.menu_dtc_bts_maintenance_dashboard',
            )
            allowed_menu_ids = {
                menu.id
                for xmlid in other_app_dashboard_xmlids
                if (menu := self.env.ref(xmlid, raise_if_not_found=False))
            }
            contract_root = self.env.ref(
                'dtc_bts_contract.menu_dtc_bts_contract_root',
                raise_if_not_found=False,
            )
            if contract_root:
                contract_root_path = contract_root.sudo().parent_path
                allowed_menu_ids.update(
                    menu.id
                    for menu in self.sudo().browse(visible_ids)
                    if (
                        menu.parent_path
                        and menu.parent_path.startswith(contract_root_path)
                    )
                )
            return set(visible_ids) & allowed_menu_ids

        if user.has_group(
            'dtc_bts_base.group_bts_enterprise_director'
        ):
            project_root = self.env.ref(
                'dtc_bts_base.menu_dtc_bts_root',
                raise_if_not_found=False,
            )
            if not project_root:
                return set()
            project_root_path = project_root.sudo().parent_path
            allowed_menu_ids = {
                menu.id
                for menu in self.sudo().browse(visible_ids)
                if (
                    menu.parent_path
                    and menu.parent_path.startswith(project_root_path)
                )
            }
            return set(visible_ids) & allowed_menu_ids
        return visible_ids
