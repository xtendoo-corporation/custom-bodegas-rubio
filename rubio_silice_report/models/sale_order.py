# -*- coding: utf-8 -*-

from odoo import models, fields, api
from . import silicie_specs


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    silicie_movement_type_mode = fields.Selection(
        [
            ('default', 'Predeterminado (Todos)'),
            ('custom', 'Personalizado'),
        ],
        string='Tipo Movimiento',
        default='default',
        required=True,
        help='Seleccione si usar el tipo de movimiento predeterminado (Todos) o personalizarlo',
    )

    silicie_movement_type = fields.Selection(
        selection=lambda self: silicie_specs.get_movement_type_choices(),
        string='Tipo de Movimiento SILICIE',
        help='Tipo de movimiento SILICIE que se aplicará a este pedido de venta',
        compute='_compute_silicie_movement_type',
        store=True,
        readonly=False,
    )

    @api.depends('silicie_movement_type_mode')
    def _compute_silicie_movement_type(self):
        """Establecer el tipo de movimiento según el modo."""
        for order in self:
            # Si está en modo predeterminado, usar el primer valor válido (A08)
            if order.silicie_movement_type_mode == 'default':
                order.silicie_movement_type = 'A08'
            # Si está en modo personalizado, no tocar el valor que el usuario ha elegido
