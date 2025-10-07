    "densidad": 0.755,
    "temperatura": 15.0
  }
}
```

### 3. Crear entregas con número de sílice

- Crear albarán de salida
- Completar campo `x_silice_number` = "SILICE-2025-001"
- Validar entrega

### 4. Exportar CSV

```
Inventario → SILICIE → Exportar Entregas (CSV)
- Fecha inicio: 01/10/2025 00:00:00
- Fecha fin: 07/10/2025 23:59:59
- Perfil: IESH1CSV
- Tipo Movimiento: A08

→ Exportar CSV SILICIE
→ Descarga: ES12345678ABC_IESH1CSV_20251007143045.csv
```

## Troubleshooting

### Error: "Debe configurar el CAE"
**Solución**: Ir a Ajustes → Inventario → SILICIE y configurar el CAE.

### Error: "Los siguientes productos no tienen mapeo SILICIE"
**Solución**: Configurar el mapeo JSON para los productos listados en el error.

### Error: "Campo 'numero_silice' es obligatorio y está vacío"
**Solución**: Asignar número de sílice a los pickings antes de exportar.

### Error: "No se encontraron entregas en el rango"
**Solución**:
- Verificar que hay pickings de tipo 'outgoing' en el rango de fechas
- Si están programados pero no realizados, marcar "Incluir Programados"
- Verificar que los pickings tienen fecha_done o scheduled_date en el rango

### CSV vacío o sin datos
**Solución**: Verificar que:
- Los pickings tienen número de sílice
- Los productos tienen mapeo configurado
- Las líneas tienen qty_done > 0

## Tests

El módulo incluye tests unitarios que validan:

- ✅ Perfiles CSV correctos con orden exacto de campos
- ✅ Validaciones de CAE, tipos de movimiento, establecimiento, unidades
- ✅ Formatos de fecha, hora y decimales
- ✅ Generación de CSV con BOM UTF-8 y separadores correctos
- ✅ Determinación automática de tipo de movimiento según país
- ✅ Exportación completa con validaciones

Ejecutar tests:
```bash
odoo-bin -c odoo.conf -d database -u rubio_silice_report --test-enable --stop-after-init
```

## Soporte Técnico

- **Autor**: custom-bodegas-rubio
- **Website**: https://xtd.es
- **Versión**: 18.0.1.0.0
- **Licencia**: LGPL-3

## Changelog

### 18.0.1.0.0 (2025-10-07)
- Versión inicial
- Soporte para perfiles IESH1CSV, IEST1CSV, IESA1CSV
- Exportación CSV con primera columna número de sílice
- Validaciones según especificación SILICIE 2.0
- Mapeo de productos vía JSON
- Determinación automática de tipo de movimiento
- Tests unitarios completos

## Referencias Legales

- [BOE - Orden HAC/998/2019](https://www.boe.es/buscar/act.php?id=BOE-A-2019-13698)
- [AEAT - SILICIE](https://www.agenciatributaria.es/AEAT.internet/Inicio/La_Agencia_Tributaria/Campanas/SILICIE/_SILICIE_.shtml)
- [AEAT - Información Técnica SILICIE](https://www.agenciatributaria.es/AEAT.internet/Inicio/La_Agencia_Tributaria/Campanas/SILICIE/Informacion_tecnica/Informacion_tecnica.shtml)
- [AEAT - Tablas SILICIE](https://www.agenciatributaria.es/AEAT.internet/Inicio/La_Agencia_Tributaria/Campanas/SILICIE/Tablas/Tablas.shtml)
# Rubio SILICIE Report

Módulo de exportación CSV SILICIE 2.0 para entregas (pickings outgoing) en Odoo 18.

## Descripción

Genera archivos CSV conformes a la especificación SILICIE 2.0 de la AEAT (Agencia Estatal de Administración Tributaria) para la declaración de movimientos de productos sujetos a Impuestos Especiales.

El módulo permite exportar entregas (stock.picking con picking_type_code='outgoing') en formato CSV según los perfiles de importación por fichero definidos por AEAT-SILICIE 2.0.

### Características principales

- ✅ **Primera columna**: Número de sílice (campo configurable)
- ✅ **Perfiles CSV soportados**: IESH1CSV (Hidrocarburos), IEST1CSV (Tabaco), IESA1CSV (Alcohol)
- ✅ **Validaciones**: Campos obligatorios, longitudes, formatos, tablas y códigos SILICIE
- ✅ **Mapeo de productos**: Configuración JSON para identificación de productos según SILICIE
- ✅ **Tipos de movimiento**: A08 (interior), A10 (UE), A11 (exportación), etc.
- ✅ **Filtrado por fechas**: Exportación por rango con normalización de zona horaria
- ✅ **Formato exacto**: UTF-8 con BOM, separador configurado por perfil, formatos de fecha/hora según especificación

## Normativa y Referencias

- **Orden HAC/998/2019** (texto consolidado)
- **Documentación técnica AEAT-SILICIE 2.0**: Importación por fichero
- **Tablas y tipos de movimiento**: [AEAT - SILICIE](https://www.agenciatributaria.es/AEAT.internet/Inicio/La_Agencia_Tributaria/Campanas/SILICIE/_SILICIE_.shtml)

## Instalación

1. Copiar el módulo en el directorio de addons custom:
   ```
   custom-bodegas-rubio/rubio_silice_report/
   ```

2. Actualizar lista de módulos:
   ```
   Aplicaciones → Actualizar lista de aplicaciones
   ```

3. Instalar el módulo:
   ```
   Buscar "Rubio SILICIE Report" → Instalar
   ```

## Configuración

### 1. Configuración SILICIE (Obligatoria)

Ir a: **Ajustes → Inventario → SILICIE 2.0**

#### Parámetros obligatorios:

- **CAE (Código de Actividad Empresarial)**: Código del establecimiento SILICIE (máx. 16 caracteres)
  - Ejemplo: `ES12345678ABC`

- **Tipo de Establecimiento**: Según tablas SILICIE
  - `FA` - Fábrica
  - `DE` - Depósito Fiscal
  - `EX` - Exportador
  - `IM` - Importador
  - `DT` - Destinatario Registrado
  - `OP` - Operador Registrado
  - `RE` - Representante Fiscal

- **Grupo Impositivo SILICIE**: Seleccionar el grupo de productos
  - Hidrocarburos
  - Tabaco / LCE
  - Alcohol y Bebidas Alcohólicas

- **Perfil CSV de Importación**: Perfil SILICIE 2.0
  - `IESH1CSV` - Altas – Hidrocarburos
  - `IEST1CSV` - Altas – Tabaco
  - `IESA1CSV` - Altas – Alcohol y Bebidas Alcohólicas

#### Parámetros opcionales:

- **Zona Horaria**: Para formateo de fechas (por defecto: `Europe/Madrid`)

- **Campo Número de Sílice**: Nombre del campo en stock.picking que contiene el número de sílice (por defecto: `x_silice_number`)

- **Unidad de Medida por Defecto**: Unidad SILICIE para cantidades
  - `LTS` - Litros (por defecto)
  - `KGS` - Kilogramos
  - `UNI` - Unidades
  - `CAJ` - Cajas
  - `HL` - Hectolitros
  - `HPA` - Hectolitros de alcohol puro

- **Tipo de Movimiento por Defecto**: Tipo de movimiento SILICIE
  - `A08` - Salida a consumo - territorio interior (por defecto)
  - `A09` - Salida a consumo - Canarias, Ceuta o Melilla
  - `A10` - Salida en régimen suspensivo - UE
  - `A11` - Salida en régimen suspensivo - exportación
  - `A12` - Salida para entrega exenta
  - Otros...

### 2. Configurar Mapeo de Productos (Obligatorio)

El mapeo de productos se configura en formato JSON en el campo **Mapeo de Productos (JSON)**.

#### Formato del JSON:

```json
{
  "PRODUCT_ID": {
    "codigo_producto": "CODIGO_SILICIE",
    "tipo_producto": "TIPO",
    "unidad_medida": "LTS",
    "campo_especifico_1": "valor",
    "campo_especifico_2": "valor"
  }
}
```

#### Ejemplo para Hidrocarburos (IESH1CSV):

```json
{
  "123": {
    "codigo_producto": "GASOIL_A",
    "tipo_producto": "HI",
    "unidad_medida": "LTS",
    "densidad": 0.85,
    "temperatura": 15.0
  },
  "124": {
    "codigo_producto": "GASOLINA_95",
    "tipo_producto": "HI",
    "unidad_medida": "LTS",
    "densidad": 0.75,
    "temperatura": 15.0
  }
}
```

#### Ejemplo para Tabaco (IEST1CSV):

```json
{
  "200": {
    "codigo_producto": "MARLBORO_RED",
    "tipo_producto": "TB",
    "marca_comercial": "Marlboro",
    "unidad_medida": "CAJ",
    "precio_venta": 5.50
  }
}
```

#### Ejemplo para Alcohol (IESA1CSV):

```json
{
  "300": {
    "codigo_producto": "VINO_TINTO",
    "tipo_producto": "AL",
    "graduacion": 13.5,
    "unidad_medida": "LTS"
  }
}
```

**Nota**: El PRODUCT_ID es el ID interno de Odoo del producto. Puedes obtenerlo desde:
- Vista de desarrollador → Producto → Ver metadatos
- O desde la URL al editar un producto: `/web#id=123&model=product.product`

