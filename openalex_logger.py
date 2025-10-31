"""
Sistema de Logging Anónimo para Búsquedas OpenAlex
Registra búsquedas y resultados en Google Sheets sin datos personales
GDPR-compliant: solo queries, parámetros y cifras agregadas
"""

import os
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
import streamlit as st

# Importaciones opcionales (no rompen si faltan)
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False


class OpenAlexLogger:
    """
    Logger anónimo para estadísticas de búsqueda

    Registra en Google Sheets:
    - Query de búsqueda
    - Parámetros (tipo, filtros, años)
    - Resultados agregados (totales, con abstract, acceso abierto)
    - Estadísticas de descarga de PDFs (si aplica)

    NO registra:
    - IPs, emails, nombres u otros datos personales
    - Solo un session_id hash anónimo por sesión
    """

    def __init__(self, enabled: bool = True):
        """
        Inicializa el logger

        Args:
            enabled: Si False, todas las llamadas son no-op (útil para testing)
        """
        self.enabled = enabled and GSPREAD_AVAILABLE
        self.client = None
        self.sheet = None
        self._initialized = False

        if self.enabled:
            self._initialize()

    def _initialize(self):
        """Inicializa la conexión a Google Sheets (lazy loading)"""
        try:
            # Verificar que existen los secrets
            if "google_sheets" not in st.secrets:
                self.enabled = False
                return

            # Cargar credenciales desde Streamlit secrets
            creds_dict = dict(st.secrets["google_sheets"])

            # Scopes necesarios para Google Sheets
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            self.client = gspread.authorize(creds)

            # Abrir la hoja (debe existir previamente)
            spreadsheet_name = st.secrets.get("google_sheets_name", "openalex_logs")
            self.sheet = self.client.open(spreadsheet_name).sheet1

            self._initialized = True

        except Exception as e:
            # Logging deshabilitado si falla la inicialización
            self.enabled = False
            print(f"⚠️ Logger deshabilitado: {e}")

    def log_search(
        self,
        query: str,
        search_params: Dict[str, Any],
        results_df: Any,  # pandas DataFrame
        pdf_stats: Optional[Dict[str, int]] = None
    ):
        """
        Registra una búsqueda realizada

        Args:
            query: Query de búsqueda ingresada por el usuario
            search_params: Diccionario con parámetros de búsqueda
                {
                    'search_type': str,
                    'max_results': int,
                    'open_access_filter': str,
                    'year_from': int,
                    'year_to': int,
                    'sort_by': str
                }
            results_df: DataFrame de pandas con los resultados
            pdf_stats: Opcional, estadísticas de descarga de PDFs
                {
                    'downloaded': int,
                    'failed': int,
                    'no_pdf': int,
                    'total': int
                }
        """
        if not self.enabled:
            return

        try:
            # Calcular estadísticas de resultados
            total_found = len(results_df)
            with_abstract = int(results_df['abstract'].notna().sum())
            open_access_count = int(results_df['open_access'].sum())

            # Calcular promedio de citaciones (manejar valores NaN)
            citations = results_df['citations'].astype(float)
            avg_citations = round(float(citations.mean()), 2) if total_found > 0 else 0

            # Generar session ID anónimo
            session_id = self._get_session_id()

            # Preparar fila para Google Sheets
            row = [
                # Timestamp
                datetime.now().isoformat(),

                # Session (anónimo)
                session_id,

                # Query y parámetros
                str(query)[:500],  # Limitar longitud
                search_params.get('search_type', 'N/A'),
                search_params.get('max_results', 0),
                search_params.get('open_access_filter', 'all'),
                search_params.get('year_from', ''),
                search_params.get('year_to', ''),
                search_params.get('sort_by', 'relevance_score:desc'),

                # Resultados agregados
                total_found,
                with_abstract,
                open_access_count,
                avg_citations,

                # PDFs (si se intentó descargar)
                bool(pdf_stats),
                pdf_stats.get('downloaded', 0) if pdf_stats else 0,
                pdf_stats.get('failed', 0) if pdf_stats else 0,
                pdf_stats.get('no_pdf', 0) if pdf_stats else 0,
                pdf_stats.get('total', 0) if pdf_stats else 0,
            ]

            # Escribir a Google Sheets (no bloquea UI en caso de error)
            if self._initialized:
                self.sheet.append_row(row, value_input_option='USER_ENTERED')

        except Exception as e:
            # Silencioso: no romper la app si falla el logging
            print(f"⚠️ Error en logging (no crítico): {e}")

    def _get_session_id(self) -> str:
        """
        Genera un ID anónimo único por sesión de Streamlit

        Returns:
            Hash SHA256 de 16 caracteres (no identificable personalmente)
        """
        if 'anonymous_session_id' not in st.session_state:
            # Generar hash basado en timestamp + bytes aleatorios
            raw_data = f"{datetime.now().timestamp()}{os.urandom(16).hex()}"
            hash_hex = hashlib.sha256(raw_data.encode()).hexdigest()
            st.session_state['anonymous_session_id'] = hash_hex[:16]

        return st.session_state['anonymous_session_id']

    @staticmethod
    def create_spreadsheet_header():
        """
        Retorna la fila de encabezado para Google Sheets
        Usar esto para crear la hoja manualmente la primera vez

        Returns:
            Lista con nombres de columnas
        """
        return [
            'timestamp',
            'session_id',
            'query',
            'search_type',
            'max_results',
            'open_access_filter',
            'year_from',
            'year_to',
            'sort_by',
            'total_found',
            'with_abstract',
            'open_access_count',
            'avg_citations',
            'pdf_download_attempted',
            'pdfs_downloaded',
            'pdfs_failed',
            'pdfs_no_available',
            'pdfs_total_processed'
        ]


# Función helper para uso simple
def log_search_event(query, search_params, results_df, pdf_stats=None):
    """
    Helper function para logging simple

    Uso:
        from openalex_logger import log_search_event
        log_search_event(query, params, df)
    """
    try:
        logger = OpenAlexLogger()
        logger.log_search(query, search_params, results_df, pdf_stats)
    except Exception:
        # Completamente silencioso si falla
        pass

