import re
import pandas as pd
from datetime import datetime
from gspread_dataframe import get_as_dataframe

def normalize_header_key(s):
    if s is None:
        return ""
    text = str(s).strip().lower().replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    for ch in [".", ",", ";", ":", "!", "?", "*", "-", "_", "(", ")", "[", "]", "{", "}", "/"]:
        text = text.replace(ch, " ")
    return re.sub(r"\s+", " ", text).strip()

def normalize_option_text(s):
    if s is None:
        return ""
    text = str(s).strip().lower().replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    for ch in [".", ",", ";", ":", "!", "?", "*", "-", "_", "(", ")", "[", "]", "{", "}", "/"]:
        text = text.replace(ch, "")
    replacements = {
        "cần gọi ý": "cần gợi ý",
        "can goi y": "cần gợi ý",
        "điêu luyện.": "điêu luyện",
        "nhận biết.": "nhận biết",
    }
    return replacements.get(text, text)

def uppercase_text(text):
    return str(text).upper().strip() if text is not None else ""

def safe_filename(text):
    return re.sub(r"\s+", " ", re.sub(r'[\\/*?:"<>|]', "", str(text))).strip()

def find_col_by_priority(df, candidates_exact=None, candidates_contains=None):
    candidates_exact = candidates_exact or []
    candidates_contains = candidates_contains or []

    normalized_cols = {col: normalize_header_key(col) for col in df.columns}
    exact_norm = [normalize_header_key(x) for x in candidates_exact]

    for col, norm in normalized_cols.items():
        if norm in exact_norm:
            return col

    contains_norm = [normalize_header_key(x) for x in candidates_contains]
    for col, norm in normalized_cols.items():
        for token in contains_norm:
            if token and token in norm:
                return col
    return None

def build_column_mapping(df):
    mapping = {}
    mapping["dau_thoi_gian"] = find_col_by_priority(df, ["Dấu thời gian"], ["dấu thời gian"])
    mapping["ten_giao_vien"] = find_col_by_priority(df, ["Tên của giáo viên", "Tên giáo viên", "TÊN CỦA GIÁO VIÊN"], ["giáo viên"])
    mapping["ten_hoc_vien"] = find_col_by_priority(
        df,
        ["Họ và tên của học viên", "Họ và tên học viên", "Tên học viên", "Học viên", "Học sinh", "HỌ VÀ TÊN CỦA HỌC VIÊN"],
        ["học viên", "học sinh"]
    )
    mapping["ten_bai_hoc"] = find_col_by_priority(df, ["Tên bài học", "TÊN BÀI HỌC"], ["tên bài học"])
    mapping["tac_pham"] = find_col_by_priority(df, ["Tác phẩm"], ["tác phẩm"])
    mapping["so_buoi_thuc_hien"] = find_col_by_priority(df, ["Số buổi thực hiện", "SỐ BUỔI THỰC HIỆN"], ["số buổi thực hiện"])
    mapping["muc_tieu_bai_hoc"] = find_col_by_priority(df, ["Mục tiêu bài học"], ["mục tiêu bài học"])
    mapping["kien_thuc_nen_tang"] = find_col_by_priority(df, ["KIẾN THỨC NỀN TẢNG", "Kiến thức nền tảng"], ["kiến thức nền tảng"])
    mapping["tao_hinh_bo_cuc"] = find_col_by_priority(df, ["TẠO HÌNH VÀ BỐ CỤC", "Tạo hình và bố cục"], ["tạo hình và bố cục"])
    mapping["kien_thuc_mau_sac"] = find_col_by_priority(df, ["KIẾN THỨC MÀU SẮC", "Kiến thức màu sắc"], ["kiến thức màu sắc"])
    mapping["ky_thuat"] = find_col_by_priority(df, ["KỸ THUẬT", "Kĩ thuật", "Kỹ thuật"], ["kỹ thuật", "kĩ thuật"])
    mapping["tu_duy_giai_quyet_van_de"] = find_col_by_priority(df, ["TƯ DUY GIẢI QUYẾT VẤN ĐỀ"], ["tư duy giải quyết vấn đề"])
    mapping["su_kien_tri_voi_du_an"] = find_col_by_priority(df, ["SỰ KIÊN TRÌ VỚI DỰ ÁN"], ["sự kiên trì với dự án"])
    mapping["uu_diem_noi_bat"] = find_col_by_priority(df, ["Ưu điểm nổi bật trong bài"], ["ưu điểm nổi bật"])
    mapping["diem_can_luu_y"] = find_col_by_priority(df, ["Điểm cần lưu ý", "Điểm con cần lưu ý"], ["điểm cần lưu ý", "rèn luyện thêm"])
    return {k: v for k, v in mapping.items() if v is not None}

def build_date_str(x):
    if pd.isna(x):
        return ""
    try:
        return pd.to_datetime(str(x).strip(), dayfirst=True).strftime("%d/%m/%Y")
    except:
        try:
            return pd.to_datetime(str(x).strip()).strftime("%d/%m/%Y")
        except:
            return str(x).split(" ")[0] if str(x) else ""

def extract_datetime_info(timestamp_text):
    if not timestamp_text:
        return {"thu": "", "ngay": "", "thang": ""}
    try:
        dt = pd.to_datetime(str(timestamp_text).strip(), dayfirst=True)
    except:
        return {"thu": "", "ngay": "", "thang": ""}

    thu_map = {
        0: "THỨ HAI", 1: "THỨ BA", 2: "THỨ TƯ",
        3: "THỨ NĂM", 4: "THỨ SÁU", 5: "THỨ BẢY", 6: "CHỦ NHẬT"
    }
    return {"thu": thu_map.get(dt.weekday(), ""), "ngay": str(dt.day), "thang": str(dt.month)}

