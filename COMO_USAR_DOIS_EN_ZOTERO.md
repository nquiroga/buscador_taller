# 📚 Cómo Usar DOIs en Zotero

Esta guía te muestra cómo importar rápidamente los resultados de tu búsqueda a Zotero usando la lista de DOIs.

---

## 🎯 Ventajas de Este Método

✅ **Rápido**: Importa 40+ artículos en segundos
✅ **Completo**: Zotero descarga automáticamente todos los metadatos
✅ **Actualizado**: Los metadatos vienen de la fuente original (Crossref/OpenAlex)
✅ **PDFs automáticos**: Zotero intenta descargar PDFs si están disponibles

---

## 📖 Paso a Paso

### **1. Descargar la Lista de DOIs**

En la aplicación Streamlit:

1. Haz tu búsqueda (ej: "historia digital")
2. Revisa los resultados
3. Click en **"🔖 Descargar DOIs para Zotero"**
4. Se descarga un archivo: `dois_zotero_20251029_150000.txt`

---

### **2. Abrir el Archivo de DOIs**

El archivo `.txt` contiene todos los DOIs separados por comas:

```
10.7440/histcrit43.2011.06,10.7440/histcrit43.2011.03,10.51349/veg.2022.1.02,...
```

**Opciones:**
- Abrir con cualquier editor de texto
- O copiar directamente el contenido

---

### **3. Importar en Zotero Desktop**

#### **Opción A: Copiar y Pegar (Recomendado)**

1. Abre el archivo `dois_zotero_*.txt`
2. **Selecciona todo** el contenido (Ctrl+A / Cmd+A)
3. **Copia** (Ctrl+C / Cmd+C)
4. En Zotero, click en el ícono de la **varita mágica** en la barra superior
   - O usa el menú: `File` → `Add Item(s) by Identifier...`
5. **Pega** los DOIs (Ctrl+V / Cmd+V)
6. Click en **OK**

Zotero procesará todos los DOIs y creará los ítems automáticamente.

#### **Opción B: Arrastrar y Soltar**

1. Arrastra el archivo `.txt` directamente a la ventana de Zotero
2. Zotero lo reconocerá y procesará los DOIs

---

### **4. Importar en Zotero Web**

1. Ve a https://www.zotero.org/
2. Inicia sesión
3. Abre tu biblioteca
4. Click en el **+** verde → `Add Item by Identifier`
5. Pega los DOIs del archivo
6. Click en **Add**

---

## 🔍 Qué Hace Zotero Automáticamente

Cuando importas los DOIs, Zotero:

✅ Descarga **metadatos completos**:
- Título
- Autores
- Revista/Publicación
- Año
- Abstract
- Palabras clave
- DOI
- URL

✅ Intenta descargar el **PDF** si está disponible en acceso abierto

✅ Crea la **cita bibliográfica** en múltiples formatos (APA, Chicago, etc.)

✅ Sincroniza con tu cuenta (si está activada)

---

## 💡 Tips y Trucos

### **Importación Grande (40+ artículos)**

Si tienes muchos DOIs:

1. **Divide en lotes**: Zotero puede tardar si son 100+ artículos
2. **Revisa progreso**: Zotero muestra un indicador de progreso
3. **Paciencia**: Puede tomar 1-2 minutos para 50 artículos

### **Si Algunos DOIs Fallan**

Es normal que 1-2 DOIs no se importen:

- DOIs antiguos pueden no estar en Crossref
- Algunos artículos no tienen metadatos completos
- Error temporal de conexión

**Solución**: Agrega manualmente o busca el título en Zotero Connector

### **Descargar PDFs Después**

Si Zotero no descargó los PDFs automáticamente:

1. Usa el botón **"📄 Descargar PDFs"** de la app
2. Obtienes un ZIP con todos los PDFs nombrados: `001-Autor-Titulo.pdf`
3. En Zotero, arrastra cada PDF al ítem correspondiente

O mejor aún, usa **Zotero Connector** (extensión de navegador) para descargar PDFs mientras navegas.

---

## 🆚 Comparación de Métodos

| Método | Velocidad | Metadatos | PDFs | Mejor Para |
|--------|-----------|-----------|------|------------|
| **DOIs en Zotero** | ⚡⚡⚡ | ✅ Completos | 🟡 Algunos | Importación rápida de metadatos |
| **PDFs desde app** | 🐌 Lento | ❌ No | ✅ Máximo | Lectura offline, NotebookLM |
| **Zotero Connector** | ⚡⚡ | ✅ Completos | ✅ Sí | Navegación manual artículo por artículo |

---

## 🔄 Workflow Recomendado

### **Para Gestión Bibliográfica Completa:**

```
1. Búsqueda en app → 2. Descargar DOIs → 3. Importar a Zotero
   ↓
4. Revisar en Zotero → 5. Usar Zotero Connector para PDFs faltantes
   ↓
6. Organizar en colecciones → 7. Generar bibliografía
```

### **Para Análisis con NotebookLM:**

```
1. Búsqueda en app → 2. Descargar PDFs (ZIP) → 3. Descomprimir
   ↓
4. Subir PDFs a NotebookLM → 5. Generar notas/podcast
```

### **Combinado (Mejor Opción):**

```
1. Búsqueda en app
   ├─→ 2a. Descargar DOIs → Importar a Zotero (gestión)
   └─→ 2b. Descargar PDFs → NotebookLM (análisis)
```

---

## ❓ Preguntas Frecuentes

### **¿Puedo editar los DOIs antes de importar?**

Sí, puedes abrir el archivo `.txt` y:
- Eliminar DOIs que no te interesen
- Agregar más DOIs manualmente
- Cambiar el separador (comas, espacios, saltos de línea)

Zotero acepta múltiples formatos.

### **¿Qué pasa si hay DOIs duplicados?**

Zotero detecta duplicados automáticamente y:
- Te avisa
- Te permite elegir: mantener, combinar o descartar

### **¿Funciona con DOIs de cualquier fuente?**

Sí, Zotero soporta DOIs de:
- Crossref (mayoría de revistas académicas)
- DataCite (datasets)
- mEDRA (libros)
- Otros registros DOI

### **¿Los artículos se quedan en mi biblioteca?**

Sí, una vez importados quedan permanentemente en tu biblioteca de Zotero (local y en la nube si sincronizas).

---

## 📚 Recursos Adicionales

- **Documentación Zotero**: https://www.zotero.org/support/
- **Zotero Forums**: https://forums.zotero.org/
- **Zotero Connector**: https://www.zotero.org/download/connectors

---

## 🎯 Ejemplo Completo

**Archivo descargado**: `dois_zotero_20251029_150000.txt`

**Contenido**:
```
10.7440/histcrit43.2011.06,10.7440/histcrit43.2011.03,10.51349/veg.2022.1.02
```

**Pasos**:
1. Abrir archivo → Copiar contenido
2. Zotero → Varita mágica
3. Pegar DOIs → OK
4. ✅ 3 artículos importados con metadatos completos

**Resultado en Zotero**:
```
📄 Historia digital: la memoria en el archivo infinito
   Jairo Antonio Melo Flórez
   Historia Crítica, 2011

📄 La historia digital en la era del Web 2.0
   Stefania Gallini; Serge Noiret
   Historia Crítica, 2011

📄 Historia digital: un campo en busca de identidad
   Anaclet Pons
   Vegueta, 2022
```

---

¡Listo! Ahora tienes todos tus artículos organizados en Zotero para citar, compartir y gestionar tu investigación. 🎓
