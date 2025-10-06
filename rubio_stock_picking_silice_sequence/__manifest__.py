{
    "name": "Silíce: Secuencia para albaranes",
    "version": "18.0.1.0.0",
    "category": "Inventory/Inventory",
    "summary": "Añade secuencia personalizada Silíce a albaranes sin modificar la secuencia estándar",
    "description": """
        Silíce: Secuencia personalizada para albaranes
        ==============================================

        Este módulo añade una secuencia independiente para albaranes (stock.picking)
        que se asigna automáticamente al validar, sin modificar la secuencia estándar
        del campo 'name'.

        Características:
        ----------------
        * Nueva secuencia 'rubio.stock.picking.silice' con prefijo SIL-YYYY-NNNNNN
        * Campo silice_sequence en albaranes (solo lectura, indexado)
        * Asignación automática al validar (button_validate)
        * Soporte multi-compañía (secuencias independientes por empresa)
        * Idempotente: no reasigna si ya existe valor
        * No modifica el campo 'name' estándar de Odoo

        Configuración:
        --------------
        El prefijo y padding se pueden personalizar desde:
        Ajustes → Técnico → Secuencias → Buscar "Secuencia Silíce para albaranes"
    """,
    "author": "Bodegas Rubio",
    "website": "https://www.bodegasrubio.com",
    "license": "LGPL-3",
    "depends": ["stock"],
    "data": [
        "data/ir_sequence_data.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
