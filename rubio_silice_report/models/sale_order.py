# -*- coding: utf-8 -*-

from odoo import models, fields, api
from . import silicie_specs


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    silicie_movement_type = fields.Selection(
        selection=lambda self: silicie_specs.get_movement_type_choices(),
        string='Tipo de Movimiento SILICIE',
        help='Tipo de movimiento SILICIE que se aplicará a este pedido de venta',
        compute='_compute_silicie_movement_type',
        store=True,
        readonly=False,
    )

    @api.depends('partner_id', 'partner_id.silicie_movement_type')
    def _compute_silicie_movement_type(self):
        """Establecer el tipo de movimiento según el partner."""
        for order in self:
            # Si el partner tiene un tipo de movimiento configurado, usarlo
            if order.partner_id and order.partner_id.silicie_movement_type:
                order.silicie_movement_type = order.partner_id.silicie_movement_type
            # Si no hay valor en el partner, usar el valor por defecto (A08)
            elif not order.silicie_movement_type:
                order.silicie_movement_type = 'A08'
