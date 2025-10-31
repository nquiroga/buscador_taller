# 📊 Configuración del Sistema de Logging Anónimo

Este documento explica cómo configurar el sistema de logging de búsquedas para registrar estadísticas anónimas en Google Sheets.

---

## 🎯 ¿Qué se Registra?

### ✅ Datos que SÍ se registran (anónimos):
- Query de búsqueda (texto ingresado)
- Parámetros de búsqueda (tipo, filtros, años)
- Cantidad de resultados encontrados
- Estadísticas agregadas (% con abstract, acceso abierto, citas promedio)
- Estadísticas de descarga de PDFs (si se intentó)
- Timestamp de la búsqueda
- Session ID anónimo (hash no identificable)

### ❌ Datos que NO se registran:
- IPs de usuarios
- Emails o nombres
- Cookies persistentes
- Ubicación geográfica
- Identificadores personales de ningún tipo

**GDPR-Compliant**: Este logging cumple con GDPR ya que no recopila datos personales.

---

## 📋 Requisitos Previos

1. **Cuenta de Google** (gratuita)
2. **Google Cloud Console** (configuración de 10 minutos)
3. **Streamlit Cloud** (si vas a deployar en la nube)

---

## 🚀 Paso 1: Crear la Hoja de Google Sheets

### 1.1 Crear la Hoja