### 3. Configurar Campo de Número de Sílice en Pickings

El módulo espera que los pickings tengan un campo que contenga el número de sílice. Por defecto busca el campo `x_silice_number`.

#### Opción A: Crear el campo personalizado

1. Ir a: **Ajustes → Técnico → Campos**
2. Crear nuevo campo:
   - Modelo: `stock.picking`
   - Nombre del campo: `x_silice_number`
   - Tipo: `Char`
   - Etiqueta: `Número de Sílice`

#### Opción B: Usar otro campo existente

Si ya tienes un campo con el número de sílice (por ejemplo, desde otro módulo), configúralo en:
**Ajustes → Inventario → SILICIE → Campo Número de Sílice**

## Uso

### Exportar Entregas a CSV SILICIE

1. Ir a: **Inventario → SILICIE → Exportar Entregas (CSV)**

2. En el wizard, configurar:
   - **Fecha Inicio**: Fecha de inicio del rango de exportación
   - **Fecha Fin**: Fecha de fin del rango de exportación
   - **Incluir Programados**: Marcar si se quieren incluir pickings en estado 'assigned' usando scheduled_date
   - **Perfil CSV SILICIE**: Seleccionar el perfil (se carga automáticamente desde configuración)
   - **Tipo de Movimiento**: Seleccionar el tipo (el wizard lo determina automáticamente según país destino)

