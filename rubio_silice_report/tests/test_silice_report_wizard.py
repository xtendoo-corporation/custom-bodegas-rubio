            'date_start': datetime.now(),
            'date_end': datetime.now(),
            'csv_profile': 'IESH1CSV',
            'movement_type': 'A08',
        })

        silice_num = wizard._get_silice_number(picking)
        self.assertEqual(silice_num, 'SILICE123')

    def test_determine_movement_type_spain(self):
        """Test determinación de tipo movimiento para España."""
        picking = self._create_test_picking()

        wizard = self.env['silice.report.wizard'].create({
            'date_start': datetime.now(),
            'date_end': datetime.now(),
            'csv_profile': 'IESH1CSV',
            'movement_type': 'A08',
        })

        movement_type = wizard._determine_movement_type(picking)
        self.assertEqual(movement_type, 'A08')  # Territorio interior

    def test_determine_movement_type_eu(self):
        """Test determinación de tipo movimiento para UE."""
        # Cambiar país a Francia
        self.partner.country_id = self.env.ref('base.fr')
        picking = self._create_test_picking()

        wizard = self.env['silice.report.wizard'].create({
            'date_start': datetime.now(),
            'date_end': datetime.now(),
            'csv_profile': 'IESH1CSV',
            'movement_type': 'A08',
        })

        movement_type = wizard._determine_movement_type(picking)
        self.assertEqual(movement_type, 'A10')  # UE

    def test_determine_movement_type_export(self):
        """Test determinación de tipo movimiento para exportación."""
        # Cambiar país a USA
        self.partner.country_id = self.env.ref('base.us')
        picking = self._create_test_picking()

        wizard = self.env['silice.report.wizard'].create({
            'date_start': datetime.now(),
            'date_end': datetime.now(),
            'csv_profile': 'IESH1CSV',
            'movement_type': 'A08',
        })

        movement_type = wizard._determine_movement_type(picking)
        self.assertEqual(movement_type, 'A11')  # Exportación

    def test_export_no_pickings(self):
        """Test que falla si no hay pickings en el rango."""
        wizard = self.env['silice.report.wizard'].create({
            'date_start': datetime.now() - timedelta(days=365),
            'date_end': datetime.now() - timedelta(days=364),
            'csv_profile': 'IESH1CSV',
            'movement_type': 'A08',
        })

        with self.assertRaises(UserError):
            wizard.action_export_csv()

    def test_export_missing_product_mapping(self):
        """Test que falla si falta mapeo de producto."""
        # Borrar mapeo
        self.env['ir.config_parameter'].sudo().set_param(
            'rubio_silice_report.silicie_product_mapping_json', '{}'
        )

        # Crear picking
        picking = self._create_test_picking(date_done=datetime.now())

        wizard = self.env['silice.report.wizard'].create({
            'date_start': datetime.now() - timedelta(hours=1),
            'date_end': datetime.now() + timedelta(hours=1),
            'csv_profile': 'IESH1CSV',
            'movement_type': 'A08',
        })

        with self.assertRaises(UserError) as context:
            wizard.action_export_csv()

        # Debe mencionar el producto faltante
        self.assertIn('mapeo SILICIE', str(context.exception))

    def test_export_success(self):
        """Test exportación exitosa."""
        # Crear picking done
        picking = self._create_test_picking(date_done=datetime.now())

        wizard = self.env['silice.report.wizard'].create({
            'date_start': datetime.now() - timedelta(hours=1),
            'date_end': datetime.now() + timedelta(hours=1),
            'csv_profile': 'IESH1CSV',
            'movement_type': 'A08',
        })

        result = wizard.action_export_csv()

        # Debe retornar acción de descarga
        self.assertEqual(result['type'], 'ir.actions.act_url')
        self.assertIn('/web/content/', result['url'])

    def test_filename_generation(self):
        """Test generación del nombre de fichero."""
        wizard = self.env['silice.report.wizard'].create({
            'date_start': datetime.now(),
            'date_end': datetime.now(),
            'csv_profile': 'IESH1CSV',
            'movement_type': 'A08',
        })

        filename = wizard._generate_filename()

        # Formato: CAE_PERFIL_TIMESTAMP.csv
        self.assertTrue(filename.startswith('ES12345678TEST_IESH1CSV_'))
        self.assertTrue(filename.endswith('.csv'))
# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class TestSiliceReportWizard(TransactionCase):
    """Tests para el wizard de exportación SILICIE."""

    def setUp(self):
        super().setUp()

        # Configurar parámetros SILICIE
        self.env['ir.config_parameter'].sudo().set_param(
            'rubio_silice_report.silicie_cae', 'ES12345678TEST'
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'rubio_silice_report.silicie_establishment_type', 'FA'
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'rubio_silice_report.silicie_csv_profile', 'IESH1CSV'
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'rubio_silice_report.silicie_default_um', 'LTR'
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'rubio_silice_report.silice_field_name', 'x_silice_number'
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'rubio_silice_report.silicie_default_movement_type', 'A08'
        )

        # Crear producto de test
        self.product = self.env['product.product'].create({
            'name': 'Producto Test SILICIE',
            'type': 'product',
        })

        # Configurar mapeo de producto
        product_mapping = {
            str(self.product.id): {
                'codigo_producto': 'PROD001',
                'tipo_producto': 'HI',
                'unidad_medida': 'LTR',
                'densidad': 0.85,
                'temperatura': 15.0,
            }
        }
        import json
        self.env['ir.config_parameter'].sudo().set_param(
            'rubio_silice_report.silicie_product_mapping_json',
            json.dumps(product_mapping)
        )

        # Crear partner
        self.partner = self.env['res.partner'].create({
            'name': 'Cliente Test',
            'vat': 'ESB12345678',
            'country_id': self.env.ref('base.es').id,
        })

        # Crear tipo de picking
        self.picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing')
        ], limit=1)

        if not self.picking_type:
            self.picking_type = self.env['stock.picking.type'].create({
                'name': 'Delivery Orders Test',
                'code': 'outgoing',
                'sequence_code': 'OUT',
                'warehouse_id': self.env['stock.warehouse'].search([], limit=1).id,
            })

    def _create_test_picking(self, date_done=None, silice_number='TEST001'):
        """Helper para crear picking de test."""
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.picking_type.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'x_silice_number': silice_number,
        })

        # Crear movimiento
        move = self.env['stock.move'].create({
            'name': self.product.name,
            'product_id': self.product.id,
            'product_uom_qty': 100,
            'product_uom': self.product.uom_id.id,
            'picking_id': picking.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
        })

        # Confirmar y asignar
        picking.action_confirm()
        picking.action_assign()

        # Procesar movimiento
        for move_line in picking.move_line_ids:
            move_line.qty_done = move_line.reserved_uom_qty

        if date_done:
            picking.date_done = date_done
            picking.state = 'done'

        return picking

    def test_wizard_default_values(self):
        """Test que el wizard carga valores por defecto desde configuración."""
        wizard = self.env['silice.report.wizard'].create({
            'date_start': datetime.now(),
            'date_end': datetime.now(),
        })

        # Debe cargar perfil y tipo de movimiento desde configuración
        self.assertEqual(wizard.csv_profile, 'IESH1CSV')
        self.assertEqual(wizard.movement_type, 'A08')

    def test_validate_configuration_missing_cae(self):
        """Test que falla si no hay CAE configurado."""
        # Borrar CAE
        self.env['ir.config_parameter'].sudo().set_param(
            'rubio_silice_report.silicie_cae', ''
        )

        wizard = self.env['silice.report.wizard'].create({
            'date_start': datetime.now(),
            'date_end': datetime.now(),
            'csv_profile': 'IESH1CSV',
            'movement_type': 'A08',
        })

        with self.assertRaises(UserError):
            wizard._validate_configuration()

    def test_validate_dates_order(self):
        """Test validación de orden de fechas."""
        wizard = self.env['silice.report.wizard'].create({
            'date_start': datetime.now(),
            'date_end': datetime.now() - timedelta(days=1),
            'csv_profile': 'IESH1CSV',
            'movement_type': 'A08',
        })

        with self.assertRaises(UserError):
            wizard._validate_dates()

    def test_get_silice_number(self):
        """Test obtención del número de sílice."""
        picking = self._create_test_picking(silice_number='SILICE123')

        wizard = self.env['silice.report.wizard'].create({
from . import test_silicie_specs
from . import test_silice_report_wizard

