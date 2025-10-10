from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    boxes = fields.Float(
        string='Cajas',
        digits='Product Unit of Measure',
        help='Número de cajas para este producto'
    )
    box_units = fields.Float(
        string='Ud/Caja',
        help='Unidades por caja desde la configuración del producto'
    )

    @api.onchange('boxes', 'product_id')
    def _onchange_boxes(self):
        """Calcular cantidad según cajas y ud/caja cuando cambian las cajas"""
        if self.boxes and self.box_units:
            self.product_uom_qty = self.boxes * self.box_units

    @api.onchange('product_id')
    def _onchange_product_id_box_units(self):
        """Cargar ud/caja cuando cambia el producto y recalcular si hay cajas"""
        if self.product_id and self.boxes:
            self.box_units = self.product_id.product_tmpl_id.box_units
            self.product_uom_qty = self.boxes * self.box_units

    @api.onchange('box_units')
    def _onchange_box_units(self):
        """Actualizar cantidad cuando cambian las ud/caja"""
        if self.box_units:
            self.product_uom_qty = self.boxes * self.box_units

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty_boxes(self):
        """Actualizar cajas cuando la cantidad se modifica manualmente"""
        if self.product_uom_qty and self.box_units and self.box_units > 0:
            self.boxes = self.product_uom_qty / self.box_units

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to get boxes and box_units from sale.order.line"""
        moves = super(StockMove, self).create(vals_list)

        # Actualizar los valores después de la creación para evitar conflictos con defaults
        for move in moves:
            if move.sale_line_id:
                move.write({
                    'boxes': move.sale_line_id.boxes,
                    'box_units': move.sale_line_id.box_units,
                })

        return moves

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """Override to add boxes and box_units to move line vals"""
        res = super(StockMove, self)._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        res.update({
            'boxes': self.boxes,
            'box_units': self.box_units,
        })
        return res
