# -*- coding: utf-8 -*-

from odoo import models, fields
from . import silicie_specs


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_movement_type = fields.Selection(
        selection=lambda self: silicie_specs.get_movement_type_choices(),
        string='Tipo de Movimiento SILICIE',
        help='Tipo de movimiento SILICIE que se aplicará por defecto a este cliente/proveedor en las exportaciones.',
    )
