import os
import json
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

def get_gspread_client():
    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()

    if not creds_json:
        raise ValueError("Thiếu biến môi trường GOOGLE_SERVICE_ACCOUNT_JSON")

    try:
        creds_dict = json.loads(creds_json)
    except Exception as e:
        raise ValueError(f"GOOGLE_SERVICE_ACCOUNT_JSON không hợp lệ: {e}")

    credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(credentials)
