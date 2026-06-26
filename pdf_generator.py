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
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from pypdf import PdfReader, PdfWriter

from config import REGULAR_FONT_PATH, BOLD_FONT_PATH, WATERMARK_RUNTIME_PATH

RED_COLOR = colors.HexColor("#C00000")
BLACK_COLOR = colors.black
PAGE_WIDTH, PAGE_HEIGHT = A4
RIGHT_MARGIN = 10 * mm
LEFT_MARGIN = 15 * mm
TOP_MARGIN = 20 * mm
BOTTOM_MARGIN = 15 * mm
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
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

    missing_files = []
    if not os.path.exists(REGULAR_FONT_PATH):
        missing_files.append(REGULAR_FONT_PATH)
    if not os.path.exists(BOLD_FONT_PATH):
        missing_files.append(BOLD_FONT_PATH)

    if missing_files:
        raise FileNotFoundError("Thiếu file font: " + ", ".join(missing_files))

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
    c.saveState()
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
        except Exception:
            pass

    c.restoreState()
    c.setFillColor(BLACK_COLOR)
    c.setStrokeColor(BLACK_COLOR)


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
        can.setFillColor(BLACK_COLOR)
        can.setFont("NotoSans", 9)
        can.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, 7.5 * mm, f"Trang {i+1} / {total_pages}")
        can.save()

        overlay_buffer.seek(0)
        overlay_page = PdfReader(overlay_buffer).pages[0]
        page.merge_page(overlay_page)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.getvalue()


def split_bullet_lines(text):
    parts = []
    for line in str(text).split("."):
        line = line.strip()
        if line:
            parts.append(line)
    return parts


def make_paragraph_style(name, font_name="NotoSans", font_size=10, leading=13, bold=False, alignment=TA_LEFT, text_color=BLACK_COLOR):
    return ParagraphStyle(
        name=name,
        fontName="NotoSans-Bold" if bold else font_name,
        fontSize=font_size,
        leading=leading,
        textColor=text_color,
        alignment=alignment,
        spaceAfter=0,
        spaceBefore=0,
    )


def draw_header(c):
    c.setFillColor(BLACK_COLOR)
    c.setFont("NotoSans-Bold", 18)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - TOP_MARGIN, "PHIẾU HOÀN THÀNH BÀI HỌC MỸ THUẬT")


def draw_paragraph(c, html_text, x, y_top, width, style):
    para = Paragraph(html_text, style)
    w, h = para.wrap(width, PAGE_HEIGHT)
    para.drawOn(c, x, y_top - h)
    return y_top - h


def draw_dotted_underline_text(
    c,
    x,
    y,
    label,
    value,
    label_font="NotoSans-Bold",
    value_font="NotoSans-Bold",
    label_size=10,
    value_size=10,
    underline_color=RED_COLOR,
    text_color=RED_COLOR
):
    c.setFillColor(BLACK_COLOR)
    c.setFont(label_font, label_size)
    c.drawString(x, y, label)

    label_width = pdfmetrics.stringWidth(label, label_font, label_size)
    value_x = x + label_width + 2

    value = str(value)
    c.setFillColor(text_color)
    c.setFont(value_font, value_size)
    c.drawString(value_x, y, value)

    value_width = pdfmetrics.stringWidth(value, value_font, value_size)

    c.saveState()
    c.setStrokeColor(underline_color)
    c.setDash(1, 2)
    c.setLineWidth(0.8)
    c.line(value_x, y - 2, value_x + value_width, y - 2)
    c.restoreState()

    c.setFillColor(BLACK_COLOR)
    c.setStrokeColor(BLACK_COLOR)