def safe_get(row, mapping, key, default=""):
    col = mapping.get(key, "")
    return row[col] if (col and col in row.index and pd.notna(row[col])) else default

def prepare_sheet_dataframe(df, mapping, sheet_name):
    df = df.copy()
    timestamp_col = mapping.get("dau_thoi_gian")
    teacher_col = mapping.get("ten_giao_vien")
    student_col = mapping.get("ten_hoc_vien")

    df["_date_str"] = df[timestamp_col].apply(build_date_str) if timestamp_col in df.columns else ""
    df["_teacher_str"] = df[teacher_col].astype(str).str.strip() if teacher_col in df.columns else str(sheet_name).strip()
    df["_student_str"] = df[student_col].astype(str).str.strip() if student_col in df.columns else ""
    df["_sheet_name"] = str(sheet_name).strip()
    return df

def load_all_sheets_data(spreadsheet):
    all_dfs = []
    sheet_mappings = {}

    for ws in spreadsheet.worksheets():
        try:
            raw_df = get_as_dataframe(ws, evaluate_formulas=True).dropna(how="all").dropna(axis=1, how="all")
            if raw_df.empty:
                continue

            mapping = build_column_mapping(raw_df)
            if not mapping.get("ten_hoc_vien"):
                continue

            prepared_df = prepare_sheet_dataframe(raw_df, mapping, ws.title)
            all_dfs.append(prepared_df)
            sheet_mappings[ws.title] = mapping
        except:
            continue

    if not all_dfs:
        return pd.DataFrame(), {}

    combined_df = pd.concat(all_dfs, ignore_index=True, sort=False)
    return combined_df, sheet_mappings

def row_to_report_data(row, mapping):
    dt_info = extract_datetime_info(safe_get(row, mapping, "dau_thoi_gian"))
    dau_thoi_gian_raw = str(safe_get(row, mapping, "dau_thoi_gian")).strip()
    ngay_hoan_thanh_text = build_date_str(dau_thoi_gian_raw) if dau_thoi_gian_raw else ""

    return {
        "ten_hoc_vien": uppercase_text(safe_get(row, mapping, "ten_hoc_vien")),
        "ten_giao_vien": str(safe_get(row, mapping, "ten_giao_vien")).strip(),
        "ten_bai_hoc": uppercase_text(safe_get(row, mapping, "ten_bai_hoc")),
        "tac_pham": uppercase_text(safe_get(row, mapping, "tac_pham")),
        "thu": uppercase_text(dt_info["thu"]),
        "ngay": dt_info["ngay"],
        "thang": dt_info["thang"],
        "so_buoi_thuc_hien": str(safe_get(row, mapping, "so_buoi_thuc_hien")).strip(),
        "ngay_hoan_thanh": ngay_hoan_thanh_text,
        "muc_tieu_bai_hoc": str(safe_get(row, mapping, "muc_tieu_bai_hoc")).strip(),
        "kien_thuc_nen_tang": str(safe_get(row, mapping, "kien_thuc_nen_tang")).strip(),
        "tao_hinh_bo_cuc": str(safe_get(row, mapping, "tao_hinh_bo_cuc")).strip(),
        "kien_thuc_mau_sac": str(safe_get(row, mapping, "kien_thuc_mau_sac")).strip(),
        "ky_thuat": str(safe_get(row, mapping, "ky_thuat")).strip(),
        "tu_duy_giai_quyet_van_de": str(safe_get(row, mapping, "tu_duy_giai_quyet_van_de")).strip(),
        "su_kien_tri_voi_du_an": str(safe_get(row, mapping, "su_kien_tri_voi_du_an")).strip(),
        "uu_diem_noi_bat": str(safe_get(row, mapping, "uu_diem_noi_bat")).strip(),
        "can_luu_y_them": str(safe_get(row, mapping, "diem_can_luu_y")).strip(),
    }

def get_mapping_for_row(row, sheet_mappings):
    sheet_name = str(row.get("_sheet_name", "")).strip()
    return sheet_mappings.get(sheet_name, {})

def get_teacher_options(df):
    if df is None or df.empty:
        return ["Tất cả"]
    vals = sorted([str(x).strip() for x in df["_teacher_str"].dropna().unique().tolist() if str(x).strip()])
    return ["Tất cả"] + vals

def get_date_options(df):
    if df is None or df.empty:
        return ["Tất cả"]
    vals = sorted([d for d in df["_date_str"].dropna().unique().tolist() if d])
    return ["Tất cả"] + vals

def apply_filters(df, teachers=None, date_val=None):
    if df is None or df.empty:
        return pd.DataFrame()

    temp_df = df.copy()

    if teachers and ("Tất cả" not in teachers):
        temp_df = temp_df[temp_df["_teacher_str"].astype(str).str.strip().isin([str(v).strip() for v in teachers])]

    if date_val and date_val != "Tất cả":
        temp_df = temp_df[temp_df["_date_str"] == date_val]

    return temp_df.copy()

def update_student_list(df):
    if df is None or df.empty:
        return ["Tất cả"]

    return ["Tất cả"] + sorted([
        str(x).strip()
        for x in df["_student_str"].dropna().unique().tolist()
        if str(x).strip()
    ])
