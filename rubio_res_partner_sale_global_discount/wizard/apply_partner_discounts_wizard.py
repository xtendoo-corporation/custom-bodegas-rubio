from odoo import models, fields, api
from odoo.exceptions import UserError


class ApplyPartnerDiscountsWizard(models.TransientModel):
    _name = 'apply.partner.discounts.wizard'
    _description = 'Wizard para aplicar descuentos del cliente'

    sale_order_id = fields.Many2one('sale.order', string='Pedido de Venta', required=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', related='sale_order_id.partner_id')
    discount_summary = fields.Html(string='Resumen de Descuentos', readonly=True)
    total_discount_amount = fields.Monetary(string='Total Descuento', readonly=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='sale_order_id.currency_id')
    base_amount = fields.Monetary(string='Importe Base', readonly=True, currency_field='currency_id')

    @api.model
    def default_get(self, fields_list):
        """Cargar datos por defecto del pedido de venta"""
        defaults = super().default_get(fields_list)

        if self.env.context.get('active_model') == 'sale.order' and self.env.context.get('active_id'):
            sale_order = self.env['sale.order'].browse(self.env.context['active_id'])
            defaults['sale_order_id'] = sale_order.id

            # Calcular información de descuentos
            if sale_order.partner_id and sale_order.partner_id.has_global_discounts:
                base_amount = sale_order._get_base_amount_for_partner_discounts()
                defaults['base_amount'] = base_amount

                if base_amount > 0:
                    doc_type = 'quotation' if sale_order.state in ['draft', 'sent'] else 'sale_order'
                    applicable_discounts = sale_order.partner_id.get_applicable_discounts(
                        doc_type, base_amount, sale_order.date_order.date() if sale_order.date_order else None
                    )

                    if applicable_discounts:
                        # Calcular resumen
                        total_discount = 0
                        discount_lines = []
                        temp_base = base_amount

                        for discount in applicable_discounts:
                            discount_amount = discount.calculate_discount_amount(temp_base)
                            total_discount += discount_amount
                            discount_lines.append({
                                'name': discount.name,
                                'type': 'Porcentaje' if discount.discount_type == 'percentage' else 'Importe Fijo',
                                'value': f"{discount.discount_value}%" if discount.discount_type == 'percentage' else f"{discount.discount_value} {sale_order.currency_id.symbol}",
                                'amount': discount_amount,
                                'base': temp_base
                            })
                            temp_base -= discount_amount

                        defaults['total_discount_amount'] = total_discount

                        # Generar HTML del resumen
                        html_summary = self._generate_discount_summary_html(discount_lines, sale_order.currency_id)
                        defaults['discount_summary'] = html_summary

        return defaults

    def _generate_discount_summary_html(self, discount_lines, currency):
        """Genera el HTML para mostrar el resumen de descuentos"""
        html = """
        <div style="margin: 10px 0;">
            <h4>Descuentos a aplicar:</h4>
            <table class="table table-sm table-striped">
                <thead>
                    <tr>
                        <th>Descuento</th>
                        <th>Tipo</th>
                        <th>Valor</th>
                        <th>Base</th>
                        <th>Importe</th>
                    </tr>
                </thead>
                <tbody>
        """

        for line in discount_lines:
            html += f"""
                <tr>
                    <td>{line['name']}</td>
                    <td>{line['type']}</td>
                    <td>{line['value']}</td>
                    <td>{line['base']:.2f} {currency.symbol}</td>
                    <td><strong>{line['amount']:.2f} {currency.symbol}</strong></td>
                </tr>
            """

        html += """
                </tbody>
            </table>
        </div>
        """
        return html

    def action_apply_discounts(self):
        """Aplica los descuentos al pedido de venta"""
        self.ensure_one()

        if not self.sale_order_id:
            raise UserError('No se ha encontrado el pedido de venta.')

        sale_order = self.sale_order_id

        # Aplicar descuentos usando el método existente
        if not sale_order.partner_id:
            raise UserError('Debe seleccionar un cliente antes de aplicar descuentos.')

        if not sale_order.partner_id.has_global_discounts:
            raise UserError('Este cliente no tiene descuentos globales configurados.')

        # Calcular el subtotal base
        base_amount = sale_order._get_base_amount_for_partner_discounts()

        if base_amount <= 0:
            raise UserError('No hay importe base para aplicar descuentos.')

        # Determinar el tipo de documento
        doc_type = 'quotation' if sale_order.state in ['draft', 'sent'] else 'sale_order'

        # Obtener descuentos aplicables del cliente
        applicable_discounts = sale_order.partner_id.get_applicable_discounts(
            doc_type, base_amount, sale_order.date_order.date() if sale_order.date_order else None
        )

        if not applicable_discounts:
            raise UserError('No hay descuentos aplicables para este pedido.')

        # Limpiar descuentos anteriores del cliente
        sale_order._remove_partner_discount_lines()

        # Aplicar cada descuento
        total_discount_applied = 0
        discount_details = []

        for discount in applicable_discounts:
            discount_amount = sale_order._apply_partner_discount(discount, base_amount)
            total_discount_applied += discount_amount
            base_amount -= discount_amount

            discount_details.append({
                'name': discount.name,
                'amount': discount_amount,
                'type': discount.discount_type,
                'value': discount.discount_value
            })

        sale_order.partner_global_discounts_applied = True

        # Registrar en el chatter
        self._log_discount_application(sale_order, discount_details, total_discount_applied)

        # Retornar acción para recargar el formulario
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
            'context': {
                'default_partner_global_discounts_applied': True,
            }
        }

    def _log_discount_application(self, sale_order, discount_details, total_amount):
        """Registra la aplicación de descuentos en el chatter"""
        user_name = self.env.user.name
        currency_symbol = sale_order.currency_id.symbol

        # Crear mensaje usando formato texto plano con saltos de línea
        message_parts = []
        message_parts.append(f"{user_name} ha aplicado descuentos del cliente por un total de {currency_symbol}{total_amount:.2f}")
        message_parts.append("")  # Línea vacía
        message_parts.append("Descuentos aplicados:")

        for discount in discount_details:
            discount_type_text = "Porcentaje" if discount['type'] == 'percentage' else "Importe Fijo"
            value_text = f"{discount['value']}%" if discount['type'] == 'percentage' else f"{currency_symbol}{discount['value']}"

            message_parts.append(f"• {discount['name']} ({discount_type_text}: {value_text}) - Descuento: {currency_symbol}{discount['amount']:.2f}")

        # Unir con saltos de línea
        message_body = "\n".join(message_parts)

        # Enviar mensaje al chatter
        sale_order.message_post(
            body=message_body,
            subject="Descuentos del Cliente Aplicados",
            message_type='comment',
            subtype_xmlid='mail.mt_note'
        )

    def action_cancel(self):
        """Cancela el wizard sin aplicar descuentos"""
        return {'type': 'ir.actions.act_window_close'}
