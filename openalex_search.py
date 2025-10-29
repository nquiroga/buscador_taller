
# openalex_search.py — búsqueda intacta + descarga robusta con LOGS (ON por defecto)
import os
import time
import json
import requests
from urllib.parse import urlencode, urljoin
from bs4 import BeautifulSoup

OPENALEX_BASE = "https://api.openalex.org/works"

SELECT_FIELDS = (
    "id,doi,display_name,publication_year,"
    "primary_location,biblio,authorships,"
    "cited_by_count,open_access,best_oa_location,abstract_inverted_index,locations"
)

def _safe_progress(cb, *args):
    if not cb:
        return
    try:
        cb(*args)
    except TypeError:
        try:
            cb(args[0])
        except TypeError:
            try:
                cb()
            except TypeError:
                pass

def _sanitize_doi_for_filename(doi):
    """Sanitiza un DOI para usarlo como nombre de archivo en cualquier OS"""
    if not doi:
        return "unknown"
    # Remover prefijos URL
    doi_clean = (doi or "").replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
    # Reemplazar caracteres no válidos para nombres de archivo
    # Windows no permite: < > : " / \ | ? *
    # También reemplazamos espacios por seguridad
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', ' ']
    for char in invalid_chars:
        doi_clean = doi_clean.replace(char, '_')
    # Limitar longitud (Windows tiene límite de 260 caracteres para la ruta completa)
    if len(doi_clean) > 200:
        doi_clean = doi_clean[:200]
    return doi_clean

def _sanitize_text_for_filename(text, max_length=50):
    """Sanitiza texto (título, autor) para usarlo en nombres de archivo"""
    if not text:
        return ""

    # Convertir a string y limpiar
    text = str(text).strip()

    # Remover comillas, paréntesis y otros caracteres problemáticos
    text = text.replace('"', '').replace("'", "").replace('(', '').replace(')', '')
    text = text.replace('[', '').replace(']', '').replace('{', '').replace('}', '')

    # Reemplazar caracteres no válidos para nombres de archivo
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '\n', '\r', '\t']
    for char in invalid_chars:
        text = text.replace(char, ' ')

    # Reemplazar múltiples espacios por uno solo
    import re
    text = re.sub(r'\s+', ' ', text).strip()

    # Reemplazar espacios por guiones bajos
    text = text.replace(' ', '_')

    # Remover puntos excepto el último (para la extensión)
    text = text.replace('.', '')

    # Limitar longitud
    if len(text) > max_length:
        text = text[:max_length]

    # Remover guiones bajos al final
    text = text.rstrip('_')

    return text

def _generate_descriptive_filename(index, title, author, doi, max_total_length=150):
    """
    Genera un nombre de archivo descriptivo: ID-autor-titulo.pdf

    Args:
        index: Índice numérico del artículo (empezando en 1)
        title: Título del artículo
        author: Autor(es) del artículo
        doi: DOI como fallback
        max_total_length: Longitud máxima total del nombre

    Returns:
        Nombre de archivo sanitizado
    """
    parts = []

    # 1. ID del artículo (siempre presente)
    id_str = f"{index:03d}"  # Formato: 001, 002, etc.
    parts.append(id_str)

    # 2. Autor - extraer primer autor si hay varios
    if author and str(author).strip() and str(author).lower() not in ('nan', 'none', ''):
        author_str = str(author).strip()
        # Si hay múltiples autores separados por ; tomar el primero
        if ';' in author_str:
            author_str = author_str.split(';')[0].strip()
        # Si hay coma (apellido, nombre), tomar solo el apellido
        if ',' in author_str:
            author_str = author_str.split(',')[0].strip()
        # Tomar solo el apellido (última palabra)
        author_parts = author_str.split()
        if author_parts:
            author_str = author_parts[-1]  # Último token suele ser el apellido

        author_clean = _sanitize_text_for_filename(author_str, max_length=20)
        if author_clean:
            parts.append(author_clean)

    # 3. Título - tomar palabras significativas
    if title and str(title).strip() and str(title).lower() not in ('nan', 'none', ''):
        title_str = str(title).strip()

        # Remover artículos y palabras comunes al inicio
        stop_words = ['the', 'a', 'an', 'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas']
        title_words = title_str.split()

        # Tomar las primeras 3-5 palabras significativas
        significant_words = []
        for word in title_words:
            word_clean = word.strip('.,;:!?¿¡-–—()[]{}\"\'')
            if word_clean.lower() not in stop_words and len(word_clean) > 2:
                significant_words.append(word_clean)
            if len(significant_words) >= 4:
                break

        if significant_words:
            title_fragment = '_'.join(significant_words)
            title_clean = _sanitize_text_for_filename(title_fragment, max_length=60)
            if title_clean:
                parts.append(title_clean)

    # Si no hay ni autor ni título, usar DOI sanitizado
    if len(parts) == 1:  # Solo tiene el ID
        doi_clean = _sanitize_doi_for_filename(doi)
        parts.append(doi_clean[:30])

    # Unir las partes
    filename = '-'.join(parts)

    # Limitar longitud total
    if len(filename) > max_total_length:
        filename = filename[:max_total_length]

    # Asegurar que termina en .pdf
    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'

    return filename

