# Despliegue seguro en Streamlit Community Cloud

## Antes de publicar

1. Confirmá que la rama no contiene archivos de secretos:

~~~
git status
git check-ignore -v .streamlit/secrets.toml
~~~

2. El resultado del segundo comando debe mostrar una regla de .gitignore.
3. Subí la rama y fusionála a main mediante un pull request.

## Crear o actualizar la aplicación

1. En Streamlit Community Cloud elegí el repositorio nquiroga/buscador_taller.
2. Indicá la rama main y el archivo principal app_streamlit.py.
3. Antes de desplegar, abrí **Advanced settings** y pegá:

~~~
OPENALEX_API_KEY = "tu_clave_privada_de_openalex"
OPENALEX_MAILTO = "tu-correo-institucional@ejemplo.edu"
~~~

Para una app ya desplegada: **App settings → Secrets**, actualizá el bloque y guardá. Nunca incluyas ese bloque en un commit ni en una captura de pantalla.

La clave es opcional para el acceso básico de OpenAlex, pero recomendable en una clase con muchas consultas porque amplía el cupo disponible.

## Comprobación tras desplegar

1. Ejecutá una búsqueda breve.
2. Exportá CSV y Markdown.
3. Elegí entre 1 y 3 PDFs; verificá que el ZIP incluya manifiesto.csv.
4. Abrí un PDF y comprobá su licencia, versión y página de origen antes de cargarlo en NotebookLM.

## Incidencias frecuentes

| Situación | Acción |
| --- | --- |
| OpenAlex devuelve 401 o 403 | Revisá o regenerá OPENALEX_API_KEY en Secrets. |
| No hay PDFs en la búsqueda | Desactivá “Sólo registros con PDF” para explorar el índice; no todos los registros tienen URL de PDF. |
| Un PDF falla | El manifiesto y el panel de incidencias conservan la URL y el motivo; probá otro resultado. |
| Un archivo supera 25 MB | No se incorpora al ZIP para cuidar la memoria del despliegue. |
