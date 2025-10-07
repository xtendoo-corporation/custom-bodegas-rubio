{
    'name': 'Rubio Product Box Units',
    'version': '1.0',
    'category': 'Custom',
    'summary': 'Agrega campos de cajas y unidades por caja a facturas y ventas',
    'depends': ['sale', 'account'],
    'data': [
        'views/product_template_views.xml',
        'views/account_move_views.xml',
        'views/sale_order_views.xml',
        'views/report_invoice_document_box_units.xml',
        'views/report_saleorder_document_box_units.xml',
        'data/report_invoice_document_box_units_action.xml',
    ],
    'installable': True,
    'auto_install': False,
}