3. Clic en **Exportar CSV SILICIE**

4. Se descargará un archivo CSV con formato:
   ```
   CAE_PERFIL_YYYYMMDDHHMMSS.csv
   ```
   Ejemplo: `ES12345678ABC_IESH1CSV_20251007143045.csv`

### Determinación Automática del Tipo de Movimiento

El módulo determina automáticamente el tipo de movimiento según el país destino del partner:

- **España (ES)**: `A08` - Salida a consumo - territorio interior
- **Países UE**: `A10` - Salida en régimen suspensivo - UE
- **Resto del mundo**: `A11` - Salida en régimen suspensivo - exportación

Puedes sobreescribir manualmente el tipo de movimiento en el wizard si es necesario.

## Validaciones

El módulo realiza las siguientes validaciones antes de exportar:

### Validaciones de Configuración:
- ✅ CAE configurado y con longitud válida (máx. 16 caracteres)
- ✅ Perfil CSV seleccionado y válido
- ✅ Rango de fechas correcto (fecha inicio ≤ fecha fin)

### Validaciones de Datos:
- ✅ Tipo de movimiento existe en tablas SILICIE
- ✅ Tipo de establecimiento válido
- ✅ Unidades de medida válidas
- ✅ Todos los productos tienen mapeo configurado (si falta, lista los productos faltantes)
- ✅ Campos obligatorios según perfil completados
- ✅ Longitudes de campos respetadas
- ✅ Formatos de fecha/hora según especificación

