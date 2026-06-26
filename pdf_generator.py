import io
import os
import re

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader, PdfWriter

from config import REGULAR_FONT_PATH, BOLD_FONT_PATH, WATERMARK_RUNTIME_PATH

RED_COLOR = colors.HexColor("#C00000")
BLACK_COLOR = colors.black
PAGE_WIDTH, PAGE_HEIGHT = A4
RIGHT_MARGIN = 10 * mm
FONTS_REGISTERED = False

FOUNDATION_OPTIONS = ["Làm quen", "Tiếp thu", "Thấu hiểu", "Vận dụng", "Làm chủ"]
COMPOSITION_OPTIONS = ["Khởi đầu", "Định hình", "Cân đối", "Chặt chẽ", "Sáng tạo đột phá"]
COLOR_OPTIONS = ["Nhận biết", "Sắc độ", "Phối màu", "Điêu luyện"]
TECHNIQUE_OPTIONS = ["Thử nghiệm", "Linh hoạt", "Khéo léo", "Tỉ mỉ", "Tinh xảo"]
CREATIVE_OPTIONS = ["Chủ động và sáng tạo", "Cần gợi ý", "Đang rèn luyện"]
ATTITUDE_OPTIONS = ["Tập trung cao", "Đôi khi xao nhãng", "Cần động viên"]

def ensure_fonts_registered():
    global FONTS_REGISTERED
    if FONTS_REGISTERED:
        return
    if not os.path.exists(REGULAR_FONT_PATH) or not os.path.exists(BOLD_FONT_PATH):
        raise FileNotFoundError("Thiếu font trong thư mục assets/")
    pdfmetrics.registerFont(TTFont("NotoSans", REGULAR_FONT_PATH))
    pdfmetrics.registerFont(TTFont("NotoSans-Bold", BOLD_FONT_PATH))
    FONTS_REGISTERED = True

def set_watermark_bytes(content: bytes):
    with open(WATERMARK_RUNTIME_PATH, "wb") as f:
        f.write(content)

def clear_watermark():
    if os.path.exists(WATERMARK_RUNTIME_PATH):
        os.remove(WATERMARK_RUNTIME_PATH)

def draw_page_background_and_watermark(c):
    c.setFillColor(colors.white)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    if os.path.exists(WATERMARK_RUNTIME_PATH):
        try:
            c.saveState()
            c.setFillAlpha(0.06)
            c.setStrokeAlpha(0.06)
            wm_size = 110 * mm
            c.drawImage(
                ImageReader(WATERMARK_RUNTIME_PATH),
                (PAGE_WIDTH - wm_size) / 2,
                (PAGE_HEIGHT - wm_size) / 2,
                width=wm_size,
                height=wm_size,
                mask="auto",
                preserveAspectRatio=True,
            )
            c.restoreState()
        except:
            pass

def normalize_option_text(s):
    if s is None:
        return ""
    text = str(s).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text.replace(".", "").replace(",", "").replace(":", "").replace(";", "")

def option_checked(value, option):
    return normalize_option_text(value) == normalize_option_text(option)

def add_page_numbers(packet: io.BytesIO) -> bytes:
    packet.seek(0)
    reader = PdfReader(packet)
    writer = PdfWriter()
    total_pages = len(reader.pages)

    for i, page in enumerate(reader.pages):
        overlay_buffer = io.BytesIO()
        can = canvas.Canvas(overlay_buffer, pagesize=A4)

        text = f"Trang {i+1} / {total_pages}"
        can.setFont("NotoSans", 9)
        can.setFillColor(BLACK_COLOR)
        can.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, 7.5 * mm, text)
        can.save()

        overlay_buffer.seek(0)
        overlay_page = PdfReader(overlay_buffer).pages[0]
        page.merge_page(overlay_page)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.getvalue()

def draw_checkbox_line(c, x, y, label, checked):
    size = 4 * mm
    c.rect(x, y - size + 1, size, size, stroke=1, fill=0)
    if checked:
        c.line(x + 1, y - 1, x + 2.5, y - 3)
        c.line(x + 2.5, y - 3, x + 6, y + 1)
    c.drawString(x + 7, y - 2, label)

