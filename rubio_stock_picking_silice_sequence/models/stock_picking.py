from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = "stock.picking"

    silice_sequence = fields.Char(
        string="Silice",
        copy=False,
        readonly=True,
        index=True,
        help="Número de secuencia Silíce asignado automáticamente al validar el albarán de salida",
    )
    silicie_movement_type = fields.Selection(
        selection=[
            ('A08', 'Salida a consumo - territorio interior'),
            ('A09', 'Salida a consumo - Canarias, Ceuta o Melilla'),
            ('A10', 'Salida en régimen suspensivo - UE'),
            ('A11', 'Salida en régimen suspensivo - exportación'),
            ('A12', 'Salida para entrega exenta'),
            ('A13', 'Salida para uso de las fuerzas armadas de un Estado miembro'),
            ('A14', 'Salida para venta a bordo'),
            ('A15', 'Otras salidas'),
            ('A16', 'Salida para destrucción'),
            ('A17', 'Salida a otro depósito fiscal del mismo titular'),
        ],
        string='Tipo de Movimiento SILICIE',
        help='Tipo de movimiento SILICIE para esta entrega.'
    )

    def button_validate(self):
        for picking in self:
            if not picking.silice_sequence and picking.picking_type_code == 'outgoing':
                sequence = self.env["ir.sequence"].with_company(
                    picking.company_id.id
                ).next_by_code("rubio.stock.picking.silice")
                if sequence:
                    picking.silice_sequence = sequence
        return super().button_validate()
