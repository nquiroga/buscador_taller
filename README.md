# Buscador académico OpenAlex → NotebookLM

Aplicación Streamlit para un taller de búsqueda académica. Consulta el índice abierto de OpenAlex, exporta metadatos y prepara pequeños lotes de PDFs de acceso abierto para trabajar en NotebookLM.

## Qué hace

- Busca hasta 500 obras por palabras clave, años y orden (relevancia, citas o fecha).
- Recupera metadatos normalizados: autores, fuente, año, DOI, OpenAlex ID, estado OA, licencia, versión y URL de origen.
- Exporta resultados como CSV y como Markdown.
- Descarga, como máximo, 20 PDFs por lote desde URLs de PDF que OpenAlex declara abiertas.
- Empaqueta los archivos junto con un manifiesto.csv de procedencia.
- Limita cada PDF a 25 MB y comprueba que el recurso recibido sea realmente un PDF.

No rastrea páginas DOI ni intenta eludir paywalls. Que una URL sea accesible no reemplaza la comprobación de licencia, versión y condiciones del sitio de origen.

## Configuración de claves

La aplicación funciona con el acceso básico de OpenAlex aun sin clave. Para el uso en clase se recomienda una clave gratuita: aumenta sustancialmente el cupo diario y evita compartir una credencial en el navegador.

Nunca subas una clave a GitHub. El repositorio ignora .streamlit/secrets.toml y sólo incluye la plantilla segura [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example).

### Desarrollo local

1. Copiá la plantilla a .streamlit/secrets.toml.
2. Completá los valores, sin comillas adicionales:

~~~
OPENALEX_API_KEY = "tu_clave_privada_de_openalex"
OPENALEX_MAILTO = "tu-correo-institucional@ejemplo.edu"
~~~

3. Confirmá antes de hacer git add:

~~~
git status --ignored
~~~

El archivo secrets.toml debe figurar como ignorado y jamás como archivo a confirmar.

### Streamlit Community Cloud

1. Abrí la aplicación desplegada.
2. En **App settings**, abrí **Secrets** (o, al crear la app, **Advanced settings**).
3. Pegá el mismo bloque TOML anterior y guardá.
4. Streamlit reinicia la aplicación con el secreto disponible como st.secrets.

El secreto queda en la configuración de Streamlit, no en el repositorio público. Si una clave se publicó por error, revocala y creá otra antes de continuar.

## Instalación y ejecución

~~~
git clone https://github.com/nquiroga/buscador_taller.git
cd buscador_taller
python -m pip install -r requirements.txt
streamlit run app_streamlit.py
~~~

## Flujo recomendado para el taller

1. Formular una consulta amplia y revisar relevancia, fecha, autorías y fuente.
2. Acotar por años y/o ordenar por citas o actualidad.
3. Descargar primero el CSV: es el registro bibliográfico de la búsqueda.
4. Preparar un lote pequeño de PDFs y leer el manifiesto.csv.
5. Revisar manualmente los textos pertinentes.
6. Subir a NotebookLM sólo los PDFs seleccionados y, si sirve, el manifiesto como contexto.

El ZIP se crea temporalmente para la sesión y no constituye un repositorio ni una garantía de conservación de los archivos.

## Campos del manifiesto

| Campo | Uso |
| --- | --- |
| doi, openalex_id | Identificadores persistentes para verificar y citar. |
| oa_pdf_url, oa_landing_url | Procedencia del archivo y página de origen. |
| license, pdf_version, oa_status | Señales para revisar condiciones de reutilización y versión. |
| download_status, downloaded_file | Resultado técnico de la descarga. |

## Límites y criterios

- OpenAlex es un índice bibliográfico; no es un repositorio de texto completo.
- El filtro de PDF reduce resultados a obras con URL de PDF reportada por OpenAlex; puede dejar afuera publicaciones pertinentes sin PDF declarado.
- La licencia puede no estar informada aunque el archivo sea OA: activá el filtro de licencia sólo si ese requisito es imprescindible.
- La exportación de metadatos no sustituye los datos de citación de la revista ni la lectura crítica del texto.

## Referencias técnicas

- [API de OpenAlex](https://help.openalex.org/api/)
- [Filtros de OpenAlex](https://help.openalex.org/api/filtering/)
- [Gestión de secretos en Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
