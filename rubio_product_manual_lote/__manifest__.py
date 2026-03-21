{
    'name': 'Rubio Product Manual Lote',
    'version': '1.0.0',
    'category': 'Custom',
    'summary': 'Añade campo de lote manual informativo en líneas de pedidos de venta',
    'author': 'Xtendoo',
    'license': 'LGPL-3',
    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/report_saleorder_document_manual_lot.xml',
        'wizard/manual_lot_traceability_wizard_views.xml',
        'views/manual_lot_traceability_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
