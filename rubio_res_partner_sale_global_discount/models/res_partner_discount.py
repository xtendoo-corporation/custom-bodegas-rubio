from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResPartnerDiscount(models.Model):
    _name = 'res.partner.discount'
    _description = 'Descuentos Globales por Cliente'
    _order = 'sequence, name'

    name = fields.Char(
        string='Nombre del Descuento',
        required=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        ondelete='cascade'
    )
    discount_type = fields.Selection([
        ('percentage', 'Porcentaje'),
        ('fixed', 'Importe Fijo')
    ], string='Tipo de Descuento', required=True, default='percentage')

    discount_value = fields.Float(
        string='Valor del Descuento',
        required=True,
        help="Porcentaje (0-100) o importe fijo según el tipo"
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help="Orden de aplicación de los descuentos"
    )

    active = fields.Boolean(
        string='Activo',
        default=True
    )

    date_start = fields.Date(
        string='Fecha Inicio',
        help="Fecha desde la cual el descuento es válido"
    )

    date_end = fields.Date(
        string='Fecha Fin',
        help="Fecha hasta la cual el descuento es válido"
    )

    minimum_amount = fields.Float(
        string='Importe Mínimo',
        default=0.0,
        help="Importe mínimo del pedido/factura para aplicar el descuento"
    )

    apply_to = fields.Selection([
        ('all', 'Todos los Documentos'),
        ('quotation', 'Solo Presupuestos'),
        ('sale_order', 'Solo Pedidos'),
        ('invoice', 'Solo Facturas')
    ], string='Aplicar a', default='all')

    notes = fields.Text(string='Notas')

    @api.constrains('discount_value', 'discount_type')
    def _check_discount_value(self):
        for record in self:
            if record.discount_type == 'percentage':
                if record.discount_value < 0 or record.discount_value > 100:
                    raise ValidationError(
                        "El porcentaje de descuento debe estar entre 0 y 100."
                    )
            elif record.discount_type == 'fixed':
                if record.discount_value < 0:
                    raise ValidationError(
                        "El importe fijo de descuento no puede ser negativo."
                    )

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for record in self:
            if record.date_start and record.date_end:
                if record.date_start > record.date_end:
                    raise ValidationError(
                        "La fecha de inicio no puede ser posterior a la fecha de fin."
                    )

    def is_applicable(self, document_type, amount, date=None):
        """
        Verifica si el descuento es aplicable según los criterios configurados
        """
        self.ensure_one()

        # Verificar si está activo
        if not self.active:
            return False

        # Verificar fechas
        current_date = date or fields.Date.today()
        if self.date_start and current_date < self.date_start:
            return False
        if self.date_end and current_date > self.date_end:
            return False

        # Verificar importe mínimo
        if amount < self.minimum_amount:
            return False

        # Verificar tipo de documento
        if self.apply_to != 'all':
            if self.apply_to != document_type:
                return False

        return True

    def calculate_discount_amount(self, base_amount):
        """
        Calcula el importe de descuento basado en el tipo y valor configurado
        """
        self.ensure_one()

        if self.discount_type == 'percentage':
            return base_amount * (self.discount_value / 100.0)
        else:  # fixed
            return min(self.discount_value, base_amount)
