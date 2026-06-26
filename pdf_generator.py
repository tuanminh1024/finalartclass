import io
import os
import re

from datetime import datetime
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
GRAY_COLOR = colors.black
SOFT_BROWN = colors.black
LINE_DOT = colors.HexColor("#444444")

PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 10 * mm
RIGHT_MARGIN = 10 * mm

FONTS_REGISTERED = False

FOUNDATION_OPTIONS = [
    "Làm quen",
    "Tiếp thu",
    "Thấu hiểu",
    "Vận dụng",
    "Làm chủ"
]

COMPOSITION_OPTIONS = [
    "Khởi đầu",
    "Định hình",
    "Cân đối",
    "Chặt chẽ",
    "Sáng tạo đột phá"
]

COLOR_OPTIONS = [
    "Nhận biết",
    "Sắc độ",
    "Phối màu",
    "Điêu luyện"
]

TECHNIQUE_OPTIONS = [
    "Thử nghiệm",
    "Linh hoạt",
    "Khéo léo",
    "Tỉ mỉ",
    "Tinh xảo"
]

CREATIVE_OPTIONS = [
    "Chủ động và sáng tạo",
    "Cần gợi ý",
    "Đang rèn luyện"
]

ATTITUDE_OPTIONS = [
    "Tập trung cao",
    "Đôi khi xao nhãng",
    "Cần động viên"
]


# =========================================================
# FONT / WATERMARK
# =========================================================
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
                (PAGE_HEIGHT - wm_size) / 2 + 8 * mm,
                width=wm_size,
                height=wm_size,
                mask='auto',
                preserveAspectRatio=True,
                anchor='c'
            )
            c.restoreState()
        except Exception:
            pass


# =========================================================
# UTILITIES
# =========================================================
def normalize_option_text(s):
    if s is None:
        return ""
    text = str(s).strip().lower()
    text = text.replace("\n", " ")
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


def option_checked(value, option):
    return normalize_option_text(value) == normalize_option_text(option)


def draw_text(c, text, x, y, font="NotoSans", size=10, color=BLACK_COLOR):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawString(x, y, str(text) if text is not None else "")


def draw_centered_text(c, text, x_center, y, font="NotoSans", size=10, color=BLACK_COLOR):
    text = str(text) if text is not None else ""
    c.setFillColor(color)
    c.setFont(font, size)
    width = c.stringWidth(text, font, size)
    c.drawString(x_center - width / 2, y, text)


def draw_right_text(c, text, x_right, y, font="NotoSans", size=10, color=BLACK_COLOR):
    text = str(text) if text is not None else ""
    c.setFillColor(color)
    c.setFont(font, size)
    width = c.stringWidth(text, font, size)
    c.drawString(x_right - width, y, text)


def fit_font_size_single_line(c, text, max_width, font_name="NotoSans", start_size=10, min_size=6):
    text = "" if text is None else str(text)
    size = start_size
    while size >= min_size:
        if c.stringWidth(text, font_name, size) <= max_width:
            return size
        size -= 0.2
    return min_size


def draw_centered_text_fit(c, text, x_center, y, max_width, font="NotoSans", start_size=10, min_size=6, color=BLACK_COLOR):
    final_size = fit_font_size_single_line(c, text, max_width, font, start_size, min_size)
    draw_centered_text(c, text, x_center, y, font=font, size=final_size, color=color)


def draw_dotted_line(c, x1, x2, y, dot_gap=1.35 * mm, dot_radius=0.4, color=LINE_DOT):
    c.setFillColor(color)
    x = x1
    while x < x2:
        c.circle(x, y, dot_radius, stroke=0, fill=1)
        x += dot_gap


def draw_checkbox(c, x, y, size=4.6 * mm, checked=False):
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    c.setFillColor(colors.white)
    c.rect(x, y, size, size, fill=1, stroke=1)

    if checked:
        c.setStrokeColor(RED_COLOR)
        c.setLineWidth(1.7)
        c.line(x + size * 0.18, y + size * 0.45, x + size * 0.40, y + size * 0.22)
        c.line(x + size * 0.40, y + size * 0.22, x + size * 0.82, y + size * 0.76)
        c.setLineWidth(1)


def ensure_space_or_new_page(c, y, needed_height, top_y=PAGE_HEIGHT - 10 * mm, bottom_margin=15 * mm):
    if y - needed_height < bottom_margin:
        c.showPage()
        draw_page_background_and_watermark(c)
        return top_y
    return y


