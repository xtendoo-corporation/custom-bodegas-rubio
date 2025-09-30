from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Campo para marcar si se han aplicado descuentos del cliente
    partner_global_discounts_applied = fields.Boolean(
        string='Descuentos del Cliente Aplicados',
        default=False,
        help="Indica si se han aplicado descuentos globales configurados en el cliente",
        copy=False
    )

    def action_apply_partner_global_discounts(self):
        """
        Abre el wizard para aplicar los descuentos globales configurados en el cliente
        """
        self.ensure_one()

        if self.move_type not in ['out_invoice', 'out_refund']:
            raise UserError('Los descuentos globales solo se pueden aplicar a facturas de cliente.')

        if not self.partner_id:
            raise UserError('Debe seleccionar un cliente antes de aplicar descuentos.')

        if not self.partner_id.has_global_discounts:
            raise UserError('Este cliente no tiene descuentos globales configurados.')

        # Calcular el subtotal base (sin descuentos globales ya aplicados)
        base_amount = self._get_base_amount_for_partner_discounts()

        if base_amount <= 0:
            raise UserError('No hay importe base para aplicar descuentos.')

        # Obtener descuentos aplicables del cliente
        applicable_discounts = self.partner_id.get_applicable_discounts(
            'invoice', base_amount, self.invoice_date or fields.Date.today()
        )

        if not applicable_discounts:
            raise UserError('No hay descuentos aplicables para esta factura.')

        # Abrir el wizard
        return {
            'type': 'ir.actions.act_window',
            'name': 'Aplicar Descuentos del Cliente',
            'res_model': 'apply.partner.discounts.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_account_move_id': self.id,
                'active_model': 'account.move',
                'active_id': self.id,
            }
        }

    def _get_base_amount_for_partner_discounts(self):
        """Calcula el importe base para aplicar descuentos del cliente"""
        # Excluir líneas de descuento y líneas de sección/nota
        normal_lines = self.invoice_line_ids.filtered(
            lambda l: not self._is_line_global_discount(l) and
                     l.display_type not in ['line_section', 'line_note']
        )
        return sum(normal_lines.mapped('price_subtotal'))

    def _is_line_global_discount(self, line):
        """Verifica si una línea es de descuento global"""
        return (hasattr(line, 'is_global_discount') and line.is_global_discount) or \
               (line.price_unit < 0 and 'Descuento' in (line.name or '') and line.product_id)

    def _apply_partner_discount(self, discount_config, base_amount):
        """
        Aplica un descuento individual usando la funcionalidad del módulo account_global_discount
        """
        discount_amount = discount_config.calculate_discount_amount(base_amount)

        if discount_amount > 0:
            # Crear la línea de descuento global usando el método estándar
            self._create_global_discount_line(
                discount_config.name,
                discount_amount,
                discount_config.discount_type,
                discount_config.discount_value
            )

        return discount_amount

    def _create_global_discount_line(self, discount_name, discount_amount, discount_type, discount_value):
        """
        Crea una línea de descuento global usando la funcionalidad estándar
        """
        # Si el módulo account_global_discount tiene un método específico, lo usamos
        if hasattr(self, '_add_global_discount_line'):
            return self._add_global_discount_line(discount_name, discount_amount)

        # Si no, creamos la línea manualmente siguiendo el patrón estándar
        discount_product = self._get_global_discount_product()
        discount_account = self._get_global_discount_account(discount_product)

        line_vals = {
            'move_id': self.id,
            'product_id': discount_product.id,
            'name': f'Descuento Global - {discount_name}',
            'quantity': 1,
            'price_unit': -discount_amount,
            'account_id': discount_account.id,
            'is_global_discount': True,
            'sequence': 999,  # Al final de la factura
        }

        # Agregar campos específicos si existen
        if hasattr(self.env['account.move.line'], 'global_discount_id'):
            line_vals['global_discount_id'] = False

        self.env['account.move.line'].create(line_vals)

    def _get_global_discount_product(self):
        """Obtiene el producto de descuento global del módulo account_global_discount"""
        # Intentar obtener el producto estándar del módulo account_global_discount
        try:
            return self.env.ref('account_global_discount.product_product_global_discount')
        except:
            # Si no existe, intentar el del módulo sale_global_discount
            try:
                return self.env.ref('sale_global_discount.product_product_global_discount')
            except:
                # Si tampoco existe, crear uno compatible
                return self._create_compatible_discount_product()

    def _get_global_discount_account(self, product):
        """Obtiene la cuenta contable para el descuento global"""
        # Usar la cuenta del producto si está configurada
        if product.property_account_income_id:
            return product.property_account_income_id

        # Buscar cuenta de ingresos por defecto de la categoría del producto
        if product.categ_id and product.categ_id.property_account_income_categ_id:
            return product.categ_id.property_account_income_categ_id

        # Buscar cuenta de ingresos genérica
        account = self.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not account:
            # Si no encuentra cuenta de ingresos, buscar cualquier cuenta de tipo income_other
            account = self.env['account.account'].search([
                ('account_type', 'in', ['income_other', 'asset_receivable']),
                ('company_id', '=', self.company_id.id)
            ], limit=1)

        return account

    def _create_compatible_discount_product(self):
        """Crea un producto compatible con los módulos de descuento global"""
        return self.env['product.product'].create({
            'name': 'Global Discount',
            'default_code': 'GLOBAL_DISCOUNT',
            'type': 'service',
            'categ_id': self.env.ref('product.product_category_all').id,
            'list_price': 0.0,
            'sale_ok': True,
            'purchase_ok': False,
            'invoice_policy': 'order',
            'taxes_id': False,
        })

    def _remove_partner_discount_lines(self):
        """Elimina las líneas de descuento del cliente aplicadas anteriormente"""
        # Buscar líneas que sean descuentos globales o que contengan referencia a descuentos del cliente
        discount_lines = self.invoice_line_ids.filtered(
            lambda l: (hasattr(l, 'is_global_discount') and l.is_global_discount) or
                     'Descuento Global' in (l.name or '') or
                     (l.price_unit < 0 and l.product_id)
        )

        if discount_lines:
            discount_lines.unlink()

    @api.onchange('partner_id')
    def _onchange_partner_id_global_discounts(self):
        """Auto-aplicar descuentos del cliente cuando cambie"""
        if (self.move_type in ['out_invoice', 'out_refund'] and
            self.partner_id and
            self.partner_id.has_global_discounts and
            not self.partner_global_discounts_applied):

            # Solo auto-aplicar si hay líneas normales de producto
            normal_lines = self.invoice_line_ids.filtered(
                lambda l: l.product_id and l.display_type not in ['line_section', 'line_note']
            )

            if normal_lines:
                try:
                    self.action_apply_partner_global_discounts()
                except UserError:
                    # Si hay error, no aplicar automáticamente
                    pass


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Campo para marcar líneas de descuento global
    is_global_discount = fields.Boolean(
        string='Es Descuento Global',
        default=False,
        help="Indica si esta línea es un descuento global aplicado desde el cliente"
    )

    def _is_global_discount_line(self):
        """Verifica si la línea es de descuento global"""
        return self.is_global_discount or \
               (self.price_unit < 0 and 'Descuento' in (self.name or '') and self.product_id)