def create_report_pdf_bytes(data: dict) -> bytes:
    ensure_fonts_registered()

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    draw_page_background_and_watermark(c)

    width, height = A4
    left = 15 * mm
    y = height - 20 * mm

    c.setFont("NotoSans-Bold", 18)
    c.drawCentredString(width / 2, y, "PHIẾU HOÀN THÀNH BÀI HỌC MỸ THUẬT")
    y -= 12 * mm

    c.setFont("NotoSans", 11)
    fields = [
        ("Học viên", data.get("ten_hoc_vien", "")),
        ("Giáo viên", data.get("ten_giao_vien", "")),
        ("Tên bài học", data.get("ten_bai_hoc", "")),
        ("Tác phẩm", data.get("tac_pham", "")),
        ("Số buổi thực hiện", data.get("so_buoi_thuc_hien", "")),
        ("Ngày hoàn thành", data.get("ngay_hoan_thanh", "")),
    ]

    for label, value in fields:
        c.setFont("NotoSans-Bold", 10)
        c.drawString(left, y, f"{label}:")
        c.setFont("NotoSans", 10)
        c.drawString(left + 45 * mm, y, str(value))
        y -= 7 * mm

    c.setFont("NotoSans-Bold", 11)
    c.drawString(left, y, "1. MỤC TIÊU BÀI HỌC:")
    y -= 7 * mm
    c.setFont("NotoSans", 10)
    text = c.beginText(left, y)
    text.setFont("NotoSans", 10)
    for line in str(data.get("muc_tieu_bai_hoc", "")).split("."):
        line = line.strip()
        if line:
            text.textLine(f"- {line}")
    c.drawText(text)
    y -= 20 * mm

    c.setFont("NotoSans-Bold", 11)
    c.drawString(left, y, "2. ĐÁNH GIÁ HOÀN THIỆN BÀI:")
    y -= 8 * mm

    sections = [
        ("Kiến thức nền tảng", FOUNDATION_OPTIONS, data.get("kien_thuc_nen_tang", "")),
        ("Tạo hình và bố cục", COMPOSITION_OPTIONS, data.get("tao_hinh_bo_cuc", "")),
        ("Kiến thức màu sắc", COLOR_OPTIONS, data.get("kien_thuc_mau_sac", "")),
        ("Kỹ thuật", TECHNIQUE_OPTIONS, data.get("ky_thuat", "")),
    ]

    for title, options, selected in sections:
        c.setFont("NotoSans-Bold", 10)
        c.drawString(left, y, f"- {title}:")
        y -= 6 * mm
        c.setFont("NotoSans", 9)
        x = left + 5 * mm
        for opt in options:
            draw_checkbox_line(c, x, y, opt, option_checked(selected, opt))
            x += 38 * mm
        y -= 8 * mm

    c.setFont("NotoSans-Bold", 11)
    c.drawString(left, y, "3. CHỈ SỐ SÁNG TẠO VÀ THÁI ĐỘ:")
    y -= 8 * mm

    sections2 = [
        ("Tư duy giải quyết vấn đề", CREATIVE_OPTIONS, data.get("tu_duy_giai_quyet_van_de", "")),
        ("Sự kiên trì với dự án", ATTITUDE_OPTIONS, data.get("su_kien_tri_voi_du_an", "")),
    ]

    for title, options, selected in sections2:
        c.setFont("NotoSans-Bold", 10)
        c.drawString(left, y, f"- {title}:")
        y -= 6 * mm
        x = left + 5 * mm
        for opt in options:
            draw_checkbox_line(c, x, y, opt, option_checked(selected, opt))
            x += 55 * mm
        y -= 8 * mm

    c.setFont("NotoSans-Bold", 11)
    c.drawString(left, y, "4. LỜI NHẮN TỪ GIÁO VIÊN:")
    y -= 8 * mm

    c.setFont("NotoSans-Bold", 10)
    c.drawString(left, y, "Ưu điểm nổi bật:")
    y -= 6 * mm
    c.setFont("NotoSans", 10)
    text1 = c.beginText(left + 3 * mm, y)
    for line in str(data.get("uu_diem_noi_bat", "")).split("."):
        line = line.strip()
        if line:
            text1.textLine(f"- {line}")
    c.drawText(text1)
    y -= 18 * mm

    c.setFont("NotoSans-Bold", 10)
    c.drawString(left, y, "Cần lưu ý thêm:")
    y -= 6 * mm
    c.setFont("NotoSans", 10)
    text2 = c.beginText(left + 3 * mm, y)
    for line in str(data.get("can_luu_y_them", "")).split("."):
        line = line.strip()
        if line:
            text2.textLine(f"- {line}")
    c.drawText(text2)

    y -= 25 * mm
    c.setFont("NotoSans-Bold", 10)
    c.drawRightString(width - 20 * mm, y, "CHỮ KÝ GIÁO VIÊN")
    y -= 8 * mm
    c.setFillColor(RED_COLOR)
    c.setFont("NotoSans-Bold", 12)
    c.drawRightString(width - 20 * mm, y, str(data.get("ten_giao_vien", "")))

    c.save()
    return add_page_numbers(packet)
