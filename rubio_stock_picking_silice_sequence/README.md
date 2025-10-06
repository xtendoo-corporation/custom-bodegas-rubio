# Silíce: Secuencia para albaranes

## Descripción

Este módulo añade una secuencia personalizada independiente para albaranes (stock.picking) que se asigna automáticamente al validar, sin modificar ni interferir con la secuencia estándar del campo `name` de Odoo.

## Características

- **Nueva secuencia**: `rubio.stock.picking.silice` con prefijo configurable `SIL-%(year)s-` y padding de 6 dígitos
- **Campo personalizado**: `silice_sequence` (Char, solo lectura, indexado) en `stock.picking`
- **Asignación automática**: Al validar un albarán (`button_validate`), si el campo está vacío, se asigna el siguiente número
- **Multi-compañía**: Soporte completo con secuencias independientes por empresa
- **Idempotente**: No reasigna si el albarán ya tiene un valor en `silice_sequence`
- **No invasivo**: No modifica el campo `name` estándar ni otras secuencias de Odoo

## Requisitos

- Odoo 18.0 Community Edition
- Módulo `stock` (instalado por defecto)

## Instalación

1. Copiar la carpeta `rubio_stock_picking_silice_sequence` al repositorio `custom-bodegas-rubio`
2. Actualizar la lista de aplicaciones:
   ```bash
   odoo-bin -d <database> -u all
   ```
   O desde la interfaz: Aplicaciones → Actualizar lista de aplicaciones
3. Buscar "Silíce: Secuencia para albaranes" e instalar

## Uso

Una vez instalado, el módulo funciona automáticamente:

1. Crear un albarán (picking) de cualquier tipo (entrada, salida, interna, fabricación, etc.)
2. Al validar el albarán, el sistema asignará automáticamente el siguiente número de secuencia Silíce
3. El valor quedará guardado en el campo `silice_sequence` y será visible en la vista del albarán
4. El campo `name` estándar de Odoo no se ve afectado

### Ejemplo de secuencia generada

```
SIL-2025-000001
SIL-2025-000002
SIL-2025-000003
...
```

## Configuración

Para personalizar el prefijo, padding o reiniciar la secuencia:

1. Ir a **Ajustes → Técnico → Secuencias**
2. Buscar "Secuencia Silíce para albaranes"
3. Editar los campos:
   - **Prefijo**: Cambiar `SIL-%(year)s-` por el formato deseado
   - **Padding**: Número de dígitos (por defecto 6)
   - **Siguiente número**: Para reiniciar o ajustar el contador
   - **Compañía**: Seleccionar compañía específica o dejar vacío para todas

### Multi-compañía

El módulo soporta multi-compañía automáticamente. Cada empresa tendrá su propio contador independiente. Para configurar por compañía:

1. Duplicar la secuencia desde Ajustes → Técnico → Secuencias
2. Asignar cada copia a una compañía específica
3. Personalizar prefijo/formato según necesidad de cada empresa

## Pruebas

Para ejecutar los tests automatizados:

```bash
# Tests unitarios completos
odoo-bin -d <database> -i rubio_stock_picking_silice_sequence --test-enable --stop-after-init

# Tests específicos del módulo
odoo-bin -d <database> --test-enable --test-tags rubio_stock_picking_silice_sequence
```

Los tests cubren:
- ✅ Asignación de secuencia al validar
- ✅ No reasignación en validaciones repetidas
- ✅ Contadores independientes por compañía
- ✅ Preservación del campo `name` estándar
- ✅ Validación por lotes (múltiples pickings)

## Compatibilidad

- **Odoo**: 18.0 Community Edition
- **Python**: 3.10+
- **Base de datos**: PostgreSQL 12+

## Licencia

LGPL-3

## Autor

Bodegas Rubio

## Soporte

Para reportar problemas o solicitar mejoras, contactar con el equipo de desarrollo.
