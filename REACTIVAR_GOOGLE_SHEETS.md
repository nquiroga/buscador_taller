# Reactivar el registro de uso en Google Sheets

La aplicación registra búsquedas y estadísticas agregadas de descarga. Si faltan los secretos de Google, el buscador sigue funcionando: el logger se desactiva sin interrumpir la clase.

## 1. Crear o elegir la hoja

1. Creá una hoja de cálculo, por ejemplo openalex_logs.
2. Copiá su identificador: es el segmento de la URL entre /d/ y /edit.
3. En la fila 1, pegá estos encabezados:

~~~
timestamp	session_id	query	search_type	max_results	open_access_filter	year_from	year_to	sort_by	total_found	with_abstract	open_access_count	avg_citations	pdf_download_attempted	pdfs_downloaded	pdfs_failed	pdfs_no_available	pdfs_total_processed
~~~

## 2. Crear una cuenta de servicio

1. En Google Cloud Console, elegí o creá un proyecto.
2. Habilitá **Google Sheets API** y **Google Drive API**.
3. En **IAM y administración → Cuentas de servicio**, creá una cuenta destinada al logger.
4. En la pestaña **Keys**, generá una clave nueva de tipo JSON y guardala fuera del repositorio.
5. Compartí la hoja con el client_email de esa cuenta, con permiso **Editor**.

No reutilices una clave que haya sido expuesta. No subas el JSON a GitHub.

## 3. Cargar los secretos en Streamlit

En Streamlit Community Cloud: **App settings → Secrets**. Pegá este esquema y reemplazá sólo los valores entre comillas:

~~~
google_sheets_name = "openalex_logs"
google_sheets_key = "ID_DE_LA_HOJA"

[google_sheets]
type = "service_account"
project_id = "tu-proyecto"
private_key_id = "id-de-la-clave"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "nombre@tu-proyecto.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
~~~

Guardá los cambios. Streamlit reinicia la app automáticamente.

## 4. Verificar

1. Ejecutá una búsqueda desde la app.
2. Abrí la hoja y comprobá que se agregó una fila.
3. Probá una descarga de PDFs y comprobá que las columnas pdfs_* se actualizan en otra fila.

Si no aparece nada, revisá que la hoja esté compartida con el correo de la cuenta de servicio y que las dos APIs de Google estén habilitadas. El error del logger no bloquea las búsquedas.
