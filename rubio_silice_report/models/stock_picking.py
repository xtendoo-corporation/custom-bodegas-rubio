# -*- coding: utf-8 -*-

from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    silicie_movement_type = fields.Selection(
        string='Tipo de Movimiento SILICIE',
        help='Tipo de movimiento SILICIE para esta entrega',
        related='sale_id.silicie_movement_type',
        store=True,
        readonly=True,
    )
