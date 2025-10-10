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

# Orden y configuración de campos CSV
CSV_FIELDS = [
    'referencia_interna',
    'fecha_movimiento',
    'fecha_registro_contable',
    'tipo_movimiento',
    'cae',
    'nif_destinatario',
    'razon_social',
    'tipo_justificante',
    'num_justificante',
    'unidad_medida',
    'codigo_nc',
    'codigo_epigrafe',
    'descripcion_producto',
    'graduacion',
    'tipo_envase',
    'cantidad',
]

# Campos obligatorios
REQUIRED_FIELDS = [
    'referencia_interna',
    'fecha_movimiento',
    'fecha_registro_contable',
    'tipo_movimiento',
    'cae',
    'tipo_justificante',
    'unidad_medida',
    'cantidad',
]

# Longitudes máximas por campo
FIELD_MAX_LENGTHS = {
    'referencia_interna': 40,
    'tipo_movimiento': 3,
    'cae': 16,
    'codigo_epigrafe': 10,
    'codigo_nc': 15,
    'nif_destinatario': 15,
    'tipo_justificante': 2,
    'num_justificante': 30,
    'unidad_medida': 3,
}

# Campos de tipo fecha/datetime
DATE_FIELDS = ['fecha_movimiento']
DATETIME_FIELDS = ['fecha_registro_contable']
FLOAT_FIELDS = ['graduacion', 'cantidad']

# Cabeceras legibles
CSV_HEADERS = {
    'referencia_interna': 'Numero Referencia Interna',
    'fecha_movimiento': 'Fecha Movimiento',
    'fecha_registro_contable': 'Fecha Registro Contable',
    'tipo_movimiento': 'Tipo Movimiento',
    'cae': 'CAE',
    'nif_destinatario': 'NIF Destinatario',
    'razon_social': 'Razon Social',
    'tipo_justificante': 'Tipo Justificante',
    'num_justificante': 'Numero Justificante',
    'unidad_medida': 'Unidad Medida',
    'codigo_nc': 'Código NC',
    'codigo_epigrafe': 'Código Epígrafe',
    'descripcion_producto': 'Descripcion Producto',
    'graduacion': 'Graduacion',
    'tipo_envase': 'Tipo Envase',
    'cantidad': 'Cantidad',
}

# Opciones para campos Selection
ESTABLISHMENT_TYPES = [
    ('FA', 'Fábrica'),
    ('DE', 'Depósito Fiscal'),
    ('EX', 'Exportador'),
    ('IM', 'Importador'),
    ('DT', 'Destinatario Registrado'),
    ('OP', 'Operador Registrado'),
    ('RE', 'Representante Fiscal'),
]

MOVEMENT_TYPES = [
    ('A08', 'Salida a consumo - territorio interior'),
    ('A09', 'Salida a consumo - Canarias, Ceuta o Melilla'),
    ('A10', 'Salida en régimen suspensivo - UE'),
    ('A11', 'Salida en régimen suspensivo - exportación'),
    ('A12', 'Salida para entrega exenta'),
    ('A13', 'Salida para uso de las fuerzas armadas de un Estado miembro'),
    ('A14', 'Salida para venta a bordo'),
    ('A15', 'Otras salidas'),
    ('A16', 'Salida para destrucción'),
    ('A17', 'Salida a otro depósito fiscal del mismo titular'),
]

UNIT_MEASURES = [
    ('LTS', 'Litros'),
    ('KGS', 'Kilogramos'),
    ('UNI', 'Unidades'),
    ('CAJ', 'Cajas'),
    ('HL', 'Hectolitros'),
    ('HPA', 'Hectolitros de alcohol puro'),
]

JUSTIFICANT_TYPES = [
    ('FA', 'Factura'),
    ('AL', 'Albarán'),
    ('DU', 'DUA'),
    ('DA', 'Documento Administrativo'),
    ('ED', 'e-DA (Documento Administrativo Electrónico)'),
    ('OT', 'Otro'),
]

CSV_PROFILES = [
    ('IESA1CSV', 'Alcohol - IESA1CSV'),
]


# ============================================================================
# FUNCIONES DE FORMATO
# ============================================================================

