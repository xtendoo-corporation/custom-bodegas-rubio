# -*- coding: utf-8 -*-
"""
Especificaciones técnicas SILICIE 2.0 - Importación por fichero
Basado en:
- Orden HAC/998/2019 (texto consolidado)
- Documentación técnica AEAT-SILICIE 2.0
- Tablas y tipos de movimiento SILICIE
"""

import csv
import io
from datetime import datetime
from odoo.exceptions import ValidationError

# ============================================================================
# CONFIGURACIÓN FIJA SILICIE - ALCOHOL (IESA1CSV)
# ============================================================================

SEPARATOR = ';'
ENCODING = 'utf-8-sig'
DECIMAL_SEPARATOR = '.'
DATE_FORMAT = '%d/%m/%Y'

CSV_FIELDS = [
    'referencia_interna',
    'numero_asiento_previo',
    'fecha_movimiento',
    'fecha_registro_contable',
    'tipo_movimiento',
    'tipo_justificante',
    'regimen_fiscal',
    'nif_destinatario',
    'numero_documento_identificativo',
    'num_justificante',
    'razon_social',
    'cae_seed_number',
    'codigo_epigrafe',
    'codigo_nc',
    'clave_silicie',
    'cantidad',
    'unidad_medida',
    'producto',
    'descripcion_producto',
    'graduacion',
    'alcohol_puro',
    'tipo_envase',
    'capacidad_envase',
    'numero_envases',
    'indicador_marcas_fiscales',
    'observaciones',
]

REQUIRED_FIELDS = [
    'referencia_interna', 'fecha_movimiento', 'fecha_registro_contable',
    'tipo_movimiento', 'tipo_justificante', 'unidad_medida', 'cantidad',
]

FIELD_MAX_LENGTHS = {
    'referencia_interna': 40, 'tipo_movimiento': 3,
    'codigo_epigrafe': 10, 'codigo_nc': 15, 'nif_destinatario': 15,
    'tipo_justificante': 3,  # Cambiado de 2 a 3
    'num_justificante': 30, 'unidad_medida': 3,
}

DATE_FIELDS = ['fecha_movimiento']
DATETIME_FIELDS = ['fecha_registro_contable']
FLOAT_FIELDS = ['graduacion', 'cantidad']

CSV_HEADERS = {
    'referencia_interna': 'Numero Referencia Interna',
    'numero_asiento_previo': 'Numero Asiento Previo',  # NUEVO
    'fecha_movimiento': 'Fecha Movimiento',
    'fecha_registro_contable': 'Fecha Registro Contable',
    'tipo_justificante': 'Tipo Documento Identificativo',
    'regimen_fiscal': 'Regimen Fiscal',
    'tipo_movimiento': 'Tipo Movimiento',
    'nif_destinatario': 'NIF Destinatario',

    'tipo_justificante': 'Tipo Documento Identificativo',
    'num_justificante': 'Numero Justificante',
    'numero_documento_identificativo': 'Numero Documento Identificativo',
    'razon_social': 'Razon Social',
    'cae_seed_number': 'CAE/Numero SEED',
    'codigo_epigrafe': 'Codigo Epigrafe',
    'codigo_nc': 'Codigo NC',
    'clave_silicie': 'Clave',
    'cantidad': 'Cantidad',
    'unidad_medida': 'Unidad Medida',
    'producto': 'Producto',
    'descripcion_producto': 'Descripcion Producto',
    'graduacion': 'Graduacion',
    'alcohol_puro': 'Alcohol Puro',
    'tipo_envase': 'Tipo Envase',
    'capacidad_envase': 'Capacidad Envase',
    'numero_envases': 'Numero Envases',
    'indicador_marcas_fiscales': 'Indicador Marcas Fiscales',
    'observaciones': 'Observaciones',
}

ESTABLISHMENT_TYPES = [
    ('FA', 'Fábrica'), ('DE', 'Depósito Fiscal'), ('EX', 'Exportador'),
    ('IM', 'Importador'), ('DT', 'Destinatario Registrado'),
    ('OP', 'Operador Registrado'), ('RE', 'Representante Fiscal'),
]

MOVEMENT_TYPES = [
    ('A08', 'Salida a consumo - territorio interior'),
    ('A09', 'Salida a consumo - Canarias, Ceuta o Melilla'),
    ('A10', 'Salida en régimen suspensivo - UE'),
    ('A11', 'Salida en régimen suspensivo - exportación'),
]

UNIT_MEASURES = [
    ('LTR', 'Litros'), ('LTS', 'Litros (valor anterior)'),
    ('KGS', 'Kilogramos'), ('UNI', 'Unidades'),
    ('CAJ', 'Cajas'), ('HL', 'Hectolitros'), ('HPA', 'Hectolitros de alcohol puro'),
]

JUSTIFICANT_TYPES = [
    ('FA', 'Factura'), ('AL', 'Albarán'), ('DU', 'DUA'),
    ('DA', 'Documento Administrativo'),
    ('ED', 'e-DA (Documento Administrativo Electrónico)'), ('OT', 'Otro'),
]