def wrap_text_lines(c, text, max_width, font_name="NotoSans", font_size=9):
    if text is None:
        return []

    paragraphs = str(text).split("\n")
    all_lines = []

    for para in paragraphs:
        para = str(para).strip()
        if not para:
            all_lines.append("")
            continue

        words = para.split()
        current = ""

        for word in words:
            trial = word if not current else current + " " + word
            if c.stringWidth(trial, font_name, font_size) <= max_width:
                current = trial
            else:
                if current:
                    all_lines.append(current)
                current = word

        if current:
            all_lines.append(current)

    return all_lines


def compute_block_height(num_lines, font_size=9, line_spacing=1.5, top_padding=2*mm, bottom_padding=2*mm):
    line_height = font_size * line_spacing
    return top_padding + bottom_padding + num_lines * line_height


def split_sentences_exact_one_dot(text):
    if text is None:
        return []

    text = str(text).strip()
    if not text:
        return []

    parts = re.split(r'(?<!\.)\.(?!\.)', text)
    sentences = [p.strip() for p in parts if str(p).strip()]
    return sentences


def capitalize_first_letter(text):
    text = str(text).strip()
    if not text:
        return ""
    return text[0].upper() + text[1:]


def draw_bullet_paragraph_on_dotted_lines(
    c,
    text,
    x,
    y_top,
    width,
    bullet="-",
    min_lines=4,
    font_name="NotoSans-Bold",
    font_size=10,
    line_spacing=2.2,
    text_color=RED_COLOR,
    dotted_color=LINE_DOT,
    top_padding=2.5 * mm,
    left_padding=0,
    bullet_gap=4.2 * mm,
    dotted_offset=2.0,
    dot_gap=1.25 * mm
):
    sentences = split_sentences_exact_one_dot(text)

    all_lines = []
    bullet_x = x + left_padding
    text_x_first = bullet_x + bullet_gap
    usable_width_first = width - left_padding - bullet_gap

    for sentence in sentences:
        sentence = capitalize_first_letter(sentence)
        wrapped = wrap_text_lines(
            c,
            sentence,
            usable_width_first,
            font_name=font_name,
            font_size=font_size
        )

        if not wrapped:
            continue

        for idx, line in enumerate(wrapped):
            all_lines.append({
                "text": line.strip(),
                "is_first_line": idx == 0
            })

    if len(all_lines) < min_lines:
        for _ in range(min_lines - len(all_lines)):
            all_lines.append({
                "text": "",
                "is_first_line": False
            })

    line_height = font_size * line_spacing
    block_height = top_padding + len(all_lines) * line_height + 2 * mm
    start_baseline = y_top - top_padding - font_size

    for i, item in enumerate(all_lines):
        baseline_y = start_baseline - i * line_height
        line_text = item["text"]
        is_first_line = item["is_first_line"]

        if line_text:
            c.setFont(font_name, font_size)
            c.setFillColor(text_color)

            if is_first_line:
                c.drawString(bullet_x, baseline_y, bullet)

            c.drawString(text_x_first, baseline_y, line_text)

        dotted_y = baseline_y - dotted_offset
        draw_dotted_line(
            c,
            x,
            x + width,
            dotted_y,
            dot_gap=dot_gap,
            color=dotted_color
        )

    return block_height, len(all_lines), line_height


