"""Cliente acotado para búsqueda y descarga de PDFs abiertos desde OpenAlex."""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Callable, Iterable

import requests


OPENALEX_WORKS_URL = "https://api.openalex.org/works"
MAX_PER_PAGE = 100
MAX_PDF_BYTES = 25 * 1024 * 1024
DEFAULT_TIMEOUT = 30


class OpenAlexError(RuntimeError):
    """Error legible para la interfaz de la aplicación."""


def _reconstruct_abstract(inverted_index: dict | None) -> str:
    """Reconstruye el resumen que OpenAlex entrega como índice invertido."""
    if not inverted_index:
        return ""
    try:
        size = max(position for positions in inverted_index.values() for position in positions) + 1
        words = [""] * size
        for word, positions in inverted_index.items():
            for position in positions:
                words[position] = word
        return " ".join(word for word in words if word)
    except (TypeError, ValueError):
        return ""


def _safe_filename(index: int, title: str, authors: str, work_id: str) -> str:
    """Genera un nombre estable y portable para un PDF descargado."""
    first_author = (authors or "sin_autoria").split(";")[0].strip().split()[-1:]
    author = first_author[0] if first_author else "sin_autoria"
    title_words = re.findall(r"[\wÀ-ÿ]+", title or "")[:5]
    stem = "-".join([f"{index:03d}", author, "_".join(title_words) or work_id])
    stem = re.sub(r'[<>:"/\\|?*]', "_", stem).strip(" ._")
    return f"{stem[:140]}.pdf"


def _best_pdf_location(work: dict) -> dict:
    """Elige la primera ubicación OA con URL de PDF y conserva su procedencia."""
    candidates = [work.get("best_oa_location"), work.get("primary_location")]
    candidates.extend(work.get("locations") or [])
    for location in candidates:
        if isinstance(location, dict) and location.get("pdf_url") and location.get("is_oa"):
            return location
    return {}


