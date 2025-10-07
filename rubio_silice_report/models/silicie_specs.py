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
# PERFILES CSV SILICIE 2.0
# ============================================================================
# Cada perfil define: separador, codificación, orden EXACTO de campos,
# formatos de fecha/hora, versión del fichero, etc.

SILICIE_PROFILES = {
    'IESH1CSV': {
        'name': 'Altas – Hidrocarburos',
        'group': 'hidrocarburos',
        'separator': ';',
        'encoding': 'utf-8-sig',  # UTF-8 con BOM
        'decimal_separator': ',',
        'date_format': '%d/%m/%Y',
        'datetime_format': '%d/%m/%Y %H:%M:%S',
        'version': '1.0',
        'fields': [
            # Primera columna: número de sílice
            {'name': 'numero_silice', 'required': True, 'type': 'char', 'length': 20},

            # Bloque Identificación Establecimiento
            {'name': 'cae', 'required': True, 'type': 'char', 'length': 16},
            {'name': 'tipo_establecimiento', 'required': True, 'type': 'char', 'length': 2},

            # Bloque Presentación
            {'name': 'fecha_presentacion', 'required': True, 'type': 'datetime', 'format': 'datetime_format'},
            {'name': 'version_fichero', 'required': True, 'type': 'char', 'length': 10},

            # Bloque Datos del Asiento
            {'name': 'fecha_asiento', 'required': True, 'type': 'date', 'format': 'date_format'},
            {'name': 'tipo_movimiento', 'required': True, 'type': 'char', 'length': 3},
            {'name': 'codigo_producto', 'required': True, 'type': 'char', 'length': 20},
            {'name': 'tipo_producto', 'required': True, 'type': 'char', 'length': 2},
            {'name': 'cantidad', 'required': True, 'type': 'float', 'decimals': 3},
            {'name': 'unidad_medida', 'required': True, 'type': 'char', 'length': 3},
            {'name': 'densidad', 'required': False, 'type': 'float', 'decimals': 4},
            {'name': 'temperatura', 'required': False, 'type': 'float', 'decimals': 2},
            {'name': 'destino_nif', 'required': False, 'type': 'char', 'length': 15},
            {'name': 'destino_nombre', 'required': False, 'type': 'char', 'length': 100},
            {'name': 'destino_direccion', 'required': False, 'type': 'char', 'length': 200},
            {'name': 'destino_pais', 'required': False, 'type': 'char', 'length': 2},
            {'name': 'num_justificante', 'required': False, 'type': 'char', 'length': 30},
            {'name': 'tipo_justificante', 'required': False, 'type': 'char', 'length': 2},
            {'name': 'observaciones', 'required': False, 'type': 'char', 'length': 500},
        ],
    },
    'IEST1CSV': {
        'name': 'Altas – Tabaco',
        'group': 'tabaco',
        'separator': ';',
        'encoding': 'utf-8-sig',
        'decimal_separator': ',',
        'date_format': '%d/%m/%Y',
        'datetime_format': '%d/%m/%Y %H:%M:%S',
        'version': '1.0',
        'fields': [
            # Primera columna: número de sílice
            {'name': 'numero_silice', 'required': True, 'type': 'char', 'length': 20},

            # Bloque Identificación Establecimiento
            {'name': 'cae', 'required': True, 'type': 'char', 'length': 16},
            {'name': 'tipo_establecimiento', 'required': True, 'type': 'char', 'length': 2},

            # Bloque Presentación
            {'name': 'fecha_presentacion', 'required': True, 'type': 'datetime', 'format': 'datetime_format'},
            {'name': 'version_fichero', 'required': True, 'type': 'char', 'length': 10},

            # Bloque Datos del Asiento
            {'name': 'fecha_asiento', 'required': True, 'type': 'date', 'format': 'date_format'},
            {'name': 'tipo_movimiento', 'required': True, 'type': 'char', 'length': 3},
            {'name': 'codigo_producto', 'required': True, 'type': 'char', 'length': 20},
            {'name': 'tipo_producto', 'required': True, 'type': 'char', 'length': 2},
            {'name': 'marca_comercial', 'required': False, 'type': 'char', 'length': 100},
            {'name': 'cantidad', 'required': True, 'type': 'float', 'decimals': 3},
            {'name': 'unidad_medida', 'required': True, 'type': 'char', 'length': 3},
            {'name': 'precio_venta', 'required': False, 'type': 'float', 'decimals': 2},
            {'name': 'destino_nif', 'required': False, 'type': 'char', 'length': 15},
            {'name': 'destino_nombre', 'required': False, 'type': 'char', 'length': 100},
            {'name': 'destino_direccion', 'required': False, 'type': 'char', 'length': 200},
            {'name': 'destino_pais', 'required': False, 'type': 'char', 'length': 2},
            {'name': 'num_justificante', 'required': False, 'type': 'char', 'length': 30},
            {'name': 'tipo_justificante', 'required': False, 'type': 'char', 'length': 2},
            {'name': 'observaciones', 'required': False, 'type': 'char', 'length': 500},
        ],
    },
    'IESA1CSV': {
        'name': 'Altas – Alcohol y Bebidas Alcohólicas',
        'group': 'alcohol',
        'separator': ';',
        'encoding': 'utf-8-sig',
        'decimal_separator': ',',
        'date_format': '%d/%m/%Y',
        'datetime_format': '%d/%m/%Y %H:%M:%S',
        'version': '1.0',
        'fields': [
            # Primera columna: número de sílice
            {'name': 'numero_silice', 'required': True, 'type': 'char', 'length': 20},

            # Bloque Identificación Establecimiento
            {'name': 'cae', 'required': True, 'type': 'char', 'length': 16},
            {'name': 'tipo_establecimiento', 'required': True, 'type': 'char', 'length': 2},

            # Bloque Presentación
            {'name': 'fecha_presentacion', 'required': True, 'type': 'datetime', 'format': 'datetime_format'},
            {'name': 'version_fichero', 'required': True, 'type': 'char', 'length': 10},

            # Bloque Datos del Asiento
            {'name': 'fecha_asiento', 'required': True, 'type': 'date', 'format': 'date_format'},
            {'name': 'tipo_movimiento', 'required': True, 'type': 'char', 'length': 3},
            {'name': 'codigo_producto', 'required': True, 'type': 'char', 'length': 20},
            {'name': 'tipo_producto', 'required': True, 'type': 'char', 'length': 2},
            {'name': 'graduacion', 'required': False, 'type': 'float', 'decimals': 2},
            {'name': 'cantidad', 'required': True, 'type': 'float', 'decimals': 3},
            {'name': 'unidad_medida', 'required': True, 'type': 'char', 'length': 3},
            {'name': 'destino_nif', 'required': False, 'type': 'char', 'length': 15},
            {'name': 'destino_nombre', 'required': False, 'type': 'char', 'length': 100},
            {'name': 'destino_direccion', 'required': False, 'type': 'char', 'length': 200},
            {'name': 'destino_pais', 'required': False, 'type': 'char', 'length': 2},
            {'name': 'num_justificante', 'required': False, 'type': 'char', 'length': 30},
            {'name': 'tipo_justificante', 'required': False, 'type': 'char', 'length': 2},
            {'name': 'observaciones', 'required': False, 'type': 'char', 'length': 500},
        ],
    },
}


