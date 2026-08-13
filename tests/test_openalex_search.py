import unittest

from openalex_search import OpenAlexSearcher, _reconstruct_abstract, _safe_filename


class OpenAlexSearchTests(unittest.TestCase):
    def test_reconstructs_inverted_abstract(self):
        abstract = _reconstruct_abstract({"mundo": [1], "Hola": [0], "digital": [2]})
        self.assertEqual(abstract, "Hola mundo digital")

    def test_search_uses_safe_page_size_and_extracts_pdf_provenance(self):
        captured = []
        searcher = OpenAlexSearcher()
        searcher._request = lambda params: captured.append(params.copy()) or {
            "results": [
                {
                    "id": "https://openalex.org/W1",
                    "title": "Historia digital",
                    "doi": "https://doi.org/10.1234/ejemplo",
                    "publication_year": 2024,
                    "open_access": {"is_oa": True, "oa_status": "gold"},
                    "best_oa_location": {
                        "is_oa": True,
                        "pdf_url": "https://example.org/archivo.pdf",
                        "landing_page_url": "https://example.org/articulo",
                        "license": "cc-by",
                        "version": "publishedVersion",
                        "source": {"display_name": "Revista de prueba"},
                    },
                    "authorships": [{"author": {"display_name": "Ada Lovelace"}}],
                    "abstract_inverted_index": {"Historia": [0], "digital": [1]},
                }
            ],
            "meta": {"next_cursor": None},
        }

        rows = searcher.search(
            query="historia digital",
            max_results=250,
            year_from=2020,
            year_to=2024,
            require_known_license=True,
            sort="cited_by_count:desc",
        )

        self.assertEqual(captured[0]["per_page"], 100)
        self.assertIn("open_access.is_oa:true", captured[0]["filter"])
        self.assertIn("has_pdf_url:true", captured[0]["filter"])
        self.assertEqual(captured[0]["sort"], "cited_by_count:desc")
        self.assertEqual(rows[0]["oa_pdf_url"], "https://example.org/archivo.pdf")
        self.assertEqual(rows[0]["license"], "cc-by")
        self.assertEqual(rows[0]["abstract"], "Historia digital")

    def test_filename_is_portable(self):
        name = _safe_filename(1, 'Título: con / caracteres?', "Ana Pérez", "W1")
        self.assertTrue(name.endswith(".pdf"))
        self.assertNotRegex(name, r'[<>:"/\\|?*]')


if __name__ == "__main__":
    unittest.main()