def format_date(date_obj):
    """Formatea fecha según el formato SILICIE."""
    if not date_obj:
        return ''
    if isinstance(date_obj, str):
        return date_obj
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

    # Si es entero, no mostrar decimales
    if float(value) == int(float(value)):
        return str(int(float(value)))

    formatted = f"{float(value):.{decimals}f}"
    if DECIMAL_SEPARATOR == ',':
        formatted = formatted.replace('.', ',')
    return formatted


def truncate_field(value, max_length):
    """Trunca un campo de texto a la longitud máxima."""
    if not value:
        return ''
    return str(value)[:max_length]


# ============================================================================
# FUNCIONES DE VALIDACIÓN
# ============================================================================

def validate_cae(cae):
    """Valida formato del CAE."""
    if not cae:
        raise ValidationError("El CAE es obligatorio para exportar a SILICIE.")
    if len(cae) > 16:
        raise ValidationError(f"El CAE '{cae}' supera la longitud máxima de 16 caracteres.")
    return True


def validate_choice(value, valid_choices, field_name):
    """Valida que un valor esté en una lista de opciones válidas."""
    if value and value not in [code for code, label in valid_choices]:
        valid_codes = ', '.join([code for code, label in valid_choices])
        raise ValidationError(
            f"{field_name} '{value}' no válido. "
            f"Debe ser uno de: {valid_codes}"
        )
    return True


def validate_row(row_data):
    """Valida una fila completa según las especificaciones SILICIE."""
    errors = []

    # Validar campos requeridos
    for field_name in REQUIRED_FIELDS:
        if not row_data.get(field_name):
            errors.append(f"Campo '{field_name}' es obligatorio y está vacío.")

    # Validar longitudes
    for field_name, max_len in FIELD_MAX_LENGTHS.items():
        value = row_data.get(field_name)
        if value and len(str(value)) > max_len:
            errors.append(
                f"Campo '{field_name}' excede longitud máxima ({max_len}): '{value}'"
            )

    if errors:
        raise ValidationError('\n'.join(errors))

    return True


# ============================================================================
# FUNCIONES DE CONSTRUCCIÓN CSV
# ============================================================================

def build_csv_row(row_data):
    """Construye una fila CSV con el orden exacto de campos."""
    row = []
    missing_fields = []

    for field_name in CSV_FIELDS:
        if field_name not in row_data:
            missing_fields.append(field_name)

        value = row_data.get(field_name, '')

        # Aplicar formato según tipo de campo
        if field_name in DATE_FIELDS and value:
            value = format_date(value)
        elif field_name in DATETIME_FIELDS and value:
            value = format_datetime(value)
        elif field_name in FLOAT_FIELDS:
            value = format_float(value if value != '' else 0.0, 2)
        elif field_name in FIELD_MAX_LENGTHS:
            value = truncate_field(value, FIELD_MAX_LENGTHS[field_name])

        row.append(str(value) if value is not None else '')

    if missing_fields:
        raise ValidationError(
            f"Faltan los siguientes campos en los datos: {', '.join(missing_fields)}. "
            f"Esto provoca desplazamientos en el CSV.\nContenido: {row_data}"
        )

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
    """
    Genera el contenido CSV completo.
    rows_data: lista de dicts, cada uno representa una fila
    Retorna: bytes del CSV
    """
    output = io.StringIO()
    writer = csv.writer(
        output,
        delimiter=SEPARATOR,
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL
    )

    if include_header:
        writer.writerow(build_csv_header())

    for row_data in rows_data:
        validate_row(row_data)
        csv_row = build_csv_row(row_data)
        writer.writerow(csv_row)

    content = output.getvalue()
    return content.encode(ENCODING)


# ============================================================================
# FUNCIONES PARA CAMPOS SELECTION DE ODOO
# ============================================================================

def get_establishment_type_choices():
    return ESTABLISHMENT_TYPES

def get_movement_type_choices():
    return MOVEMENT_TYPES

def get_unit_measure_choices():
    return UNIT_MEASURES

def get_justificant_type_choices():
    return JUSTIFICANT_TYPES

def get_profile_choices():
    return CSV_PROFILES
