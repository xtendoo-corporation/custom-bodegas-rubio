# Copyright 2025 Bodegas Rubio
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    tax_breakdown_display = fields.Char(
        string='Desglose impuestos',
        compute='_compute_tax_breakdown_display',
        help='Importe de cada impuesto aplicado en la linea.',
    )

    @api.depends('taxes_id', 'price_unit', 'product_qty', 'discount', 'currency_id', 'product_id', 'order_id.partner_id')
    def _compute_tax_breakdown_display(self):
        for line in self:
            parts = []
            partner = line.order_id.partner_id
            for tax in line.taxes_id:
                taxes_res = tax.compute_all(
                    line.price_unit * (1 - (line.discount or 0.0) / 100.0),
                    currency=line.currency_id,
                    quantity=line.product_qty,
                    product=line.product_id,
                    partner=partner,
                )
                amount = sum(t.get('amount', 0.0) for t in taxes_res.get('taxes', []))
                parts.append(f"{tax.display_name}: {amount:.4f}")
            line.tax_breakdown_display = ' | '.join(parts)

