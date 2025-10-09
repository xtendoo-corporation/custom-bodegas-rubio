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

# Configuración del CSV
SEPARATOR = ';'
ENCODING = 'utf-8-sig'
DECIMAL_SEPARATOR = '.'
DATE_FORMAT = '%d/%m/%Y'
DATETIME_FORMAT = '%d/%m/%Y'  # Solo fecha
# ============================================================================
# FUNCIONES DE FORMATO Y VALIDACIÓN
# ============================================================================

def format_date(date_obj):
    """Formatea fecha según el formato SILICIE."""
    if not date_obj:
        return ''
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime(DATE_FORMAT)


def format_datetime(datetime_obj):
    """Formatea fecha-hora según el formato SILICIE, solo dd/mm/yyyy."""
    if not datetime_obj:
        return ''
    if isinstance(datetime_obj, str):
        # Si ya es string, intenta truncar a solo fecha
        try:
            return datetime.strptime(datetime_obj[:10], '%d/%m/%Y').strftime(DATE_FORMAT)
        except Exception:
            return datetime_obj[:10]
    return datetime_obj.strftime(DATE_FORMAT)


def format_float(value, decimals=2):
    """Formatea número decimal según el separador SILICIE."""
    if value is None:
        return ''

    # Si el valor es un entero, no mostrar decimales
    if float(value) == int(float(value)):
        formatted = str(int(float(value)))
    else:
        formatted = f"{float(value):.{decimals}f}"
        if DECIMAL_SEPARATOR == ',':
            formatted = formatted.replace('.', ',')
    return formatted


def truncate_field(value, max_length):
    """Trunca un campo de texto a la longitud máxima."""
    if not value:
        return ''
    return str(value)[:max_length]


def validate_cae(cae):
    """Valida formato del CAE (Código de Actividad Empresarial)."""
    if not cae:
        raise ValidationError("El CAE es obligatorio para exportar a SILICIE.")
    if len(cae) > 16:
        raise ValidationError(f"El CAE '{cae}' supera la longitud máxima de 16 caracteres.")
    return True


def validate_movement_type(movement_type):
    """Valida que el tipo de movimiento exista en tablas SILICIE."""
    valid_types = ['A08', 'A09', 'A10', 'A11', 'A12', 'A13', 'A14', 'A15', 'A16', 'A17']
    if movement_type not in valid_types:
        raise ValidationError(
            f"Tipo de movimiento '{movement_type}' no válido. "
            f"Debe ser uno de: {', '.join(valid_types)}"
        )
    return True


def validate_establishment_type(est_type):
    """Valida tipo de establecimiento."""
    if est_type:
        valid_types = ['FA', 'DE', 'EX', 'IM', 'DT', 'OP', 'RE']
        if est_type not in valid_types:
            raise ValidationError(
                f"Tipo de establecimiento '{est_type}' no válido. "
                f"Debe ser uno de: {', '.join(valid_types)}"
            )
    return True


def validate_unit_measure(unit):
    """Valida unidad de medida."""
    if unit:
        valid_units = ['LTS', 'KGS', 'UNI', 'CAJ', 'HL', 'HPA']
        if unit not in valid_units:
            raise ValidationError(
                f"Unidad de medida '{unit}' no válida. "
                f"Debe ser una de: {', '.join(valid_units)}"
            )
    return True