### Validaciones de Pickings:
- ✅ Solo pickings de tipo 'outgoing' (entregas)
- ✅ Estado 'done' o 'assigned' (si incluir programados)
- ✅ Número de sílice presente
- ✅ Cantidad realizada > 0

## Estructura del CSV

El CSV generado sigue **exactamente** el orden de campos exigido por el perfil SILICIE 2.0 seleccionado.

### Características del CSV:
- **Codificación**: UTF-8 con BOM
- **Separador**: `;` (punto y coma)
- **Separador decimal**: `,` (coma)
- **Formato fecha**: `DD/MM/YYYY`
- **Formato fecha-hora**: `DD/MM/YYYY HH:MM:SS`

### Estructura de columnas (ejemplo IESH1CSV):

| Columna | Campo | Descripción | Obligatorio |
|---------|-------|-------------|-------------|
| 1 | numero_silice | Número de sílice | Sí |
| 2 | cae | Código Actividad Empresarial | Sí |
| 3 | tipo_establecimiento | Tipo de establecimiento | Sí |
| 4 | fecha_presentacion | Fecha/hora presentación | Sí |
| 5 | version_fichero | Versión del fichero | Sí |
| 6 | fecha_asiento | Fecha del asiento | Sí |
| 7 | tipo_movimiento | Tipo de movimiento (A08, A10...) | Sí |
| 8 | codigo_producto | Código del producto | Sí |
| 9 | tipo_producto | Tipo de producto | Sí |
| 10 | cantidad | Cantidad | Sí |
| 11 | unidad_medida | Unidad de medida (LTS, KGS...) | Sí |
| 12 | densidad | Densidad (solo hidrocarburos) | No |
| 13 | temperatura | Temperatura (solo hidrocarburos) | No |
| 14 | destino_nif | NIF del destinatario | No |
| 15 | destino_nombre | Nombre del destinatario | No |
| 16 | destino_direccion | Dirección del destinatario | No |
| 17 | destino_pais | País del destinatario (ISO 2) | No |
| 18 | num_justificante | Número de justificante | No |
| 19 | tipo_justificante | Tipo de justificante | No |
| 20 | observaciones | Observaciones | No |

**Nota**: Los campos específicos varían según el perfil (IESH1CSV, IEST1CSV, IESA1CSV).

## Ejemplo de Flujo Completo

### 1. Configuración inicial

```
Ajustes → Inventario → SILICIE 2.0:
- CAE: ES12345678ABC
- Tipo Establecimiento: DE (Depósito Fiscal)
- Grupo: Hidrocarburos
- Perfil CSV: IESH1CSV
- Zona Horaria: Europe/Madrid
- Campo Sílice: x_silice_number
- UM por defecto: LTS
- Tipo Movimiento: A08
```

### 2. Mapeo de productos

```json
{
  "45": {
    "codigo_producto": "GASOIL_A",
    "tipo_producto": "HI",
    "unidad_medida": "LTS",
    "densidad": 0.845,
    "temperatura": 15.0
  },
  "46": {
    "codigo_producto": "GASOLINA_95",
    "tipo_producto": "HI",
    "unidad_medida": "LTS",

