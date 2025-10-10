from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to update boxes and box_units in moves from sale order lines"""
        pickings = super(StockPicking, self).create(vals_list)

        for picking in pickings:
            picking._update_moves_boxes_from_sale()

        return pickings

    def write(self, vals):
        """Override write to update boxes and box_units when moves are added"""
        res = super(StockPicking, self).write(vals)

        # Si se actualizaron los movimientos, actualizar boxes y box_units
        if 'move_ids_without_package' in vals or 'move_ids' in vals:
            for picking in self:
                picking._update_moves_boxes_from_sale()

        return res

    def action_confirm(self):
        """Override action_confirm to update boxes and box_units after moves are confirmed"""
        res = super(StockPicking, self).action_confirm()

        # Actualizar boxes y box_units después de confirmar
        for picking in self:
            picking._update_moves_boxes_from_sale()

        return res

    def _update_moves_boxes_from_sale(self):
        """Update boxes and box_units in moves from related sale order lines"""
        self.ensure_one()

        # Solo procesar si viene de un pedido de venta
        if not self.sale_id:
            return

        # Iterar sobre los movimientos del albarán usando move_ids_without_package
        for move in self.move_ids_without_package:
            # Buscar la línea de pedido correspondiente
            if move.sale_line_id:
                # Actualizar los valores desde la línea de pedido
                move.boxes = move.sale_line_id.boxes
                move.box_units = move.sale_line_id.box_units