# ============================================================================
# TABLAS Y CÓDIGOS SILICIE
# ============================================================================

# Tipos de Establecimiento SILICIE
ESTABLISHMENT_TYPES = {
    'FA': 'Fábrica',
    'DE': 'Depósito Fiscal',
    'EX': 'Exportador',
    'IM': 'Importador',
    'DT': 'Destinatario Registrado',
    'OP': 'Operador Registrado',
    'RE': 'Representante Fiscal',
}

# Tipos de Movimiento SILICIE (Salidas)
MOVEMENT_TYPES = {
    'A08': 'Salida a consumo - territorio interior',
    'A09': 'Salida a consumo - Canarias, Ceuta o Melilla',
    'A10': 'Salida en régimen suspensivo - UE',
    'A11': 'Salida en régimen suspensivo - exportación',
    'A12': 'Salida para entrega exenta',
    'A13': 'Salida para uso de las fuerzas armadas de un Estado miembro',
    'A14': 'Salida para venta a bordo',
    'A15': 'Otras salidas',
    'A16': 'Salida para destrucción',
    'A17': 'Salida a otro depósito fiscal del mismo titular',
}

# Tipos de Justificante
JUSTIFICANT_TYPES = {
    'FA': 'Factura',
    'AL': 'Albarán',
    'DU': 'DUA',
    'DA': 'Documento Administrativo',
    'ED': 'e-DA (Documento Administrativo Electrónico)',
    'OT': 'Otro',
}

