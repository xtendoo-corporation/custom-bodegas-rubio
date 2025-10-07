{
    "name": "Rubio SILICIE Report",
    "version": "18.0.1.0.0",
    "summary": "Exportación CSV SILICIE 2.0 de entregas (n.º de sílice como primera columna).",
    "author": "custom-bodegas-rubio",
    "website": "https://xtendoo.es",
    "category": "Inventory/Reporting",
    "license": "LGPL-3",
    "depends": ["stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/actions.xml",
        "views/res_config_settings_view.xml",
        "views/silice_report_wizard_views.xml",
        "views/menuitems.xml",
    ],
    "installable": True,
    "application": False,
}