CSV_PROFILES = [('IESA1CSV', 'Alcohol - IESA1CSV')]


# ============================================================================
# FUNCIONES DE FORMATO
# ============================================================================

def format_date(date_obj):
    """Formatea fecha según el formato SILICIE."""
    if not date_obj or isinstance(date_obj, str):
        return date_obj or ''
    return date_obj.strftime(DATE_FORMAT)


def format_datetime(datetime_obj):
    """Formatea fecha-hora según el formato SILICIE (solo dd/mm/yyyy)."""
    if not datetime_obj:
        return ''
    if isinstance(datetime_obj, str):
        try:
            return datetime.strptime(datetime_obj[:10], '%d/%m/%Y').strftime(DATE_FORMAT)
        except Exception:
            return datetime_obj[:10]
    return datetime_obj.strftime(DATE_FORMAT)


def format_float(value, decimals=2):
    """Formatea número decimal según el separador SILICIE."""
    if value is None:
        return ''

    float_value = float(value)
    if float_value == int(float_value):
        return str(int(float_value))

    formatted = f"{float_value:.{decimals}f}"
    return formatted.replace('.', ',') if DECIMAL_SEPARATOR == ',' else formatted


def truncate_field(value, max_length):
    """Trunca un campo de texto a la longitud máxima."""
    return str(value)[:max_length] if value else ''


# ============================================================================
# FUNCIONES DE VALIDACIÓN
# ============================================================================


def validate_choice(value, valid_choices, field_name):
    """Valida que un valor esté en una lista de opciones válidas."""
    if value and value not in [code for code, label in valid_choices]:
        valid_codes = ', '.join([code for code, label in valid_choices])
        raise ValidationError(f"{field_name} '{value}' no válido. Debe ser uno de: {valid_codes}")
    return True


def validate_movement_type(movement_type):
    """Valida que el tipo de movimiento sea válido según SILICIE."""
    if not movement_type:
        return True  # Es opcional, puede estar vacío
    return validate_choice(movement_type, MOVEMENT_TYPES, 'Tipo de Movimiento')


def validate_row(row_data):
    """Valida una fila completa según las especificaciones SILICIE."""
    errors = []

    for field_name in REQUIRED_FIELDS:
        if not row_data.get(field_name):
            errors.append(f"Campo '{field_name}' es obligatorio y está vacío.")

    for field_name, max_len in FIELD_MAX_LENGTHS.items():
        value = row_data.get(field_name)
        if value and len(str(value)) > max_len:
            errors.append(f"Campo '{field_name}' excede longitud máxima ({max_len}): '{value}'")

    if errors:
        raise ValidationError('\n'.join(errors))
    return True


# ============================================================================
# FUNCIONES DE CONSTRUCCIÓN CSV
# ============================================================================

def build_csv_row(row_data):
    """Construye una fila CSV con el orden exacto de campos."""
    row = []
    for field_name in CSV_FIELDS:
        if field_name == 'regimen_fiscal':
            value = row_data.get('regimen_fiscal', '')
        else:
            value = row_data.get(field_name, '')
            if field_name in DATE_FIELDS and value:
                value = format_date(value)
            elif field_name in DATETIME_FIELDS and value:
                value = format_datetime(value)
            elif field_name in FLOAT_FIELDS:
                value = format_float(value if value != '' else 0.0, 2)
            elif field_name in FIELD_MAX_LENGTHS:
                value = truncate_field(value, FIELD_MAX_LENGTHS[field_name])
        row.append(str(value) if value is not None else '')

    if len(row) != len(CSV_FIELDS):
        raise ValidationError(
            f"La fila generada tiene {len(row)} columnas pero se esperan {len(CSV_FIELDS)}."
            f"\nFila: {row}\nContenido: {row_data}"
        )
    return row


def build_csv_header():
    """Construye la cabecera CSV con nombres legibles."""
    return [CSV_HEADERS.get(field, field) for field in CSV_FIELDS]


def generate_csv_content(rows_data, include_header=True):
    """Genera el contenido CSV completo. Retorna bytes del CSV."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=SEPARATOR, quotechar='"', quoting=csv.QUOTE_MINIMAL)

    if include_header:
        writer.writerow(build_csv_header())

    for row_data in rows_data:
        validate_row(row_data)
        writer.writerow(build_csv_row(row_data))

    return output.getvalue().encode(ENCODING)


# ============================================================================
# FUNCIONES PARA CAMPOS SELECTION DE ODOO
# ============================================================================

def get_establishment_type_choices():
    return ESTABLISHMENT_TYPES


def get_movement_type_choices():
    """Devuelve las opciones de tipos de movimiento SILICIE"""
    return MOVEMENT_TYPES


def get_unit_measure_choices():
    return UNIT_MEASURES


def get_justificant_type_choices():
    return JUSTIFICANT_TYPES


def get_profile_choices():
    return CSV_PROFILES
