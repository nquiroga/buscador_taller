"""Taller NotebookLM: búsqueda trazable y descarga acotada de PDFs abiertos."""

from __future__ import annotations

import io
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from openalex_search import OpenAlexError, OpenAlexSearcher


st.set_page_config(page_title="Búsqueda académica · OpenAlex", page_icon="📚", layout="wide")


def get_secret(name: str) -> str:
    """Obtiene secretos de Streamlit Cloud o variables de entorno locales."""
    try:
        value = st.secrets.get(name, "")
    except FileNotFoundError:
        value = ""
    return str(value or os.getenv(name, "")).strip()


def dataframe_to_markdown(results: pd.DataFrame) -> str:
    header = [
        "# Resultados de búsqueda académica",
        "",
        f"- Consulta: {results['search_query'].iloc[0]}",
        f"- Fecha: {datetime.now().isoformat(timespec='seconds')}",
        f"- Registros: {len(results)}",
        "- Fuente: OpenAlex API; verificar cada obra en su enlace de origen antes de citar.",
        "",
    ]
    entries = []
    for index, row in results.iterrows():
        entries.extend(
            [
                f"## {index + 1}. {row['title']}",
                f"- Autorías: {row['author'] or 'No disponibles'}",
                f"- Publicación: {row['publication'] or 'No disponible'} ({row['year'] or 's. f.'})",
                f"- DOI: {row['doi'] or 'No disponible'}",
                f"- OpenAlex: {row['openalex_id']}",
                f"- Acceso: {row['oa_status'] or 'sin clasificar'}; licencia: {row['license'] or 'sin licencia informada'}",
                f"- PDF: {row['oa_pdf_url'] or 'No disponible'}",
                "",
                "### Resumen",
                row['abstract'] or "No disponible",
                "",
            ]
        )
    return "\n".join(header + entries)


st.title("📚 Búsqueda académica abierta")
st.caption("Taller NotebookLM · OpenAlex · PDFs abiertos con procedencia verificable")
st.info("La búsqueda orienta; la lectura y la cita deben verificarse siempre en el texto y la página de origen.")

api_key = get_secret("OPENALEX_API_KEY")
mailto = get_secret("OPENALEX_MAILTO")
if not api_key:
    st.warning("La app puede consultar OpenAlex sin clave, pero una clave privada aumenta el cupo disponible. Consultá README.md para configurarla.")

with st.sidebar:
    st.header("Cómo buscar")
    st.markdown("""
    OpenAlex admite `AND`, `OR`, `NOT`, paréntesis y frases entre comillas.

    La aplicación recupera registros de acceso abierto y, si lo indicás, sólo aquellos con URL de PDF. La disponibilidad no sustituye la comprobación de licencia, versión y pertinencia.
    """)
    st.header("Preparar NotebookLM")
    st.markdown("""
    1. Revisá la lista de resultados.
    2. Descargá un conjunto pequeño de PDFs abiertos.
    3. Conservá el manifiesto incluido en el ZIP.
    4. Subí los PDFs y el manifiesto a NotebookLM.
    """)

query = st.text_input(
    "Consulta",
    placeholder='Ej.: (peronismo OR justicialismo) AND argentina',
    help="Usá MAYÚSCULAS para los operadores booleanos.",
)

left, middle, right = st.columns(3)
with left:
    max_results = st.number_input("Resultados máximos", min_value=10, max_value=500, value=100, step=10)
with middle:
    sort_options = {
        "Relevancia": "relevance_score:desc",
        "Más citados": "cited_by_count:desc",
        "Más recientes": "publication_date:desc",
    }
    sort_choice = st.selectbox(
        "Orden",
        options=list(sort_options),
    )
with right:
    require_pdf = st.checkbox("Sólo registros con PDF", value=True)

year_from, year_to = st.slider(
    "Años de publicación",
    min_value=1900,
    max_value=datetime.now().year,
    value=(2000, datetime.now().year),
)
require_known_license = st.checkbox("Sólo PDFs con licencia informada", value=True)

