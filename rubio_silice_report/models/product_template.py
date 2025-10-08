from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . import silicie_specs


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Campos SILICIE específicos
    silicie_codigo_producto = fields.Char(
        string='Código Producto SILICIE',
        help='Código del producto para reportes SILICIE',
    )

    silicie_unidad_medida = fields.Selection(
        selection=lambda self: silicie_specs.get_unit_measure_choices(),
        string='Unidad Medida SILICIE',
        help='Unidad de medida estandarizada SILICIE',
        default='UN',
    )

    # Campos específicos para alcohol (IESA1CSV)
    silicie_graduacion = fields.Float(
        string='Graduación Alcohólica',
        help='Graduación alcohólica para productos de alcohol',
        digits=(5, 2),
    )

    numero_silice = fields.Char(
        string='Número SILICIE',
        size=20,
        help='Número identificativo SILICIE para el producto'
    )

    @api.constrains('silicie_tipo_producto')
    def _check_silicie_tipo_producto(self):
        """Validar que el tipo de producto SILICIE tenga máximo 2 caracteres."""
        for record in self:
            if record.silicie_tipo_producto and len(record.silicie_tipo_producto) > 2:
                raise ValidationError(
                    f"El tipo de producto SILICIE debe tener máximo 2 caracteres: {record.silicie_tipo_producto}"
                )