class OpenAlexSearcher:
    def __init__(self, timeout=25, mailto=None):
        self.timeout = timeout
        self.mailto = mailto or os.getenv("OPENALEX_MAILTO")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "OpenAlex-Streamlit/1.4 (+mailto)",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.8",
        })

    def _request(self, params):
        p = {k: v for k, v in params.items() if v not in (None, "")}
        if self.mailto:
            p["mailto"] = self.mailto
        url = f"{OPENALEX_BASE}?{urlencode(p, doseq=True)}"

        for delay in (0, 1.0, 2.0):
            if delay:
                time.sleep(delay)
            r = self.session.get(url, timeout=self.timeout)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (403, 429):
                ra = r.headers.get("Retry-After")
                if ra:
                    try:
                        time.sleep(float(ra))
                    except Exception:
                        time.sleep(2.0)
                continue
            r.raise_for_status()
        r.raise_for_status()

    def _reconstruct_abstract(self, inverted):
        if not inverted:
            return ""
        try:
            max_pos = 0
            for positions in inverted.values():
                max_pos = max(max_pos, max(positions))
            words = [""] * (max_pos + 1)
            for w, poss in inverted.items():
                for p in poss:
                    if 0 <= p < len(words):
                        words[p] = w
            return " ".join([w for w in words if w])
        except Exception:
            return ""

    def _extract_row(self, w):
        doi = (w.get("doi") or "").replace("https://doi.org/", "").replace("http://doi.org/", "")
        oa = w.get("open_access") or {}
        is_oa = bool(oa.get("is_oa")) if isinstance(oa, dict) else bool(oa)
        authors = []
        for a in (w.get("authorships") or []):
            person = a.get("author") or {}
            name = person.get("display_name")
            if name:
                authors.append(name)
        pub = ""
        prim = (w.get("primary_location") or {})
        if isinstance(prim, dict):
            src = prim.get("source") or {}
            pub = src.get("display_name") or ""
        abstract = self._reconstruct_abstract(w.get("abstract_inverted_index"))
        best = w.get("best_oa_location") or {}
        pdf_url = best.get("pdf_url") or (prim.get("pdf_url") if isinstance(prim, dict) else None)
        landing_url = best.get("landing_page_url") or (prim.get("landing_page_url") if isinstance(prim, dict) else None)
        return {
            "title": w.get("display_name", ""),
            "author": "; ".join(authors),
            "publication": pub,
            "year": w.get("publication_year") or "",
            "citations": w.get("cited_by_count", 0),
            "doi": doi,
            "openalex_id": w.get("id", ""),
            "open_access": is_oa,
            "abstract": abstract,
            "oa_pdf_url": pdf_url or "",
            "oa_landing_url": landing_url or "",
        }

    def get_all_results(self, query, max_results=50, search_type="general", open_access_filter="all"):
        params = {
            "per_page": min(max_results, 200),
            "select": SELECT_FIELDS,
            "sort": "relevance_score:desc",
            "cursor": "*",
            "search": query.strip(),
        }
        if open_access_filter == "open_access_only":
            params["filter"] = "is_oa:true"
        elif open_access_filter == "closed_only":
            params["filter"] = "is_oa:false"
        out = []
        while len(out) < max_results:
            data = self._request(params)
            batch = data.get("results", []) or []
            out.extend(batch)
            cur = data.get("meta", {}).get("next_cursor")
            if not cur or not batch:
                break
            params["cursor"] = cur
        rows = [self._extract_row(w) for w in out[:max_results]]
        sq = query.strip()
        for r in rows:
            r.setdefault("search_query", sq)
        return rows

    def _find_meta_pdf_url(self, html_bytes, base_url):
        soup = BeautifulSoup(html_bytes, "html.parser")

        # Lista extendida de meta tags que pueden contener URL del PDF
        meta_names = [
            "citation_pdf_url",
            "pdf_url",
            "og:pdf",
            "dc.identifier.uri",
            "dc.relation.uri",
            "bepress_citation_pdf_url",
            "fulltext_pdf"
        ]

        # Buscar en meta tags
        for m in soup.find_all("meta"):
            name = (m.get("name") or m.get("property") or "").lower()
            content = (m.get("content") or "").strip()

            if not content:
                continue

            # Verificar si el nombre del meta tag indica PDF
            if name in meta_names:
                return urljoin(base_url, content)

            # Verificar si el contenido parece ser una URL de PDF
            if name and "pdf" in name and (content.lower().endswith(".pdf") or "/pdf" in content.lower()):
                return urljoin(base_url, content)

        # Buscar en link tags con type="application/pdf"
        for l in soup.find_all("link", href=True):
            rel = l.get("rel", [])
            if isinstance(rel, str):
                rel = [rel]
            typ = (l.get("type") or "").lower()
            title = (l.get("title") or "").lower()
            href = (l.get("href") or "").strip()

            if not href:
                continue

            # Link con type PDF
            if "application/pdf" in typ:
                return urljoin(base_url, href)

            # Link alternativo que apunta a PDF
            if "alternate" in rel and (".pdf" in href.lower() or "pdf" in title):
                return urljoin(base_url, href)

        return None

    def _find_view_link(self, html_bytes, base_url):
        soup = BeautifulSoup(html_bytes, "html.parser")

        view_patterns = [
            "view", "/article/view", "/viewarticle",
            "fulltext", "full-text", "full_text",
            "/ver", "leer"
        ]

        # Buscar en enlaces <a>
        for a in soup.find_all("a", href=True):
            href = (a.get("href") or "").strip()
            txt = (a.get_text() or "").strip().lower()

            if not href:
                continue

            low_href = href.lower()

            # Verificar patrones en el href
            if any(pattern in low_href for pattern in view_patterns):
                return urljoin(base_url, href)

            # Verificar si el texto indica visualización
            if any(pattern in txt for pattern in view_patterns):
                return urljoin(base_url, href)

        # Buscar en iframes, embeds y objects
        for tag in soup.find_all(["iframe", "embed", "object"]):
            src = tag.get("src") or tag.get("data")
            if not src:
                continue

            low_src = src.lower()
            if any(pattern in low_src for pattern in view_patterns):
                return urljoin(base_url, src)

        return None

    def _find_direct_pdf_links(self, html_bytes, base_url):
        """Busca enlaces directos a PDFs en la página landing, priorizando el dominio actual"""
        from urllib.parse import urlparse
        soup = BeautifulSoup(html_bytes, "html.parser")
        same_domain = []
        other_domain = []

        base_domain = urlparse(base_url).netloc

        pdf_patterns = [".pdf", "download", "descargar", "pdf", "galley", "/article/download"]
        text_patterns = ["pdf", "download", "descargar", "texto completo", "full text", "ver pdf", "view pdf"]

        for a in soup.find_all("a", href=True):
            href = (a.get("href") or "").strip()
            txt = (a.get_text() or "").strip().lower()
            css_classes = " ".join(a.get("class", [])).lower()

            if not href:
                continue

            low_href = href.lower()
            full_url = urljoin(base_url, href)
            url_domain = urlparse(full_url).netloc

            # Determinar si este enlace es candidato a PDF
            is_candidate = False

            # Enlaces que terminan en .pdf
            if low_href.endswith(".pdf"):
                is_candidate = True

            # Enlaces OJS con class="pdf" o class="obj_galley_link"
            elif "pdf" in css_classes or "galley" in css_classes:
                is_candidate = True

            # Enlaces con patrones de descarga
            elif any(pattern in low_href for pattern in pdf_patterns):
                # Verificar que también el texto o clases sugieran descarga/PDF
                if any(pattern in txt for pattern in text_patterns) or any(pattern in css_classes for pattern in ["pdf", "download", "galley"]) or any(pattern in low_href for pattern in [".pdf", "download", "galley"]):
                    is_candidate = True

            if is_candidate:
                # Separar por dominio
                if url_domain == base_domain:
                    same_domain.append(full_url)
                else:
                    other_domain.append(full_url)

        # Deduplicar preservando orden
        def dedup(lst):
            seen, result = set(), []
            for item in lst:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            return result

        # Priorizar: mismo dominio primero, luego otros dominios
        return dedup(same_domain) + dedup(other_domain)

    def _extract_download_links_from_view(self, html_bytes, base_url):
        soup = BeautifulSoup(html_bytes, "html.parser")
        out = []

        # Patrones que indican un enlace de descarga
        download_patterns = [
            "download", "descargar", "pdf", "full-text", "fulltext",
            "/article/download", "/article/view/", "view/",
            ".pdf", "galley", "viewfile"
        ]

        text_patterns = [
            "download", "descargar", "pdf", "texto completo",
            "full text", "full-text", "article pdf"
        ]

        for a in soup.find_all("a", href=True):
            href = (a.get("href") or "").strip()
            txt = (a.get_text() or "").strip().lower()

            if not href:
                continue

            low_href = href.lower()

            # Verificar si el href contiene algún patrón de descarga
            if any(pattern in low_href for pattern in download_patterns):
                out.append(urljoin(base_url, href))
                continue

            # Verificar si el texto del enlace indica descarga
            if any(pattern in txt for pattern in text_patterns):
                out.append(urljoin(base_url, href))
                continue

            # Patrón OJS específico: /article/view/ID/GALLEY_ID
            # donde GALLEY_ID es un número (usualmente el PDF)
            if "/article/view/" in low_href:
                parts = href.split("/")
                # Verificar si tiene formato /article/view/123/456
                if len(parts) >= 5 and parts[-1].isdigit() and parts[-2].isdigit():
                    out.append(urljoin(base_url, href))

        # Buscar también en iframes, embeds y objects que puedan contener PDFs
        for tag in soup.find_all(["iframe", "embed", "object"]):
            src = tag.get("src") or tag.get("data")
            if src:
                low_src = src.lower()
                if any(pattern in low_src for pattern in download_patterns):
                    out.append(urljoin(base_url, src))

        # Deduplicar manteniendo el orden
        seen, dedup = set(), []
        for u in out:
            if u not in seen:
                seen.add(u)
                dedup.append(u)
        return dedup

    def _try_get_pdf(self, url, referer=None, stream=False):
        headers = {
            "User-Agent": self.session.headers.get("User-Agent", "Mozilla/5.0"),
            "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8",
        }
        if referer:
            headers["Referer"] = referer

        # Intenta HEAD request primero (más rápido)
        try:
            r = self.session.head(url, timeout=self.timeout, allow_redirects=True, headers=headers)
            ct = (r.headers.get("content-type") or "").lower()
            if "application/pdf" in ct:
                return True, r.url, None
        except Exception:
            pass

        # GET request - verificar por content-type Y firma PDF
        try:
            r = self.session.get(url, timeout=self.timeout, allow_redirects=True, headers=headers, stream=stream)
            if not r.ok:
                return False, None, None

            ct = (r.headers.get("content-type") or "").lower()

            # Si el content-type indica PDF, es PDF
            if "application/pdf" in ct:
                return True, r.url, r

            # Si no hay stream, verificar firma mágica
            if not stream:
                if r.content.startswith(b"%PDF"):
                    return True, r.url, r
                return False, None, None

            # Con stream: leer solo los primeros bytes para verificar firma
            # IMPORTANTE: usar peek() si está disponible, sino leer y conservar
            try:
                # Peek permite mirar sin consumir el stream
                chunk = r.raw.peek(5)[:5] if hasattr(r.raw, 'peek') else None
                if chunk and chunk.startswith(b"%PDF"):
                    return True, r.url, r

                # Si peek no está disponible, leer el chunk inicial
                if chunk is None:
                    first_chunk = next(r.iter_content(chunk_size=5), b"")
                    if first_chunk.startswith(b"%PDF"):
                        # Es un PDF pero ya consumimos bytes
                        # Retornar None para que el caller haga una nueva petición
                        r.close()
                        return True, r.url, None
            except Exception:
                pass

            return False, None, None

        except Exception as e:
            return False, None, None

    def _resolve_pdf_with_logs(self, doi, debug=True, debug_dir="debug_openalex"):
        log = {"doi": doi, "steps": []}
        doi_norm = (doi or "").replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
        doi_safe = _sanitize_doi_for_filename(doi)

        def _log(step):
            log["steps"].append(step)

        try:
            landing = self.session.get(f"https://doi.org/{doi_norm}", timeout=self.timeout, allow_redirects=True)
            _log({"phase":"landing", "request": f"https://doi.org/{doi_norm}", "status": landing.status_code, "final_url": landing.url})
        except Exception as e:
            _log({"phase":"landing", "error": str(e)})
            return None, None, None, log

        if not landing.ok:
            return None, None, None, log
        base = landing.url

        # Detectar si Crossref redirect a su API (devuelve JSON en lugar de HTML)
        if "api.crossref.org" in landing.url.lower():
            _log({"phase":"crossref_api_detected", "url": landing.url})
            try:
                data = landing.json()
                primary_url = data.get("resource", {}).get("primary", {}).get("URL")
                if primary_url:
                    _log({"phase":"crossref_primary_url", "url": primary_url})
                    # Hacer nueva petición a la URL real del artículo
                    try:
                        landing = self.session.get(primary_url, timeout=self.timeout, allow_redirects=True)
                        base = landing.url
                        _log({"phase":"article_page", "status": landing.status_code, "url": landing.url})
                        if not landing.ok:
                            return None, None, None, log
                    except Exception as e:
                        _log({"phase":"article_page_error", "error": str(e)})
                        return None, None, None, log
            except Exception as e:
                _log({"phase":"crossref_json_parse_error", "error": str(e)})
                # Intentar continuar con el HTML aunque sea Crossref
                pass

        if debug and debug_dir:
            try:
                os.makedirs(debug_dir, exist_ok=True)
                with open(os.path.join(debug_dir, f"{doi_safe}_landing.html"), "wb") as fh:
                    fh.write(landing.content)
            except Exception as e:
                _log({"phase":"debug_save_landing", "error": str(e)})

        # Estrategia 1: Buscar meta tags PDF
        meta_pdf = self._find_meta_pdf_url(landing.content, base)
        _log({"phase":"meta_lookup", "meta_pdf": meta_pdf or ""})
        if meta_pdf:
            ok, fin, r = self._try_get_pdf(meta_pdf, referer=base, stream=False)
            _log({"phase":"meta_try", "url": meta_pdf, "ok": bool(ok), "final_url": fin or ""})
            if ok:
                return fin, "meta_pdf", base, log

        # Estrategia 2: Buscar enlaces directos a PDF en la página landing
        direct_links = self._find_direct_pdf_links(landing.content, base)
        _log({"phase":"direct_links_lookup", "count": len(direct_links), "links": direct_links})
        for dlink in direct_links:
            # Patrón OJS: convertir /article/view/ID/GALLEY a /article/download/ID/GALLEY
            test_url = dlink
            if "/article/view/" in dlink.lower():
                test_url_download = dlink.replace("/article/view/", "/article/download/").replace("/Article/View/", "/Article/Download/")
                _log({"phase":"ojs_view_to_download", "original": dlink, "converted": test_url_download})
                # Probar primero la versión download
                ok, fin, r = self._try_get_pdf(test_url_download, referer=base, stream=False)
                _log({"phase":"direct_link_try", "url": test_url_download, "ok": bool(ok), "final_url": fin or ""})
                if ok:
                    return fin, "direct_link_ojs", base, log
                # Si falla, probar la URL original view
                test_url = dlink

            ok, fin, r = self._try_get_pdf(test_url, referer=base, stream=False)
            _log({"phase":"direct_link_try", "url": test_url, "ok": bool(ok), "final_url": fin or ""})
            if ok:
                return fin, "direct_link", base, log

        # Estrategia 3: Pipeline view → download
        view_url = self._find_view_link(landing.content, base)
        _log({"phase":"view_lookup", "view_url": view_url or ""})
        if view_url:
            try:
                view = self.session.get(view_url, timeout=self.timeout, allow_redirects=True, headers={"Referer": base})
                _log({"phase":"view_request", "status": view.status_code, "final_url": view.url})
            except Exception as e:
                _log({"phase":"view_request", "error": str(e)})
                return None, None, None, log

            if view.ok:
                if debug and debug_dir:
                    try:
                        with open(os.path.join(debug_dir, f"{doi_safe}_view.html"), "wb") as fh:
                            fh.write(view.content)
                    except Exception as e:
                        _log({"phase":"debug_save_view", "error": str(e)})
                dlinks = self._extract_download_links_from_view(view.content, view.url)
                _log({"phase":"download_links", "count": len(dlinks), "links": dlinks})
                for durl in dlinks:
                    ok, fin, r = self._try_get_pdf(durl, referer=view.url, stream=False)
                    _log({"phase":"download_try", "url": durl, "ok": bool(ok), "final_url": fin or ""})
                    if ok:
                        return fin, "view_download", view.url, log

        return None, None, None, log

    def download_pdfs_from_dois(self, dois, output_dir, progress_callback=None, debug=True, debug_dir="debug_openalex", metadata=None):
        """
        Descarga PDFs desde una lista de DOIs

        Args:
            dois: Lista de DOIs
            output_dir: Directorio donde guardar los PDFs
            progress_callback: Función de callback para progreso
            debug: Si True, guarda logs y HTML
            debug_dir: Directorio para logs de debug
            metadata: Diccionario opcional {doi: {'title': ..., 'author': ..., 'index': ...}}
                      Si se provee, usa nombres descriptivos: ID-autor-titulo.pdf

        Returns:
            Diccionario con estadísticas de descarga
        """
        os.makedirs(output_dir, exist_ok=True)
        if debug and debug_dir:
            os.makedirs(debug_dir, exist_ok=True)

        stats = {"total": len(dois), "downloaded": 0, "failed": 0, "no_pdf": 0, "log": [], "errors": []}

        for idx, doi in enumerate(dois, start=1):
            doi_safe = _sanitize_doi_for_filename(doi)
            pdf_url, method, referer, flow_log = self._resolve_pdf_with_logs(doi, debug=debug, debug_dir=debug_dir)

            if debug and debug_dir:
                try:
                    with open(os.path.join(debug_dir, f"{doi_safe}_log.json"), "w", encoding="utf-8") as fh:
                        json.dump(flow_log, fh, ensure_ascii=False, indent=2)
                except Exception as e:
                    stats["errors"].append(f"{doi}: error guardando log: {e}")

            try:
                if pdf_url:
                    ok, fin, r = self._try_get_pdf(pdf_url, referer=referer, stream=True)
                    if ok:
                        if r is None:
                            r = self.session.get(fin, timeout=self.timeout, headers=({"Referer": referer} if referer else None), stream=True)

                        # Generar nombre de archivo
                        name = None

                        # Opción 1: Usar metadatos si están disponibles (preferido)
                        if metadata and doi in metadata:
                            meta = metadata[doi]
                            name = _generate_descriptive_filename(
                                index=meta.get('index', idx),
                                title=meta.get('title', ''),
                                author=meta.get('author', ''),
                                doi=doi
                            )

                        # Opción 2: Parsear Content-Disposition del servidor
                        if not name:
                            disp = r.headers.get("Content-Disposition", "") if r else ""
                            if disp:
                                # Intentar extraer filename= o filename*=
                                import re
                                # Buscar filename*=UTF-8''nombre o filename="nombre" o filename=nombre
                                match = re.search(r"filename\*=UTF-8''([^;]+)", disp)
                                if match:
                                    name = match.group(1)
                                else:
                                    match = re.search(r'filename="?([^";]+)"?', disp)
                                    if match:
                                        name = match.group(1)

                        # Opción 3: Fallback al DOI sanitizado
                        if not name:
                            name = doi_safe + ".pdf"

                        # Sanitizar el nombre de archivo (por si viene del servidor)
                        if not metadata or doi not in metadata:
                            name = _sanitize_doi_for_filename(name) if not name.lower().endswith('.pdf') else name
                            if not name.lower().endswith('.pdf'):
                                name += '.pdf'

                        fpath = os.path.join(output_dir, name)
                        with open(fpath, "wb") as f:
                            for chunk in r.iter_content(chunk_size=65536):
                                if chunk:
                                    f.write(chunk)
                        stats["downloaded"] += 1
                        stats["log"].append({"doi": doi, "status": "downloaded", "url": fin, "method": method, "file_path": fpath})
                    else:
                        stats["failed"] += 1
                        stats["errors"].append(f"Descarga fallida desde {pdf_url}")
                        stats["log"].append({"doi": doi, "status": "failed", "method": method})
                else:
                    stats["no_pdf"] += 1
                    stats["log"].append({"doi": doi, "status": "no_pdf"})
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append(f"{doi}: {e}")
                stats["log"].append({"doi": doi, "status": "error", "error": str(e)})
            finally:
                _safe_progress(progress_callback, idx, len(dois), stats['downloaded'])

        return stats
