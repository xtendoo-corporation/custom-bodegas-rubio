from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    silice_sequence = fields.Char(
        string="Secuencia Silíce",
        copy=False,
        readonly=True,
        index=True,
        help="Número de secuencia Silíce asignado automáticamente al validar el albarán",
    )

    def button_validate(self):
        """
        Override button_validate to assign Silíce sequence before validation.

        This method assigns the next sequence number from 'rubio.stock.picking.silice'
        to pickings that don't have a value in silice_sequence yet.

        The assignment is:
        - Idempotent: won't reassign if already exists
        - Multi-company aware: uses the picking's company_id
        - Batch-safe: handles multiple pickings correctly
        """
        # Assign sequence to pickings that don't have it yet
        for picking in self:
            if not picking.silice_sequence:
                sequence = self.env["ir.sequence"].with_company(
                    picking.company_id.id
                ).next_by_code("rubio.stock.picking.silice")
                if sequence:
                    picking.silice_sequence = sequence

        # Call parent method to perform standard validation
        return super().button_validate()