# Unidades de Medida
UNIT_MEASURES = {
    'LTS': 'Litros',
    'KGS': 'Kilogramos',
    'UNI': 'Unidades',
    'CAJ': 'Cajas',
    'HL': 'Hectolitros',
    'HPA': 'Hectolitros de alcohol puro',
}

# Códigos de País (ISO 3166-1 alpha-2)
COUNTRY_CODES = {
    'ES': 'España',
    'FR': 'Francia',
    'DE': 'Alemania',
    'IT': 'Italia',
    'PT': 'Portugal',
    'GB': 'Reino Unido',
    'US': 'Estados Unidos',
    # Añadir más según necesidad
}


# ============================================================================
# FUNCIONES DE FORMATO Y VALIDACIÓN
# ============================================================================

def format_date(date_obj, profile_key='IESH1CSV'):
    """Formatea fecha según el formato del perfil SILICIE."""
    if not date_obj:
        return ''
    profile = SILICIE_PROFILES.get(profile_key, {})
    date_format = profile.get('date_format', '%d/%m/%Y')
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime(date_format)


def format_datetime(datetime_obj, profile_key='IESH1CSV'):
    """Formatea fecha-hora según el formato del perfil SILICIE."""
    if not datetime_obj:
        return ''
    profile = SILICIE_PROFILES.get(profile_key, {})
    datetime_format = profile.get('datetime_format', '%d/%m/%Y %H:%M:%S')
    if isinstance(datetime_obj, str):
        return datetime_obj
    return datetime_obj.strftime(datetime_format)


def format_float(value, decimals=2, profile_key='IESH1CSV'):
    """Formatea número decimal según el separador del perfil."""
    if value is None:
        return ''
    profile = SILICIE_PROFILES.get(profile_key, {})
    decimal_sep = profile.get('decimal_separator', ',')
    formatted = f"{float(value):.{decimals}f}"
    if decimal_sep == ',':
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
    if movement_type not in MOVEMENT_TYPES:
        raise ValidationError(
            f"Tipo de movimiento '{movement_type}' no válido. "
            f"Debe ser uno de: {', '.join(MOVEMENT_TYPES.keys())}"
        )
    return True


def validate_establishment_type(est_type):
    """Valida tipo de establecimiento."""
    if est_type and est_type not in ESTABLISHMENT_TYPES:
        raise ValidationError(
            f"Tipo de establecimiento '{est_type}' no válido. "
            f"Debe ser uno de: {', '.join(ESTABLISHMENT_TYPES.keys())}"
        )
    return True


def validate_unit_measure(unit):
    """Valida unidad de medida."""
    if unit and unit not in UNIT_MEASURES:
        raise ValidationError(
            f"Unidad de medida '{unit}' no válida. "
            f"Debe ser una de: {', '.join(UNIT_MEASURES.keys())}"
        )
    return True


