import unicodedata

from odoo import _, api, fields, models
from odoo.exceptions import AccessError


def _is_warehouse_readonly_user(env):
    return (
        not env.su
        and env.user.has_group('dtc_bts_base.group_dtc_bts_warehouse')
        and not env.user.has_group('dtc_bts_base.group_dtc_bts_pkh')
        and not env.user.has_group('base.group_system')
    )


def _check_warehouse_catalog_readonly(env):
    if _is_warehouse_readonly_user(env):
        raise AccessError(_(
            'Thủ kho chỉ được xem danh mục vật tư BTS.'
        ))


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_bts_material = fields.Boolean(
        string='Vật tư BTS',
        default=True,
        help='Đánh dấu sản phẩm là vật tư xây dựng/thiết bị phục vụ triển khai trạm BTS.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        _check_warehouse_catalog_readonly(self.env)
        return super().create(vals_list)

    def write(self, vals):
        _check_warehouse_catalog_readonly(self.env)
        return super().write(vals)

    def unlink(self):
        _check_warehouse_catalog_readonly(self.env)
        return super().unlink()

    @api.model
    def load(self, field_names, data):
        """Accept common Vietnamese spreadsheet aliases during imports."""
        type_indexes = [
            field_names.index(field_name)
            for field_name in ('type', 'detailed_type')
            if field_name in field_names
        ]
        if not type_indexes:
            return super().load(field_names, data)

        aliases = {'hàng hóa', 'hàng hoá'}
        normalized_data = [list(row) for row in data]
        for row in normalized_data:
            for index in type_indexes:
                value = row[index]
                if (
                    isinstance(value, str)
                    and unicodedata.normalize('NFC', value.strip()).casefold()
                    in aliases
                ):
                    row[index] = 'product'
        return super().load(field_names, normalized_data)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_bts_material = fields.Boolean(
        related='product_tmpl_id.is_bts_material',
        store=True,
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        _check_warehouse_catalog_readonly(self.env)
        return super().create(vals_list)

    def write(self, vals):
        _check_warehouse_catalog_readonly(self.env)
        return super().write(vals)

    def unlink(self):
        _check_warehouse_catalog_readonly(self.env)
        return super().unlink()