class OpenAlexSearcher:
    """Consulta paginada de OpenAlex y descarga directa de PDFs de acceso abierto."""

    def __init__(
        self,
        api_key: str | None = None,
        mailto: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key or os.getenv("OPENALEX_API_KEY")
        self.mailto = mailto or os.getenv("OPENALEX_MAILTO")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "buscador-taller/2.0 (academic teaching tool)",
                "Accept": "application/json",
            }
        )

    def _request(self, params: dict) -> dict:
        params = {key: value for key, value in params.items() if value not in (None, "")}
        if self.api_key:
            params["api_key"] = self.api_key
        if self.mailto:
            params["mailto"] = self.mailto

        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = self.session.get(OPENALEX_WORKS_URL, params=params, timeout=self.timeout)
                if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(float(response.headers.get("Retry-After", 2 ** attempt)))
                    continue
                if response.status_code in (401, 403):
                    raise OpenAlexError("OpenAlex rechazó la clave configurada. Revisá OPENALEX_API_KEY.")
                response.raise_for_status()
                return response.json()
            except requests.RequestException as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(2 ** attempt)
        raise OpenAlexError(f"No fue posible consultar OpenAlex: {last_error}")

    def search(
        self,
        query: str,
        max_results: int = 100,
        year_from: int | None = None,
        year_to: int | None = None,
        open_access_only: bool = True,
        require_pdf: bool = True,
        require_known_license: bool = False,
        sort: str = "relevance_score:desc",
    ) -> list[dict]:
        """Busca obras y devuelve sólo los campos necesarios para el taller."""
        filters: list[str] = []
        if open_access_only:
            filters.append("open_access.is_oa:true")
        if require_pdf:
            filters.append("has_pdf_url:true")
        if year_from is not None:
            filters.append(f"publication_year:>{year_from - 1}")
        if year_to is not None:
            filters.append(f"publication_year:<{year_to + 1}")

        params = {
            "search": query.strip(),
            "filter": ",".join(filters),
            "sort": sort,
            "per_page": min(MAX_PER_PAGE, max_results),
            "cursor": "*",
        }

        works: list[dict] = []
        while len(works) < max_results:
            payload = self._request(params)
            batch = payload.get("results") or []
            works.extend(batch)
            cursor = (payload.get("meta") or {}).get("next_cursor")
            if not batch or not cursor:
                break
            params["cursor"] = cursor

        rows = [self._extract_row(work) for work in works[:max_results]]
        if require_known_license:
            rows = [row for row in rows if row["license"]]
        for row in rows:
            row["search_query"] = query.strip()
        return rows

    def _extract_row(self, work: dict) -> dict:
        location = _best_pdf_location(work)
        authors = [
            ((authorship.get("author") or {}).get("display_name"))
            for authorship in (work.get("authorships") or [])
        ]
        authors = [author for author in authors if author]
        source = location.get("source") or (work.get("primary_location") or {}).get("source") or {}
        doi = (work.get("doi") or "").removeprefix("https://doi.org/")
        work_id = (work.get("id") or "").removeprefix("https://openalex.org/")
        return {
            "title": work.get("title") or work.get("display_name") or "Sin título",
            "author": "; ".join(authors),
            "publication": source.get("display_name") or "",
            "year": work.get("publication_year") or "",
            "date": work.get("publication_date") or "",
            "citations": work.get("cited_by_count") or 0,
            "doi": doi,
            "openalex_id": work_id,
            "open_access": bool((work.get("open_access") or {}).get("is_oa")),
            "oa_status": (work.get("open_access") or {}).get("oa_status") or "",
            "license": location.get("license") or "",
            "pdf_version": location.get("version") or "",
            "oa_pdf_url": location.get("pdf_url") or "",
            "oa_landing_url": location.get("landing_page_url") or "",
            "abstract": _reconstruct_abstract(work.get("abstract_inverted_index")),
            "type": work.get("type") or "",
            "language": work.get("language") or "",
        }

    def download_pdfs(
        self,
        records: Iterable[dict],
        output_dir: Path,
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> dict:
        """Descarga únicamente URLs de PDF ya declaradas como OA por OpenAlex."""
        output_dir.mkdir(parents=True, exist_ok=True)
        records = list(records)
        stats = {"total": len(records), "downloaded": 0, "failed": 0, "skipped": 0, "files": [], "errors": []}

        for index, record in enumerate(records, start=1):
            url = record.get("oa_pdf_url")
            if not url:
                stats["skipped"] += 1
                continue
            try:
                response = self.session.get(url, timeout=self.timeout, stream=True)
                response.raise_for_status()
                content_length = int(response.headers.get("Content-Length", 0) or 0)
                if content_length > MAX_PDF_BYTES:
                    stats["skipped"] += 1
                    stats["errors"].append(f"{record['title']}: supera 25 MB")
                    continue

                filename = _safe_filename(index, record.get("title", ""), record.get("author", ""), record.get("openalex_id", "obra"))
                path = output_dir / filename
                written = 0
                with path.open("wb") as file:
                    for chunk in response.iter_content(chunk_size=64 * 1024):
                        if not chunk:
                            continue
                        written += len(chunk)
                        if written > MAX_PDF_BYTES:
                            raise OpenAlexError("el archivo supera 25 MB")
                        file.write(chunk)
                with path.open("rb") as file:
                    if file.read(4) != b"%PDF":
                        raise OpenAlexError("la URL no devolvió un PDF válido")

                record["downloaded_file"] = filename
                record["download_status"] = "downloaded"
                stats["files"].append(path)
                stats["downloaded"] += 1
            except (OSError, requests.RequestException, OpenAlexError) as exc:
                path = output_dir / _safe_filename(index, record.get("title", ""), record.get("author", ""), record.get("openalex_id", "obra"))
                path.unlink(missing_ok=True)
                record["download_status"] = "failed"
                stats["failed"] += 1
                stats["errors"].append(f"{record.get('title', 'Sin título')}: {exc}")
            finally:
                if progress_callback:
                    progress_callback(index, len(records), stats["downloaded"])
        return stats
