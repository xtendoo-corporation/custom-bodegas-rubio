from odoo import api, fields, models

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

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
            self.quantity = self.boxes * self.box_units

    @api.onchange('product_id')
    def _onchange_product_id_box_units(self):
        """Cargar ud/caja cuando cambia el producto y recalcular si hay cajas"""
        if self.product_id and self.boxes:
            self.box_units = self.product_id.product_tmpl_id.box_units
            self.quantity = self.boxes * self.box_units

    @api.onchange('box_units')
    def _onchange_box_units(self):
        """Actualizar cantidad cuando cambian las ud/caja"""
        if self.box_units:
            self.quantity = self.boxes * self.box_units

    @api.onchange('quantity')
    def _onchange_quantity_boxes(self):
        """Actualizar cajas cuando la cantidad se modifica manualmente"""
        if self.quantity and self.box_units and self.box_units > 0:
            self.boxes = self.quantity / self.box_units
