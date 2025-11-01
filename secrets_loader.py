import os
import json
import streamlit as st

class SecretsError(RuntimeError):
    pass

def _from_st_secrets():
    if "google_sheets" in st.secrets:
        # sección [google_sheets]
        cfg = dict(st.secrets["google_sheets"])
        sheet_name = st.secrets.get("google_sheets_name", "openalex_logs")
        return sheet_name, cfg
    if "GOOGLE_SERVICE_ACCOUNT_JSON" in st.secrets:
        cfg = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT_JSON"])
        sheet_name = st.secrets.get("google_sheets_name", "openalex_logs")
        return sheet_name, cfg
    raise SecretsError("No se encontraron claves google_sheets ni GOOGLE_SERVICE_ACCOUNT_JSON.")

def _from_env():
    if os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"):
        cfg = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
        sheet_name = os.getenv("GOOGLE_SHEETS_NAME", "openalex_logs")
        return sheet_name, cfg
    raise SecretsError("Sin variables de entorno para Google.")

def load_google_sheets_secrets():
    try:
        return _from_st_secrets()
    except Exception:
        return _from_env()
