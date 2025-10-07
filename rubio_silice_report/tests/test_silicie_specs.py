# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from ..models import silicie_specs
from datetime import datetime


class TestSilicieSpecs(TransactionCase):
    """Tests para las especificaciones y validaciones SILICIE."""

    def test_profile_exists(self):
        """Test que los perfiles SILICIE existen."""
        self.assertIn('IESH1CSV', silicie_specs.SILICIE_PROFILES)
        self.assertIn('IEST1CSV', silicie_specs.SILICIE_PROFILES)
        self.assertIn('IESA1CSV', silicie_specs.SILICIE_PROFILES)

    def test_profile_fields_order(self):
        """Test que el orden de campos es correcto y empieza con numero_silice."""
        for profile_key, profile in silicie_specs.SILICIE_PROFILES.items():
            fields = profile['fields']
            self.assertTrue(len(fields) > 0, f"Perfil {profile_key} debe tener campos")

            # Primera columna debe ser numero_silice
            first_field = fields[0]
            self.assertEqual(
                first_field['name'],
                'numero_silice',
                f"Primera columna de {profile_key} debe ser 'numero_silice'"
            )

    def test_validate_cae(self):
        """Test validación de CAE."""
        # CAE válido
        self.assertTrue(silicie_specs.validate_cae('ES12345678'))

        # CAE vacío debe fallar
        with self.assertRaises(ValidationError):
            silicie_specs.validate_cae('')

        # CAE muy largo debe fallar
        with self.assertRaises(ValidationError):
            silicie_specs.validate_cae('X' * 20)

    def test_validate_movement_type(self):
        """Test validación de tipos de movimiento."""
        # Tipos válidos
        self.assertTrue(silicie_specs.validate_movement_type('A08'))
        self.assertTrue(silicie_specs.validate_movement_type('A10'))
        self.assertTrue(silicie_specs.validate_movement_type('A11'))

        # Tipo inválido
        with self.assertRaises(ValidationError):
            silicie_specs.validate_movement_type('X99')

    def test_validate_establishment_type(self):
        """Test validación de tipo de establecimiento."""
        # Tipos válidos
        self.assertTrue(silicie_specs.validate_establishment_type('FA'))
        self.assertTrue(silicie_specs.validate_establishment_type('DE'))

        # Tipo inválido
        with self.assertRaises(ValidationError):
            silicie_specs.validate_establishment_type('XX')

    def test_validate_unit_measure(self):
        """Test validación de unidad de medida."""
        # Unidades válidas
        self.assertTrue(silicie_specs.validate_unit_measure('LTS'))
        self.assertTrue(silicie_specs.validate_unit_measure('KGS'))

        # Unidad inválida
        with self.assertRaises(ValidationError):
            silicie_specs.validate_unit_measure('XXX')

    def test_format_date(self):
        """Test formateo de fechas."""
        test_date = datetime(2025, 10, 7)
        formatted = silicie_specs.format_date(test_date, 'IESH1CSV')
        self.assertEqual(formatted, '07/10/2025')

    def test_format_datetime(self):
        """Test formateo de fecha-hora."""
        test_datetime = datetime(2025, 10, 7, 14, 30, 45)
        formatted = silicie_specs.format_datetime(test_datetime, 'IESH1CSV')
        self.assertEqual(formatted, '07/10/2025 14:30:45')

    def test_format_float(self):
        """Test formateo de decimales con separador correcto."""
        # Con separador coma (español)
        formatted = silicie_specs.format_float(123.456, decimals=2, profile_key='IESH1CSV')
        self.assertEqual(formatted, '123,46')

        # Con 3 decimales
        formatted = silicie_specs.format_float(123.456, decimals=3, profile_key='IESH1CSV')
        self.assertEqual(formatted, '123,456')

    def test_truncate_field(self):
        """Test truncado de campos largos."""
        long_text = 'A' * 100
        truncated = silicie_specs.truncate_field(long_text, 50)
        self.assertEqual(len(truncated), 50)

    def test_build_csv_header(self):
        """Test construcción de cabecera CSV."""
        header = silicie_specs.build_csv_header('IESH1CSV')
        self.assertIsInstance(header, list)
        self.assertEqual(header[0], 'numero_silice')
        self.assertIn('cae', header)
        self.assertIn('tipo_movimiento', header)

    def test_build_csv_row(self):
        """Test construcción de fila CSV con orden correcto."""
        row_data = {
            'numero_silice': '12345',
            'cae': 'ES12345678',
            'tipo_establecimiento': 'FA',
            'fecha_presentacion': datetime(2025, 10, 7, 14, 30, 0),
            'version_fichero': '1.0',
            'fecha_asiento': datetime(2025, 10, 7),
            'tipo_movimiento': 'A08',
            'codigo_producto': 'PROD001',
            'tipo_producto': 'HI',
            'cantidad': 1000.500,
            'unidad_medida': 'LTS',
        }

        csv_row = silicie_specs.build_csv_row(row_data, 'IESH1CSV')

        # Verificar orden: primera columna es numero_silice
        self.assertEqual(csv_row[0], '12345')
        # Segunda es CAE
        self.assertEqual(csv_row[1], 'ES12345678')

    def test_validate_row_required_fields(self):
        """Test validación de campos requeridos."""
        # Fila incompleta (falta campo requerido)
        incomplete_row = {
            'numero_silice': '12345',
            'cae': 'ES12345678',
            # Falta tipo_establecimiento (requerido)
        }

        with self.assertRaises(ValidationError):
            silicie_specs.validate_row(incomplete_row, 'IESH1CSV')

    def test_generate_csv_content(self):
        """Test generación completa de CSV."""
        rows_data = [{
            'numero_silice': '12345',
            'cae': 'ES12345678',
            'tipo_establecimiento': 'FA',
            'fecha_presentacion': datetime(2025, 10, 7, 14, 30, 0),
            'version_fichero': '1.0',
            'fecha_asiento': datetime(2025, 10, 7),
            'tipo_movimiento': 'A08',
            'codigo_producto': 'PROD001',
            'tipo_producto': 'HI',
            'cantidad': 1000.500,
            'unidad_medida': 'LTS',
            'densidad': 0.8500,
            'temperatura': 15.50,
            'destino_nif': 'B12345678',
            'destino_nombre': 'Cliente Test',
            'destino_direccion': 'Calle Test 123',
            'destino_pais': 'ES',
            'num_justificante': 'ALB001',
            'tipo_justificante': 'AL',
            'observaciones': 'Test',
        }]

        csv_content = silicie_specs.generate_csv_content(rows_data, 'IESH1CSV')

        # Debe ser bytes
        self.assertIsInstance(csv_content, bytes)

        # Debe contener BOM UTF-8
        self.assertTrue(csv_content.startswith(b'\xef\xbb\xbf'))

        # Decodificar y verificar contenido
        content_str = csv_content.decode('utf-8-sig')
        lines = content_str.strip().split('\n')

        # Debe tener cabecera + 1 fila
        self.assertEqual(len(lines), 2)

        # Primera línea debe ser cabecera empezando con numero_silice
        self.assertTrue(lines[0].startswith('numero_silice'))

        # Segunda línea debe empezar con el valor 12345
        self.assertTrue(lines[1].startswith('12345'))

