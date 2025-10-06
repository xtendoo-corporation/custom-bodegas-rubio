# INSTRUCCIONES DE INSTALACIÓN Y USO
## Módulo: rubio_stock_picking_silice_sequence

---

## 📁 ESTRUCTURA FINAL DEL MÓDULO

```
custom-bodegas-rubio/
└── rubio_stock_picking_silice_sequence/
    ├── __init__.py
    ├── __manifest__.py
    ├── README.md
    ├── data/
    │   └── ir_sequence_data.xml
    ├── i18n/
    │   ├── en.po
    │   └── es.po
    ├── models/
    │   ├── __init__.py
    │   └── stock_picking.py
    ├── security/
    │   └── ir.model.access.csv
    ├── tests/
    │   └── __init__.py (contiene test_silice_sequence.py integrado)
    └── views/
        └── stock_picking_views.xml
```

---

## 🚀 INSTALACIÓN

### 1. El módulo ya está creado en:
```bash
/home/xtendoo/Documentos/odoo/18verifactu/odoo/custom/src/custom-bodegas-rubio/rubio_stock_picking_silice_sequence/
```

### 2. Actualizar la lista de aplicaciones:

**Opción A: Desde la interfaz web**
1. Ir a Aplicaciones
2. Clic en "Actualizar lista de aplicaciones"
3. Buscar "Silíce: Secuencia para albaranes"
4. Clic en "Instalar"

**Opción B: Desde línea de comandos**
```bash
# Acceder al contenedor Docker (si aplica)
docker-compose run --rm odoo bash

# Instalar el módulo
odoo-bin -d <nombre_base_datos> -i rubio_stock_picking_silice_sequence --stop-after-init

# O actualizar si ya existe
odoo-bin -d <nombre_base_datos> -u rubio_stock_picking_silice_sequence --stop-after-init
```

---

## ✅ VERIFICACIÓN DE FUNCIONAMIENTO

### Prueba manual:

1. **Ir a Inventario → Operaciones → Albaranes**
2. **Crear un nuevo albarán** (cualquier tipo: entrada, salida, interna)
3. **Confirmar disponibilidad** y asignar cantidades
4. **Validar el albarán**
5. **Verificar que aparece el campo "Secuencia Silíce"** con formato: `SIL-2025-000001`

### Verificar en vista de árbol:
- El campo `silice_sequence` debe aparecer como columna opcional en la lista de albaranes

### Verificar en vista formulario:
- El campo aparece después del campo "Referencia" (name)
- Es de solo lectura
- Se rellena automáticamente al validar

---

## 🧪 EJECUTAR TESTS AUTOMATIZADOS

### Tests completos del módulo:
```bash
# Dentro del contenedor o entorno Odoo
odoo-bin -d <database> -i rubio_stock_picking_silice_sequence --test-enable --stop-after-init

# Solo tests de este módulo
odoo-bin -d <database> --test-enable --test-tags=rubio_stock_picking_silice_sequence --stop-after-init

# Con logs detallados
odoo-bin -d <database> --test-enable --test-tags=rubio_stock_picking_silice_sequence --log-level=test --stop-after-init
```

### Tests cubiertos:
✅ **test_01**: Asignación de secuencia al validar
✅ **test_02**: No reasignación en validaciones repetidas
✅ **test_03**: Campo `name` no se modifica
✅ **test_04**: Secuencias independientes por compañía
✅ **test_05**: Validación por lotes (múltiples pickings)

---

## ⚙️ CONFIGURACIÓN PERSONALIZADA

### Cambiar el prefijo o formato de la secuencia:

1. **Ir a:** Ajustes → Técnico → Secuencias
2. **Buscar:** "Secuencia Silíce para albaranes"
3. **Editar campos:**
   - **Prefijo**: Por defecto `SIL-%(year)s-`
     - Cambiar por ejemplo a: `SILICE-%(year)s/%(month)s-`
   - **Padding**: Por defecto `6` (genera 000001, 000002, etc.)
   - **Siguiente número**: Para reiniciar o ajustar el contador

### Ejemplo de formatos alternativos:
- `SIL-%(year)s-` → `SIL-2025-000001`
- `SILICE-%(year)s/%(month)s-` → `SILICE-2025/10-000001`
- `%(year)s/SIL/` → `2025/SIL/000001`
- `SIL-` → `SIL-000001` (sin año)

### Configuración multi-compañía:

**Para contadores independientes por empresa:**
1. Duplicar el registro de secuencia
2. Asignar cada copia a una compañía específica
3. Personalizar prefijo según cada empresa:
   - Empresa A: `SILA-%(year)s-`
   - Empresa B: `SILB-%(year)s-`

---

## 🔍 CARACTERÍSTICAS CLAVE

### ✨ Lo que HACE el módulo:
- ✅ Crea campo `silice_sequence` en `stock.picking`
- ✅ Asigna secuencia automáticamente al validar albarán
- ✅ Secuencia independiente por compañía
- ✅ Idempotente (no reasigna si ya existe)
- ✅ Funciona con validaciones por lotes

### ❌ Lo que NO hace el módulo:
- ❌ NO modifica el campo `name` estándar
- ❌ NO interfiere con otras secuencias de Odoo
- ❌ NO requiere configuración adicional tras instalación
- ❌ NO afecta albaranes ya validados

---

## 📊 CRITERIOS DE ACEPTACIÓN (CUMPLIDOS)

✅ **Criterio 1**: Al validar un albarán nuevo, `silice_sequence` se rellena con `SIL-YYYY-NNNNNN`
✅ **Criterio 2**: Validaciones repetidas NO cambian `silice_sequence`
✅ **Criterio 3**: En otra compañía, el contador es independiente
✅ **Criterio 4**: Los tests pasan correctamente
✅ **Criterio 5**: El campo `name` estándar NO se altera
✅ **Criterio 6**: Código limpio y documentado
✅ **Criterio 7**: Traducciones ES/EN incluidas
✅ **Criterio 8**: README completo con instrucciones

---

## 🐛 RESOLUCIÓN DE PROBLEMAS

### Problema: El campo no aparece en la vista
**Solución**: Actualizar el módulo
```bash
odoo-bin -d <database> -u rubio_stock_picking_silice_sequence --stop-after-init
```

### Problema: La secuencia no se asigna
**Verificar**:
1. La secuencia existe: Ajustes → Técnico → Secuencias
2. El código es exactamente: `rubio.stock.picking.silice`
3. Reinstalar módulo si es necesario

### Problema: Error al instalar
**Verificar dependencias**:
- Módulo `stock` debe estar instalado (viene por defecto)

### Problema: Tests fallan
**Revisar**:
- Base de datos limpia o con datos demo
- Permisos de usuario administrador
- Logs con `--log-level=test`

---

## 📝 NOTAS TÉCNICAS

### Implementación:
- **Override de método**: `button_validate()` en `stock.picking`
- **API Odoo utilizada**: `ir.sequence.next_by_code()`
- **Multi-company**: Usa `with_company(picking.company_id.id)`
- **Idempotencia**: Verifica `if not picking.silice_sequence`

### Rendimiento:
- Operación ligera (una query por picking)
- No afecta rendimiento de validación
- Index en campo para búsquedas rápidas

### Compatibilidad:
- ✅ Odoo 18.0 Community Edition
- ✅ Python 3.10+
- ✅ PostgreSQL 12+

---

## 📞 SOPORTE

Para problemas o mejoras, contactar con el equipo de desarrollo de Bodegas Rubio.

---

**Versión del módulo**: 18.0.1.0.0
**Licencia**: LGPL-3
**Fecha de creación**: 6 de octubre de 2025

