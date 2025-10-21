# -*- coding: utf-8 -*-

from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    numero_justificante = fields.Char(
        string='Número Justificante',
        help='Número Justificante que se debe introducir manualmente en el albarán.'
    )

    observaciones_entrega = fields.Text(
        string='Observaciones',
        help='Observaciones adicionales para la entrega.'
    )
    num_documento_identificativo = fields.Char(
        string='Número Documento Identificativo',
        help='Número de documento identificativo para el CSV SILICIE'
    )

