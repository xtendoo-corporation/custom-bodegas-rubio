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

    date_start = fields.Date(
        string='Fecha Inicio',
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
    )

    date_end = fields.Date(
        string='Fecha Fin',
        required=True,
        default=fields.Date.today,
    )

    csv_profile = fields.Selection(
        selection=[('IESA1CSV', 'Alcohol (IESA1CSV)')],
        string='Perfil CSV SILICIE',
        required=True,
        default='IESA1CSV',
        help='Solo se permite Alcohol para la exportación SILICIE.',
    )

    all_movement_types = fields.Boolean(
        string='Todos los tipos de movimiento',
        default=True,
        help='Si está marcado, se incluirán todos los tipos de movimiento en el reporte',
    )

    movement_type = fields.Selection(
        selection=lambda self: silicie_specs.get_movement_type_choices(),
        string='Tipo de Movimiento',
        required=False,
        help='Tipo de movimiento SILICIE para las salidas (solo si no está marcado "Todos")',
    )

    @api.model
    def default_get(self, fields_list):
        """Cargar valores por defecto desde configuración."""
        res = super().default_get(fields_list)
        # Por defecto, marcar "Todos los tipos de movimiento"
        res['all_movement_types'] = True
        return res

    @api.onchange('all_movement_types')
    def _onchange_all_movement_types(self):
        """Cuando se marca/desmarca el checkbox, limpiar el campo movement_type"""
        if self.all_movement_types:
            self.movement_type = False

    def _validate_configuration(self):
        """Valida que la configuración SILICIE esté completa."""
        ICP = self.env['ir.config_parameter'].sudo()

        # Eliminar referencia a cae
        # cae = ICP.get_param('rubio_silice_report.silicie_cae')
        # if not cae:
        #     raise UserError(_(
        #         'Debe configurar el CAE en:\n'
        #         'Ajustes → Inventario → SILICIE'
        #     ))

        # silicie_specs.validate_cae(cae)
        return True

    def _validate_dates(self):
        """Valida y normaliza el rango de fechas."""
        if self.date_start > self.date_end:
            raise UserError(_('La fecha de inicio debe ser anterior a la fecha de fin.'))

        # Normalizar a inicio/fin del día en zona horaria de compañía
        ICP = self.env['ir.config_parameter'].sudo()
        tz_name = ICP.get_param('rubio_silice_report.silicie_date_tz', 'Europe/Madrid')
        tz = pytz.timezone(tz_name)

        # Convertir fecha a datetime con hora 00:00:00 y 23:59:59
        date_start_normalized = tz.localize(
            datetime.combine(self.date_start, time.min)
        ).astimezone(pytz.utc).replace(tzinfo=None)

        date_end_normalized = tz.localize(
            datetime.combine(self.date_end, time.max)
        ).astimezone(pytz.utc).replace(tzinfo=None)

        return date_start_normalized, date_end_normalized

    def _get_pickings(self, date_start, date_end):
        """Busca los pickings de salida en el rango de fechas (solo los realizados)."""
        domain = [
            ('picking_type_code', '=', 'outgoing'),
            ('state', '=', 'done'),
            ('date_done', '>=', date_start),
            ('date_done', '<=', date_end),
            ('partner_id', '!=', False),  # Excluir pickings sin dirección de entrega
        ]
        pickings = self.env['stock.picking'].search(domain, order='date_done, scheduled_date')

        # Si está marcado "Todos los tipos", devolver todos los pickings sin filtrar
        if self.all_movement_types:
            return pickings

        # Si NO está marcado "Todos los tipos", filtrar por el tipo seleccionado
        if self.movement_type:
            filtered_pickings = self.env['stock.picking']
            for picking in pickings:
                # Determinar el tipo de movimiento que se usará para este picking
                picking_movement_type = self._determine_movement_type(picking)
                # Si coincide con el filtro del wizard, incluirlo
                if picking_movement_type == self.movement_type:
                    filtered_pickings |= picking
            return filtered_pickings

        # Si no está marcado "Todos" y no hay tipo seleccionado, devolver todos
        return pickings

    def _sanitize_text(self, text):
        """Elimina caracteres prohibidos del texto para SILICIE."""
        if not text:
            return ''
        # Eliminar espacios al principio y al final
        text = text.strip()
        # Eliminar los caracteres: , ; :
        for char in [',', ';', ':']:
            text = text.replace(char, '')
        return text

    def _get_silice_number(self, picking):
        """Obtiene el número de referencia para el picking."""
        # Usar el número del albarán (picking.name) como referencia principal
        # Si no existe, usar silice_sequence como fallback
        return picking.silice_sequence or ''

    def _determine_movement_type(self, picking):
        """
        Determina el tipo de movimiento SILICIE según el picking.
        Prioridad:
        1. Campo silicie_movement_type del picking (copiado del pedido de venta)
        2. Campo silicie_movement_type del cliente
        3. Valor por defecto A08
        """
        # Prioridad 1: Si el picking tiene tipo de movimiento asignado (copiado del pedido), usar ese
        if picking.silicie_movement_type:
            return picking.silicie_movement_type

        # Prioridad 2: Si el partner tiene un tipo de movimiento asignado, usar ese
        partner = picking.partner_id
        if partner and partner.silicie_movement_type:
            return partner.silicie_movement_type

        # Prioridad 3: Usar A08 como valor por defecto
        return 'A08'

    def _get_product_mapping(self, product_id):
        """Obtiene los datos SILICIE del producto directamente desde sus campos."""
        product = self.env['product.product'].browse(product_id)

        # Si no tiene configuración SILICIE, retornar None
        if not product.silicie_codigo_producto:
            return None

        return {
            'codigo_nc': product.silicie_codigo_nc or '',
            'unidad_medida': product.silicie_unidad_medida or 'LTS',  # Por defecto Litros
            'graduacion': str(product.silicie_graduacion) if product.silicie_graduacion else '',
        }

    def _build_csv_rows(self, pickings):
        """Construye las filas de datos para el CSV SILICIE."""
        ICP = self.env['ir.config_parameter'].sudo()
        # Eliminar referencia a cae
        # cae = ICP.get_param('rubio_silice_report.silicie_cae', '')
        # codigo_epigrafe = ICP.get_param('rubio_silice_report.silicie_codigo_epigrafe', 'A3')
        # establishment_type = ICP.get_param('rubio_silice_report.silicie_establishment_type', '')
        default_um = ICP.get_param('rubio_silice_report.silicie_default_um', 'LTS')

        fecha_presentacion = datetime.now()
        rows_data = []
        missing_products = set()

        for picking in pickings:
            global_line_counter = 0  # Contador global para todas las líneas
            fecha_asiento = picking.date_done or picking.scheduled_date
            if not fecha_asiento:
                continue
            movement_type = self._determine_movement_type(picking)
            partner = picking.partner_id
            nif_destinatario = partner.vat or ''
            num_justificante = picking.name


            # Obtener número de sílice del picking usando el método existente
            silice_number_base = self._get_silice_number(picking)

            for move_line in picking.move_line_ids.filtered(lambda ml: ml.quantity > 0):
                product = move_line.product_id
                product_mapping = self._get_product_mapping(product.id)
                if not product_mapping:
                    missing_products.add(f"{product.id} - {product.display_name}")
                    continue

                global_line_counter += 1

                referencia_interna = f"{silice_number_base}-{global_line_counter}"
                numero_envases = int(move_line.quantity) if move_line.quantity is not None else 0
                capacidad_envase = product.product_tmpl_id.silicie_capacidad_envase if product.product_tmpl_id.silicie_capacidad_envase is not None else 0
                cantidad = numero_envases * capacidad_envase

                # Determinar el tipo de justificante según el tipo de documento identificativo del cliente
                if partner.silicie_document_type == '1':
                    tipo_justificante = 'J01'
                elif partner.silicie_document_type == '3':
                    tipo_justificante = 'J03'
                else:
                    tipo_justificante = ''

                # Construir fila directamente campo a campo en el orden exacto del CSV
                row_data = {
                    'referencia_interna': referencia_interna,
                    'fecha_movimiento': fecha_asiento,
                    'fecha_registro_contable': fecha_presentacion,
                    'tipo_movimiento': movement_type,
                    'codigo_nc': product_mapping.get('codigo_nc', ''),
                    'nif_destinatario': nif_destinatario,
                    'razon_social': self._sanitize_text(partner.name),
                    'tipo_documento_identificativo': partner.silicie_document_type or '',
                    'tipo_justificante': tipo_justificante,
                    'num_justificante': picking.numero_justificante or picking.name,
                    'numero_documento_identificativo': picking.num_documento_identificativo or nif_destinatario,
                    'cae_seed_number': partner.cae_seed_number or '',
                    'clave_silicie': product.product_tmpl_id.clave_silicie or '',
                    'numero_envases': numero_envases,
                    'unidad_medida': product_mapping.get('unidad_medida', default_um),
                    'descripcion_producto': self._sanitize_text(product.product_tmpl_id.silicie_descripcion_articulo) if product.product_tmpl_id.silicie_descripcion_articulo else self._sanitize_text(product.name),
                    'graduacion': product_mapping.get('graduacion', ''),
                    'tipo_envase': 'ADO1',
                    'cantidad': cantidad,
                    'codigo_epigrafe': 'A0',
                    'capacidad_envase': capacidad_envase,
                    'densidad': '',
                    'alcohol_puro': round((cantidad * float(product_mapping.get('graduacion', 0))) / 100, 2) if product_mapping.get('graduacion', '') else 0,
                    'indicador_marcas_fiscales': '',
                    'observaciones': picking.observaciones_entrega or '',
                    'producto': product.display_name,
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

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{self.csv_profile}_{timestamp}.csv"

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