if st.button("Buscar", type="primary", width="stretch"):
    if not query.strip():
        st.warning("Ingresá una consulta antes de buscar.")
    else:
        try:
            with st.spinner("Consultando OpenAlex…"):
                searcher = OpenAlexSearcher(api_key=api_key, mailto=mailto)
                rows = searcher.search(
                    query=query,
                    max_results=max_results,
                    year_from=year_from,
                    year_to=year_to,
                    open_access_only=True,
                    require_pdf=require_pdf,
                    require_known_license=require_known_license,
                    sort=sort_options[sort_choice],
                )
            st.session_state["results"] = pd.DataFrame(rows)
        except OpenAlexError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"La búsqueda no pudo completarse: {exc}")

results = st.session_state.get("results")
if results is not None and not results.empty:
    st.success(f"Se recuperaron {len(results)} registros.")
    st.dataframe(
        results[["title", "author", "publication", "year", "citations", "oa_status", "license", "oa_pdf_url"]],
        width="stretch",
        height=420,
        column_config={"oa_pdf_url": st.column_config.LinkColumn("PDF abierto")},
    )

    csv_data = results.to_csv(index=False).encode("utf-8")
    markdown_data = dataframe_to_markdown(results).encode("utf-8")
    export_left, export_right = st.columns(2)
    export_left.download_button("Descargar metadatos CSV", csv_data, "resultados_openalex.csv", "text/csv", width="stretch")
    export_right.download_button("Descargar resumen Markdown", markdown_data, "resultados_openalex.md", "text/markdown", width="stretch")

    st.subheader("PDFs para NotebookLM")
    eligible = results[results["oa_pdf_url"].notna() & (results["oa_pdf_url"] != "")].copy()
    if eligible.empty:
        st.info("Esta búsqueda no tiene URLs de PDF abierto para preparar.")
    else:
        quantity = st.number_input(
            "PDFs a descargar (máximo 20, hasta 25 MB por archivo)",
            min_value=1,
            max_value=min(20, len(eligible)),
            value=min(10, len(eligible)),
        )
    if not eligible.empty and st.button("Preparar ZIP con PDFs y manifiesto", width="stretch"):
        selected = eligible.head(int(quantity)).to_dict("records")
        progress_bar = st.progress(0)
        status = st.empty()

        def update_progress(current: int, total: int, downloaded: int) -> None:
            progress_bar.progress(current / total)
            status.caption(f"Procesados: {current}/{total}; PDFs válidos: {downloaded}")

        temporary_directory = tempfile.mkdtemp(prefix="openalex-pdfs-")
        try:
            searcher = OpenAlexSearcher(api_key=api_key, mailto=mailto)
            stats = searcher.download_pdfs(selected, Path(temporary_directory), update_progress)
            manifest = pd.DataFrame(selected).drop(columns=["abstract"], errors="ignore")
            readme = (
                "Este ZIP contiene PDFs abiertos descargados desde URLs declaradas por OpenAlex.\n"
                "El archivo manifiesto.csv conserva DOI, ID OpenAlex, URL, licencia, versión y estado de descarga.\n"
                "Verifique cada fuente y sus condiciones de uso antes de citar, redistribuir o cargarla en otros servicios.\n"
            )
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in stats["files"]:
                    archive.write(path, path.name)
                archive.writestr("manifiesto.csv", manifest.to_csv(index=False))
                archive.writestr("LEEME.txt", readme)
            st.session_state["pdf_zip"] = zip_buffer.getvalue()
            st.session_state["pdf_stats"] = stats
        finally:
            shutil.rmtree(temporary_directory, ignore_errors=True)
            progress_bar.empty()
            status.empty()

if st.session_state.get("pdf_zip"):
    stats = st.session_state["pdf_stats"]
    st.success(f"PDFs válidos: {stats['downloaded']} · omitidos: {stats['skipped']} · con error: {stats['failed']}")
    st.download_button(
        "Descargar ZIP para NotebookLM",
        st.session_state["pdf_zip"],
        "openalex_notebooklm.zip",
        "application/zip",
        width="stretch",
    )
    if stats["errors"]:
        with st.expander("Ver incidencias de descarga"):
            st.write("\n".join(f"- {error}" for error in stats["errors"]))
