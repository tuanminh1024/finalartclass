import zipfile
import streamlit as st

from auth import get_gspread_client
from auth_app import require_login, logout_button
from sheet_utils import (
    load_all_sheets_data,
    apply_filters,
    get_teacher_options,
    get_date_options,
    update_student_list,
    get_mapping_for_row,
    row_to_report_data,
    safe_filename,
)
from pdf_generator import create_report_pdf_bytes, set_watermark_bytes, clear_watermark

st.set_page_config(
    page_title="Phiếu Hoàn Thành Bài Học Mỹ Thuật",
    page_icon="🎨",
    layout="wide"
)

# =========================
# LOGIN REQUIRED
# =========================
require_login()

st.title("🎨 HỆ THỐNG TẠO PHIẾU HOÀN THÀNH MỸ THUẬT")

@st.cache_resource
def init_gspread():
    return get_gspread_client()

@st.cache_data(ttl=300)
def load_workbook(sheet_url):
    gc = init_gspread()
    spreadsheet = gc.open_by_url(sheet_url)
    return load_all_sheets_data(spreadsheet)

def build_zip(df, sheet_mappings, group_by_sheet=False):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for _, row in df.iterrows():
            mapping = get_mapping_for_row(row, sheet_mappings)
            if not mapping:
                continue
            report_data = row_to_report_data(row, mapping)
            if not report_data.get("ten_hoc_vien"):
                continue
            filename = f"{safe_filename(report_data['ten_hoc_vien'])}_{safe_filename(report_data['ten_bai_hoc'])}.pdf"
            pdf_bytes = create_report_pdf_bytes(report_data)
            if group_by_sheet:
                sheet_name = safe_filename(str(row.get("_sheet_name", "UnknownSheet")))
                zipf.writestr(f"{sheet_name}/{filename}", pdf_bytes)
            else:
                zipf.writestr(filename, pdf_bytes)
    return zip_buffer.getvalue()

# =========================
# SIDEBAR
# =========================
st.sidebar.header("Cấu hình")
st.sidebar.success(f"Đăng nhập: {st.session_state.get('username', '')}")
logout_button()

sheet_url = st.sidebar.text_input("Google Sheet URL")
uploaded_watermark = st.sidebar.file_uploader("Watermark PNG", type=["png"])

c1, c2 = st.sidebar.columns(2)
with c1:
    if st.button("Nạp watermark", use_container_width=True):
        if uploaded_watermark:
            set_watermark_bytes(uploaded_watermark.read())
            st.success("Đã nạp watermark")
        else:
            st.warning("Vui lòng chọn file PNG trước")

with c2:
    if st.button("Xóa watermark", use_container_width=True):
        clear_watermark()
        st.info("Đã xóa watermark")

if st.sidebar.button("Tải dữ liệu", type="primary", use_container_width=True):
    if not sheet_url.strip():
        st.error("Vui lòng nhập Google Sheet URL")
    else:
        try:
            with st.spinner("Đang tải workbook..."):
                df, mappings = load_workbook(sheet_url.strip())
            st.session_state["selected_df"] = df
            st.session_state["sheet_mappings"] = mappings
            st.success(f"Đã tải {len(df)} phiếu")
        except Exception as e:
            st.error(f"Lỗi tải dữ liệu: {e}")

if "selected_df" not in st.session_state or st.session_state["selected_df"] is None:
    st.info("Nhập Google Sheet URL để bắt đầu.")
    st.stop()

selected_df = st.session_state["selected_df"]
sheet_mappings = st.session_state["sheet_mappings"]

teacher_options = get_teacher_options(selected_df)
date_options = get_date_options(selected_df)

f1, f2, f3 = st.columns([2, 1, 1])

with f1:
    teachers = st.multiselect("Giáo viên", teacher_options, default=["Tất cả"])
with f2:
    date_val = st.selectbox("Ngày tháng", date_options)
with f3:
    preview_n = st.selectbox("Preview", [10, 20, 50], index=0)

filtered_df = apply_filters(selected_df, teachers=teachers, date_val=date_val)

st.info(f"Tìm thấy {len(filtered_df)} phiếu phù hợp")

st.subheader("Preview dữ liệu")
st.dataframe(filtered_df.head(preview_n), use_container_width=True)

student_options = update_student_list(filtered_df)
student_name = st.selectbox("Tên học viên", student_options)

a1, a2, a3 = st.columns(3)

with a1:
    if st.button("Tạo PDF 1 học viên", use_container_width=True):
        if student_name == "Tất cả":
            st.warning("Vui lòng chọn học viên")
        else:
            student_rows = filtered_df[
                filtered_df["_student_str"].astype(str).str.strip() == str(student_name).strip()
            ]
            if student_rows.empty:
                st.error("Không tìm thấy dữ liệu học viên")
            else:
                row = student_rows.iloc[-1]
                mapping = get_mapping_for_row(row, sheet_mappings)
                report_data = row_to_report_data(row, mapping)
                pdf_bytes = create_report_pdf_bytes(report_data)
                filename = f"{safe_filename(report_data['ten_hoc_vien'])}_{safe_filename(report_data['ten_bai_hoc'])}.pdf"
                st.download_button(
                    "⬇️ Tải PDF",
                    pdf_bytes,
                    filename,
                    "application/pdf",
                    use_container_width=True
                )

with a2:
    if st.button("ZIP theo bộ lọc", use_container_width=True):
        if filtered_df.empty:
            st.warning("Không có dữ liệu để xuất")
        else:
            zip_bytes = build_zip(filtered_df, sheet_mappings, group_by_sheet=False)
            st.download_button(
                "⬇️ Tải ZIP theo bộ lọc",
                zip_bytes,
                "BaoCao_TheoBoLoc.zip",
                "application/zip",
                use_container_width=True
            )

with a3:
    if st.button("ZIP toàn bộ workbook", use_container_width=True):
        zip_bytes = build_zip(selected_df, sheet_mappings, group_by_sheet=True)
        st.download_button(
            "⬇️ Tải ZIP toàn bộ",
            zip_bytes,
            "ToanBo_Workbook.zip",
            "application/zip",
            use_container_width=True
        )
