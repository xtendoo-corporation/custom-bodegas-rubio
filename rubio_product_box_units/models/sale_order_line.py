from odoo import api, fields, models

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    boxes = fields.Float(
        string='Cajas',
        digits='Product Unit of Measure',
        default=1.0,
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

    def _prepare_invoice_line(self, **optional_values):
        """Sobrescribe para pasar el valor de cajas a la línea de factura"""
        values = super()._prepare_invoice_line(**optional_values)
        values.update({
            'boxes': self.boxes,
        })
        return values
