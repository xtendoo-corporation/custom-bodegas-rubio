# -*- coding: utf-8 -*-

import json
import base64
from datetime import datetime, time
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from ..models import silicie_specs
import pytz


class SiliceReportWizard(models.TransientModel):
    _name = 'silice.report.wizard'
    _description = 'Wizard de Exportación SILICIE 2.0'

    date_start = fields.Datetime(
        string='Fecha Inicio',
        required=True,
        default=fields.Datetime.now,
    )

    date_end = fields.Datetime(
        string='Fecha Fin',
        required=True,
        default=fields.Datetime.now,
    )

    csv_profile = fields.Selection(
        selection=[('IESA1CSV', 'Alcohol (IESA1CSV)')],
        string='Perfil CSV SILICIE',
        required=True,
        default='IESA1CSV',
        help='Solo se permite Alcohol para la exportación SILICIE.',
    )

    movement_type = fields.Selection(
        selection=lambda self: silicie_specs.get_movement_type_choices(),
        string='Tipo de Movimiento',
        required=True,
        help='Tipo de movimiento SILICIE para las salidas',
    )

    @api.model
    def default_get(self, fields_list):
        """Cargar valores por defecto desde configuración."""
        res = super().default_get(fields_list)
        ICP = self.env['ir.config_parameter'].sudo()

        if 'csv_profile' in fields_list:
            profile = ICP.get_param('rubio_silice_report.silicie_csv_profile')
            if profile:
                res['csv_profile'] = profile

        if 'movement_type' in fields_list:
            mov_type = ICP.get_param('rubio_silice_report.silicie_default_movement_type')
            if mov_type:
                res['movement_type'] = mov_type

        return res

    def _validate_configuration(self):
        """Valida que la configuración SILICIE esté completa."""
        ICP = self.env['ir.config_parameter'].sudo()

        cae = ICP.get_param('rubio_silice_report.silicie_cae')
        if not cae:
            raise UserError(_(
                'Debe configurar el CAE en:\n'
                'Ajustes → Inventario → SILICIE'
            ))

        silicie_specs.validate_cae(cae)
        return True

    def _validate_dates(self):
        """Valida y normaliza el rango de fechas."""
        if self.date_start > self.date_end:
            raise UserError(_('La fecha de inicio debe ser anterior a la fecha de fin.'))

        # Normalizar a inicio/fin del día en zona horaria de compañía
        ICP = self.env['ir.config_parameter'].sudo()
        tz_name = ICP.get_param('rubio_silice_report.silicie_date_tz', 'Europe/Madrid')
        tz = pytz.timezone(tz_name)

        # Convertir a zona horaria local
        date_start_local = pytz.utc.localize(self.date_start).astimezone(tz)
        date_end_local = pytz.utc.localize(self.date_end).astimezone(tz)

        # Normalizar a 00:00:00 y 23:59:59
        date_start_normalized = tz.localize(
            datetime.combine(date_start_local.date(), time.min)
        ).astimezone(pytz.utc).replace(tzinfo=None)

        date_end_normalized = tz.localize(
            datetime.combine(date_end_local.date(), time.max)
        ).astimezone(pytz.utc).replace(tzinfo=None)

        return date_start_normalized, date_end_normalized

    def _get_pickings(self, date_start, date_end):
        """Busca los pickings de salida en el rango de fechas (solo los realizados)."""
        domain = [
            ('picking_type_code', '=', 'outgoing'),
            ('state', '=', 'done'),
            ('date_done', '>=', date_start),
            ('date_done', '<=', date_end),
        ]
        pickings = self.env['stock.picking'].search(domain, order='date_done, scheduled_date')
        return pickings

    def _get_silice_number(self, picking):
        """Obtiene el número de sílice del picking."""
        # Usar directamente el campo silice_sequence del picking
        silice_number = picking.silice_sequence or ''
        return str(silice_number).strip()

    def _determine_movement_type(self, picking):
        """
        Determina el tipo de movimiento SILICIE según destino.
        Por defecto: interior=A08, UE=A10, exportación=A11
        """
        # Usar el tipo configurado en el wizard como base
        movement_type = self.movement_type

        # Intentar determinar automáticamente según país destino
        partner = picking.partner_id
        if partner and partner.country_id:
            country_code = partner.country_id.code

            # España = territorio interior
            if country_code == 'ES':
                movement_type = 'A08'
            # UE
            elif partner.country_id.id in self.env.ref('base.europe').country_ids.ids:
                movement_type = 'A10'
            # Resto del mundo = exportación
            else:
                movement_type = 'A11'

        return movement_type

    def _get_product_mapping(self, product_id):
        """Obtiene los datos SILICIE del producto directamente desde sus campos."""
        product = self.env['product.product'].browse(product_id)

        # Si no tiene configuración SILICIE, retornar None
        if not product.silicie_codigo_producto:
            return None

        return {
            'codigo_producto': product.silicie_codigo_producto,
            'unidad_medida': product.silicie_unidad_medida or 'UN',
            'graduacion': str(product.silicie_graduacion) if product.silicie_graduacion else '',
            'numero_silice': product.numero_silice or '',
        }

    def _build_csv_rows(self, pickings):
        """Construye las filas de datos para el CSV SILICIE."""
        ICP = self.env['ir.config_parameter'].sudo()
        cae = ICP.get_param('rubio_silice_report.silicie_cae', '')
        establishment_type = ICP.get_param('rubio_silice_report.silicie_establishment_type', '')
        default_um = ICP.get_param('rubio_silice_report.silicie_default_um', 'LTS')

        fecha_presentacion = datetime.now()
        rows_data = []
        missing_products = set()

        for picking in pickings:
            fecha_asiento = picking.date_done or picking.scheduled_date
            if not fecha_asiento:
                continue
            movement_type = self._determine_movement_type(picking)
            partner = picking.partner_id
            destino_nif = partner.vat or ''
            destino_nombre = partner.name or ''
            destino_direccion = partner.contact_address or ''
            destino_pais = partner.country_id.code if partner.country_id else 'ES'
            num_justificante = picking.origin or picking.name
            tipo_justificante = 'AL'
            # Obtener número de sílice del picking usando el método existente
            silice_number_base = self._get_silice_number(picking) or picking.name

            for line_index, move_line in enumerate(picking.move_line_ids.filtered(lambda ml: ml.quantity > 0)):
                product = move_line.product_id
                product_mapping = self._get_product_mapping(product.id)
                if not product_mapping:
                    missing_products.add(f"{product.id} - {product.display_name}")
                    continue
                numero_silice = f"{silice_number_base}-{line_index+1}"
                # Cambiar referencia_interna para usar silice_number_base en lugar de picking.name
                referencia_interna = f"{silice_number_base}-{line_index+1}"
                cantidad = move_line.quantity if move_line.quantity is not None else 0.0

                # Construir fila directamente campo a campo en el orden exacto del CSV
                row_data = {
                    'referencia_interna': referencia_interna,
                    'fecha_movimiento': fecha_asiento,
                    'fecha_registro_contable': fecha_presentacion,
                    'tipo_movimiento': movement_type,
                    'numero_silice': product_mapping.get('numero_silice', ''),  # Usar numero_silice del producto
                    'cae': cae,
                    'destino_nif': destino_nif,
                    'destino_nombre': destino_nombre,
                    'destino_direccion': destino_direccion,
                    'destino_pais': destino_pais,
                    'tipo_justificante': tipo_justificante,
                    'num_justificante': num_justificante,
                    'unidad_medida': product_mapping.get('unidad_medida', default_um),
                    'fecha_asiento': fecha_asiento,
                    'tipo_establecimiento': establishment_type,
                    'fecha_presentacion': fecha_presentacion,
                    'codigo_producto': product_mapping.get('codigo_producto', ''),
                    'graduacion': product_mapping.get('graduacion', ''),
                    'cantidad': cantidad,
                }

                rows_data.append(row_data)

        if missing_products:
            raise UserError(_(
                'Los siguientes productos no tienen configuración SILICIE completa:\n\n%s\n\n'
                'Configure los campos SILICIE directamente en cada producto:\n'
                'Inventario → Productos → [Producto] → Pestaña "SILICIE"'
            ) % '\n'.join(sorted(missing_products)))
        return rows_data

    def _generate_filename(self):
        """Genera el nombre del fichero CSV."""
        ICP = self.env['ir.config_parameter'].sudo()
        cae = ICP.get_param('rubio_silice_report.silicie_cae', 'CAE')

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{cae}_{self.csv_profile}_{timestamp}.csv"

        return filename

    def action_export_csv(self):
        """Ejecuta la exportación del CSV SILICIE."""
        self.ensure_one()

        # Validaciones previas
        self._validate_configuration()
        date_start, date_end = self._validate_dates()

        # Validar tipo de movimiento
        silicie_specs.validate_movement_type(self.movement_type)

        # Obtener pickings
        pickings = self._get_pickings(date_start, date_end)

        if not pickings:
            raise UserError(_(
                'No se encontraron entregas en el rango de fechas seleccionado.\n'
                'Fecha inicio: %s\n'
                'Fecha fin: %s'
            ) % (date_start, date_end))

        # Construir filas CSV
        rows_data = self._build_csv_rows(pickings)

        if not rows_data:
            raise UserError(_(
                'No se generaron datos para exportar.\n'
                'Verifique que los pickings tengan:\n'
                '- Número de sílice configurado\n'
                '- Productos con mapeo SILICIE\n'
                '- Cantidades realizadas > 0'
            ))

        # Generar CSV
        try:
            csv_content = silicie_specs.generate_csv_content(
                rows_data,
                include_header=True
            )
        except ValidationError as e:
            raise UserError(_(
                'Error al generar el CSV:\n%s'
            ) % str(e))

        # Crear attachment para descarga
        filename = self._generate_filename()
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(csv_content),
            'mimetype': 'text/csv',
            'res_model': self._name,
            'res_id': self.id,
        })

        # Log de la exportación
        self.env['ir.logging'].sudo().create({
            'name': 'SILICIE Export',
            'type': 'server',
            'dbname': self.env.cr.dbname,
            'level': 'INFO',
            'message': f'Exportación SILICIE realizada: {len(rows_data)} registros, '
                      f'perfil {self.csv_profile}, fichero {filename}',
            'path': 'rubio_silice_report',
            'func': 'action_export_csv',
            'line': '1',
        })

        # Retornar acción de descarga
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
