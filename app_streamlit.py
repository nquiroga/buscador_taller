"""
Taller NotebookLM - 2025
Herramienta de Búsqueda Académica con OpenAlex API
Permite búsquedas avanzadas con operadores booleanos y exportación a Markdown
"""

import streamlit as st
import pandas as pd
from openalex_search import OpenAlexSearcher
from semantic_scholar_search import SemanticScholarSearcher
from openalex_logger import OpenAlexLogger
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import io
import zipfile
import os
import shutil

# Logging anónimo de búsquedas (opcional, no rompe si falla)
try:
    from openalex_logger import log_search_event
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False

# Configuración de la página
st.set_page_config(
    page_title="Búsqueda Académica - OpenAlex",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("📚 Búsqueda Académica Avanzada")
st.caption("Taller NotebookLM - 2025")

# Sidebar con ayuda
with st.sidebar:
    st.header("📖 Guía de Uso")

    st.subheader("Operadores Booleanos")
    st.markdown("""
    **Operadores disponibles (MAYÚSCULAS):**
    - `AND` - Ambos términos deben aparecer
    - `OR` - Al menos uno debe aparecer
    - `NOT` - Excluye resultados

    **Ejemplos:**
    - `peronismo AND argentina`
    - `"Juan Perón" OR "Eva Perón"`
    - `peronismo NOT militar`
    - `(peronismo OR justicialismo) AND argentina`
    """)

    st.subheader("Búsqueda Avanzada")
    st.markdown("""
    **Frases exactas:**
    - Use comillas: `"historia argentina"`

    **Múltiples términos (OR automático):**
    - Separe con comas: `peronismo, justicialismo`
    - Se convierte a: `peronismo OR justicialismo`

    **Paréntesis:**
    - Controla el orden: `(A OR B) AND C`
    """)

    st.subheader("Tipos de Búsqueda")
    st.markdown("""
    - **Título y Abstract**: Busca en título y resumen
    - **General**: Busca en todo el documento
    - **Solo Título**: Busca únicamente en títulos
    """)

    st.subheader("Filtros Disponibles")
    st.markdown("""
    - **Rango de años**: Selector deslizante para filtrar por período de publicación (1900-presente)
    - **Acceso abierto**: Filtrar por disponibilidad de PDF
    - **Cantidad de resultados**: Máximo 1000 por búsqueda
    - **Ordenamiento**: Por relevancia, citaciones o fecha
    """)

    st.subheader("Exportar a Zotero")
    st.markdown("""
    **🔖 Descargar DOIs para Zotero:**
    - Descarga un archivo `.txt` con todos los DOIs separados por comas
    - Abre Zotero → Click en la varita mágica ("Add Item(s) by Identifier")
    - Pega el contenido del archivo o arrastra el archivo
    - ¡Zotero importa automáticamente los metadatos!

    **Ventajas:**
    - Importación rápida de 40+ artículos a la vez
    - Metadatos completos desde la fuente original
    - Compatible con Zotero desktop y web
    """)

    st.subheader("Descarga de PDFs")
    st.markdown("""
    El botón **📄 Descargar PDFs** funciona así:

    **Pipeline de búsqueda:**
    1. Accede a la página del DOI (detecta redirecciones Crossref)
    2. Busca meta tags PDF (`citation_pdf_url`, etc.)
    3. Busca enlaces directos a PDF (prioriza mismo dominio)
    4. Detecta enlaces OJS y convierte `/view/` → `/download/`
    5. Verifica que sea PDF real (Content-Type + firma `%PDF`)

    **Nombres de archivo:**
    - Formato: `001-Apellido-Fragmento_Titulo.pdf`
    - Ejemplo: `001-Pons-Historia_digital_campo_busca.pdf`
    - El número corresponde al índice del CSV

    **Descarga:**
    - Los PDFs se empaquetan en un archivo **ZIP**
    - Descargas el ZIP a tu dispositivo
    - Descomprimes y tienes acceso directo a los PDFs
    - Úsalos para lectura offline, NotebookLM, o agrégalos a Zotero manualmente

    **Compatible con:** Streamlit Cloud y ejecución local
    _ℹ️ Esta aplicación registra un **log anónimo** de uso:_
    solo se guardan estadísticas generales de las búsquedas y descargas,
    sin datos personales ni información de los documentos.
    """)

# Formulario de búsqueda
st.header("🔍 Nueva Búsqueda")

col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_input(
        "Ingrese su consulta de búsqueda",
        placeholder='Ej: (peronismo OR justicialismo) AND argentina',
        help="Use operadores booleanos (AND, OR, NOT) y comillas para frases exactas"
    )

with col2:
    search_type = st.selectbox(
        "Tipo de búsqueda",
        ["title_abstract", "general", "title_only"],
        format_func=lambda x: {
            "title_abstract": "Título y Abstract",
            "general": "General",
            "title_only": "Solo Título"
        }[x]
    )

col3, col4, col5 = st.columns([1, 1, 1])

with col3:
    max_results = st.number_input(
        "Cantidad de resultados",
        min_value=10,
        max_value=1000,
        value=100,
        step=10,
        help="Máximo 1000 resultados"
    )

with col4:
    sort_by = st.selectbox(
        "Ordenar por",
        ["relevance_score:desc", "cited_by_count:desc", "publication_year:desc"],
        format_func=lambda x: {
            "relevance_score:desc": "Relevancia",
            "cited_by_count:desc": "Más citados",
            "publication_year:desc": "Más recientes"
        }[x]
    )

with col5:
    open_access_filter = st.selectbox(
        "Filtro de acceso",
        ["all", "open_access_only", "closed_only"],
        format_func=lambda x: {
            "all": "Todos",
            "open_access_only": "Solo acceso abierto",
            "closed_only": "Solo restringido"
        }[x],
        help="Filtrar por disponibilidad del PDF"
    )

# Selector de rango de años
from datetime import datetime
current_year = datetime.now().year

st.subheader("📅 Filtro por Año de Publicación")
year_range = st.slider(
    "Seleccione el rango de años",
    min_value=1900,
    max_value=current_year,
    value=(2000, current_year),
    step=1,
    help="Arrastra los extremos para filtrar por año de publicación"
)
year_from, year_to = year_range

# Botón de búsqueda
search_button = st.button("🔍 Buscar", type="primary", width="stretch")

# Función para convertir resultados a Markdown
def convert_to_markdown(results_df):
    """Convierte los resultados a formato Markdown optimizado para NotebookLM"""

    md_content = f"""# Resultados de Búsqueda Académica

**Consulta:** {results_df['search_query'].iloc[0] if len(results_df) > 0 else 'N/A'}
**Fecha de búsqueda:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total de resultados:** {len(results_df)}
**Fuente:** OpenAlex API

---

"""

    for idx, row in results_df.iterrows():
        md_content += f"""## {idx + 1}. {row['title']}

**Autores:** {row['author'] if row['author'] else 'N/A'}
**Publicación:** {row['publication'] if row['publication'] else 'N/A'}
**Año:** {row['year']}
**Citaciones:** {row['citations']}
**DOI:** {row['doi'] if row['doi'] else 'N/A'}
**OpenAlex ID:** {row['openalex_id']}
**Acceso Abierto:** {'Sí' if row['open_access'] else 'No'}

### Abstract

{row['abstract'] if row['abstract'] else 'No disponible'}

---

"""

    return md_content


def deduplicate_by_doi(results):
    """Evita duplicados exactos entre fuentes sin descartar obras sin DOI."""
    unique_results = []
    seen_dois = set()
    for result in results:
        doi = (result.get("doi") or "").strip().lower()
        if doi and doi in seen_dois:
            continue
        if doi:
            seen_dois.add(doi)
        unique_results.append(result)
    return unique_results

# Realizar búsqueda
if search_button:
    if not query:
        st.error("⚠️ Por favor ingrese una consulta de búsqueda")
    else:
        with st.spinner("🔄 Buscando en OpenAlex y Semantic Scholar..."):
            try:
                results = []
                source_errors = []

                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = {
                        executor.submit(
                            OpenAlexSearcher().get_all_results,
                            query=query,
                            max_results=max_results,
                            search_type=search_type,
                            open_access_filter=open_access_filter,
                            year_from=year_from,
                            year_to=year_to,
                        ): "OpenAlex",
                        executor.submit(
                            SemanticScholarSearcher().get_all_results,
                            query=query,
                            max_results=max_results,
                            open_access_filter=open_access_filter,
                            year_from=year_from,
                            year_to=year_to,
                        ): "Semantic Scholar",
                    }
                    for future in as_completed(futures):
                        source = futures[future]
                        try:
                            source_results = future.result()
                            for result in source_results:
                                result.setdefault("source", source)
                            results.extend(source_results)
                        except Exception as error:
                            source_errors.append(f"{source}: {error}")

                results = deduplicate_by_doi(results)

                if not results:
                    st.warning("No se encontraron resultados en OpenAlex ni en Semantic Scholar")
                else:
                    # Convertir a DataFrame
                    df = pd.DataFrame(results)

                    # Guardar CSV automáticamente en el directorio
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    csv_filename = f"resultados_{timestamp}.csv"
                    df.to_csv(csv_filename, index=False, encoding='utf-8')

                    # Guardar en session state
                    st.session_state['results'] = df
                    st.session_state['query'] = query
                    st.session_state['csv_filename'] = csv_filename

                    # Logging anónimo (no bloquea si falla)
                    if LOGGING_AVAILABLE:
                        try:
                            log_search_event(
                                query=query,
                                search_params={
                                    'search_type': search_type,
                                    'max_results': max_results,
                                    'open_access_filter': open_access_filter,
                                    'year_from': year_from,
                                    'year_to': year_to,
                                    'sort_by': sort_by
                                },
                                results_df=df
                            )
                        except Exception:
                            pass  # Silencioso

                    st.success(f"✅ Se encontraron {len(df)} resultados")
                    st.info(f"📁 CSV guardado automáticamente: {csv_filename}")
                    if source_errors:
                        st.warning("Una fuente no respondió; se muestran los resultados de la otra.")
                        with st.expander("Detalle técnico de la fuente que falló"):
                            for source_error in source_errors:
                                st.text(source_error)

            except Exception as e:
                st.error(f"❌ Error durante la búsqueda: {str(e)}")

# Mostrar resultados
if 'results' in st.session_state and st.session_state['results'] is not None:
    df = st.session_state['results']

    st.header("📊 Resultados")

    # Estadísticas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de resultados", len(df))
    col2.metric("Con abstract", df['abstract'].notna().sum())
    col3.metric("Acceso abierto", df['open_access'].sum())
    col4.metric("Promedio de citas", int(df['citations'].astype(float).mean()))

    # Botones de descarga
    st.subheader("💾 Exportar Resultados")

    col1, col2 = st.columns(2)

    with col1:
        # Descargar DOIs para Zotero
        # Filtrar solo DOIs válidos
        valid_dois = df[df['doi'].notna() & (df['doi'] != '')]['doi'].unique().tolist()

        if len(valid_dois) > 0:
            # Crear texto con DOIs separados por comas
            dois_text = ','.join(valid_dois)

            st.download_button(
                label="🔖 Descargar DOIs para Zotero",
                data=dois_text,
                file_name=f"dois_zotero_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                help=f"Descarga {len(valid_dois)} DOIs separados por comas. Úsalos con la 'varita mágica' de Zotero.",
                width="stretch"
            )
        else:
            st.button(
                "🔖 Descargar DOIs para Zotero",
                disabled=True,
                help="No hay DOIs disponibles en los resultados",
                width="stretch"
            )

    with col2:
        # Botón para descargar PDFs
        if st.button("📄 Descargar PDFs", width="stretch", help="Descarga PDFs y genera archivo ZIP con nombres descriptivos: ID-Autor-Titulo.pdf"):
            # Obtener DOIs únicos y sus metadatos
            df_with_doi = df[df['doi'].notna() & (df['doi'] != '')].copy()

            if len(df_with_doi) == 0:
                st.warning("⚠️ No hay artículos con DOI en los resultados")
            else:
                # Construir diccionario de metadatos: {doi: {title, author, index}}
                metadata = {}
                for idx, row in df_with_doi.iterrows():
                    doi = row['doi']
                    # Usar el índice original del DataFrame (idx + 1 para empezar en 1)
                    metadata[doi] = {
                        'index': idx + 1,  # Índice empezando en 1
                        'title': row.get('title', ''),
                        'author': row.get('author', '')
                    }

                unique_dois = list(metadata.keys())

                st.info(f"ℹ️ Se procesarán {len(unique_dois)} DOIs únicos")
                with st.spinner(f"🔄 Descargando PDFs..."):
                    # Crear directorio de PDFs
                    pdf_dir = f"pdfs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                    # Crear barra de progreso
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Definir callback de progreso
                    def update_progress(current, total, downloaded):
                        progress = current / total
                        progress_bar.progress(progress)
                        status_text.text(f"Procesando: {current}/{total} | Descargados: {downloaded}")

                    # Inicializar buscador y descargar con metadatos
                    searcher = OpenAlexSearcher()
                    stats = searcher.download_pdfs_from_dois(
                        unique_dois,
                        output_dir=pdf_dir,
                        progress_callback=update_progress,
                        metadata=metadata
                    )

                    # Limpiar elementos de progreso
                    progress_bar.empty()
                    status_text.empty()

                    # Crear archivo ZIP con todos los PDFs descargados
                    if stats['downloaded'] > 0:
                        status_text.text("📦 Empaquetando PDFs en archivo ZIP...")

                        # Crear ZIP en memoria
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            # Agregar todos los PDFs al ZIP
                            for pdf_file in os.listdir(pdf_dir):
                                if pdf_file.endswith('.pdf'):
                                    pdf_path = os.path.join(pdf_dir, pdf_file)
                                    # Agregar al ZIP con el mismo nombre
                                    zip_file.write(pdf_path, pdf_file)

                        # Guardar ZIP en session state
                        zip_buffer.seek(0)
                        st.session_state['pdf_zip'] = zip_buffer.getvalue()
                        st.session_state['pdf_zip_name'] = f"pdfs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                        st.session_state['pdf_stats'] = stats

                        # Logging de descarga de PDFs (no bloquea si falla)
                        if LOGGING_AVAILABLE and 'results' in st.session_state:
                            try:
                                log_search_event(
                                    query=st.session_state.get('query', 'N/A'),
                                    search_params={
                                        'search_type': 'pdf_download',
                                        'max_results': len(unique_dois),
                                        'open_access_filter': 'N/A',
                                        'year_from': '',
                                        'year_to': '',
                                        'sort_by': 'N/A'
                                    },
                                    results_df=st.session_state['results'],
                                    pdf_stats=stats
                                )
                            except Exception:
                                pass  # Silencioso

                        # Limpiar directorio temporal de PDFs
                        try:
                            shutil.rmtree(pdf_dir)
                        except Exception:
                            pass  # No es crítico si falla la limpieza

                        status_text.empty()

                # Mostrar resultados si hay un ZIP disponible
                if 'pdf_zip' in st.session_state:
                    stats = st.session_state.get('pdf_stats', {})

                    st.success(f"✅ Descarga completada")

                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("✅ PDFs descargados", stats.get('downloaded', 0))
                    col_b.metric("❌ Sin PDF", stats.get('no_pdf', 0))
                    col_c.metric("⚠️ Errores", stats.get('failed', 0))

                    # Botón para descargar el ZIP
                    st.download_button(
                        label="📦 Descargar ZIP con PDFs",
                        data=st.session_state['pdf_zip'],
                        file_name=st.session_state['pdf_zip_name'],
                        mime="application/zip",
                        help=f"Descarga {stats.get('downloaded', 0)} PDFs con nombres: ID-Autor-Titulo.pdf"
                    )

                    st.info(f"💡 **Tip:** Descomprime el archivo ZIP en tu dispositivo y sube los PDFs a NotebookLM")

                    # Mostrar errores si los hay
                    if stats.get('errors') and len(stats['errors']) > 0:
                        with st.expander(f"⚠️ Ver detalles de errores ({len(stats['errors'])} total)"):
                            for error in stats['errors'][:20]:  # Mostrar primeros 20
                                st.text(error)

    # Tabla de resultados
    st.subheader("📋 Vista de Resultados")

    # Configurar columnas a mostrar
    display_columns = ['title', 'author', 'publication', 'year', 'citations', 'open_access']

    # Crear DataFrame para mostrar
    display_df = df[display_columns].copy()
    display_df['open_access'] = display_df['open_access'].map({True: '✅', False: '❌'})

    # Renombrar columnas
    display_df.columns = ['Título', 'Autores', 'Publicación', 'Año', 'Citas', 'Acceso Abierto']

    st.dataframe(
        display_df,
        width="stretch",
        height=400
    )

    # Detalle de resultados individuales
    st.subheader("🔍 Ver Detalle Individual")

    df = df.copy()
    # Si title viene como lista, tomar el primer elemento; si viene NaN/None, reemplazar
    df["__title"] = df["title"].apply(lambda v: (v[0] if isinstance(v, list) and v else v))
    df["__title"] = df["__title"].fillna("(sin título)").astype(str).str.strip()
    df.loc[df["__title"] == "", "__title"] = "(sin título)"

    selected_index = st.selectbox(
        "Seleccione un resultado para ver el detalle completo",
        options=range(len(df)),
        format_func=lambda i: f"{i+1}. {df.iloc[i]['__title'][:80]}…"
        )


    if selected_index is not None:
        selected = df.iloc[selected_index]

        with st.expander("📄 Detalle Completo", expanded=True):
            st.markdown(f"### {selected['title']}")
            st.markdown(f"**Autores:** {selected['author']}")
            st.markdown(f"**Publicación:** {selected['publication']}")
            st.markdown(f"**Año:** {selected['year']}")
            st.markdown(f"**Citaciones:** {selected['citations']}")
            st.markdown(f"**DOI:** {selected['doi'] if selected['doi'] else 'N/A'}")
            st.markdown(f"**OpenAlex ID:** {selected['openalex_id']}")
            st.markdown(f"**Acceso Abierto:** {'Sí' if selected['open_access'] else 'No'}")

            st.markdown("#### Abstract")
            st.write(selected['abstract'] if selected['abstract'] else "No disponible")

# Footer
st.divider()
st.caption("Taller NotebookLM - 2025 | Datos de OpenAlex API")




