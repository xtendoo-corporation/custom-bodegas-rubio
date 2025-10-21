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

    _silicie_unidad_medida_stored = fields.Selection(
        selection=lambda self: silicie_specs.get_unit_measure_choices(),
        string='Unidad Medida SILICIE Storage',
        help='Campo de almacenamiento interno',
        copy=False,
    )

    silicie_unidad_medida = fields.Selection(
        selection=lambda self: silicie_specs.get_unit_measure_choices(),
        string='Unidad Medida SILICIE',
        help='Unidad de medida estandarizada SILICIE',
        compute='_compute_silicie_unidad_medida',
        inverse='_inverse_silicie_unidad_medida',
        store=False,
    )

    clave_silicie = fields.Char(
        string='Clave SILICIE',
        help='Clave para SILICIE. Rellenar manualmente si aplica.'
    )

    silicie_capacidad_envase = fields.Float(
        string='Capacidad Envase (Volumen)',
        help='Volumen del envase para SILICIE, en litros o la unidad que corresponda.'
    )

    silicie_descripcion_articulo = fields.Char(
        string='Descripción Artículo',
        help='Descripción manual del artículo para exportar en el CSV SILICIE.'
    )

    @api.depends('_silicie_unidad_medida_stored')
    def _compute_silicie_unidad_medida(self):
        """Siempre devolver LTS si está vacío."""
        for record in self:
            record.silicie_unidad_medida = record._silicie_unidad_medida_stored or 'LTS'

    def _inverse_silicie_unidad_medida(self):
        """Guardar el valor cuando el usuario lo cambia."""
        for record in self:
            record._silicie_unidad_medida_stored = record.silicie_unidad_medida

    @api.model
    def default_get(self, fields_list):
        """Forzar valores predeterminados para productos nuevos."""
        res = super().default_get(fields_list)

        # Forzar LTS para productos nuevos
        if 'silicie_unidad_medida' in fields_list or '_silicie_unidad_medida_stored' in fields_list:
            res['_silicie_unidad_medida_stored'] = 'LTS'
            res['silicie_unidad_medida'] = 'LTS'

        return res

    # Campos específicos para alcohol (IESA1CSV)
    silicie_graduacion = fields.Float(
        string='Graduación Alcohólica',
        help='Graduación alcohólica para productos de alcohol',
        digits=(5, 2),
    )

    silicie_codigo_nc = fields.Char(
        string='Código NC',
        help='Código de nomenclatura combinada para SILICIE',
        size=15,
    )

    @api.constrains('silicie_tipo_producto')
    def _check_silicie_tipo_producto(self):
        """Validar que el tipo de producto SILICIE tenga máximo 2 caracteres."""
        for record in self:
            if record.silicie_tipo_producto and len(record.silicie_tipo_producto) > 2:
                raise ValidationError(
                    f"El tipo de producto SILICIE debe tener máximo 2 caracteres: {record.silicie_tipo_producto}"
                )
