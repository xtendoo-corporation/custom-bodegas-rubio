# Copyright 2025 Bodegas Rubio
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    tax_breakdown_display = fields.Char(
        string='Desglose impuestos',
        compute='_compute_tax_breakdown_display',
        help='Importe de cada impuesto aplicado en la linea.',
    )

    @api.depends('tax_ids', 'price_unit', 'quantity', 'discount', 'currency_id', 'product_id', 'partner_id')
    def _compute_tax_breakdown_display(self):
        for line in self:
            parts = []
            for tax in line.tax_ids:
                taxes_res = tax.compute_all(
                    line.price_unit * (1 - (line.discount or 0.0) / 100.0),
                    currency=line.currency_id,
                    quantity=line.quantity,
                    product=line.product_id,
                    partner=line.partner_id,
                )
                amount = sum(t.get('amount', 0.0) for t in taxes_res.get('taxes', []))
                parts.append(f"{tax.display_name}: {amount:.4f}")
            line.tax_breakdown_display = ' | '.join(parts)