def draw_bullet_lines_in_column(
    c,
    text,
    x,
    y_top,
    width,
    bullet="-",
    min_lines=2,
    font_name="NotoSans-Bold",
    font_size=10,
    line_spacing=2.1,
    text_color=RED_COLOR,
    dotted_color=LINE_DOT,
    top_padding=0,
    left_padding=0,
    bullet_gap=3.5 * mm,
    dotted_offset=1.8,
    dot_gap=1.25 * mm
):
    sentences = split_sentences_exact_one_dot(text)

    all_lines = []
    bullet_x = x + left_padding
    text_x = bullet_x + bullet_gap
    usable_width = width - left_padding - bullet_gap

    for sentence in sentences:
        sentence = capitalize_first_letter(sentence)
        wrapped = wrap_text_lines(
            c,
            sentence,
            usable_width,
            font_name=font_name,
            font_size=font_size
        )

        if not wrapped:
            continue

        for idx, line in enumerate(wrapped):
            all_lines.append({
                "text": line.strip(),
                "is_first_line": idx == 0
            })

    if len(all_lines) < min_lines:
        for _ in range(min_lines - len(all_lines)):
            all_lines.append({
                "text": "",
                "is_first_line": False
            })

    line_height = font_size * line_spacing
    block_height = top_padding + len(all_lines) * line_height + 2 * mm
    start_baseline = y_top - top_padding - font_size

    for i, item in enumerate(all_lines):
        baseline_y = start_baseline - i * line_height
        line_text = item["text"]
        is_first_line = item["is_first_line"]

        if line_text:
            c.setFont(font_name, font_size)
            c.setFillColor(text_color)

            if is_first_line:
                c.drawString(bullet_x, baseline_y, bullet)

            c.drawString(text_x, baseline_y, line_text)

            dotted_y = baseline_y - dotted_offset
            draw_dotted_line(
                c,
                x,
                x + width,
                dotted_y,
                dot_gap=dot_gap,
                color=dotted_color
            )

    return block_height, len(all_lines), line_height


# =========================================================
# PAGE NUMBER
# =========================================================
def add_page_numbers(packet: io.BytesIO) -> bytes:
    packet.seek(0)
    reader = PdfReader(packet)
    writer = PdfWriter()
    total_pages = len(reader.pages)

    for i, page in enumerate(reader.pages):
        page_num_packet = io.BytesIO()
        can = canvas.Canvas(page_num_packet, pagesize=A4)

        txt_trang = "Trang "
        txt_num1 = str(i + 1)
        txt_slash = " / "
        txt_num2 = str(total_pages)

        w_trang = pdfmetrics.stringWidth(txt_trang, "NotoSans", 9)
        w_num1 = pdfmetrics.stringWidth(txt_num1, "NotoSans-Bold", 9)
        w_slash = pdfmetrics.stringWidth(txt_slash, "NotoSans", 9)
        w_num2 = pdfmetrics.stringWidth(txt_num2, "NotoSans-Bold", 9)

        total_width = w_trang + w_num1 + w_slash + w_num2
        x_start = PAGE_WIDTH - RIGHT_MARGIN - total_width
        y_pos = 7.5 * mm

        can.setFont("NotoSans", 9)
        can.setFillColor(BLACK_COLOR)
        can.drawString(x_start, y_pos, txt_trang)
        x_start += w_trang

        can.setFont("NotoSans-Bold", 9)
        can.drawString(x_start, y_pos, txt_num1)
        x_start += w_num1

        can.setFont("NotoSans", 9)
        can.drawString(x_start, y_pos, txt_slash)
        x_start += w_slash

        can.setFont("NotoSans-Bold", 9)
        can.drawString(x_start, y_pos, txt_num2)
        can.save()

        page_num_packet.seek(0)
        page.merge_page(PdfReader(page_num_packet).pages[0])
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.getvalue()