def draw_checkbox_line(c, x, y, label, checked):
    """
    Ve checkbox gon, tick do nam giua o, label do neu duoc tick
    y la baseline text
    """
    size = 4 * mm

    c.saveState()
    c.setStrokeColor(BLACK_COLOR)
    c.setLineWidth(0.8)
    c.rect(x, y - size + 1.2, size, size, stroke=1, fill=0)

    if checked:
        c.setStrokeColor(RED_COLOR)
        c.setLineWidth(1.2)

        x1 = x + 0.9 * mm
        y1 = y - 2.3 * mm
        x2 = x + 1.8 * mm
        y2 = y - 3.4 * mm
        x3 = x + 3.3 * mm
        y3 = y - 0.8 * mm

        c.line(x1, y1, x2, y2)
        c.line(x2, y2, x3, y3)

    c.restoreState()

    c.setFont("NotoSans", 9)
    c.setFillColor(RED_COLOR if checked else BLACK_COLOR)
    c.drawString(x + size + 2, y - 2, label)

    c.setFillColor(BLACK_COLOR)
    c.setStrokeColor(BLACK_COLOR)


def draw_teacher_message_table(c, left_text, right_text, y_top):
    header_style = make_paragraph_style("tbl_header", font_size=10, leading=12, bold=True, text_color=BLACK_COLOR)
    body_style = make_paragraph_style("tbl_body", font_size=10, leading=14, bold=True, text_color=BLACK_COLOR)

    left_lines = split_bullet_lines(left_text)
    right_lines = split_bullet_lines(right_text)

    left_html = "<br/>".join([f"- {line}" for line in left_lines]) if left_lines else ""
    right_html = "<br/>".join([f"- {line}" for line in right_lines]) if right_lines else ""

    data = [
        [
            Paragraph("1. Ưu điểm nổi bật trong bài này:", header_style),
            Paragraph("2. Điểm con cần lưu ý/rèn luyện thêm:", header_style),
        ],
        [
            Paragraph(left_html, body_style),
            Paragraph(right_html, body_style),
        ],
    ]

    table = Table(data, colWidths=[85 * mm, 85 * mm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    w, h = table.wrapOn(c, CONTENT_WIDTH, 120 * mm)
    table.drawOn(c, LEFT_MARGIN, y_top - h)
    return y_top - h


def create_report_pdf_bytes(data: dict) -> bytes:
    ensure_fonts_registered()

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)

    title_style = make_paragraph_style("title_style", font_size=12, leading=15, bold=True, text_color=BLACK_COLOR)
    bullet_style = make_paragraph_style("bullet_style", font_size=10, leading=14, bold=True, text_color=BLACK_COLOR)
    section_style = make_paragraph_style("section_style", font_size=11, leading=14, bold=True, text_color=BLACK_COLOR)

    # ================= PAGE 1 =================
    draw_page_background_and_watermark(c)
    draw_header(c)

    y = PAGE_HEIGHT - 32 * mm

    # Dong hoc vien + ten bai hoc
    draw_dotted_underline_text(
        c, LEFT_MARGIN, y,
        "Học viên: ",
        data.get("ten_hoc_vien", ""),
        label_font="NotoSans-Bold",
        value_font="NotoSans-Bold",
        label_size=12,
        value_size=12
    )

    draw_dotted_underline_text(
        c, LEFT_MARGIN + 82 * mm, y,
        " / Tên bài học: ",
        data.get("ten_bai_hoc", ""),
        label_font="NotoSans-Bold",
        value_font="NotoSans-Bold",
        label_size=12,
        value_size=12
    )
    y -= 12 * mm

    # Dong so buoi + ngay hoan thanh
    draw_dotted_underline_text(
        c, LEFT_MARGIN, y,
        "Số buổi thực hiện: ",
        data.get("so_buoi_thuc_hien", ""),
        label_font="NotoSans-Bold",
        value_font="NotoSans-Bold",
        label_size=12,
        value_size=12
    )

    draw_dotted_underline_text(
        c, LEFT_MARGIN + 62 * mm, y,
        "Ngày hoàn thành: ",
        data.get("ngay_hoan_thanh", ""),
        label_font="NotoSans-Bold",
        value_font="NotoSans-Bold",
        label_size=12,
        value_size=12
    )
    y -= 10 * mm

    y = draw_paragraph(c, "1. MỤC TIÊU BÀI HỌC:", LEFT_MARGIN, y, CONTENT_WIDTH, section_style)
    y -= 5 * mm

    for line in split_bullet_lines(data.get("muc_tieu_bai_hoc", "")):
        y = draw_paragraph(c, f"- {line}", LEFT_MARGIN + 2 * mm, y, CONTENT_WIDTH - 2 * mm, bullet_style)
        y -= 1.5 * mm

    y -= 5 * mm
    y = draw_paragraph(c, "2. ĐÁNH GIÁ HOÀN THIỆN BÀI:", LEFT_MARGIN, y, CONTENT_WIDTH, section_style)
    y -= 7 * mm

    sections = [
        ("Kiến thức nền tảng", FOUNDATION_OPTIONS, data.get("kien_thuc_nen_tang", "")),
        ("Tạo hình và bố cục", COMPOSITION_OPTIONS, data.get("tao_hinh_bo_cuc", "")),
        ("Kiến thức màu sắc", COLOR_OPTIONS, data.get("kien_thuc_mau_sac", "")),
        ("Kỹ thuật", TECHNIQUE_OPTIONS, data.get("ky_thuat", "")),
    ]

    for title, options, selected in sections:
        c.setFillColor(BLACK_COLOR)
        c.setFont("NotoSans-Bold", 10)
        c.drawString(LEFT_MARGIN, y, f"- {title}:")
        y -= 6 * mm

        x = LEFT_MARGIN + 5 * mm
        for opt in options:
            draw_checkbox_line(c, x, y, opt, option_checked(selected, opt))
            x += 38 * mm
        y -= 8 * mm

    y = draw_paragraph(c, "3. CHỈ SỐ SÁNG TẠO VÀ THÁI ĐỘ", LEFT_MARGIN, y, CONTENT_WIDTH, section_style)
    y -= 7 * mm

    sections2 = [
        ("Tư duy giải quyết vấn đề", CREATIVE_OPTIONS, data.get("tu_duy_giai_quyet_van_de", "")),
        ("Sự kiên trì với dự án", ATTITUDE_OPTIONS, data.get("su_kien_tri_voi_du_an", "")),
    ]

    for title, options, selected in sections2:
        c.setFillColor(BLACK_COLOR)
        c.setFont("NotoSans-Bold", 10)
        c.drawString(LEFT_MARGIN, y, f"- {title}:")
        y -= 6 * mm

        x = LEFT_MARGIN + 5 * mm
        for opt in options:
            draw_checkbox_line(c, x, y, opt, option_checked(selected, opt))
            x += 55 * mm
        y -= 8 * mm

    c.showPage()

    # ================= PAGE 2 =================
    draw_page_background_and_watermark(c)
    draw_header(c)

    y = PAGE_HEIGHT - 32 * mm
    y = draw_paragraph(c, "4. LỜI NHẮN TỪ GIÁO VIÊN", LEFT_MARGIN, y, CONTENT_WIDTH, section_style)
    y -= 8 * mm

    y = draw_teacher_message_table(
        c,
        data.get("uu_diem_noi_bat", ""),
        data.get("can_luu_y_them", ""),
        y
    )

    y -= 20 * mm

    c.setFillColor(BLACK_COLOR)
    c.setFont("NotoSans-Bold", 10)
    c.drawRightString(PAGE_WIDTH - 20 * mm, y, "CHỮ KÝ GIÁO VIÊN")

    y -= 8 * mm
    c.setFillColor(RED_COLOR)
    c.setFont("NotoSans-Bold", 12)
    c.drawRightString(PAGE_WIDTH - 20 * mm, y, str(data.get("ten_giao_vien", "")))

    c.save()
    return add_page_numbers(packet)
