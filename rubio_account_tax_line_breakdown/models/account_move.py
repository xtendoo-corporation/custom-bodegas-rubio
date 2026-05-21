# Copyright 2025 Bodegas Rubio
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import api, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('invoice_line_ids', 'invoice_line_ids.tax_ids', 'invoice_line_ids.price_subtotal')
    def _compute_tax_by_line(self):
        """Group tax information by line for reporting"""
        for move in self:
            # This method helps organize tax data for reports
            pass

