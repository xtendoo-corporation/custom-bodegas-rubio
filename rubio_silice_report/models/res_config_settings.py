# -*- coding: utf-8 -*-

from odoo import models, fields, api
from . import silicie_specs


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Parámetros SILICIE persistentes vía ir.config_parameter
    silicie_cae = fields.Char(
        string='CAE (Código de Actividad Empresarial)',
        help='Código de Actividad Empresarial del establecimiento SILICIE',
        config_parameter='rubio_silice_report.silicie_cae',
    )

    silicie_establishment_type = fields.Selection(
        selection=lambda self: silicie_specs.get_establishment_type_choices(),
        string='Tipo de Establecimiento',
        help='Tipo de establecimiento según tablas SILICIE',
        config_parameter='rubio_silice_report.silicie_establishment_type',
    )

    silicie_group = fields.Selection(
        selection=[
            ('hidrocarburos', 'Hidrocarburos'),
            ('tabaco', 'Tabaco / LCE'),
            ('alcohol', 'Alcohol y Bebidas Alcohólicas'),
        ],
        string='Grupo Impositivo SILICIE',
        help='Grupo impositivo para determinar el perfil de fichero CSV',
        config_parameter='rubio_silice_report.silicie_group',
    )

    silicie_csv_profile = fields.Selection(
        selection=lambda self: silicie_specs.get_profile_choices(),
        string='Perfil CSV de Importación',
        help='Perfil de importación por fichero SILICIE 2.0 (ej: IESH1CSV, IEST1CSV...)',
        config_parameter='rubio_silice_report.silicie_csv_profile',
    )

    silicie_date_tz = fields.Char(
        string='Zona Horaria',
        help='Zona horaria para formateo de fechas (ej: Europe/Madrid)',
        config_parameter='rubio_silice_report.silicie_date_tz',
        default='Europe/Madrid',
    )

    silice_field_name = fields.Char(
        string='Campo Número de Sílice',
        help='Nombre del campo en stock.picking que contiene el número de sílice',
        config_parameter='rubio_silice_report.silice_field_name',
        default='x_silice_number',
    )

    silicie_default_um = fields.Selection(
        selection=lambda self: silicie_specs.get_unit_measure_choices(),
        string='Unidad de Medida por Defecto',
        help='Unidad de medida estandarizada SILICIE para cantidades',
        config_parameter='rubio_silice_report.silicie_default_um',
        default='LTS',
    )

    silicie_product_mapping_json = fields.Char(
        string='Mapeo de Productos (JSON)',
        help='Mapeo desde productos Odoo → identificación producto SILICIE\n'
             'Formato: {"product_id": {"codigo_producto": "X", "tipo_producto": "Y", ...}}',
        config_parameter='rubio_silice_report.silicie_product_mapping_json',
        default='{}',
    )

    silicie_default_movement_type = fields.Selection(
        selection=lambda self: silicie_specs.get_movement_type_choices(),
        string='Tipo de Movimiento por Defecto',
        help='Tipo de movimiento SILICIE por defecto para salidas (A08, A10, A11...)',
        config_parameter='rubio_silice_report.silicie_default_movement_type',
        default='A08',
    )

    silicie_codigo_epigrafe = fields.Char(
        string='Código Epígrafe',
        help='Código epígrafe SILICIE de la empresa (ej: A3 para bebidas espirituales)',
        config_parameter='rubio_silice_report.silicie_codigo_epigrafe',
        default='A3',
    )
