import sys
from rubio_silice_report.models.silicie_specs import generate_csv_content

row_data = {
    'referencia_interna': 'REF123',
    'fecha_movimiento': '08/10/2025',
    'fecha_registro_contable': '08/10/2025',
    'tipo_movimiento': 'A08',
    'numero_silice': 'SIL123',
    'cae': 'CAE123456789012',
    'tipo_establecimiento': 'FA',
    'fecha_presentacion': '08/10/2025',
    'version_fichero': '1.0',
    'fecha_asiento': '08/10/2025',
    'codigo_producto': 'PROD001',
    'graduacion': '40',
    'cantidad': '100.000',
    'unidad_medida': 'LTS',
    'destino_nif': 'B12345678',
    'destino_nombre': 'Cliente S.A.',
    'destino_direccion': 'Calle Ejemplo 1',
    'destino_pais': 'ES',
    'num_justificante': 'JUS12345',
    'tipo_justificante': 'FA',
    'observaciones': 'Sin observaciones'
}

csv_bytes = generate_csv_content([row_data], profile_key='IESA1CSV', include_header=True)
with open('test_silicie.csv', 'wb') as f:
    f.write(csv_bytes)
print('CSV generado correctamente. Revisa test_silicie.csv para comprobar que no hay desplazamientos.')