1. Ve a [Google Sheets](https://sheets.google.com)
2. Crea una nueva hoja
3. Nómbrala: **`openalex_logs`** (o el nombre que prefieras)
4. En la primera fila, agrega estos encabezados:

```
timestamp | session_id | query | search_type | max_results | open_access_filter | year_from | year_to | sort_by | total_found | with_abstract | open_access_count | avg_citations | pdf_download_attempted | pdfs_downloaded | pdfs_failed | pdfs_no_available | pdfs_total_processed
```

**Tip**: Copia y pega esta fila completa en A1:

```
timestamp	session_id	query	search_type	max_results	open_access_filter	year_from	year_to	sort_by	total_found	with_abstract	open_access_count	avg_citations	pdf_download_attempted	pdfs_downloaded	pdfs_failed	pdfs_no_available	pdfs_total_processed
```

### 1.2 Configurar Permisos (Opcional)

- **Privada**: Solo tú puedes ver los datos
- **Compartida**: Comparte con tu equipo con permisos de "Lector"

---

## 🔧 Paso 2: Configurar Google Cloud Console

### 2.1 Crear Proyecto

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto:
   - Click en el selector de proyectos (arriba)
   - **"New Project"**
   - Nombre: `openalex-logger` (o el que prefieras)
   - Click **"Create"**

### 2.2 Habilitar APIs

1. En el proyecto creado, ve a **"APIs & Services"** → **"Library"**
2. Busca y habilita:
   - ✅ **Google Sheets API**
   - ✅ **Google Drive API**

### 2.3 Crear Service Account

1. Ve a **"APIs & Services"** → **"Credentials"**
2. Click en **"Create Credentials"** → **"Service Account"**
3. Configuración:
   - **Service account name**: `streamlit-logger`
   - **Service account ID**: (se genera automáticamente)
   - Click **"Create and Continue"**
4. **Grant access** (opcional):
   - Role: **Editor** (o solo "Sheets Editor" si quieres mínimo privilegio)
   - Click **"Continue"** → **"Done"**

### 2.4 Crear Clave JSON

1. En la lista de Service Accounts, click en el que acabas de crear
2. Ve a la pestaña **"Keys"**
3. Click **"Add Key"** → **"Create new key"**
4. Formato: **JSON**
5. Click **"Create"**
6. Se descarga un archivo JSON (ej: `openalex-logger-abc123.json`)

**⚠️ IMPORTANTE**: Este archivo contiene credenciales. NO lo subas a GitHub ni lo compartas.

---

## 📝 Paso 3: Compartir la Hoja con el Service Account

1. Abre el archivo JSON descargado
2. Busca el campo `"client_email"`:
   ```json
   "client_email": "streamlit-logger@openalex-logger.iam.gserviceaccount.com"
   ```
3. **Copia ese email**
4. Abre tu Google Sheet (`openalex_logs`)
5. Click en **"Share"** (Compartir)
6. Pega el email del service account
7. Permisos: **Editor**
8. **Desactiva** "Notify people" (no es necesario)
9. Click **"Share"**

✅ Ahora el service account puede escribir en la hoja.

---

## 🔐 Paso 4: Configurar Streamlit Secrets

### 4.1 Local (desarrollo)

1. Crea el directorio `.streamlit/` en la raíz del proyecto (si no existe):
   ```bash
   mkdir -p .streamlit
   ```

2. Crea el archivo `.streamlit/secrets.toml`:
   ```bash
   touch .streamlit/secrets.toml
   ```

3. Abre el archivo JSON descargado del service account

4. Copia y pega este contenido en `.streamlit/secrets.toml`, reemplazando los valores con los de tu JSON:

```toml
# Nombre de la hoja de Google Sheets
google_sheets_name = "openalex_logs"

# Credenciales del service account (copiar desde el JSON descargado)
[google_sheets]
type = "service_account"
project_id = "openalex-logger"
private_key_id = "abc123def456..."
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkq...\n-----END PRIVATE KEY-----\n"
client_email = "streamlit-logger@openalex-logger.iam.gserviceaccount.com"
client_id = "123456789012345678901"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/streamlit-logger%40openalex-logger.iam.gserviceaccount.com"
```

**⚠️ IMPORTANTE**:
- El campo `private_key` debe incluir `\n` para los saltos de línea
- NO subas este archivo a GitHub (ya está en `.gitignore`)

5. Agrega `.streamlit/secrets.toml` a `.gitignore`:
   ```bash
   echo ".streamlit/secrets.toml" >> .gitignore
   ```

### 4.2 Streamlit Cloud (producción)

1. Ve a tu app en [Streamlit Cloud](https://share.streamlit.io/)
2. Click en **"⋮"** (menú) → **"Settings"**
3. Ve a la sección **"Secrets"**
4. Pega el mismo contenido del archivo `secrets.toml` (formato TOML)
5. Click **"Save"**
6. La app se reiniciará automáticamente

---

## ✅ Paso 5: Verificar que Funciona

### 5.1 Test Local

1. Ejecuta la app localmente:
   ```bash
   streamlit run app_streamlit.py
   ```

2. Haz una búsqueda de prueba (ej: "machine learning")

3. Revisa tu Google Sheet `openalex_logs`:
   - Debe aparecer una nueva fila con los datos de la búsqueda
   - Si no aparece, revisa la terminal por errores

### 5.2 Debugging

Si no funciona, verifica:

1. **¿La hoja tiene el nombre correcto?**
   - Debe coincidir con `google_sheets_name` en secrets

2. **¿El service account tiene acceso?**
   - Revisa que esté en "Share" de la hoja con permisos de Editor

3. **¿Las credenciales son correctas?**
   - Verifica que copiaste todo el `private_key` (incluye `\n`)

4. **¿Las APIs están habilitadas?**
   - Google Sheets API y Google Drive API en Cloud Console

5. **Terminal con errores:**
   ```
   ⚠️ Logger deshabilitado: ...
   ```
   - Lee el mensaje de error específico

---

## 📊 Paso 6: Analizar los Datos

### Opción A: Directamente en Google Sheets

1. Abre la hoja `openalex_logs`
2. Usa filtros y tablas dinámicas de Sheets
3. Ejemplos de análisis:
   - Queries más frecuentes
   - Distribución de resultados por tipo de búsqueda
   - Tasa de éxito de descarga de PDFs

### Opción B: Google Looker Studio (Dashboard Profesional)

1. Abre tu hoja `openalex_logs`
2. Ve a **"Extensions"** → **"Looker Studio"** → **"Create"**
3. Crea visualizaciones:
   - **Tabla**: Top 10 queries más buscadas
   - **Gráfico de barras**: Resultados promedio por tipo de búsqueda
   - **Serie temporal**: Búsquedas por día
   - **KPIs**: Total de búsquedas, PDFs descargados, tasa de éxito

### Opción C: Exportar a CSV y Analizar en Python/R

```python
import pandas as pd

# Descargar hoja como CSV desde Google Sheets
# File → Download → CSV

df = pd.read_csv('openalex_logs.csv')

# Análisis
print("Top 10 queries:")
print(df['query'].value_counts().head(10))

print("\nPromedio de resultados por tipo de búsqueda:")
print(df.groupby('search_type')['total_found'].mean())
```

---

## 🔒 Seguridad y Privacidad

### Buenas Prácticas

1. ✅ **NO registres datos personales**: Ya está implementado
2. ✅ **Rota las credenciales**: Cambia el service account cada 6-12 meses
3. ✅ **Hoja privada**: No hagas pública la hoja de logs
4. ✅ **Secrets seguros**: Nunca subas `secrets.toml` a GitHub
5. ✅ **Mínimos privilegios**: Service account solo con acceso a esta hoja

### Transparencia con Usuarios

Agrega en la UI (opcional pero recomendado):

```python
# En app_streamlit.py, en el sidebar
st.sidebar.info(
    "ℹ️ Esta app registra búsquedas anónimas (query + resultados) "
    "para análisis académico. No recopilamos datos personales."
)
```

---

## 🛠️ Troubleshooting

### Error: "Module 'gspread' not found"

**Solución**:
```bash
pip install gspread google-auth
```

### Error: "Spreadsheet not found"

**Solución**:
1. Verifica que el nombre en `google_sheets_name` coincide con el nombre real
2. Verifica que compartiste la hoja con el `client_email`

### Error: "Insufficient permissions"

**Solución**:
1. El service account debe tener permisos de **Editor** (no solo Viewer)
2. Revisa que las APIs estén habilitadas en Cloud Console

### Error: "Invalid private key"

**Solución**:
1. Copia el `private_key` completo del JSON, incluyendo:
   - `-----BEGIN PRIVATE KEY-----\n`
   - Todo el contenido (con `\n` para saltos de línea)
   - `\n-----END PRIVATE KEY-----\n`

### La app funciona pero no se registran logs

**Causas posibles**:
1. `secrets.toml` no configurado → Logging se desactiva automáticamente
2. Error silencioso → Revisa la terminal por mensajes `⚠️`
3. Rate limit de Google API → Espera 1 minuto y prueba de nuevo

---

## 📈 Límites y Cuotas (Google Sheets API)

| Recurso | Límite Gratis | Tu Uso Estimado |
|---------|---------------|-----------------|
| **Requests/minuto** | 300 | <10 (salvo spam) |
| **Requests/día** | 500,000 | <1,000 |
| **Celdas por hoja** | 10,000,000 | <100,000 (varios años) |
| **Hojas por spreadsheet** | 200 | 1 |

**Conclusión**: Con uso académico normal (100 búsquedas/día), NUNCA alcanzarás los límites.

---

## 🔄 Mantenimiento

### Cada 6 meses:
- ✅ Revisar logs acumulados
- ✅ Exportar a CSV y limpiar hoja si tiene >10,000 filas
- ✅ Analizar estadísticas para mejorar la app

### Cada 12 meses:
- ✅ Rotar credenciales del service account
- ✅ Revisar permisos de acceso a la hoja

---

## 💡 Extensiones Futuras

Si quieres expandir el logging:

1. **Agregar campos**:
   - Duración de la búsqueda (tiempo de respuesta)
   - User agent (navegador usado)
   - Errores específicos de OpenAlex API

2. **Dashboard en tiempo real**:
   - Streamlit app separada que lee la hoja
   - Gráficos interactivos con plotly

3. **Alertas**:
   - Google Apps Script para alertar si queries fallan
   - Notificación si tasa de éxito de PDFs baja <50%

---

## 📚 Referencias

- [Google Sheets API Docs](https://developers.google.com/sheets/api)
- [gspread Documentation](https://docs.gspread.org/)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [GDPR Compliance Guide](https://gdpr.eu/)

---

## ❓ Preguntas Frecuentes

### ¿Puedo usar otra hoja de cálculo (Excel, LibreOffice)?

No directamente. Este sistema está diseñado para Google Sheets. Para otras opciones, necesitarías implementar un backend diferente (ej: Supabase, MongoDB).

### ¿Cuánto cuesta Google Sheets API?

**Gratis** para uso estándar (hasta 500,000 requests/día). Este proyecto usa <1% de ese límite.

### ¿Los usuarios saben que se registra su búsqueda?

Depende de ti. Es buena práctica agregar un aviso en la UI (ver sección "Transparencia con Usuarios").

### ¿Puedo desactivar el logging?

Sí. Simplemente **no configures** el archivo `secrets.toml`. El logging se desactiva automáticamente sin romper la app.

### ¿Qué pasa si la API de Google falla?

El logging falla silenciosamente (no afecta la app). El usuario no nota nada.

---

**¿Necesitas ayuda?** Revisa los logs de la terminal o abre un issue en GitHub.