def validate_row(row_data):
    """Valida una fila completa según las especificaciones SILICIE."""
    errors = []
    required_fields = [
        'referencia_interna',
        'fecha_movimiento',
        'fecha_registro_contable',
        'tipo_movimiento',
        'cae',
        'tipo_justificante',
        'unidad_medida',
        'cantidad',
    ]

    csv_fields = [
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

    for field_name in csv_fields:
        value = row_data.get(field_name)

        # Validar campos requeridos
        if field_name in required_fields and not value:
            errors.append(f"Campo '{field_name}' es obligatorio y está vacío.")

        # Validar longitud
        if value:
            max_len = None
            if field_name == 'referencia_interna':
                max_len = 40
            elif field_name == 'tipo_movimiento':
                max_len = 3
            elif field_name == 'cae':
                max_len = 16
            elif field_name == 'codigo_epigrafe':
                max_len = 10
            elif field_name == 'codigo_nc':
                max_len = 15
            elif field_name == 'nif_destinatario':
                max_len = 15
            elif field_name == 'tipo_justificante':
                max_len = 2
            elif field_name == 'num_justificante':
                max_len = 30
            elif field_name == 'unidad_medida':
                max_len = 3

            if max_len and len(str(value)) > max_len:
                errors.append(
                    f"Campo '{field_name}' excede longitud máxima ({max_len}): '{value}'"
                )

    if errors:
        raise ValidationError('\n'.join(errors))

    return True


def build_csv_row(row_data):
    """
    Construye una fila CSV con el orden EXACTO de campos.
    row_data: dict con los valores
    Retorna: lista de valores en el orden correcto
    """
    csv_fields = [
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

    row = []
    missing_fields = []

    for field_name in csv_fields:
        if field_name not in row_data:
            missing_fields.append(field_name)
        value = row_data.get(field_name, '')

        # Aplicar formato según tipo
        # Campos tipo fecha
        if field_name in ['fecha_movimiento'] and value:
            value = format_date(value)
        # Campos tipo datetime
        elif field_name in ['fecha_registro_contable'] and value:
            value = format_datetime(value)
        # Campos tipo float
        elif field_name in ['graduacion', 'cantidad']:
            decimals = 2  # Por defecto 2 decimales para campos float
            value = format_float(value if value != '' else 0.0, decimals)
        else:
            # Aplicar truncamiento según longitud máxima
            max_len = None
            if field_name == 'referencia_interna':
                max_len = 40
            elif field_name == 'tipo_movimiento':
                max_len = 3
            elif field_name == 'cae':
                max_len = 16
            elif field_name == 'codigo_epigrafe':
                max_len = 10
            elif field_name == 'codigo_nc':
                max_len = 15
            elif field_name == 'nif_destinatario':
                max_len = 15
            elif field_name == 'tipo_justificante':
                max_len = 2
            elif field_name == 'num_justificante':
                max_len = 30
            elif field_name == 'unidad_medida':
                max_len = 3

            if max_len:
                value = truncate_field(value, max_len)

        row.append(str(value) if value is not None else '')

    if missing_fields:
        raise ValidationError(f"Faltan los siguientes campos en los datos: {', '.join(missing_fields)}. Esto provoca desplazamientos en el CSV.\nContenido: {row_data}")

    if len(row) != len(csv_fields):
        raise ValidationError(f"La fila generada tiene {len(row)} columnas pero se esperan {len(csv_fields)}.\nFila: {row}\nContenido: {row_data}")

    return row


def build_csv_header():
    """Construye la cabecera CSV con nombres legibles."""
    csv_fields = [
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

    headers = []
    for field_name in csv_fields:
        if field_name == 'referencia_interna':
            headers.append('Numero Referencia Interna')
        elif field_name == 'fecha_movimiento':
            headers.append('Fecha Movimiento')
        elif field_name == 'fecha_registro_contable':
            headers.append('Fecha Registro Contable')
        elif field_name == 'tipo_movimiento':
            headers.append('Tipo Movimiento')
        elif field_name == 'cae':
            headers.append('CAE')
        elif field_name == 'codigo_epigrafe':
            headers.append('Código Epígrafe')
        elif field_name == 'codigo_nc':
            headers.append('Código NC')
        elif field_name == 'nif_destinatario':
            headers.append('NIF Destinatario')
        elif field_name == 'razon_social':
            headers.append('Razon Social')
        elif field_name == 'tipo_justificante':
            headers.append('Tipo Justificante')
        elif field_name == 'num_justificante':
            headers.append('Numero Justificante')
        elif field_name == 'unidad_medida':
            headers.append('Unidad Medida')
        elif field_name == 'descripcion_producto':
            headers.append('Descripcion Producto')
        elif field_name == 'tipo_envase':
            headers.append('Tipo Envase')
        elif field_name == 'graduacion':
            headers.append('Graduacion')
        elif field_name == 'cantidad':
            headers.append('Cantidad')
        else:
            headers.append(field_name)

    return headers


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

    # Cabecera
    if include_header:
        header = build_csv_header()
        writer.writerow(header)

    # Filas de datos
    for row_data in rows_data:
        # Validar antes de escribir
        validate_row(row_data)
        csv_row = build_csv_row(row_data)
        writer.writerow(csv_row)

    # Convertir a bytes con la codificación fija
    content = output.getvalue()
    return content.encode(ENCODING)


def get_establishment_type_choices():
    """Retorna las opciones de tipos de establecimiento para un campo Selection."""
    return [
        ('FA', 'Fábrica'),
        ('DE', 'Depósito Fiscal'),
        ('EX', 'Exportador'),
        ('IM', 'Importador'),
        ('DT', 'Destinatario Registrado'),
        ('OP', 'Operador Registrado'),
        ('RE', 'Representante Fiscal'),
    ]

def get_movement_type_choices():
    """Retorna las opciones de tipos de movimiento para un campo Selection."""
    return [
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

def get_unit_measure_choices():
    """Retorna las opciones de unidades de medida para un campo Selection."""
    return [
        ('LTS', 'Litros'),
        ('KGS', 'Kilogramos'),
        ('UNI', 'Unidades'),
        ('CAJ', 'Cajas'),
        ('HL', 'Hectolitros'),
        ('HPA', 'Hectolitros de alcohol puro'),
    ]

def get_justificant_type_choices():
    """Retorna las opciones de tipos de justificante para un campo Selection."""
    return [
        ('FA', 'Factura'),
        ('AL', 'Albarán'),
        ('DU', 'DUA'),
        ('DA', 'Documento Administrativo'),
        ('ED', 'e-DA (Documento Administrativo Electrónico)'),
        ('OT', 'Otro'),
    ]

def get_country_choices():
    """Retorna las opciones de países para un campo Selection."""
    return [
        ('ES', 'España'),
        ('FR', 'Francia'),
        ('DE', 'Alemania'),
        ('IT', 'Italia'),
        ('PT', 'Portugal'),
        ('GB', 'Reino Unido'),
        ('US', 'Estados Unidos'),
    ]

def get_product_type_choices():
    """Retorna las opciones de tipos de producto SILICIE para un campo Selection (solo alcohol)."""
    return [
        ('AL', 'Alcohol'),
    ]

def get_profile_choices():
    """Retorna las opciones de perfiles CSV SILICIE para un campo Selection."""
    return [
        ('IESA1CSV', 'Alcohol - IESA1CSV'),
    ]
