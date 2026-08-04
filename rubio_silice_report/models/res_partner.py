# -*- coding: utf-8 -*-

from odoo import models, fields
from . import silicie_specs


class ResPartner(models.Model):
    _inherit = 'res.partner'

    silicie_movement_type = fields.Selection(
        selection=lambda self: silicie_specs.get_movement_type_choices(),
        string='Tipo de Movimiento SILICIE',
        help='Tipo de movimiento SILICIE que se aplicará por defecto a este cliente/proveedor en las exportaciones.',
    )
    silicie_document_type = fields.Selection(
        selection=[('1', '1. NIF o NIE Español'), ('2', '2. Intracomunitario'), ('3', '3. Otros'), ('4', '4. Aduanas')],
        string='Tipo Documento Identificativo',
        help='Tipo de documento identificativo para SILICIE: 1 - 4 .'
    )
    cae_seed_number = fields.Char(
        string='CAE/Numero SEED',
        help='Número CAE o SEED para SILICIE. Rellenar manualmente si aplica.'
    )
    silicie_regimen_fiscal = fields.Selection(
        selection=[('2', '2. Suspensivo'), ('3', '3. Excento'), ('4', '4. Imp. Devengado'), ('6', '6. Imp. Devengado Canarias')],
        string='Régimen Fiscal SILICIE',
        help='Selecciona el régimen fiscal para SILICIE: 3 o 4.'
    )