def validate_row(row_data, profile_key='IESH1CSV'):
    """
    Valida una fila completa según el perfil SILICIE.
    row_data: dict con los valores de cada campo
    """
    profile = SILICIE_PROFILES.get(profile_key)
    if not profile:
        raise ValidationError(f"Perfil '{profile_key}' no encontrado.")

    errors = []
    for field_spec in profile['fields']:
        field_name = field_spec['name']
        value = row_data.get(field_name)

        # Validar campos requeridos
        if field_spec.get('required') and not value:
            errors.append(f"Campo '{field_name}' es obligatorio y está vacío.")

        # Validar longitud
        if value and field_spec['type'] == 'char':
            max_len = field_spec.get('length', 0)
            if len(str(value)) > max_len:
                errors.append(
                    f"Campo '{field_name}' excede longitud máxima ({max_len}): '{value}'"
                )

    if errors:
        raise ValidationError('\n'.join(errors))

    return True


def build_csv_row(row_data, profile_key='IESH1CSV'):
    """
    Construye una fila CSV con el orden EXACTO de campos del perfil.
    row_data: dict con los valores
    Retorna: lista de valores en el orden correcto
    """
    profile = SILICIE_PROFILES.get(profile_key)
    if not profile:
        raise ValidationError(f"Perfil '{profile_key}' no encontrado.")

    row = []
    for field_spec in profile['fields']:
        field_name = field_spec['name']
        value = row_data.get(field_name, '')

        # Aplicar formato según tipo
        if field_spec['type'] == 'date' and value:
            value = format_date(value, profile_key)
        elif field_spec['type'] == 'datetime' and value:
            value = format_datetime(value, profile_key)
        elif field_spec['type'] == 'float' and value:
            decimals = field_spec.get('decimals', 2)
            value = format_float(value, decimals, profile_key)
        elif field_spec['type'] == 'char':
            max_len = field_spec.get('length', 0)
            value = truncate_field(value, max_len)

        row.append(str(value) if value else '')

    return row


def build_csv_header(profile_key='IESH1CSV'):
    """Construye la cabecera CSV con nombres de campos del perfil."""
    profile = SILICIE_PROFILES.get(profile_key)
    if not profile:
        raise ValidationError(f"Perfil '{profile_key}' no encontrado.")

    return [field['name'] for field in profile['fields']]


def generate_csv_content(rows_data, profile_key='IESH1CSV', include_header=True):
    """
    Genera el contenido CSV completo.
    rows_data: lista de dicts, cada uno representa una fila
    Retorna: bytes del CSV
    """
    profile = SILICIE_PROFILES.get(profile_key)
    if not profile:
        raise ValidationError(f"Perfil '{profile_key}' no encontrado.")

    output = io.StringIO()
    writer = csv.writer(
        output,
        delimiter=profile['separator'],
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL
    )

    # Cabecera
    if include_header:
        header = build_csv_header(profile_key)
        writer.writerow(header)

    # Filas de datos
    for row_data in rows_data:
        # Validar antes de escribir
        validate_row(row_data, profile_key)
        csv_row = build_csv_row(row_data, profile_key)
        writer.writerow(csv_row)

    # Convertir a bytes con la codificación del perfil
    content = output.getvalue()
    encoding = profile.get('encoding', 'utf-8-sig')
    return content.encode(encoding)


def get_profile_choices():
    """Retorna las opciones de perfiles para un campo Selection."""
    return [(key, val['name']) for key, val in SILICIE_PROFILES.items()]


def get_establishment_type_choices():
    """Retorna las opciones de tipos de establecimiento."""
    return [(key, val) for key, val in ESTABLISHMENT_TYPES.items()]


def get_movement_type_choices():
    """Retorna las opciones de tipos de movimiento."""
    return [(key, val) for key, val in MOVEMENT_TYPES.items()]


def get_unit_measure_choices():
    """Retorna las opciones de unidades de medida."""
    return [(key, val) for key, val in UNIT_MEASURES.items()]

