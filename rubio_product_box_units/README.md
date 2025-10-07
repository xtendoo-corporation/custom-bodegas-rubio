# Rubio Product Box Units

## Descripción

Este módulo añade funcionalidad de manejo de cajas y unidades por caja para productos en Bodegas Rubio.

## Funcionalidades

* **Campo `box_units` en productos**: Define cuántas unidades contiene una caja del producto
* **Campos `boxes` y `box_units` en líneas de venta**: Permite especificar número de cajas y ver unidades por caja
* **Cálculo automático**: La cantidad total se calcula automáticamente como cajas × unidades por caja
* **Integración completa**: Funciona en pedidos de venta, facturas y todo el ciclo de ventas

## Instalación

1. Copiar este módulo a la carpeta `custom-bodegas-rubio`
2. Actualizar la lista de aplicaciones
3. Buscar "Rubio Product Box Units" e instalar

## Uso

1. **En productos**: Ir a la ficha del producto y configurar el campo "Units per Box"
2. **En pedidos de venta**: Los campos "Cajas" y "Ud/Caja" aparecerán antes de la cantidad
3. **Cálculo automático**: Al cambiar el número de cajas, la cantidad se actualiza automáticamente

## Compatibilidad

* Odoo 18.0 Community
* Dependencias: sale, product, stock, account

## Autor

Bodegas Rubio - 2025
