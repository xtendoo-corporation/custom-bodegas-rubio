from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

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
            self.quantity = self.boxes * self.box_units

    @api.onchange('product_id')
    def _onchange_product_id_box_units(self):
        """Cargar ud/caja cuando cambia el producto"""
        if self.product_id and self.boxes:
            self.box_units = self.product_id.product_tmpl_id.box_units
            self.quantity = self.boxes * self.box_units

    @api.onchange('box_units')
    def _onchange_box_units(self):
        """Actualizar cantidad cuando cambian las ud/caja"""
        if self.box_units and self.boxes:
            self.quantity = self.boxes * self.box_units

    @api.onchange('quantity')
    def _onchange_quantity_boxes(self):
        """Actualizar cajas cuando la cantidad se modifica manualmente"""
        if self.quantity and self.box_units and self.box_units > 0:
            self.boxes = self.quantity / self.box_units

    def _get_aggregated_product_quantities(self, **kwargs):
        """Sobrescribir para añadir boxes y box_units al diccionario agregado"""
        aggregated_move_lines = super()._get_aggregated_product_quantities(**kwargs)

        # Añadir boxes y box_units a cada línea agregada
        for move_line in self:
            if kwargs.get('except_package') and move_line.result_package_id:
                continue

            aggregated_properties = self._get_aggregated_properties(move_line=move_line)
            line_key = aggregated_properties['line_key']

            if line_key in aggregated_move_lines:
                # Obtener boxes y box_units del move_id
                boxes = move_line.move_id.boxes if move_line.move_id else move_line.boxes
                box_units = move_line.move_id.box_units if move_line.move_id else move_line.box_units

                # Si ya existe, sumar las cajas
                if 'boxes' not in aggregated_move_lines[line_key]:
                    aggregated_move_lines[line_key]['boxes'] = boxes
                    aggregated_move_lines[line_key]['box_units'] = box_units
                else:
                    aggregated_move_lines[line_key]['boxes'] += boxes

        return aggregated_move_lines
