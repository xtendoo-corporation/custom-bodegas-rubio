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

    def button_validate(self):
        for picking in self:
            if not picking.silice_sequence and picking.picking_type_code == 'outgoing':
                sequence = self.env["ir.sequence"].with_company(
                    picking.company_id.id
                ).next_by_code("rubio.stock.picking.silice")
                if sequence:
                    picking.silice_sequence = sequence
        return super().button_validate()
