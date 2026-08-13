# 🚀 Despliegue en Streamlit Cloud

Esta aplicación está lista para desplegarse en **Streamlit Cloud** (gratuito) y funciona perfectamente tanto en local como en la nube.

## ✅ Características Listas para la Nube

- ✅ **Descarga de PDFs como ZIP**: Los PDFs se empaquetan en un archivo ZIP que el usuario descarga a su dispositivo
- ✅ **Nombres descriptivos**: `001-Autor-Titulo.pdf` para fácil identificación
- ✅ **Sin almacenamiento permanente**: Los archivos temporales se limpian automáticamente
- ✅ **Compatible con NotebookLM**: Descomprime el ZIP y sube los PDFs directamente

## 📋 Requisitos Previos

1. Cuenta de GitHub (gratuita)
2. Cuenta de Streamlit Cloud (gratuita - usa GitHub OAuth)
3. Este código en un repositorio de GitHub

## 🔧 Paso 1: Subir a GitHub

```bash
# En el directorio del proyecto
git init
git add .
git commit -m "Initial commit - OpenAlex PDF Downloader"

# Crear repositorio en GitHub (https://github.com/new)
# Luego conectar y subir:
git remote add origin https://github.com/TU_USUARIO/openalex-app.git
git branch -M main
git push -u origin main
```

## 🌐 Paso 2: Desplegar en Streamlit Cloud

### Opción A: Desde Streamlit Cloud

1. Ve a https://share.streamlit.io/
2. Click en **"New app"**
3. Selecciona tu repositorio de GitHub
4. Configura:
   - **Branch**: `main`
   - **Main file path**: `app_streamlit.py`
   - **Python version**: 3.9+ (recomendado)
5. Click en **"Deploy!"**

### Opción B: Desde GitHub (más rápido)

1. Ve a tu repositorio en GitHub
2. Agrega el badge de Streamlit al README:

```markdown
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
```

3. Click en el badge y sigue las instrucciones

## 📦 Estructura de Archivos Necesaria

Tu repositorio debe tener estos archivos:

```
openalex-app/
├── app_streamlit.py              # Aplicación principal ✓
├── openalex_search.py            # Motor de búsqueda ✓
├── requirements.txt              # Dependencias ✓
├── README_STREAMLIT.md           # Documentación (opcional)
├── DESPLIEGUE_STREAMLIT_CLOUD.md # Esta guía
└── .streamlit/
    └── config.toml               # Configuración de tema (opcional)
```

## 📝 Archivo requirements.txt

Asegúrate de que `requirements.txt` contiene:

```
streamlit>=1.28.0
pandas>=2.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
```

## ⚙️ Configuración Opcional

Crea `.streamlit/config.toml` para personalizar:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
maxUploadSize = 200
enableXsrfProtection = true
```

## 🎯 Flujo de Trabajo en Producción

### Para el Usuario:

1. **Buscar** → Ingresa "historia digital" y busca
2. **Descargar PDFs** → Click en botón
3. **Esperar** → Progreso en pantalla (puede tomar varios minutos)
4. **Descargar ZIP** → Click en botón "📦 Descargar ZIP con PDFs"
5. **Usar en NotebookLM** → Descomprime y sube los PDFs

### Ejemplo de Nombres de Archivo:

```
pdfs_20251029_153000.zip
├── 001-Melo-Historia_digital_memoria_archivo.pdf
├── 002-Gallini-historia_digital_era_Web.pdf
├── 003-Pons-Historia_digital_campo_busca.pdf
└── ... (hasta 48 PDFs)
```

## 🔍 Debug y Logs

### Ver Logs en Streamlit Cloud:

1. Ve a tu app en Streamlit Cloud
2. Click en "≡" (menú hamburguesa)
3. Selecciona "Manage app"
4. Ve a la pestaña "Logs"

### Logs de Debug Local:

Los logs se guardan en `debug_openalex/` (solo en local):
- `{doi}_landing.html` - Página del artículo
- `{doi}_view.html` - Página de vista (si existe)
- `{doi}_log.json` - Log completo del pipeline

**Nota**: En Streamlit Cloud estos archivos NO se guardan para ahorrar espacio.

## ⚠️ Limitaciones de Streamlit Cloud

### Tiempo de Ejecución:
- **Timeout**: ~10 minutos para requests largos
- **Solución**: La app maneja timeouts automáticamente

### Memoria:
- **Límite**: 1GB RAM
- **Solución**: Los PDFs se procesan en stream y se limpian

### Almacenamiento:
- **Temporal**: Solo durante la ejecución
- **Solución**: El ZIP se guarda en `session_state` (memoria)

## 🔧 Troubleshooting

### Error: "Requirements file not found"
**Solución**: Asegúrate de que `requirements.txt` está en la raíz del repo

### Error: "Module not found"
**Solución**: Revisa que todas las dependencias están en `requirements.txt`

### La descarga es muy lenta
**Solución**: Normal para 48 artículos (~2-5 minutos). Cada PDF se descarga individualmente.

### El ZIP no se descarga
**Solución**: Verifica que al menos 1 PDF se descargó. Si stats['downloaded'] = 0, no se genera ZIP.

## 🎓 Mejores Prácticas

### Para Búsquedas Grandes:
1. Usa filtros de "Acceso abierto" para mayor éxito
2. Limita a 50-100 resultados inicialmente
3. Ordena por "Más citados" para artículos importantes

### Para NotebookLM:
1. Descomprime el ZIP completamente
2. Sube solo los PDFs más relevantes (máx. 50)
3. Los nombres descriptivos te ayudan a seleccionar

## 📊 Monitoreo

### Métricas Clave:
- **PDFs descargados**: Indica éxito
- **Sin PDF**: DOIs sin acceso al PDF
- **Errores**: Problemas de conexión o formato

### Tasa de Éxito Esperada:
- Revistas OJS: ~70-80%
- Revistas comerciales: ~30-50%
- Preprints: ~90%

## 🔄 Actualizaciones

Para actualizar la app desplegada:

```bash
# Hacer cambios en local
git add .
git commit -m "Descripción del cambio"
git push

# Streamlit Cloud detecta el push y redespliega automáticamente
```

## 🆘 Soporte

- **Documentación Streamlit**: https://docs.streamlit.io/
- **Issues de la app**: Reporta en el repo de GitHub
- **OpenAlex API**: https://docs.openalex.org/

## ✨ Ejemplo de URL Desplegada

Después del despliegue, tu URL será algo como:

```
https://TU_USUARIO-openalex-app-main-app-streamlit-HASH.streamlit.app
```

¡Compártela con quien quieras! 🎉
