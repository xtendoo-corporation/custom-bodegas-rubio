{
    'name': 'Rubio Account Tax Line Breakdown',
    'version': '18.0.1.0.0',
    'category': 'Custom',
    'summary': 'Muestra el desglose de impuestos por línea en facturas, pedidos y presupuestos',
    'author': 'Bodegas Rubio, Xtendoo SLU',
    'depends': ['sale', 'account', 'purchase'],
    'data': [
        'views/account_move_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'report/report_invoice_taxes.xml',
        'report/report_sale_order_taxes.xml',
        'report/report_purchase_order_taxes.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

