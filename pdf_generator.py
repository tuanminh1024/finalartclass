import io
import os
import re
from pathlib import Path

from xhtml2pdf import pisa

from config import REGULAR_FONT_PATH, BOLD_FONT_PATH, WATERMARK_RUNTIME_PATH

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATE_PATH = TEMPLATES_DIR / "report.html"


def ensure_assets_ready():
    missing_files = []

    if not os.path.exists(REGULAR_FONT_PATH):
        missing_files.append(REGULAR_FONT_PATH)
    if not os.path.exists(BOLD_FONT_PATH):
        missing_files.append(BOLD_FONT_PATH)
    if not os.path.exists(TEMPLATE_PATH):
        missing_files.append(str(TEMPLATE_PATH))

    if missing_files:
        raise FileNotFoundError("Thiếu file: " + ", ".join(missing_files))


def set_watermark_bytes(content: bytes):
    with open(WATERMARK_RUNTIME_PATH, "wb") as f:
        f.write(content)


def clear_watermark():
    if os.path.exists(WATERMARK_RUNTIME_PATH):
        os.remove(WATERMARK_RUNTIME_PATH)


def normalize_option_text(s):
    if s is None:
        return ""
    text = str(s).strip().lower().replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    for ch in [".", ",", ";", ":", "!", "?", "*", "-", "_", "(", ")", "[", "]", "{", "}", "/"]:
        text = text.replace(ch, "")
    return text.strip()


def option_checked(value, option):
    return normalize_option_text(value) == normalize_option_text(option)


def to_bullet_html(text):
    items = []
    for line in str(text).split("."):
        line = line.strip()
        if line:
            items.append(f"<li>{escape_html(line)}</li>")
    if not items:
        return "<ul><li>&nbsp;</li></ul>"
    return f"<ul>{''.join(items)}</ul>"


def escape_html(text):
    text = str(text)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_checkbox_html(options, selected_value):
    html_parts = []
    for opt in options:
        checked = "☑" if option_checked(selected_value, opt) else "☐"
        html_parts.append(
            f'<span class="checkbox-item">{checked} {escape_html(opt)}</span>'
        )
    return "".join(html_parts)


def build_report_html(data: dict) -> str:
    ensure_assets_ready()

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    watermark_html = ""
    if os.path.exists(WATERMARK_RUNTIME_PATH):
        watermark_uri = Path(WATERMARK_RUNTIME_PATH).resolve().as_uri()
        watermark_html = f'<img class="watermark" src="{watermark_uri}" alt="watermark" />'

    regular_font_uri = Path(REGULAR_FONT_PATH).resolve().as_uri()
    bold_font_uri = Path(BOLD_FONT_PATH).resolve().as_uri()

    replacements = {
        "{{REGULAR_FONT_URI}}": regular_font_uri,
        "{{BOLD_FONT_URI}}": bold_font_uri,
        "{{WATERMARK_HTML}}": watermark_html,

        "{{TEN_HOC_VIEN}}": escape_html(data.get("ten_hoc_vien", "")),
        "{{TEN_GIAO_VIEN}}": escape_html(data.get("ten_giao_vien", "")),
        "{{TEN_BAI_HOC}}": escape_html(data.get("ten_bai_hoc", "")),
        "{{TAC_PHAM}}": escape_html(data.get("tac_pham", "")),
        "{{SO_BUOI_THUC_HIEN}}": escape_html(data.get("so_buoi_thuc_hien", "")),
        "{{NGAY_HOAN_THANH}}": escape_html(data.get("ngay_hoan_thanh", "")),

        "{{MUC_TIEU_BAI_HOC}}": to_bullet_html(data.get("muc_tieu_bai_hoc", "")),
        "{{UU_DIEM_NOI_BAT}}": to_bullet_html(data.get("uu_diem_noi_bat", "")),
        "{{CAN_LUU_Y_THEM}}": to_bullet_html(data.get("can_luu_y_them", "")),

        "{{FOUNDATION_HTML}}": build_checkbox_html(
            ["Làm quen", "Tiếp thu", "Thấu hiểu", "Vận dụng", "Làm chủ"],
            data.get("kien_thuc_nen_tang", ""),
        ),
        "{{COMPOSITION_HTML}}": build_checkbox_html(
            ["Khởi đầu", "Định hình", "Cân đối", "Chặt chẽ", "Sáng tạo đột phá"],
            data.get("tao_hinh_bo_cuc", ""),
        ),
        "{{COLOR_HTML}}": build_checkbox_html(
            ["Nhận biết", "Sắc độ", "Phối màu", "Điêu luyện"],
            data.get("kien_thuc_mau_sac", ""),
        ),
        "{{TECHNIQUE_HTML}}": build_checkbox_html(
            ["Thử nghiệm", "Linh hoạt", "Khéo léo", "Tỉ mỉ", "Tinh xảo"],
            data.get("ky_thuat", ""),
        ),
        "{{CREATIVE_HTML}}": build_checkbox_html(
            ["Chủ động và sáng tạo", "Cần gợi ý", "Đang rèn luyện"],
            data.get("tu_duy_giai_quyet_van_de", ""),
        ),
        "{{ATTITUDE_HTML}}": build_checkbox_html(
            ["Tập trung cao", "Đôi khi xao nhãng", "Cần động viên"],
            data.get("su_kien_tri_voi_du_an", ""),
        ),
    }

    html = template
    for key, value in replacements.items():
        html = html.replace(key, value)

    return html


def create_report_pdf_bytes(data: dict) -> bytes:
    html = build_report_html(data)

    output = io.BytesIO()
    result = pisa.CreatePDF(src=html, dest=output, encoding="utf-8")

    if result.err:
        raise ValueError("Không thể tạo PDF từ HTML.")

    output.seek(0)
    return output.getvalue()
