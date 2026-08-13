"""Cliente de Semantic Scholar para el buscador de taller."""

import os
import re
import time

import requests


SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,abstract,authors,year,venue,citationCount,externalIds,openAccessPdf,url"


class SemanticScholarSearcher:
    def __init__(self, timeout=25, api_key=None):
        self.timeout = timeout
        self.api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        if self.api_key:
            self.session.headers["x-api-key"] = self.api_key

    @staticmethod
    def _plain_query(query):
        """Semantic Scholar usa consulta de texto; conserva los términos del formulario."""
        return re.sub(r"\s+", " ", re.sub(r"\b(?:AND|OR|NOT)\b|[()\"]", " ", query, flags=re.IGNORECASE)).strip()

    @staticmethod
    def _is_open_access(paper):
        return bool((paper.get("openAccessPdf") or {}).get("url"))

    def _request(self, params):
        last_error = None
        for delay in (0, 1, 2):
            if delay:
                time.sleep(delay)
            try:
                response = self.session.get(SEMANTIC_SCHOLAR_URL, params=params, timeout=self.timeout)
                if response.status_code in (429, 500, 502, 503, 504):
                    last_error = RuntimeError(f"Semantic Scholar respondió {response.status_code}")
                    continue
                response.raise_for_status()
                return response.json()
            except requests.RequestException as error:
                last_error = error
        raise RuntimeError(f"Semantic Scholar no respondió: {last_error}")

    def _extract_row(self, paper):
        external_ids = paper.get("externalIds") or {}
        doi = external_ids.get("DOI") or ""
        pdf = (paper.get("openAccessPdf") or {}).get("url") or ""
        authors = "; ".join(author.get("name", "") for author in paper.get("authors") or [] if author.get("name"))
        return {
            "title": paper.get("title") or "",
            "author": authors,
            "publication": paper.get("venue") or "",
            "year": paper.get("year") or "",
            "citations": paper.get("citationCount") or 0,
            "doi": doi,
            "openalex_id": paper.get("paperId") or "",
            "open_access": self._is_open_access(paper),
            "abstract": paper.get("abstract") or "",
            "oa_pdf_url": pdf,
            "oa_landing_url": paper.get("url") or "",
            "source": "Semantic Scholar",
        }

    def get_all_results(self, query, max_results=50, open_access_filter="all", year_from=None, year_to=None):
        query = self._plain_query(query)
        if not query:
            return []
        rows = []
        offset = 0
        while len(rows) < max_results and offset < 1000:
            params = {
                "query": query,
                "fields": FIELDS,
                "limit": min(100, max_results - len(rows)),
                "offset": offset,
            }
            if year_from is not None and year_to is not None:
                params["year"] = f"{year_from}-{year_to}"
            elif year_from is not None:
                params["year"] = f"{year_from}-"
            elif year_to is not None:
                params["year"] = f"-{year_to}"
            if open_access_filter == "open_access_only":
                params["openAccessPdf"] = ""

            data = self._request(params)
            batch = data.get("data") or []
            if not batch:
                break
            for paper in batch:
                is_oa = self._is_open_access(paper)
                if open_access_filter == "closed_only" and is_oa:
                    continue
                row = self._extract_row(paper)
                row["search_query"] = query
                rows.append(row)
                if len(rows) >= max_results:
                    break
            offset = data.get("next")
            if offset is None:
                break
        return rows
