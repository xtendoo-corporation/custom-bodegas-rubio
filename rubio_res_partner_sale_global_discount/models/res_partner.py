from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    global_discount_ids = fields.One2many(
        'res.partner.discount',
        'partner_id',
        string='Descuentos Globales',
        help="Descuentos que se aplicarán automáticamente en ventas"
    )

    has_global_discounts = fields.Boolean(
        string='Tiene Descuentos Globales',
        compute='_compute_has_global_discounts',
        store=True
    )

    @api.depends('global_discount_ids', 'global_discount_ids.active')
    def _compute_has_global_discounts(self):
        for partner in self:
            partner.has_global_discounts = bool(
                partner.global_discount_ids.filtered('active')
            )

    def get_applicable_discounts(self, document_type, amount, date=None):
        """
        Obtiene los descuentos aplicables para un tipo de documento y importe
        """
        self.ensure_one()
        applicable_discounts = []

        for discount in self.global_discount_ids.filtered('active'):
            if discount.is_applicable(document_type, amount, date):
                applicable_discounts.append(discount)

        return applicable_discounts

    def calculate_total_discount(self, document_type, base_amount, date=None):
        """
        Calcula el descuento total aplicable
        """
        self.ensure_one()
        applicable_discounts = self.get_applicable_discounts(
            document_type, base_amount, date
        )

        total_discount = 0.0
        remaining_amount = base_amount

        # Aplicar descuentos en orden de secuencia
        for discount in applicable_discounts:
            discount_amount = discount.calculate_discount_amount(remaining_amount)
            total_discount += discount_amount
            remaining_amount -= discount_amount

        return total_discount
