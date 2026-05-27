# Rubio Stock Picking Albaran Valorado

Este modulo crea formatos de impresion para `sale.order`:

- **Albaran valorado**
- **Albaran sin valorar**
- **Albaran valorado (direccion entrega)**
- **Albaran sin valorar (direccion entrega)**

## Incluye

- Copia del formato de pedido para imprimir desde el propio pedido de venta.
- Columna **Lote manual** por linea, usando el campo `manual_lot` de `rubio_product_manual_lote`.
- Columna **Desglose impuestos** por linea (campo `tax_breakdown_display`).
- Totales por tipo de impuesto en el pie del documento.
- Version sin valorar sin precios ni totales.
- Versiones de direccion de entrega que muestran la direccion de envio en lugar de cliente/facturacion.

## Dependencias

- `sale`
- `rubio_product_manual_lote`
- `rubio_account_tax_line_breakdown`