# =========================================================
# MAIN PDF CREATE
# =========================================================
def create_report_pdf_bytes(data: dict) -> bytes:
    ensure_fonts_registered()

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)

    page_w, page_h = A4
    left = 10 * mm
    right = page_w - 10 * mm
    top = page_h - 10 * mm
    bottom_margin = 15 * mm

    draw_page_background_and_watermark(c)

    BODY_FONT = "NotoSans-Bold"
    BODY_COLOR = RED_COLOR
    BODY_FONT_SIZE = 10
    SECTION_TITLE_GAP = 7 * mm
    SECTION_BOTTOM_GAP = 6 * mm

    def draw_header(current_top):
        draw_centered_text(
            c,
            "PHIẾU HOÀN THÀNH BÀI HỌC MỸ THUẬT",
            page_w / 2,
            current_top,
            font="NotoSans-Bold",
            size=20,
            color=BLACK_COLOR
        )

        y = current_top - 11 * mm

        draw_text(c, "Học viên:", left + 6 * mm, y, font="NotoSans", size=10.5, color=BLACK_COLOR)
        draw_dotted_line(c, left + 22 * mm, left + 78 * mm, y - 1.2)

        hv_x1 = left + 22 * mm
        hv_x2 = left + 78 * mm
        draw_centered_text_fit(
            c,
            data.get("ten_hoc_vien", ""),
            (hv_x1 + hv_x2) / 2,
            y,
            max_width=(hv_x2 - hv_x1) - 2 * mm,
            font="NotoSans-Bold",
            start_size=10,
            min_size=6.5,
            color=RED_COLOR
        )

        draw_text(c, "/ Tên bài học:", left + 82 * mm, y, font="NotoSans", size=10.5, color=BLACK_COLOR)
        draw_dotted_line(c, left + 108 * mm, right - 2 * mm, y - 1.2)

        bh_x1 = left + 108 * mm
        bh_x2 = right - 2 * mm
        draw_centered_text_fit(
            c,
            data.get("ten_bai_hoc", ""),
            (bh_x1 + bh_x2) / 2,
            y,
            max_width=(bh_x2 - bh_x1) - 2 * mm,
            font="NotoSans-Bold",
            start_size=10,
            min_size=6.5,
            color=RED_COLOR
        )

        y -= 9 * mm

        draw_text(c, "Số buổi thực hiện:", left + 6 * mm, y, font="NotoSans", size=10.5, color=BLACK_COLOR)
        draw_dotted_line(c, left + 36 * mm, left + 62 * mm, y - 1.2)

        sb_x1 = left + 36 * mm
        sb_x2 = left + 62 * mm
        draw_centered_text_fit(
            c,
            data.get("so_buoi_thuc_hien", ""),
            (sb_x1 + sb_x2) / 2,
            y,
            max_width=(sb_x2 - sb_x1) - 1 * mm,
            font="NotoSans-Bold",
            start_size=10,
            min_size=7,
            color=RED_COLOR
        )

        draw_text(c, "Ngày hoàn thành:", left + 68 * mm, y, font="NotoSans", size=10.5, color=BLACK_COLOR)
        draw_dotted_line(c, left + 98 * mm, left + 142 * mm, y - 1.2)

        ngay_x1 = left + 98 * mm
        ngay_x2 = left + 142 * mm
        draw_centered_text_fit(
            c,
            data.get("ngay_hoan_thanh", ""),
            (ngay_x1 + ngay_x2) / 2,
            y,
            max_width=(ngay_x2 - ngay_x1) - 1 * mm,
            font="NotoSans-Bold",
            start_size=10,
            min_size=7,
            color=RED_COLOR
        )

        return y - 14 * mm

    def draw_continuation_header(current_top):
        draw_centered_text(
            c,
            "PHIẾU HOÀN THÀNH BÀI HỌC MỸ THUẬT",
            page_w / 2,
            current_top,
            font="NotoSans-Bold",
            size=13,
            color=BLACK_COLOR
        )
        return current_top - 12 * mm

    def draw_objective_section(y):
        y = ensure_space_or_new_page(c, y, 40 * mm, top, bottom_margin)
        if y == top:
            y = draw_continuation_header(top)

        draw_text(
            c,
            "1. MỤC TIÊU BÀI HỌC:",
            left + 2 * mm,
            y,
            font="NotoSans-Bold",
            size=11,
            color=BLACK_COLOR
        )

        y -= SECTION_TITLE_GAP

        muc_tieu = str(data.get("muc_tieu_bai_hoc", "")).strip()
        objective_width = right - left - 8 * mm

        sentences = split_sentences_exact_one_dot(muc_tieu)
        estimated_lines = 0
        for sentence in sentences:
            sentence = capitalize_first_letter(sentence)
            wrapped = wrap_text_lines(
                c,
                sentence,
                objective_width - 4.2 * mm,
                font_name="NotoSans-Bold",
                font_size=10
            )
            estimated_lines += max(1, len(wrapped))

        num_obj_lines = max(4, estimated_lines)

        muc_tieu_h = compute_block_height(
            num_obj_lines,
            font_size=10,
            line_spacing=2.2,
            top_padding=2.5 * mm,
            bottom_padding=2.5 * mm
        )

        y = ensure_space_or_new_page(c, y, muc_tieu_h + 8 * mm, top, bottom_margin)
        if y == top:
            y = draw_continuation_header(top)

        draw_bullet_paragraph_on_dotted_lines(
            c,
            muc_tieu,
            x=left + 3 * mm,
            y_top=y,
            width=objective_width,
            bullet="-",
            min_lines=4,
            font_name="NotoSans-Bold",
            font_size=10,
            line_spacing=2.2,
            text_color=RED_COLOR,
            dotted_color=LINE_DOT,
            top_padding=2.5 * mm,
            left_padding=0,
            bullet_gap=4.2 * mm,
            dotted_offset=2.0,
            dot_gap=1.25 * mm
        )

        return y - (muc_tieu_h + SECTION_BOTTOM_GAP)

    def draw_horizontal_checklist_row(y, title, selected_value, options, row_height=16*mm):
        y = ensure_space_or_new_page(c, y, row_height + 3 * mm, top, bottom_margin)
        if y == top:
            y = draw_continuation_header(top)

        title_y = y - 3.5 * mm
        draw_text(c, title, left + 2 * mm, title_y, font="NotoSans-Bold", size=9.8, color=BLACK_COLOR)

        start_x = left + 50 * mm
        available_w = right - start_x - 2 * mm
        cell_w = available_w / len(options)

        box_size = 4.8 * mm
        option_text_y = title_y
        box_y = option_text_y - 1.2 * mm

        for i, opt in enumerate(options):
            cell_x = start_x + i * cell_w
            checked = option_checked(selected_value, opt)
            draw_checkbox(c, cell_x, box_y, size=box_size, checked=checked)
            draw_text(
                c,
                opt,
                cell_x + 6.5 * mm,
                option_text_y,
                font=BODY_FONT if checked else "NotoSans",
                size=9,
                color=BODY_COLOR if checked else BLACK_COLOR
            )

        return y - row_height

    def draw_assessment_section(y):
        y = ensure_space_or_new_page(c, y, 78 * mm, top, bottom_margin)
        if y == top:
            y = draw_continuation_header(top)

        draw_text(c, "2. ĐÁNH GIÁ HOÀN THIỆN BÀI:", left + 2 * mm, y, font="NotoSans-Bold", size=11, color=BLACK_COLOR)
        y -= SECTION_TITLE_GAP

        y = draw_horizontal_checklist_row(y, "1. Kiến thức nền tảng:", data.get("kien_thuc_nen_tang", ""), FOUNDATION_OPTIONS, row_height=15 * mm)
        y = draw_horizontal_checklist_row(y, "2. Tạo hình và Bố cục:", data.get("tao_hinh_bo_cuc", ""), COMPOSITION_OPTIONS, row_height=15 * mm)
        y = draw_horizontal_checklist_row(y, "3. Kiến thức Màu sắc:", data.get("kien_thuc_mau_sac", ""), COLOR_OPTIONS, row_height=15 * mm)
        y = draw_horizontal_checklist_row(y, "4. Kĩ thuật:", data.get("ky_thuat", ""), TECHNIQUE_OPTIONS, row_height=15 * mm)

        return y - SECTION_BOTTOM_GAP

    def draw_creativity_section(y):
        y = ensure_space_or_new_page(c, y, 45 * mm, top, bottom_margin)
        if y == top:
            y = draw_continuation_header(top)

        draw_text(c, "3. CHỈ SỐ SÁNG TẠO VÀ THÁI ĐỘ", left + 2 * mm, y, font="NotoSans-Bold", size=11, color=BLACK_COLOR)
        y -= SECTION_TITLE_GAP

        y = draw_horizontal_checklist_row(
            y,
            "Tư duy giải quyết vấn đề:",
            data.get("tu_duy_giai_quyet_van_de", ""),
            CREATIVE_OPTIONS,
            row_height=14 * mm
        )
        y = draw_horizontal_checklist_row(
            y,
            "Sự kiên trì với dự án:",
            data.get("su_kien_tri_voi_du_an", ""),
            ATTITUDE_OPTIONS,
            row_height=14 * mm
        )

        return y - SECTION_BOTTOM_GAP

    def draw_teacher_message_section(y):
        uu_diem = str(data.get("uu_diem_noi_bat", "")).strip()
        can_luu_y = str(data.get("can_luu_y_them", "")).strip()
        ten_giao_vien = str(data.get("ten_giao_vien", "")).strip()

        table_w = right - left
        col1_w = table_w / 2
        col2_w = table_w / 2
        cell_pad = 2.5 * mm

        cell_font_name = "NotoSans-Bold"
        cell_font_size = 10
        header_h = 8 * mm
        min_content_lines = 2
        extra_bottom_padding = 4 * mm

        lines1_count = 0
        for sentence in split_sentences_exact_one_dot(uu_diem):
            sentence = capitalize_first_letter(sentence)
            wrapped = wrap_text_lines(
                c,
                sentence,
                col1_w - 2 * cell_pad - 3.8 * mm,
                font_name=cell_font_name,
                font_size=cell_font_size
            )
            lines1_count += max(1, len(wrapped))

        lines2_count = 0
        for sentence in split_sentences_exact_one_dot(can_luu_y):
            sentence = capitalize_first_letter(sentence)
            wrapped = wrap_text_lines(
                c,
                sentence,
                col2_w - 2 * cell_pad - 3.8 * mm,
                font_name=cell_font_name,
                font_size=cell_font_size
            )
            lines2_count += max(1, len(wrapped))

        num_content_lines = max(lines1_count, lines2_count, min_content_lines)
        cell_line_height = cell_font_size * 2.0
        content_h = num_content_lines * cell_line_height + extra_bottom_padding
        total_h = header_h + content_h

        needed_height = 16 * mm + total_h + 18 * mm
        y = ensure_space_or_new_page(c, y, needed_height, top, bottom_margin)
        if y == top:
            y = draw_continuation_header(top)

        draw_text(
            c,
            "4. LỜI NHẮN TỪ GIÁO VIÊN",
            left + 2 * mm,
            y,
            font="NotoSans-Bold",
            size=12,
            color=BLACK_COLOR
        )
        y -= 9 * mm

        box_top = y
        box_bottom = box_top - total_h

        c.setStrokeColor(BLACK_COLOR)
        c.setLineWidth(0.8)

        c.rect(left, box_bottom, table_w, total_h, stroke=1, fill=0)
        c.line(left, box_top - header_h, left + table_w, box_top - header_h)
        c.line(left + col1_w, box_top, left + col1_w, box_bottom)

        draw_text(
            c,
            "1. Ưu điểm nổi bật trong bài này:",
            left + cell_pad,
            box_top - 5.2 * mm,
            font="NotoSans-Bold",
            size=9.5,
            color=BLACK_COLOR
        )
        draw_text(
            c,
            "2. Điểm con cần lưu ý/rèn luyện thêm:",
            left + col1_w + cell_pad,
            box_top - 5.2 * mm,
            font="NotoSans-Bold",
            size=9.5,
            color=BLACK_COLOR
        )

        content_top = box_top - header_h

        draw_bullet_lines_in_column(
            c,
            uu_diem,
            x=left + cell_pad,
            y_top=content_top - 1.5 * mm,
            width=col1_w - 2 * cell_pad,
            bullet="-",
            min_lines=min_content_lines,
            font_name=cell_font_name,
            font_size=cell_font_size,
            line_spacing=2.0,
            text_color=RED_COLOR,
            dotted_color=LINE_DOT,
            top_padding=0,
            left_padding=0,
            bullet_gap=3.8 * mm,
            dotted_offset=1.8,
            dot_gap=1.25 * mm
        )

        draw_bullet_lines_in_column(
            c,
            can_luu_y,
            x=left + col1_w + cell_pad,
            y_top=content_top - 1.5 * mm,
            width=col2_w - 2 * cell_pad,
            bullet="-",
            min_lines=min_content_lines,
            font_name=cell_font_name,
            font_size=cell_font_size,
            line_spacing=2.0,
            text_color=RED_COLOR,
            dotted_color=LINE_DOT,
            top_padding=0,
            left_padding=0,
            bullet_gap=3.8 * mm,
            dotted_offset=1.8,
            dot_gap=1.25 * mm
        )

        y = box_bottom - 10 * mm

        y = ensure_space_or_new_page(c, y, 18 * mm, top, bottom_margin)
        if y == top:
            y = draw_continuation_header(top)

        title_text = "CHỮ KÝ GIÁO VIÊN"
        title_width = pdfmetrics.stringWidth(title_text, "NotoSans-Bold", 10)
        x_center = (right - 2 * mm) - (title_width / 2)

        c.setFont("NotoSans-Bold", 10)
        c.setFillColor(BLACK_COLOR)
        c.drawCentredString(x_center, y, title_text)

        y -= 8 * mm

        c.setFont("NotoSans-Bold", 12)
        c.setFillColor(RED_COLOR)
        c.drawCentredString(x_center, y, ten_giao_vien)

        y -= 10 * mm
        return y

    y = draw_header(top)
    y = draw_objective_section(y)
    y = draw_assessment_section(y)
    y = draw_creativity_section(y)
    y = draw_teacher_message_section(y)

    c.save()
    return add_page_numbers(packet)
