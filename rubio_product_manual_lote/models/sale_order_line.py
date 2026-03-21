# Copyright 2026 Bodegas Rubio
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    manual_lot = fields.Char(
        string="Lote Manual",
        help="Campo informativo para indicar el lote manualmente en la linea de pedido",
    )
    order_date = fields.Datetime(
        related="order_id.date_order",
        string="Fecha pedido",
        store=True,
        index=True,
        readonly=True,
    )
    partner_name = fields.Char(
        related="order_partner_id.name",
        string="Nombre cliente",
        readonly=True,
    )
    partner_vat = fields.Char(
        related="order_partner_id.vat",
        string="NIF/CIF",
        readonly=True,
    )
    partner_email = fields.Char(
        related="order_partner_id.email",
        string="Email",
        readonly=True,
    )
    partner_phone = fields.Char(
        related="order_partner_id.phone",
        string="Telefono",
        readonly=True,
    )
    partner_mobile = fields.Char(
        related="order_partner_id.mobile",
        string="Movil",
        readonly=True,
    )
    partner_street = fields.Char(
        related="order_partner_id.street",
        string="Calle",
        readonly=True,
    )
    partner_street2 = fields.Char(
        related="order_partner_id.street2",
        string="Calle 2",
        readonly=True,
    )
    partner_zip = fields.Char(
        related="order_partner_id.zip",
        string="Codigo postal",
        readonly=True,
    )
    partner_city = fields.Char(
        related="order_partner_id.city",
        string="Ciudad",
        readonly=True,
    )
    partner_state_id = fields.Many2one(
        related="order_partner_id.state_id",
        string="Provincia",
        readonly=True,
    )
    partner_country_id = fields.Many2one(
        related="order_partner_id.country_id",
        string="Pais",
        readonly=True,
    )
