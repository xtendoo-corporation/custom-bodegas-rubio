# Copyright 2026 Bodegas Rubio
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from datetime import datetime, time

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class ManualLotTraceabilityWizard(models.TransientModel):
	_name = "manual.lot.traceability.wizard"
	_description = "Asistente de trazabilidad de lotes manuales"

	date_from = fields.Date(string="Fecha desde")
	date_to = fields.Date(string="Fecha hasta")
	product_id = fields.Many2one("product.product", string="Producto")
	lot_number = fields.Char(string="Numero de lote")

	def _get_domain(self):
		self.ensure_one()
		domain = [
			("display_type", "=", False),
			("manual_lot", "!=", False),
			("manual_lot", "!=", ""),
		]
		if self.date_from:
			domain.append(
				(
					"order_date",
					">=",
					fields.Datetime.to_string(datetime.combine(self.date_from, time.min)),
				)
			)
		if self.date_to:
			domain.append(
				(
					"order_date",
					"<=",
					fields.Datetime.to_string(datetime.combine(self.date_to, time.max)),
				)
			)
		if self.product_id:
			domain.append(("product_id", "=", self.product_id.id))
		lot_value = (self.lot_number or "").strip()
		if lot_value:
			domain.append(("manual_lot", "ilike", lot_value))
		return domain

	def action_open_report(self):
		self.ensure_one()
		if self.date_from and self.date_to and self.date_from > self.date_to:
			raise ValidationError(
				_("La fecha inicial no puede ser posterior a la fecha final.")
			)

		action = self.env.ref(
			"rubio_product_manual_lote.action_manual_lot_traceability_report"
		).read()[0]
		action["domain"] = self._get_domain()
		return action

