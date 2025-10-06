{
    'name': "Silíce: Secuencia para albaranes de salida",
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Añade una secuencia específica para albaranes de salida',
    'description': '''
        Este módulo añade una nueva secuencia específica para albaranes de salida (SIL-) que:
        * Se aplica solo a albaranes de salida (entregas)
        * No interfiere con la numeración estándar de los albaranes
        * Es configurable por compañía
        * Se asigna automáticamente al validar el albarán de salida
    ''',
    'author': 'Bodegas Rubio',
    'website': 'https://www.bodegas-rubio.com',
    'depends': ['stock'],
    'data': [
        'data/ir_sequence_data.xml',
        'views/stock_picking_views.xml',
        'views/stock_picking_tree.xml',
        'security/ir.model.access.csv',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
