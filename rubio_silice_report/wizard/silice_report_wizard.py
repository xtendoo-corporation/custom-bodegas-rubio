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

    include_not_done = fields.Boolean(
        string='Incluir Programados',
        default=False,
        help='Incluir pickings programados (scheduled_date) si date_done es nulo',
    )

    csv_profile = fields.Selection(
        selection=lambda self: silicie_specs.get_profile_choices(),
        string='Perfil CSV SILICIE',
        required=True,
        help='Perfil de importación por fichero SILICIE 2.0',
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

        if not self.csv_profile:
            raise UserError(_('Debe seleccionar un perfil CSV SILICIE.'))

        if self.csv_profile not in silicie_specs.SILICIE_PROFILES:
            raise UserError(_(
                'Perfil CSV "%s" no encontrado en las especificaciones.'
            ) % self.csv_profile)

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
        """Busca los pickings de salida en el rango de fechas."""
        domain = [
            ('picking_type_code', '=', 'outgoing'),
            ('state', 'in', ['done', 'assigned']),
        ]

        if self.include_not_done:
            # Incluir done + programados
            domain = [
                ('picking_type_code', '=', 'outgoing'),
                '|',
                '&', ('state', '=', 'done'),
                     ('date_done', '>=', date_start),
                     ('date_done', '<=', date_end),
                '&', ('state', '=', 'assigned'),
                     ('scheduled_date', '>=', date_start),
                     ('scheduled_date', '<=', date_end),
            ]
        else:
            # Solo done con date_done
            domain.extend([
                ('state', '=', 'done'),
                ('date_done', '>=', date_start),
                ('date_done', '<=', date_end),
            ])

        pickings = self.env['stock.picking'].search(domain, order='date_done, scheduled_date')
        return pickings

    def _get_silice_number(self, picking):
        """Obtiene el número de sílice del picking."""
        ICP = self.env['ir.config_parameter'].sudo()
        field_name = ICP.get_param('rubio_silice_report.silice_field_name', 'x_silice_number')

        silice_number = getattr(picking, field_name, '') or ''
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
        """Obtiene el mapeo SILICIE del producto desde configuración JSON."""
        ICP = self.env['ir.config_parameter'].sudo()
        mapping_json = ICP.get_param('rubio_silice_report.silicie_product_mapping_json', '{}')

        try:
            mapping = json.loads(mapping_json)
        except json.JSONDecodeError:
            mapping = {}

        product_key = str(product_id)
        if product_key not in mapping:
            return None

        return mapping[product_key]

    def _build_csv_rows(self, pickings):
        """Construye las filas CSV desde los pickings."""
        ICP = self.env['ir.config_parameter'].sudo()

        # Obtener parámetros de configuración
        cae = ICP.get_param('rubio_silice_report.silicie_cae', '')
        establishment_type = ICP.get_param('rubio_silice_report.silicie_establishment_type', '')
        default_um = ICP.get_param('rubio_silice_report.silicie_default_um', 'LTS')

        profile = silicie_specs.SILICIE_PROFILES.get(self.csv_profile)
        version = profile.get('version', '1.0')

        fecha_presentacion = datetime.now()

        rows_data = []
        missing_products = set()

        for picking in pickings:
            silice_number = self._get_silice_number(picking)

            # Fecha del asiento: date_done o scheduled_date
            fecha_asiento = picking.date_done or picking.scheduled_date
            if not fecha_asiento:
                continue

            movement_type = self._determine_movement_type(picking)

            # Datos de destino
            partner = picking.partner_id
            destino_nif = partner.vat or ''
            destino_nombre = partner.name or ''
            destino_direccion = partner.contact_address or ''
            destino_pais = partner.country_id.code if partner.country_id else 'ES'

            # Justificante (usar origin como num_justificante)
            num_justificante = picking.origin or picking.name
            tipo_justificante = 'AL'  # Albarán por defecto

            # Procesar líneas de movimiento
            for move_line in picking.move_line_ids.filtered(lambda ml: ml.qty_done > 0):
                product = move_line.product_id

                # Obtener mapeo del producto
                product_mapping = self._get_product_mapping(product.id)
                if not product_mapping:
                    missing_products.add(f"{product.id} - {product.display_name}")
                    continue

                # Construir fila según perfil
                row_data = {
                    'numero_silice': silice_number,
                    'cae': cae,
                    'tipo_establecimiento': establishment_type,
                    'fecha_presentacion': fecha_presentacion,
                    'version_fichero': version,
                    'fecha_asiento': fecha_asiento,
                    'tipo_movimiento': movement_type,
                    'codigo_producto': product_mapping.get('codigo_producto', ''),
                    'tipo_producto': product_mapping.get('tipo_producto', ''),
                    'cantidad': move_line.qty_done,
                    'unidad_medida': product_mapping.get('unidad_medida', default_um),
                    'destino_nif': destino_nif,
                    'destino_nombre': destino_nombre,
                    'destino_direccion': destino_direccion,
                    'destino_pais': destino_pais,
                    'num_justificante': num_justificante,
                    'tipo_justificante': tipo_justificante,
                    'observaciones': picking.note or '',
                }

                # Campos específicos según perfil/grupo
                if self.csv_profile == 'IESH1CSV':  # Hidrocarburos
                    row_data['densidad'] = product_mapping.get('densidad', '')
                    row_data['temperatura'] = product_mapping.get('temperatura', '')
                elif self.csv_profile == 'IEST1CSV':  # Tabaco
                    row_data['marca_comercial'] = product_mapping.get('marca_comercial', '')
                    row_data['precio_venta'] = product_mapping.get('precio_venta', '')
                elif self.csv_profile == 'IESA1CSV':  # Alcohol
                    row_data['graduacion'] = product_mapping.get('graduacion', '')

                rows_data.append(row_data)

        if missing_products:
            raise UserError(_(
                'Los siguientes productos no tienen mapeo SILICIE configurado:\n\n%s\n\n'
                'Configure el mapeo en: Ajustes → Inventario → SILICIE → Mapeo de Productos'
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
                profile_key=self.csv_profile,
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

