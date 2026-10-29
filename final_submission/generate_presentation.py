"""Generate the complete 17-slide PPTX presentation for CSD203 Group 4 Report."""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

ROOT = Path(__file__).resolve().parents[1]
FINAL_DIR = ROOT / "final_submission"
FIGS_DIR = FINAL_DIR / "figures"
OUTPUT_PPTX = FINAL_DIR / "CSD203_DA4_Presentation.pptx"

# Color Palette
NAVY_950 = RGBColor(10, 15, 30)      # #0A0F1E
NAVY_900 = RGBColor(15, 23, 42)      # #0F172A
SLATE_800 = RGBColor(30, 41, 59)     # #1E293B
SLATE_700 = RGBColor(51, 65, 85)     # #334155
SLATE_600 = RGBColor(71, 85, 105)    # #475569
SLATE_500 = RGBColor(100, 116, 139)  # #64748B
SLATE_400 = RGBColor(148, 163, 184)  # #94A3B8
SLATE_300 = RGBColor(203, 213, 225)  # #CBD5E1
SLATE_200 = RGBColor(226, 232, 240)  # #E2E8F0
SLATE_100 = RGBColor(241, 245, 249)  # #F1F5F9
SLATE_50  = RGBColor(248, 250, 252)  # #F8FAFC
WHITE     = RGBColor(255, 255, 255)  # #FFFFFF

BLUE_700  = RGBColor(29, 78, 216)    # #1D4ED8
BLUE_600  = RGBColor(37, 99, 235)    # #2563EB
BLUE_500  = RGBColor(59, 130, 246)   # #3B82F6
BLUE_100  = RGBColor(219, 234, 254)  # #DBEAFE
BLUE_50   = RGBColor(239, 246, 255)  # #EFF6FF

EMERALD_700 = RGBColor(4, 120, 87)   # #047857
EMERALD_600 = RGBColor(5, 150, 105)  # #059669
EMERALD_500 = RGBColor(16, 185, 129) # #10B981
EMERALD_50  = RGBColor(236, 253, 245) # #ECFDF5

AMBER_600   = RGBColor(217, 119, 6)  # #D97706
AMBER_500   = RGBColor(245, 158, 11) # #F59E0B
AMBER_50    = RGBColor(254, 243, 199) # #FEF3C7

ROSE_600    = RGBColor(225, 29, 72)  # #E11D48
ROSE_500    = RGBColor(244, 63, 94)  # #F43F5E
ROSE_50     = RGBColor(255, 241, 242) # #FFF1F2

INDIGO_600  = RGBColor(79, 70, 229)  # #4F46E5
INDIGO_50   = RGBColor(238, 242, 255) # #EEF2FF
CYAN_600    = RGBColor(8, 145, 178)  # #0891B2
CYAN_50     = RGBColor(236, 254, 255) # #ECFEFF

FONT_HEADING = "Segoe UI"
FONT_BODY = "Segoe UI"


def add_bg(slide, color=SLATE_50):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background()
    return bg


def add_header(slide, category_text, title_text, subtitle_text=None, cat_bg=BLUE_600, cat_fg=WHITE):
    pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.40), Inches(2.3), Inches(0.28))
    pill.fill.solid()
    pill.fill.fore_color.rgb = cat_bg
    pill.line.fill.background()
    tf_pill = pill.text_frame
    tf_pill.word_wrap = False
    tf_pill.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_pill.margin_left = tf_pill.margin_top = tf_pill.margin_right = tf_pill.margin_bottom = 0
    p_pill = tf_pill.paragraphs[0]
    p_pill.text = category_text.upper()
    p_pill.alignment = PP_ALIGN.CENTER
    p_pill.font.name = FONT_HEADING
    p_pill.font.size = Pt(8.5)
    p_pill.font.bold = True
    p_pill.font.color.rgb = cat_fg

    txbox = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.733), Inches(0.65))
    tf = txbox.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.name = FONT_HEADING
    p.font.size = Pt(19)
    p.font.bold = True
    p.font.color.rgb = NAVY_900

    if subtitle_text:
        p2 = tf.add_paragraph()
        p2.text = subtitle_text
        p2.font.name = FONT_BODY
        p2.font.size = Pt(10)
        p2.font.color.rgb = SLATE_500
        p2.space_before = Pt(2)

    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.42), Inches(11.733), Inches(0.015))
    line.fill.solid()
    line.fill.fore_color.rgb = SLATE_200
    line.line.fill.background()


def add_footer(slide, current_slide, total_slides=17):
    txbox = slide.shapes.add_textbox(Inches(0.8), Inches(7.08), Inches(8.5), Inches(0.25))
    tf = txbox.text_frame
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = "CSD203 — Data Structures and Algorithms with Python · Đề tài 4: Nén Dữ Liệu & BPE Tokenizer · Nhóm 4 — AI21B"
    p.font.name = FONT_BODY
    p.font.size = Pt(8)
    p.font.color.rgb = SLATE_400

    txbox2 = slide.shapes.add_textbox(Inches(11.0), Inches(7.08), Inches(1.533), Inches(0.25))
    tf2 = txbox2.text_frame
    tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = 0
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.RIGHT
    p2.text = f"{current_slide} / {total_slides}"
    p2.font.name = FONT_BODY
    p2.font.size = Pt(8.5)
    p2.font.bold = True
    p2.font.color.rgb = SLATE_500


def add_card(slide, left, top, width, height, bg_color=WHITE, border_color=SLATE_200, rounded=True):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    card = slide.shapes.add_shape(shape_type, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
    else:
        card.line.fill.background()
    return card


def add_metric_callout(slide, left, top, width, height, value_text, label_text, subtext=None, val_color=BLUE_600, bg_color=WHITE, border_color=SLATE_200):
    add_card(slide, left, top, width, height, bg_color=bg_color, border_color=border_color, rounded=True)
    txbox = slide.shapes.add_textbox(left + Inches(0.18), top + Inches(0.12), width - Inches(0.36), height - Inches(0.24))
    tf = txbox.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_val = tf.paragraphs[0]
    p_val.text = value_text
    p_val.font.name = FONT_HEADING
    p_val.font.size = Pt(21)
    p_val.font.bold = True
    p_val.font.color.rgb = val_color

    p_lbl = tf.add_paragraph()
    p_lbl.text = label_text
    p_lbl.font.name = FONT_HEADING
    p_lbl.font.size = Pt(10)
    p_lbl.font.bold = True
    p_lbl.font.color.rgb = NAVY_900
    p_lbl.space_before = Pt(2)

    if subtext:
        p_sub = tf.add_paragraph()
        p_sub.text = subtext
        p_sub.font.name = FONT_BODY
        p_sub.font.size = Pt(8.2)
        p_sub.font.color.rgb = SLATE_500
        p_sub.space_before = Pt(2)


def add_table_custom(slide, left, top, width, height, headers, rows, col_widths=None, highlight_idx=-1):
    num_rows = len(rows) + 1
    num_cols = len(headers)
    table_shape = slide.shapes.add_table(num_rows, num_cols, left, top, width, height)
    table = table_shape.table

    if col_widths and len(col_widths) == num_cols:
        for idx, w in enumerate(col_widths):
            table.columns[idx].width = w

    for c_idx, h in enumerate(headers):
        cell = table.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = SLATE_800
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = Inches(0.08)
        cell.margin_right = Inches(0.08)
        cell.margin_top = Inches(0.04)
        cell.margin_bottom = Inches(0.04)
        p = cell.text_frame.paragraphs[0]
        p.text = str(h)
        p.font.name = FONT_HEADING
        p.font.size = Pt(8.5)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT

    for r_idx, row in enumerate(rows):
        is_hl = (r_idx == highlight_idx)
        bg = BLUE_50 if is_hl else (SLATE_100 if r_idx % 2 == 1 else WHITE)
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx + 1, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)
            p = cell.text_frame.paragraphs[0]
            p.text = str(val)
            p.font.name = FONT_BODY
            p.font.size = Pt(8.2)
            p.font.bold = is_hl or (c_idx == 0)
            p.font.color.rgb = BLUE_700 if is_hl else NAVY_900
            p.alignment = PP_ALIGN.RIGHT if (c_idx > 0 and any(char.isdigit() for char in str(val))) else PP_ALIGN.LEFT

    return table_shape


# Build Presentation
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

# ==========================================================
# SLIDE 1: Title Slide (Dark Elegant Academic Theme)
# ==========================================================
s1 = prs.slides.add_slide(blank_layout)
add_bg(s1, NAVY_900)

# Top badge
badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.9), Inches(0.8), Inches(4.5), Inches(0.35))
badge.fill.solid()
badge.fill.fore_color.rgb = BLUE_600
badge.line.fill.background()
tf_badge = badge.text_frame
tf_badge.word_wrap = False
tf_badge.vertical_anchor = MSO_ANCHOR.MIDDLE
p_b = tf_badge.paragraphs[0]
p_b.text = "HỌC PHẦN CSD203 — DATA STRUCTURES & ALGORITHMS"
p_b.font.name = FONT_HEADING
p_b.font.size = Pt(9)
p_b.font.bold = True
p_b.font.color.rgb = WHITE
p_b.alignment = PP_ALIGN.CENTER

# Main Title Box
tx_title = s1.shapes.add_textbox(Inches(0.9), Inches(1.35), Inches(11.5), Inches(1.8))
tf_title = tx_title.text_frame
tf_title.word_wrap = True
tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0

p_t1 = tf_title.paragraphs[0]
p_t1.text = "Khảo sát thực nghiệm các thuật toán nén không mất mát"
p_t1.font.name = FONT_HEADING
p_t1.font.size = Pt(25)
p_t1.font.bold = True
p_t1.font.color.rgb = WHITE

p_t2 = tf_title.add_paragraph()
p_t2.text = "và tokenizer Byte Pair Encoding của mô hình ngôn ngữ lớn"
p_t2.font.name = FONT_HEADING
p_t2.font.size = Pt(25)
p_t2.font.bold = True
p_t2.font.color.rgb = BLUE_500
p_t2.space_before = Pt(3)

p_sub = tf_title.add_paragraph()
p_sub.text = "Empirical Evaluation of Lossless Compression (RLE, Huffman, LZW) and Byte-level BPE Tokenizer for LLMs"
p_sub.font.name = FONT_BODY
p_sub.font.size = Pt(11.5)
p_sub.font.color.rgb = SLATE_400
p_sub.space_before = Pt(8)

# Team Card Container
team_card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.9), Inches(3.6), Inches(11.533), Inches(3.1))
team_card.fill.solid()
team_card.fill.fore_color.rgb = SLATE_800
team_card.line.color.rgb = SLATE_700
team_card.line.width = Pt(1)

# Team Header inside card
tx_th = s1.shapes.add_textbox(Inches(1.2), Inches(3.8), Inches(11.0), Inches(0.4))
tf_th = tx_th.text_frame
tf_th.margin_left = tf_th.margin_top = tf_th.margin_right = tf_th.margin_bottom = 0
p_th = tf_th.paragraphs[0]
p_th.text = "NHÓM 4 — LỚP AI21B · HỌC KỲ FA26 · ĐỀ TÀI 4"
p_th.font.name = FONT_HEADING
p_th.font.size = Pt(12)
p_th.font.bold = True
p_th.font.color.rgb = CYAN_600

# Members Grid (2 columns, 3 rows)
members = [
    ("Trần Châu Hoàng Nam", "QE210145", "Trưởng nhóm · Kiến trúc & Pipeline BPE"),
    ("Nguyễn Trí Viễn", "QE210041", "Nghiên cứu RQ1 & Thực nghiệm Codec"),
    ("Phạm Minh Tiến", "QE210079", "Nghiên cứu RQ2 & Phân tích Hoán vị"),
    ("Hoàng Đức Khánh", "SE180114", "Nghiên cứu RQ3 & Tối ưu thuật toán Heap"),
    ("Trương Đình Tân", "QE210065", "Kiểm thử hệ thống & Hardening Decoder"),
    ("Dương Quốc Thịnh", "QE210121", "Trực quan hóa dữ liệu & Soạn thảo báo cáo")
]

for idx, (name, m_id, role) in enumerate(members):
    col = idx % 2
    row = idx // 2
    c_left = Inches(1.2 + col * 5.6)
    c_top = Inches(4.3 + row * 0.72)
    
    # Member pill box
    m_box = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left, c_top, Inches(5.3), Inches(0.62))
    m_box.fill.solid()
    m_box.fill.fore_color.rgb = NAVY_900
    m_box.line.color.rgb = SLATE_700
    m_box.line.width = Pt(0.75)
    
    tf_m = m_box.text_frame
    tf_m.word_wrap = True
    tf_m.margin_left = Inches(0.18)
    tf_m.margin_right = Inches(0.18)
    tf_m.margin_top = Inches(0.08)
    tf_m.margin_bottom = Inches(0.08)
    
    p_m1 = tf_m.paragraphs[0]
    p_m1.text = f"{name}  "
    p_m1.font.name = FONT_HEADING
    p_m1.font.size = Pt(10)
    p_m1.font.bold = True
    p_m1.font.color.rgb = WHITE
    
    r_id = p_m1.add_run()
    r_id.text = f"[{m_id}]"
    r_id.font.name = FONT_HEADING
    r_id.font.size = Pt(9)
    r_id.font.bold = False
    r_id.font.color.rgb = BLUE_500
    
    p_m2 = tf_m.add_paragraph()
    p_m2.text = role
    p_m2.font.name = FONT_BODY
    p_m2.font.size = Pt(8)
    p_m2.font.color.rgb = SLATE_400


# ==========================================================
# SLIDE 2: Agenda & Highlights
# ==========================================================
s2 = prs.slides.add_slide(blank_layout)
add_bg(s2)
add_header(s2, "TỔNG QUAN", "Lộ trình báo cáo & 3 Điểm nhấn định lượng cốt lõi", "Khảo sát thực nghiệm nén dữ liệu & Tokenizer BPE trên văn bản Tiếng Việt - Tiếng Anh")
add_footer(s2, 2)

# Left Column: 6 Agenda Cards
agenda_items = [
    ("1", "Bối cảnh & 3 Câu hỏi Nghiên cứu", "Tách bạch Codec độc lập vs Tokenizer chia sẻ từ điển"),
    ("2", "Nguyên lý Thuật toán & Chuẩn hóa Thực nghiệm", "Đặc tả container tự giải mã, cấu trúc dữ liệu & manifest"),
    ("3", "RQ1: Họ dữ liệu & Quy mô nén", "Khảo sát RLE, Huffman, LZW từ 256 KiB đến 4096 KiB"),
    ("4", "RQ2: Hoán vị byte & Entropy bậc 0", "Hiện tượng bất biến Huffman và nghịch lý đóng băng LZW"),
    ("5", "RQ3: BPE Tokenizer, Đa ngữ & Tối ưu Heap", "Ma trận Việt–Anh 2x2, lạm phát token và tăng tốc 104x"),
    ("6", "Kiểm thử 761 Tests, Giới hạn & Đóng góp", "Hardening decoder, toàn vẹn SHA-256 và tính trung thực")
]

for idx, (num, title, desc) in enumerate(agenda_items):
    c_top = Inches(1.6 + idx * 0.85)
    card = add_card(s2, Inches(0.8), c_top, Inches(6.8), Inches(0.75), bg_color=WHITE, border_color=SLATE_200)
    
    # Number circle
    num_box = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.95), c_top + Inches(0.12), Inches(0.48), Inches(0.48))
    num_box.fill.solid()
    num_box.fill.fore_color.rgb = BLUE_600
    num_box.line.fill.background()
    tf_num = num_box.text_frame
    tf_num.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_num.margin_left = tf_num.margin_right = tf_num.margin_top = tf_num.margin_bottom = 0
    p_n = tf_num.paragraphs[0]
    p_n.text = num
    p_n.font.name = FONT_HEADING
    p_n.font.size = Pt(12)
    p_n.font.bold = True
    p_n.font.color.rgb = WHITE
    p_n.alignment = PP_ALIGN.CENTER
    
    # Text box
    txbox = s2.shapes.add_textbox(Inches(1.55), c_top + Inches(0.08), Inches(5.8), Inches(0.58))
    tf = txbox.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p1 = tf.paragraphs[0]
    p1.text = title
    p1.font.name = FONT_HEADING
    p1.font.size = Pt(10.5)
    p1.font.bold = True
    p1.font.color.rgb = NAVY_900
    
    p2 = tf.add_paragraph()
    p2.text = desc
    p2.font.name = FONT_BODY
    p2.font.size = Pt(8.5)
    p2.font.color.rgb = SLATE_500
    p2.space_before = Pt(1)

# Right Column: 3 High-Impact Result Metric Cards
add_metric_callout(s2, Inches(8.0), Inches(1.6), Inches(4.533), Inches(1.55),
                   "32.6% & 13.7%", "BPE Vượt Trội LZW ở K=3840",
                   "Tại ngân sách K cao, BPE huấn luyện cùng ngôn ngữ tạo container nhỏ hơn LZW 32.6% trên Wikipedia Tiếng Việt và 13.7% trên Tiếng Anh (đã tính đủ overhead bảng merge).",
                   val_color=EMERALD_600, bg_color=WHITE)

add_metric_callout(s2, Inches(8.0), Inches(3.35), Inches(4.533), Inches(1.55),
                   "3.54× Lạm Phát Token", "Thách Thức Tokenizer Xuyên Ngữ",
                   "Trên cùng văn bản Tiếng Việt V1, tokenizer học từ Tiếng Anh (E1) sinh ra 795,855 tokens, gấp 3.54 lần tokenizer học từ Tiếng Việt (224,618 tokens) do vỡ vụn ký tự UTF-8.",
                   val_color=ROSE_600, bg_color=WHITE)

add_metric_callout(s2, Inches(8.0), Inches(5.1), Inches(4.533), Inches(1.55),
                   "104.72× Speedup", "Tối Ưu Huấn Luyện BPE với Heap",
                   "Cấu trúc Incremental Heap kết hợp Lazy Deletion giảm thời gian train BPE trên V1 full 1 MiB từ 78.3 giây (Naive) xuống chỉ còn 0.75 giây (Inc) mà vẫn giữ nguyên 100% thứ tự merge.",
                   val_color=BLUE_600, bg_color=WHITE)


# ==========================================================
# SLIDE 3: Motivation & Research Questions
# ==========================================================
s3 = prs.slides.add_slide(blank_layout)
add_bg(s3)
add_header(s3, "BỐI CẢNH & MỤC TIÊU", "Bối cảnh nghiên cứu & 3 Câu hỏi Thực nghiệm (RQ1 - RQ3)", "Giao thoa giữa Nén dữ liệu truyền thống và Tiền xử lý văn bản cho Mô hình Ngôn ngữ lớn (LLM)")
add_footer(s3, 3)

# Top Context Banner
banner = add_card(s3, Inches(0.8), Inches(1.6), Inches(11.733), Inches(1.15), bg_color=INDIGO_50, border_color=INDIGO_600)
tx_b = s3.shapes.add_textbox(Inches(1.05), Inches(1.72), Inches(11.2), Inches(0.9))
tf_b = tx_b.text_frame
tf_b.word_wrap = True
tf_b.margin_left = tf_b.margin_right = tf_b.margin_top = tf_b.margin_bottom = 0
pb1 = tf_b.paragraphs[0]
pb1.text = "Sự chuyển dịch từ Nén Không Mất Mát sang Tokenizer Subword trong LLM:"
pb1.font.name = FONT_HEADING
pb1.font.size = Pt(11)
pb1.font.bold = True
pb1.font.color.rgb = INDIGO_600

pb2 = tf_b.add_paragraph()
pb2.text = "• Nén không mất mát (RLE, Huffman, LZW) tập trung vào tỷ lệ nén tối đa của một tệp độc lập, mang theo toàn bộ siêu dữ liệu giải mã.\n• Tokenizer BPE (GPT-2/3, LLaMA) là codec subword chia sẻ từ điển: bên nén và giải nén thỏa thuận trước bảng merge, tối ưu hóa số lượng token và mở rộng vốn từ vựng mở."
pb2.font.name = FONT_BODY
pb2.font.size = Pt(9)
pb2.font.color.rgb = SLATE_700
pb2.space_before = Pt(3)

# 3 Column Cards for RQ1, RQ2, RQ3
rq_cards = [
    ("RQ1", "Họ dữ liệu & Quy mô nén", BLUE_600, BLUE_50, [
        "Khảo sát hiệu quả của RLE, Huffman chính tắc và LZW 12-bit.",
        "Quy mô từ 256 KiB đến 4096 KiB trên 4 họ dữ liệu:",
        "— C1: Run dài hình học (geometric runs, mean 32B).",
        "— C2: Từ vựng lặp theo phân bố Zipf (s=1, 1000 từ).",
        "— C3: Byte ngẫu nhiên phân bố đều (cực đại entropy).",
        "— V1: Wikipedia tiếng Việt thực tế.",
        "Đánh giá: Tỷ lệ nén, thông lượng (KiB/s) và đỉnh RAM."
    ]),
    ("RQ2", "Hoán vị byte & Entropy bậc 0", AMBER_600, AMBER_50, [
        "Kiểm chứng tác động của thứ tự byte khi giữ nguyên histogram.",
        "Dữ liệu: Canterbury (alice29, kennedy) & Wiki V1.",
        "3 Trạng thái hoán vị:",
        "— Original: Thứ tự văn bản tự nhiên ban đầu.",
        "— Runs: Counting sort theo byte để gom run tối đa.",
        "— Shuffled: Xáo trộn ngẫu nhiên Fisher–Yates (3 seeds).",
        "Khảo sát tính bất biến của Huffman và hiện tượng bão hòa/đóng băng từ điển của LZW."
    ]),
    ("RQ3", "BPE: Codec, Tokenizer & Heap", EMERALD_600, EMRALD_50 if 'EMRALD_50' in locals() else EMERALD_50, [
        "So sánh BPE với LZW ở cả hai vai trò: Codec tự chứa và Tokenizer chỉ payload.",
        "Thử thách xuyên ngữ (Cross-lingual): Đánh giá ma trận 2x2 Train V1/E1 → Test V1/E1.",
        "Tối ưu thuật toán huấn luyện BPE:",
        "— Naive: Quét lại toàn bộ đoạn duy nhất mỗi vòng.",
        "— No-heap: Cập nhật cục bộ qua linked-list & inverted index.",
        "— Incremental Heap: Lazy deletion, đạt speedup >100x."
    ])
]

for idx, (rq_id, rq_title, color, bg_c, bullets) in enumerate(rq_cards):
    c_left = Inches(0.8 + idx * 4.0)
    card = add_card(s3, c_left, Inches(2.95), Inches(3.733), Inches(3.9), bg_color=WHITE, border_color=SLATE_200)
    
    # Top header bar
    top_bar = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left + Inches(0.18), Inches(3.1), Inches(3.373), Inches(0.48))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = color
    top_bar.line.fill.background()
    tf_tb = top_bar.text_frame
    tf_tb.word_wrap = True
    tf_tb.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_rq = tf_tb.paragraphs[0]
    p_rq.text = f"{rq_id}: {rq_title}"
    p_rq.font.name = FONT_HEADING
    p_rq.font.size = Pt(10)
    p_rq.font.bold = True
    p_rq.font.color.rgb = WHITE
    p_rq.alignment = PP_ALIGN.CENTER
    
    # Bullet texts
    txbox = s3.shapes.add_textbox(c_left + Inches(0.18), Inches(3.68), Inches(3.373), Inches(3.05))
    tf = txbox.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for b_idx, bullet in enumerate(bullets):
        p = tf.paragraphs[0] if b_idx == 0 else tf.add_paragraph()
        p.text = bullet
        p.font.name = FONT_BODY
        p.font.size = Pt(8.5)
        p.font.color.rgb = NAVY_900 if bullet.startswith("—") or bullet.startswith("Khảo sát") else SLATE_600
        p.space_before = Pt(3)


# ==========================================================
# SLIDE 4: Algorithmic Principles & Redundancy
# ==========================================================
s4 = prs.slides.add_slide(blank_layout)
add_bg(s4)
add_header(s4, "CƠ SỞ LÝ THUYẾT", "Nguyên lý 4 Thuật toán & Bản chất Dạng Dư thừa Khai thác", "So sánh RLE, Huffman Chính tắc, LZW 12-bit và Tokenizer Byte Pair Encoding (BPE)")
add_footer(s4, 4)

algos = [
    ("RLE", "Run-Length Encoding", "Dư thừa lặp liên tiếp", BLUE_600, [
        "Nguyên lý: Gom các byte giống nhau xuất hiện liên tiếp thành cặp (count, byte).",
        "Quy cách cài đặt: count từ 1 đến 255 (1 byte); run dài hơn 255 được chia nhỏ thành nhiều khối.",
        "Ưu điểm: Tốc độ nén/giải nén cực cao (O(N)), không cần bảng mã phụ trợ.",
        "Nhược điểm: Làm phình dữ liệu lên gấp đôi (2x) nếu văn bản không có byte lặp liên tiếp."
    ]),
    ("Canonical Huffman", "Huffman Chính Tắc (2-pass)", "Dư thừa tần suất bậc 0", INDIGO_600, [
        "Nguyên lý: Mã hóa tiền tố biến thiên độ dài (VLC) dựa trên tần suất xuất hiện của từng byte.",
        "Hai lượt duyệt (2-pass): Lượt 1 đếm tần suất dựng cây; Lượt 2 ghi bảng độ dài mã và bitstream.",
        "Chính tắc (Canonical): Chỉ lưu 256 độ dài mã (code lengths), tái dựng mã theo thứ tự từ điển.",
        "Giới hạn: Bị chặn dưới bởi entropy bậc 0 H₀; không khai thác được quan hệ giữa các ký tự kế tiếp."
    ]),
    ("LZW", "Lempel-Ziv-Welch 12-bit", "Dư thừa chuỗi con tuần tự", CYAN_600, [
        "Nguyên lý: Học từ điển chuỗi con trong quá trình nén theo luồng một lượt (single-pass).",
        "Quy cách: Từ điển 4096 mã cố định 12-bit (0-255 là byte gốc, 256-4095 cho chuỗi mới).",
        "Đóng băng từ điển: Khi đủ 4096 mã, từ điển ngừng học để duy trì đồng bộ bên giải nén.",
        "Đặc tính: Khai thác ngữ cảnh chuỗi dài; có thể vượt qua mốc entropy H₀/8 của Huffman."
    ]),
    ("Byte-level BPE", "Byte Pair Encoding", "Dư thừa cặp ký hiệu lặp", EMERALD_600, [
        "Nguyên lý: Khởi tạo vốn từ 256 byte UTF-8; lặp lại việc tìm và gộp cặp token xuất hiện nhiều nhất.",
        r"Ranh giới từ: Phân đoạn bằng regex ` ?[^\s]+|\s+`, không gộp cặp qua ranh giới từ/khoảng trắng.",
        "Hai vai trò: Là codec nén hoàn chỉnh (khi lưu kèm bảng merge) hoặc tokenizer LLM (chia sẻ bảng).",
        "Ứng dụng: Xử lý từ vựng mở (open vocabulary), giải quyết từ hiếm và là cốt lõi của GPT, LLaMA."
    ])
]

for idx, (short_name, full_name, red_type, col, points) in enumerate(algos):
    c_left = Inches(0.8 + idx * 3.0)
    card = add_card(s4, c_left, Inches(1.6), Inches(2.733), Inches(5.25), bg_color=WHITE, border_color=SLATE_200)
    
    # Badge
    bg_b = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left + Inches(0.15), Inches(1.8), Inches(2.433), Inches(0.72))
    bg_b.fill.solid()
    bg_b.fill.fore_color.rgb = col
    bg_b.line.fill.background()
    tf_b = bg_b.text_frame
    tf_b.word_wrap = True
    tf_b.vertical_anchor = MSO_ANCHOR.MIDDLE
    p1 = tf_b.paragraphs[0]
    p1.text = short_name
    p1.font.name = FONT_HEADING
    p1.font.size = Pt(12)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p1.alignment = PP_ALIGN.CENTER
    p2 = tf_b.add_paragraph()
    p2.text = red_type
    p2.font.name = FONT_BODY
    p2.font.size = Pt(8)
    p2.font.color.rgb = WHITE
    p2.alignment = PP_ALIGN.CENTER
    
    # Subtitle
    tx_fn = s4.shapes.add_textbox(c_left + Inches(0.15), Inches(2.6), Inches(2.433), Inches(0.4))
    tf_fn = tx_fn.text_frame
    tf_fn.word_wrap = True
    tf_fn.margin_left = tf_fn.margin_right = tf_fn.margin_top = tf_fn.margin_bottom = 0
    p_fn = tf_fn.paragraphs[0]
    p_fn.text = full_name
    p_fn.font.name = FONT_HEADING
    p_fn.font.size = Pt(9)
    p_fn.font.bold = True
    p_fn.font.color.rgb = NAVY_900
    
    # Bullets
    tx_p = s4.shapes.add_textbox(c_left + Inches(0.15), Inches(3.05), Inches(2.433), Inches(3.65))
    tf_p = tx_p.text_frame
    tf_p.word_wrap = True
    tf_p.margin_left = tf_p.margin_right = tf_p.margin_top = tf_p.margin_bottom = 0
    for pt_idx, pt in enumerate(points):
        p = tf_p.paragraphs[0] if pt_idx == 0 else tf_p.add_paragraph()
        p.text = pt
        p.font.name = FONT_BODY
        p.font.size = Pt(8.2)
        p.font.color.rgb = SLATE_700
        p.space_before = Pt(4)


# ==========================================================
# SLIDE 5: Container Specification & Experimental Methodology
# ==========================================================
s5 = prs.slides.add_slide(blank_layout)
add_bg(s5)
add_header(s5, "PHƯƠNG PHÁP NGHIÊN CỨU", "Quy cách Container Nhị phân Tự giải mã & Pipeline Đo lường", "Thiết kế chuẩn hóa đảm bảo tính độc lập, an toàn và tái lập 100% kết quả")
add_footer(s5, 5)

# Left Side: Binary Containers
add_card(s5, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.25), bg_color=WHITE, border_color=SLATE_200)
tx_c1 = s5.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.3), Inches(0.4))
tf_c1 = tx_c1.text_frame
p = tf_c1.paragraphs[0]
p.text = "Quy cách Container Nhị phân Tự giải mã"
p.font.name = FONT_HEADING
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = NAVY_900

c_items = [
    ("Phần đầu chuẩn hóa (Header)", "Mọi container bắt đầu bằng Magic 4 byte ('RLE1', 'HUF1', 'LZW1', 'BPE1') cùng độ dài tệp gốc 8 byte (uint64 big-endian)."),
    ("RLE Container", "Payload gồm các cặp (count, byte). Count từ 1-255. Tổng dung lượng = 12 + 2 × n_runs byte."),
    ("Canonical Huffman Container", "Lưu 256 byte bảng độ dài mã (code lengths). Bitstream đóng gói MSB-first, đệm 0 ở byte cuối cùng. Tổng dung lượng = 12 + 256 + ceil(total_bits / 8)."),
    ("LZW 12-bit Container", "Từ điển 4096 mục. Chuỗi mã 12-bit đóng gói 3 byte cho mỗi 2 mã (MSB-first). Đệm 0 ở nibble cuối. Dung lượng = 12 + ceil(12 × n_codes / 8)."),
    ("BPE Container Độc Lập", "Magic 'BPE1' (4B) + orig_len (8B) + n_merges m (2B) + m mục merge (3m B: 2B first + 1B second) + n_tokens T (8B) + payload mã 12-bit (ceil(12T/8) B). Tổng = 22 + 3m + ceil(12T/8) byte.")
]

tx_desc = s5.shapes.add_textbox(Inches(1.0), Inches(2.25), Inches(5.3), Inches(4.4))
tf_d = tx_desc.text_frame
tf_d.word_wrap = True
tf_d.margin_left = tf_d.margin_right = tf_d.margin_top = tf_d.margin_bottom = 0

for i, (title, desc) in enumerate(c_items):
    p_t = tf_d.paragraphs[0] if i == 0 else tf_d.add_paragraph()
    p_t.text = f"{i+1}. {title}"
    p_t.font.name = FONT_HEADING
    p_t.font.size = Pt(9.5)
    p_t.font.bold = True
    p_t.font.color.rgb = BLUE_700
    p_t.space_before = Pt(4)
    
    p_b = tf_d.add_paragraph()
    p_b.text = desc
    p_b.font.name = FONT_BODY
    p_b.font.size = Pt(8.2)
    p_b.font.color.rgb = SLATE_600
    p_b.space_before = Pt(1)

# Right Side: Experimental Design & Measurement Pipeline
add_card(s5, Inches(6.8), Inches(1.6), Inches(5.733), Inches(5.25), bg_color=WHITE, border_color=SLATE_200)
tx_c2 = s5.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.333), Inches(0.4))
tf_c2 = tx_c2.text_frame
p2 = tf_c2.paragraphs[0]
p2.text = "Thiết kế Thực nghiệm & Quy trình Đo lường"
p2.font.name = FONT_HEADING
p2.font.size = Pt(13)
p2.font.bold = True
p2.font.color.rgb = NAVY_900

m_items = [
    ("Bộ Ngữ liệu Thí nghiệm", "• Tổng hợp: C1 (Run lặp ~32B), C2 (Zipf 1000 từ), C3 (Uniform random). 3 seeds ở 256, 512, 1024, 2048, 4096 KiB.\n• Thực tế: Canterbury (alice29, kennedy) và Wikipedia Việt–Anh (V1, E1) chuẩn hóa NFC, UTF-8. Train 1 MiB, Test 1 MiB."),
    ("Chỉ số Đánh giá (Metrics)", "• Tỷ lệ nén Codec: comp_bytes / orig_bytes (càng nhỏ càng tốt).\n• Tỷ lệ BPE Token-only: ceil(12T/8) / orig_bytes.\n• Mật độ Token: byte/token = orig_bytes / T.\n• Thông lượng: (orig_bytes / 1024) / time_sec (KiB/s)."),
    ("Quy trình Đo lường Nghiêm ngặt", "• Thời gian nén/giải nén: Lấy trung vị 3 lượt đo `time.perf_counter`.\n• Bộ nhớ: Đo trong tiến trình riêng qua `tracemalloc`, theo dõi đỉnh cấp phát heap Python (Peak Memory KiB).\n• Đối chiếu Toàn vẹn: 100% đối chiếu SHA-256 sau khi giải nén."),
    ("Môi trường Phần cứng", "Intel Core i7-13650HX, 24 GB RAM, Windows 11, Python 3.13.2. Toàn bộ mã nguồn và dữ liệu kiểm chứng độc lập.")
]

tx_m = s5.shapes.add_textbox(Inches(7.0), Inches(2.25), Inches(5.333), Inches(4.4))
tf_m = tx_m.text_frame
tf_m.word_wrap = True
tf_m.margin_left = tf_m.margin_right = tf_m.margin_top = tf_m.margin_bottom = 0

for i, (title, desc) in enumerate(m_items):
    p_t = tf_m.paragraphs[0] if i == 0 else tf_m.add_paragraph()
    p_t.text = f"{i+1}. {title}"
    p_t.font.name = FONT_HEADING
    p_t.font.size = Pt(9.5)
    p_t.font.bold = True
    p_t.font.color.rgb = EMERALD_700
    p_t.space_before = Pt(4)
    
    p_b = tf_m.add_paragraph()
    p_b.text = desc
    p_b.font.name = FONT_BODY
    p_b.font.size = Pt(8.2)
    p_b.font.color.rgb = SLATE_600
    p_b.space_before = Pt(1)


# ==========================================================
# SLIDE 6: RQ1 - Data Families & Compression Ratio
# ==========================================================
s6 = prs.slides.add_slide(blank_layout)
add_bg(s6)
add_header(s6, "KẾT QUẢ RQ1", "Ảnh hưởng của Họ Dữ liệu & Quy mô lên Tỷ lệ Nén", "Khảo sát RLE, Canonical Huffman và LZW trên 4 họ dữ liệu ở quy mô 256 KiB đến 4096 KiB")
add_footer(s6, 6)

# Left Side: Table I and Insights
add_card(s6, Inches(0.8), Inches(1.6), Inches(6.0), Inches(5.25), bg_color=WHITE, border_color=SLATE_200)

tx_t1 = s6.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(5.6), Inches(0.35))
tf_t1 = tx_t1.text_frame
p = tf_t1.paragraphs[0]
p.text = "Bảng I: Tỷ lệ nén tại 4096 KiB danh nghĩa"
p.font.name = FONT_HEADING
p.font.size = Pt(11.5)
p.font.bold = True
p.font.color.rgb = NAVY_900

# Table I
headers_t1 = ["Họ dữ liệu", "Đặc tính", "RLE", "Huffman", "LZW"]
rows_t1 = [
    ["C1", "Run lặp hình học (~32B)", "0.062526", "1.000064", "0.216611"],
    ["C2", "Zipfian 1000 từ (s=1)", "1.960098", "0.569210", "0.379549"],
    ["C3", "Uniform random byte", "1.992249", "1.000064", "1.419488"],
    ["V1", "Wikipedia tiếng Việt", "1.988627", "0.669362", "0.500129"]
]
widths_t1 = [Inches(1.0), Inches(1.8), Inches(1.0), Inches(1.0), Inches(1.0)]
add_table_custom(s6, Inches(1.0), Inches(2.15), Inches(5.6), Inches(1.5), headers_t1, rows_t1, widths_t1, highlight_idx=3)

# Key Insights box
tx_in = s6.shapes.add_textbox(Inches(1.0), Inches(3.9), Inches(5.6), Inches(2.8))
tf_in = tx_in.text_frame
tf_in.word_wrap = True
tf_in.margin_left = tf_in.margin_right = tf_in.margin_top = tf_in.margin_bottom = 0

insights_rq1 = [
    ("C1 (Run dài): RLE vô địch tuyệt đối (0.0625)", "Nén giảm dung lượng tới 93.7% nhờ khai thác trực tiếp byte lặp liên tiếp. Huffman thất bại hoàn toàn (~1.000) do phân bố histogram byte gần đều."),
    ("C2 (Zipfian): LZW đạt hiệu quả cao nhất (0.3795)", "Sự lặp lại của các từ vựng giúp LZW nhanh chóng xây dựng chuỗi từ điển phong phú. Huffman đạt 0.5692. RLE làm phình file lên gần gấp đôi (1.96x)."),
    ("C3 (Ngẫu nhiên đều): Minh chứng 'No Free Lunch'", "Cực đại entropy khiến không codec nào nén được; overhead header và bit padding làm kích thước file phình to (LZW phình 41.9%, RLE phình 99.2%)."),
    ("V1 (Văn bản Tiếng Việt): LZW vượt trội Huffman", "LZW đạt tỷ lệ 0.5001 so với Huffman 0.6694, khẳng định ưu thế của việc khai thác cụm từ con (higher-order context) so với tần suất ký tự đơn lẻ.")
]

for i, (head, body) in enumerate(insights_rq1):
    p_h = tf_in.paragraphs[0] if i == 0 else tf_in.add_paragraph()
    p_h.text = f"• {head}:"
    p_h.font.name = FONT_HEADING
    p_h.font.size = Pt(8.8)
    p_h.font.bold = True
    p_h.font.color.rgb = BLUE_700
    p_h.space_before = Pt(3)
    
    p_b = tf_in.add_paragraph()
    p_b.text = f"  {body}"
    p_b.font.name = FONT_BODY
    p_b.font.size = Pt(8.0)
    p_b.font.color.rgb = SLATE_600

# Right Side: Figure 1
add_card(s6, Inches(7.1), Inches(1.6), Inches(5.433), Inches(5.25), bg_color=WHITE, border_color=SLATE_200)
fig1_path = FIGS_DIR / "rq1_ratio.png"
if fig1_path.exists():
    s6.shapes.add_picture(str(fig1_path), Inches(7.25), Inches(1.75), width=Inches(5.133))

tx_cap1 = s6.shapes.add_textbox(Inches(7.25), Inches(6.3), Inches(5.133), Inches(0.45))
tf_cap1 = tx_cap1.text_frame
tf_cap1.word_wrap = True
tf_cap1.margin_left = tf_cap1.margin_right = tf_cap1.margin_top = tf_cap1.margin_bottom = 0
p_c1 = tf_cap1.paragraphs[0]
p_c1.text = "Hình 1: Tỷ lệ nén qua 5 kích thước (256 - 4096 KiB). Tăng kích thước giảm tỷ trọng header nhưng không tự tạo cấu trúc dễ nén."
p_c1.font.name = FONT_BODY
p_c1.font.size = Pt(8)
p_c1.font.color.rgb = SLATE_500
p_c1.alignment = PP_ALIGN.CENTER


# ==========================================================
# SLIDE 7: RQ1 - Throughput & Peak Memory
# ==========================================================
s7 = prs.slides.add_slide(blank_layout)
add_bg(s7)
add_header(s7, "KẾT QUẢ RQ1", "Đánh giá Thông lượng (KiB/s) & Chi phí Bộ nhớ Đỉnh", "Phân tích tốc độ xử lý và nguyên nhân gây đột biến bộ nhớ trong quá trình thực thi")
add_footer(s7, 7)

# Left Side: Table II and Analysis
add_card(s7, Inches(0.8), Inches(1.6), Inches(6.4), Inches(5.25), bg_color=WHITE, border_color=SLATE_200)

tx_t2 = s7.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(6.0), Inches(0.35))
tf_t2 = tx_t2.text_frame
p = tf_t2.paragraphs[0]
p.text = "Bảng II: Thông lượng & Bộ nhớ đỉnh tại 4096 KiB (Trung vị seed)"
p.font.name = FONT_HEADING
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = NAVY_900

headers_t2 = ["Họ", "Codec", "Nén (KiB/s)", "Giải nén (KiB/s)", "Đỉnh RAM (KiB)"]
rows_t2 = [
    ["C1", "rle", "29,495.6", "140,597.5", "8,629.3"],
    ["C1", "huffman", "5,724.7", "1,811.2", "275,579.5"],
    ["C1", "lzw", "12,541.4", "34,385.2", "9,570.1"],
    ["C2", "rle", "8,602.6", "7,093.1", "16,628.0"],
    ["C2", "huffman", "7,521.5", "2,783.3", "156,365.0"],
    ["C2", "lzw", "10,588.9", "20,581.5", "10,070.7"],
    ["V1", "rle", "8,845.6", "7,089.0", "17,250.9"],
    ["V1", "huffman", "6,892.0", "2,420.7", "185,566.6"],
    ["V1", "lzw", "9,577.2", "15,614.5", "10,426.7"]
]
widths_t2 = [Inches(0.6), Inches(1.2), Inches(1.4), Inches(1.5), Inches(1.3)]
add_table_custom(s7, Inches(1.0), Inches(2.12), Inches(6.0), Inches(2.3), headers_t2, rows_t2, widths_t2, highlight_idx=8)

# Analytical findings
tx_t2_f = s7.shapes.add_textbox(Inches(1.0), Inches(4.55), Inches(6.0), Inches(2.15))
tf_f = tx_t2_f.text_frame
tf_f.word_wrap = True
tf_f.margin_left = tf_f.margin_right = tf_f.margin_top = tf_f.margin_bottom = 0

findings = [
    ("RLE — Đỉnh cao tốc độ giải nén C1", "Đạt tới 140,597 KiB/s (~140 MB/s), vượt xa mọi codec nhờ vòng lặp nhân bản byte trực tiếp. Bộ nhớ duy trì mức tối thiểu (~8-17 MB)."),
    ("LZW — Cân bằng xuất sắc giữa Nén và Giải nén", "Thông lượng giải nén nhanh gấp 1.6 - 2.7 lần nén (15 - 34 MB/s). Bộ nhớ kiểm soát chặt chẽ quanh 9.5 - 14.5 MB nhờ từ điển giới hạn 4096 mục."),
    ("Huffman — Điểm nghẽn bộ nhớ do Cài đặt Python", "Đỉnh RAM vọt lên 275 MB! Nguyên nhân: Việc ghép chuỗi bit trung gian (`0` và `1`) trong Python tạo ra hàng triệu đối tượng chuỗi, tiêu tốn bộ nhớ gấp 67 lần kích thước tệp gốc.")
]

for i, (title, desc) in enumerate(findings):
    p_t = tf_f.paragraphs[0] if i == 0 else tf_f.add_paragraph()
    p_t.text = f"• {title}:"
    p_t.font.name = FONT_HEADING
    p_t.font.size = Pt(8.5)
    p_t.font.bold = True
    p_t.font.color.rgb = ROSE_600 if "Huffman" in title else BLUE_700
    p_t.space_before = Pt(2)
    
    p_b = tf_f.add_paragraph()
    p_b.text = f"  {desc}"
    p_b.font.name = FONT_BODY
    p_b.font.size = Pt(7.8)
    p_b.font.color.rgb = SLATE_600

# Right Side: Figures 2 & 3
add_card(s7, Inches(7.5), Inches(1.6), Inches(5.033), Inches(5.25), bg_color=WHITE, border_color=SLATE_200)
fig2_path = FIGS_DIR / "rq1_throughput.png"
fig3_path = FIGS_DIR / "rq1_memory.png"

if fig2_path.exists():
    s7.shapes.add_picture(str(fig2_path), Inches(7.65), Inches(1.75), width=Inches(4.733), height=Inches(2.45))
if fig3_path.exists():
    s7.shapes.add_picture(str(fig3_path), Inches(7.65), Inches(4.35), width=Inches(4.733), height=Inches(2.35))


# ==========================================================
# SLIDE 8: RQ2 - Permutation Invariance & Entropy
# ==========================================================
s8 = prs.slides.add_slide(blank_layout)
add_bg(s8)
add_header(s8, "KẾT QUẢ RQ2", "Giữ nguyên Histogram, Đổi Thứ tự: Tác động của Hoán vị Byte", "Khảo sát tính bất biến của Huffman và độ nhạy ngữ cảnh của RLE & LZW trên Canterbury & Wikipedia")
add_footer(s8, 8)

# Left Side: Table III
add_card(s8, Inches(0.8), Inches(1.6), Inches(6.6), Inches(5.25), bg_color=WHITE, border_color=SLATE_200)

tx_t3 = s8.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(6.2), Inches(0.35))
tf_t3 = tx_t3.text_frame
p = tf_t3.paragraphs[0]
p.text = "Bảng III: Tỷ lệ nén và Entropy H₀/8 theo 3 trạng thái hoán vị"
p.font.name = FONT_HEADING
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = NAVY_900

headers_t3 = ["Tệp", "Trạng thái", "H₀/8", "RLE", "Huffman", "LZW"]
rows_t3 = [
    ["alice29.txt", "original", "0.570960", "1.905880", "0.578319", "0.475577"],
    ["alice29.txt", "runs", "0.570960", "0.008469", "0.578319", "0.032645"],
    ["alice29.txt", "shuffled", "0.570960", "1.862670", "0.578319", "0.686418"],
    ["kennedy.xls", "original", "0.446684", "1.681770", "0.449432", "0.407137"],
    ["kennedy.xls", "runs", "0.446684", "0.008167", "0.449432", "0.212572"],
    ["kennedy.xls", "shuffled", "0.446684", "1.525510", "0.449432", "0.544609"],
    ["v1_test_1mib", "original", "0.660910", "1.988550", "0.665004", "0.492817"],
    ["v1_test_1mib", "runs", "0.660910", "0.008083", "0.665004", "1.044570"],
    ["v1_test_1mib", "shuffled", "0.660910", "1.894910", "0.665004", "0.820334"]
]
widths_t3 = [Inches(1.4), Inches(1.1), Inches(1.0), Inches(1.0), Inches(1.0), Inches(1.1)]
add_table_custom(s8, Inches(1.0), Inches(2.12), Inches(6.2), Inches(2.4), headers_t3, rows_t3, widths_t3, highlight_idx=7)

# Key Takeaways
tx_rq2_t = s8.shapes.add_textbox(Inches(1.0), Inches(4.65), Inches(6.2), Inches(2.05))
tf_2t = tx_rq2_t.text_frame
tf_2t.word_wrap = True
tf_2t.margin_left = tf_2t.margin_right = tf_2t.margin_top = tf_2t.margin_bottom = 0

t_items = [
    ("Huffman — Bất biến tuyệt đối qua hoán vị", "Tỷ lệ nén và kích thước nén byte giữ nguyên 100% qua mọi trạng thái hoán vị. Lý do: Bảng đếm tần suất byte không thay đổi, cây Huffman và độ dài mã chính tắc hoàn toàn cố định."),
    ("RLE — Cực kỳ nhạy cảm với việc gom cụm", "Khi gom nhóm bằng counting sort (runs), RLE giảm dung lượng tới 99.2% (tỷ lệ ~0.008). Khi xáo trộn (shuffled), các run bị phá vỡ hoàn toàn khiến file phình to gần 2x."),
    ("LZW — Suy giảm rõ rệt khi xáo trộn thứ tự", "Việc xáo trộn phá hủy quan hệ chuỗi con tự nhiên, khiến tỷ lệ LZW tăng mạnh từ 0.47 lên 0.68 trên alice29 và 0.49 lên 0.82 trên V1.")
]

for i, (title, desc) in enumerate(t_items):
    p_t = tf_2t.paragraphs[0] if i == 0 else tf_2t.add_paragraph()
    p_t.text = f"• {title}:"
    p_t.font.name = FONT_HEADING
    p_t.font.size = Pt(8.5)
    p_t.font.bold = True
    p_t.font.color.rgb = BLUE_700
    p_t.space_before = Pt(2)
    
    p_b = tf_2t.add_paragraph()
    p_b.text = f"  {desc}"
    p_b.font.name = FONT_BODY
    p_b.font.size = Pt(8.0)
    p_b.font.color.rgb = SLATE_600

# Right Side: Figure 4
add_card(s8, Inches(7.7), Inches(1.6), Inches(4.833), Inches(5.25), bg_color=WHITE, border_color=SLATE_200)
fig4_path = FIGS_DIR / "rq2_ratio.png"
if fig4_path.exists():
    s8.shapes.add_picture(str(fig4_path), Inches(7.85), Inches(1.75), width=Inches(4.533))

tx_cap4 = s8.shapes.add_textbox(Inches(7.85), Inches(6.3), Inches(4.533), Inches(0.45))
tf_cap4 = tx_cap4.text_frame
tf_cap4.word_wrap = True
tf_cap4.margin_left = tf_cap4.margin_right = tf_cap4.margin_top = tf_cap4.margin_bottom = 0
p_c4 = tf_cap4.paragraphs[0]
p_c4.text = "Hình 4: Ảnh hưởng của thứ tự byte. Lưu ý cột LZW V1-runs (màu đỏ) bị phình to bất thường."
p_c4.font.name = FONT_BODY
p_c4.font.size = Pt(8)
p_c4.font.color.rgb = SLATE_500
p_c4.alignment = PP_ALIGN.CENTER


# ==========================================================
# SLIDE 9: RQ2 Deep Dive - V1-runs Anomaly & Dictionary Freezing
# ==========================================================
s9 = prs.slides.add_slide(blank_layout)
add_bg(s9)
add_header(s9, "KẾT QUẢ RQ2 CHUYÊN SÂU", "Giải mã Ngoại lệ V1-runs: Hiện tượng Đóng băng Từ điển LZW", "Tại sao dữ liệu sau khi gom run tối đa lại khiến LZW bị phình to (>1.0)?")
add_footer(s9, 9)

# Left Card: Detailed Mechanism of Dictionary Freezing
add_card(s9, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.25), bg_color=WHITE, border_color=SLATE_200)
tx_mech = s9.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.3), Inches(0.4))
tf_m = tx_mech.text_frame
p = tf_m.paragraphs[0]
p.text = "Cơ chế Đóng Băng Từ Điển (Frozen Dictionary)"
p.font.name = FONT_HEADING
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = ROSE_600

steps = [
    ("Hiện tượng nghịch lý tại V1-runs", "Trên v1_test_1mib đã counting sort (runs), tỷ lệ LZW là 1.044570 (> 1) — kích thước tệp nén lớn hơn cả tệp gốc! Trong khi trên alice29-runs, LZW nén siêu tốt (0.0326)."),
    ("Truy vết Log luồng dữ liệu (Mechanism Checker)", "• File V1 có kích thước lớn (1 MiB) với các run byte cực kỳ dài.\n• Từ điển 12-bit (4096 entries) bị lấp đầy hoàn toàn ngay tại byte thứ 319,103 (chỉ mới ~30.4% tệp đầu vào)!\n• Tại thời điểm này, toàn bộ 4096 mã đều bị chiếm bởi các tiền tố run lặp đơn điệu ban đầu."),
    ("Hậu quả của chính sách đóng băng (Freeze Policy)", "• Ở 70% dữ liệu còn lại, từ điển bị 'đóng băng', không thể học thêm bất kỳ chuỗi con mới nào.\n• Khi gặp các ký tự và run byte mới ở phần sau, LZW không tìm thấy mã ghép phù hợp, buộc phải phát từng byte đơn lẻ dưới dạng mã 12-bit.\n• Hệ quả: Mỗi byte đơn 8-bit bị phình thành mã 12-bit (tăng 50% dung lượng)!"),
    ("Đối chiếu với alice29-runs", "alice29 chỉ có 152 KiB, từ điển không bị lấp đầy nên LZW liên tục sinh các mã chuỗi dài thành công.")
]

tx_s = s9.shapes.add_textbox(Inches(1.0), Inches(2.25), Inches(5.3), Inches(4.4))
tf_s = tx_s.text_frame
tf_s.word_wrap = True
tf_s.margin_left = tf_s.margin_right = tf_s.margin_top = tf_s.margin_bottom = 0

for i, (title, desc) in enumerate(steps):
    p_t = tf_s.paragraphs[0] if i == 0 else tf_s.add_paragraph()
    p_t.text = f"{i+1}. {title}"
    p_t.font.name = FONT_HEADING
    p_t.font.size = Pt(9.5)
    p_t.font.bold = True
    p_t.font.color.rgb = NAVY_900
    p_t.space_before = Pt(4)
    
    p_b = tf_s.add_paragraph()
    p_b.text = desc
    p_b.font.name = FONT_BODY
    p_b.font.size = Pt(8.2)
    p_b.font.color.rgb = SLATE_600
    p_b.space_before = Pt(1)

# Right Side: Theoretical Insights
add_card(s9, Inches(6.8), Inches(1.6), Inches(5.733), Inches(5.25), bg_color=WHITE, border_color=SLATE_200)

tx_th2 = s9.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.333), Inches(0.4))
tf_th2 = tx_th2.text_frame
p2 = tf_th2.paragraphs[0]
p2.text = "Ý nghĩa Lý thuyết Thông tin & Cận Dưới Nén"
p2.font.name = FONT_HEADING
p2.font.size = Pt(13)
p2.font.bold = True
p2.font.color.rgb = BLUE_700

theories = [
    ("Bản chất của Entropy bậc 0 (Zero-order Entropy H₀)", "H₀ = −Σ pᵢ log₂ pᵢ chỉ mô tả phân bố xác suất biên của từng byte riêng lẻ, hoàn toàn bỏ qua thứ tự sắp xếp và tương quan chuỗi. Do đó H₀/8 là bất biến trước mọi phép hoán vị."),
    ("H₀/8 không phải là Cận dưới Tuyệt đối cho mọi Codec", "• Đối với codec độc lập ngữ cảnh (như Huffman), H₀/8 là cận dưới lý thuyết.\n• Nhưng đối với codec khai thác ngữ cảnh chuỗi (như LZW), tỷ lệ nén có thể thấp hơn H₀/8 rất nhiều trên văn bản tự nhiên (alice29: LZW 0.475 < H₀/8 0.571; V1: LZW 0.492 < H₀/8 0.661)."),
    ("Bài học thiết kế thuật toán cho LZW", "Cơ chế đóng băng cố định (freeze) có điểm yếu chí mạng khi phân bố dữ liệu thay đổi đột ngột giữa chừng. Trong thực tế, các biến thể LZW hiện đại (như trong Unix compress hay GIF) sử dụng cơ chế xóa từ điển (clear code) hoặc LRU eviction khi hiệu suất nén bắt đầu suy giảm.")
]

tx_th_d = s9.shapes.add_textbox(Inches(7.0), Inches(2.25), Inches(5.333), Inches(4.4))
tf_th_d = tx_th_d.text_frame
tf_th_d.word_wrap = True
tf_th_d.margin_left = tf_th_d.margin_right = tf_th_d.margin_top = tf_th_d.margin_bottom = 0

for i, (title, desc) in enumerate(theories):
    p_t = tf_th_d.paragraphs[0] if i == 0 else tf_th_d.add_paragraph()
    p_t.text = f"{i+1}. {title}"
    p_t.font.name = FONT_HEADING
    p_t.font.size = Pt(9.5)
    p_t.font.bold = True
    p_t.font.color.rgb = BLUE_700
    p_t.space_before = Pt(5)
    
    p_b = tf_th_d.add_paragraph()
    p_b.text = desc
    p_b.font.name = FONT_BODY
    p_b.font.size = Pt(8.2)
    p_b.font.color.rgb = SLATE_600
    p_b.space_before = Pt(1)


# ==========================================================
# SLIDE 10: RQ3.A - BPE Codec vs Tokenizer & Baseline LZW
# ==========================================================
s10 = prs.slides.add_slide(blank_layout)
add_bg(s10)
add_header(s10, "KẾT QUẢ RQ3.A", "BPE: Codec Độc Lập vs Tokenizer Chia Sẻ Từ Điển", "Đối chiếu BPE với Baseline LZW ở các mức ngân sách K = 256, 1024, 3840 merges")
add_footer(s10, 10)

# Top 3 Highlight Cards
add_metric_callout(s10, Inches(0.8), Inches(1.6), Inches(3.733), Inches(1.35),
                   "32.6% Nén Tốt Hơn", "BPE Vượt LZW trên Tiếng Việt (V1)",
                   "Tại K=3840, BPE V1→V1 đạt tỷ lệ 0.3323 so với LZW 0.4928 (nhỏ hơn 32.6% đã tính cả overhead bảng merge).",
                   val_color=EMERALD_600, bg_color=WHITE)

add_metric_callout(s10, Inches(4.8), Inches(1.6), Inches(3.733), Inches(1.35),
                   "13.7% Nén Tốt Hơn", "BPE Vượt LZW trên Tiếng Anh (E1)",
                   "Tại K=3840, BPE E1→E1 đạt tỷ lệ 0.4645 so với LZW 0.5380 (nhỏ hơn 13.7% đã tính cả overhead).",
                   val_color=EMERALD_600, bg_color=WHITE)

add_metric_callout(s10, Inches(8.8), Inches(1.6), Inches(3.733), Inches(1.35),
                   "11,542 Bytes", "Chi Phí Overhead Bảng Merge",
                   "Overhead = 22 + 3m byte. Tại m=3840, bảng merge chiếm 11.5 KiB. Khi tệp đủ lớn (1 MiB), overhead chỉ chiếm ~1.1%.",
                   val_color=BLUE_600, bg_color=WHITE)

# Bottom: Table IV Full
add_card(s10, Inches(0.8), Inches(3.1), Inches(11.733), Inches(3.75), bg_color=WHITE, border_color=SLATE_200)

tx_t4 = s10.shapes.add_textbox(Inches(1.0), Inches(3.2), Inches(11.333), Inches(0.3))
tf_t4 = tx_t4.text_frame
p = tf_t4.paragraphs[0]
p.text = "Bảng IV: So sánh Tỷ lệ nén BPE Codec (có header), Token-only (chỉ payload) và Baseline LZW trên cùng tập test 1 MiB"
p.font.name = FONT_HEADING
p.font.size = Pt(10)
p.font.bold = True
p.font.color.rgb = NAVY_900

headers_t4 = ["K merges", "Train → Test", "BPE Codec (Toàn bộ container)", "BPE Token-only (Chỉ mã 12-bit)", "LZW Baseline (Cùng test)", "Đánh giá"]
rows_t4 = [
    ["256", "V1 → V1", "0.605747", "0.604994", "0.492817", "LZW tốt hơn (BPE chưa đủ merge)"],
    ["256", "V1 → E1", "1.257490", "1.256730", "0.538014", "Chéo ngữ liệu: BPE phình to"],
    ["256", "E1 → V1", "1.219690", "1.218940", "0.492817", "Chéo ngữ liệu: BPE phình to"],
    ["256", "E1 → E1", "0.747497", "0.746743", "0.538014", "LZW tốt hơn"],
    ["1024", "V1 → V1", "0.409581", "0.406631", "0.492817", "BPE vượt LZW (+16.9%)"],
    ["1024", "E1 → E1", "0.581138", "0.578187", "0.538014", "BPE xấp xỉ LZW"],
    ["3840", "V1 → V1", "0.332326", "0.321319", "0.492817", "BPE THẮNG ÁP ĐẢO (Nhỏ hơn 32.6%)"],
    ["3840", "V1 → E1", "0.775084", "0.764076", "0.538014", "Chéo ngữ liệu kém LZW"],
    ["3840", "E1 → V1", "1.149490", "1.138480", "0.492817", "Phình to: E1 không có merge tiếng Việt"],
    ["3840", "E1 → E1", "0.464467", "0.453460", "0.538014", "BPE THẮNG ÁP ĐẢO (Nhỏ hơn 13.7%)"]
]
widths_t4 = [Inches(1.0), Inches(1.8), Inches(2.6), Inches(2.4), Inches(2.0), Inches(1.933)]
add_table_custom(s10, Inches(1.0), Inches(3.55), Inches(11.333), Inches(3.15), headers_t4, rows_t4, widths_t4, highlight_idx=6)


# ==========================================================
# SLIDE 11: RQ3.B - 2x2 Cross-lingual Tokenizer Matrix
# ==========================================================
s11 = prs.slides.add_slide(blank_layout)
add_bg(s11)
add_header(s11, "KẾT QUẢ RQ3.B", "Ma trận Tokenizer Việt–Anh 2×2 & Hiện tượng Vỡ vụn Token", "Tác động nghiêm trọng của việc dùng sai lệch ngôn ngữ huấn luyện tokenizer đến số lượng token")
add_footer(s11, 11)

# Left Side: Table V and Analysis
add_card(s11, Inches(0.8), Inches(1.6), Inches(6.2), Inches(5.25), bg_color=WHITE, border_color=SLATE_200)

tx_t5 = s11.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(5.8), Inches(0.35))
tf_t5 = tx_t5.text_frame
p = tf_t5.paragraphs[0]
p.text = "Bảng V: Ma trận 2×2 tại K=3840 (Byte/token / Số token trên test 1 MiB)"
p.font.name = FONT_HEADING
p.font.size = Pt(10.5)
p.font.bold = True
p.font.color.rgb = NAVY_900

headers_t5 = ["Train Corpus", "Test Tiếng Việt (V1)", "Test Tiếng Anh (E1)"]
rows_t5 = [
    ["Train V1 (Wiki Tiếng Việt)", "4.66826 / 224,618", "1.96315 / 534,128"],
    ["Train E1 (Wiki Tiếng Anh)", "1.31755 / 795,855", "3.30790 / 316,991"]
]
widths_t5 = [Inches(2.2), Inches(2.0), Inches(1.6)]
add_table_custom(s11, Inches(1.0), Inches(2.15), Inches(5.8), Inches(1.2), headers_t5, rows_t5, widths_t5, highlight_idx=1)

# Critical Insights
tx_2x2 = s11.shapes.add_textbox(Inches(1.0), Inches(3.5), Inches(5.8), Inches(3.2))
tf_2x = tx_2x2.text_frame
tf_2x.word_wrap = True
tf_2x.margin_left = tf_2x.margin_right = tf_2x.margin_top = tf_2x.margin_bottom = 0

cross_insights = [
    ("Lạm phát Token Tiếng Việt lên tới 3.54 lần (354%)", "Trên cùng văn bản test V1, tokenizer học từ tiếng Anh (E1) sinh ra 795,855 tokens, gấp 3.54 lần so với tokenizer học từ tiếng Việt (224,618 tokens)! Mật độ nén sụt giảm thê thảm từ 4.67 bytes/token xuống chỉ còn 1.32 bytes/token."),
    ("Cơ chế Vỡ vụn Token (Token Fragmentation)", "Tiếng Việt UTF-8 sử dụng từ 2 đến 3 bytes cho mỗi ký tự có dấu (ví dụ: 'ế', 'ặ', 'đ'). Bảng merge học từ tiếng Anh không có quy tắc gộp các byte tiếng Việt này, buộc tokenizer phải phát ra từng byte đơn lẻ."),
    ("Hệ quả nghiêm trọng trong Mô hình Ngôn ngữ lớn (LLM)", "• Chi phí gọi API: Người dùng tiếng Việt phải trả tiền gấp 3.5 lần cho cùng một đoạn văn bản.\n• Giới hạn Context Window: Cửa sổ ngữ cảnh bị chiếm dụng gấp 3.5 lần, làm giảm khả năng xử lý tài liệu dài.\n• Tốc độ sinh: Tốc độ suy luận (inference latency) bị chậm lại rõ rệt."),
    ("Cảnh báo phương pháp luận", "Không thể vội kết luận tiếng Việt luôn tốn token hơn tiếng Anh cho cùng nội dung vì hai tập Wikipedia V1 và E1 không phải là ngữ liệu song song (non-parallel corpus).")
]

for i, (head, body) in enumerate(cross_insights):
    p_h = tf_2x.paragraphs[0] if i == 0 else tf_2x.add_paragraph()
    p_h.text = f"• {head}:"
    p_h.font.name = FONT_HEADING
    p_h.font.size = Pt(8.5)
    p_h.font.bold = True
    p_h.font.color.rgb = ROSE_600 if "3.54" in head else BLUE_700
    p_h.space_before = Pt(3)
    
    p_b = tf_2x.add_paragraph()
    p_b.text = f"  {body}"
    p_b.font.name = FONT_BODY
    p_b.font.size = Pt(7.8)
    p_b.font.color.rgb = SLATE_600

# Right Side: Figure 5
add_card(s11, Inches(7.3), Inches(1.6), Inches(5.233), Inches(5.25), bg_color=WHITE, border_color=SLATE_200)
fig5_path = FIGS_DIR / "rq3_bytes_per_token.png"
if fig5_path.exists():
    s11.shapes.add_picture(str(fig5_path), Inches(7.45), Inches(1.75), width=Inches(4.933))

tx_cap5 = s11.shapes.add_textbox(Inches(7.45), Inches(6.3), Inches(4.933), Inches(0.45))
tf_cap5 = tx_cap5.text_frame
tf_cap5.word_wrap = True
tf_cap5.margin_left = tf_cap5.margin_right = tf_cap5.margin_top = tf_cap5.margin_bottom = 0
p_c5 = tf_cap5.paragraphs[0]
p_c5.text = "Hình 5: Byte/token qua 3 mức K. Chú ý đường E1→V1 nằm bẹp ở đáy (~1.3 B/token)."
p_c5.font.name = FONT_BODY
p_c5.font.size = Pt(8)
p_c5.font.color.rgb = SLATE_500
p_c5.alignment = PP_ALIGN.CENTER


# ==========================================================
# SLIDE 12: RQ3.C - BPE Training Algorithms & Data Structures
# ==========================================================
s12 = prs.slides.add_slide(blank_layout)
add_bg(s12)
add_header(s12, "KẾT QUẢ RQ3.C", "Tối ưu hóa Thuật toán Huấn luyện BPE: Đột phá Cấu trúc Dữ liệu", "So sánh 3 biến thể: Naive (quét lại), No-heap (cập nhật cục bộ) và Incremental Heap (lazy deletion)")
add_footer(s12, 12)

# 3 Algorithm Architecture Cards
trainers = [
    ("Naive Trainer", "Quét lại toàn bộ đoạn duy nhất", "Độ phức tạp: O(N + K · U)", ROSE_600, [
        "Cách hoạt động: Sau mỗi vòng merge, biến thể Naive duyệt lại toàn bộ danh sách các đoạn duy nhất (unique segments) để đếm lại tần suất mọi cặp ký hiệu.",
        "Điểm nghẽn thuật toán: Duyệt lặp qua hàng chục nghìn đoạn không hề bị ảnh hưởng bởi cặp vừa merge.",
        "Bộ nhớ: O(U + Pₜ) — Thấp nhưng lãng phí tài nguyên CPU nghiêm trọng.",
        "Hậu quả: Thời gian huấn luyện bùng nổ theo cấp số nhân khi tăng K."
    ]),
    ("No-Heap Trainer", "Cập nhật cục bộ bằng Linked-List", "Độ phức tạp: O(N + K · Pₜ)", AMBER_600, [
        "Cách hoạt động: Biểu diễn chuỗi token bằng Doubly Linked List. Duy trì Inverted Index từ cặp (a, b) tới danh sách các vị trí xuất hiện.",
        "Ưu điểm: Chỉ cập nhật tần suất của các cặp nằm ngay cạnh ranh giới bị thay thế (cập nhật cục bộ).",
        "Điểm nghẽn: Vẫn phải quét tuyến tính O(Pₜ) trên toàn bộ từ điển cặp hoạt động để tìm cặp có tần suất lớn nhất.",
        "Kết quả: Nhanh hơn Naive 5 - 15 lần, nhưng vẫn bị chậm ở K lớn."
    ]),
    ("Incremental Heap (Inc)", "Cập nhật cục bộ + Heap & Lazy Deletion", "Độ phức tạp: O(R log H)", EMERALD_600, [
        "Đột phá cấu trúc: Kết hợp cập nhật cục bộ với Min/Max-Heap lưu các phần tử `(-count, a, b)`.",
        "Kỹ thuật Xóa Lười (Lazy Deletion): Khi tần suất của một cặp thay đổi, không tốn chi phí tìm kiếm trong heap để sửa; thay vào đó, chỉ việc push entry mới vào heap.",
        "Chọn cực đại: Pop đỉnh heap và kiểm tra xem count có khớp với từ điển tần suất thực tế không; nếu cũ (stale) thì bỏ qua.",
        "Chi phí chọn max: Giảm ngoạn mục từ O(Pₜ) xuống O(log H)."
    ])
]

for idx, (title, sub, comp, col, points) in enumerate(trainers):
    c_left = Inches(0.8 + idx * 4.0)
    card = add_card(s12, c_left, Inches(1.6), Inches(3.733), Inches(5.25), bg_color=WHITE, border_color=SLATE_200)
    
    # Header badge
    hb = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left + Inches(0.18), Inches(1.8), Inches(3.373), Inches(0.68))
    hb.fill.solid()
    hb.fill.fore_color.rgb = col
    hb.line.fill.background()
    tf_hb = hb.text_frame
    tf_hb.word_wrap = True
    tf_hb.vertical_anchor = MSO_ANCHOR.MIDDLE
    p1 = tf_hb.paragraphs[0]
    p1.text = title
    p1.font.name = FONT_HEADING
    p1.font.size = Pt(11)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p1.alignment = PP_ALIGN.CENTER
    p2 = tf_hb.add_paragraph()
    p2.text = comp
    p2.font.name = FONT_BODY
    p2.font.size = Pt(8.5)
    p2.font.color.rgb = WHITE
    p2.alignment = PP_ALIGN.CENTER
    
    # Subtitle
    tx_sub = s12.shapes.add_textbox(c_left + Inches(0.18), Inches(2.55), Inches(3.373), Inches(0.35))
    tf_sub = tx_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_s = tf_sub.paragraphs[0]
    p_s.text = sub
    p_s.font.name = FONT_HEADING
    p_s.font.size = Pt(9)
    p_s.font.bold = True
    p_s.font.color.rgb = NAVY_900
    
    # Points
    tx_pts = s12.shapes.add_textbox(c_left + Inches(0.18), Inches(2.95), Inches(3.373), Inches(3.75))
    tf_pts = tx_pts.text_frame
    tf_pts.word_wrap = True
    tf_pts.margin_left = tf_pts.margin_right = tf_pts.margin_top = tf_pts.margin_bottom = 0
    for pt_idx, pt in enumerate(points):
        p = tf_pts.paragraphs[0] if pt_idx == 0 else tf_pts.add_paragraph()
        p.text = f"• {pt}"
        p.font.name = FONT_BODY
        p.font.size = Pt(8.2)
        p.font.color.rgb = SLATE_700
        p.space_before = Pt(4)


# ==========================================================
# SLIDE 13: RQ3.C - Empirical Training Speedup (Up to 104.7x)
# ==========================================================
s13 = prs.slides.add_slide(blank_layout)
add_bg(s13)
add_header(s13, "KẾT QUẢ RQ3.C", "Thực nghiệm Thời gian Huấn luyện: Tăng tốc Lên tới 104.72×", "Đo lường trên Full Corpus 1 MiB đảm bảo tính nhất quán tuyệt đối về danh sách merge")
add_footer(s13, 13)

# Left Side: Table VI
add_card(s13, Inches(0.8), Inches(1.6), Inches(6.6), Inches(5.25), bg_color=WHITE, border_color=SLATE_200)

tx_t6 = s13.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(6.2), Inches(0.35))
tf_t6 = tx_t6.text_frame
p = tf_t6.paragraphs[0]
p.text = "Bảng VI: Thời gian train full 1 MiB (ms) và Tỷ số tăng tốc (Speedup)"
p.font.name = FONT_HEADING
p.font.size = Pt(10.5)
p.font.bold = True
p.font.color.rgb = NAVY_900

headers_t6 = ["Train", "K", "Naive (ms)", "Noheap (ms)", "Inc (ms)", "Naive / Inc", "Noheap / Inc"]
rows_t6 = [
    ["V1", "256", "11,265.3", "784.8", "272.1", "41.40×", "2.88×"],
    ["V1", "1024", "22,819.3", "2,542.6", "687.3", "33.20×", "3.70×"],
    ["V1", "3840", "78,275.2", "12,748.9", "747.5", "104.72×", "17.06×"],
    ["E1", "256", "29,447.5", "2,195.8", "1,657.9", "17.76×", "1.32×"],
    ["E1", "1024", "56,807.8", "6,712.4", "1,888.0", "30.09×", "3.56×"],
    ["E1", "3840", "193,328.0", "24,234.9", "2,247.5", "86.02×", "10.78×"]
]
widths_t6 = [Inches(0.7), Inches(0.6), Inches(1.2), Inches(1.2), Inches(1.0), Inches(1.1), Inches(1.1)]
add_table_custom(s13, Inches(1.0), Inches(2.12), Inches(6.2), Inches(2.1), headers_t6, rows_t6, widths_t6, highlight_idx=2)

# Quantitative Analysis
tx_q6 = s13.shapes.add_textbox(Inches(1.0), Inches(4.35), Inches(6.2), Inches(2.35))
tf_q6 = tx_q6.text_frame
tf_q6.word_wrap = True
tf_q6.margin_left = tf_q6.margin_right = tf_q6.margin_top = tf_q6.margin_bottom = 0

q_points = [
    ("Kỷ lục tăng tốc 104.72× tại V1 (K=3840)", "Thuật toán Naive mất tới 78.3 giây (~1.3 phút), trong khi Incremental Heap hoàn thành chỉ trong 0.75 giây!"),
    ("E1 K=3840: Naive mất hơn 3.2 phút (193s) → Inc chỉ 2.25 giây", "Tăng tốc 86.02× giúp tiết kiệm tài nguyên tính toán khổng lồ khi huấn luyện các bộ từ điển subword quy mô lớn."),
    ("Tăng tốc Noheap so với Inc", "Inc nhanh hơn Noheap từ 1.32× đến 17.06×, chứng minh việc thay thế quét tuyến tính O(Pₜ) bằng Heap O(log H) mang lại lợi ích bứt phá ở K lớn."),
    ("Bảo đảm tính chính xác toán học", "Toàn bộ 3 biến thể sinh ra cùng một danh sách merge chính xác 100% trên cùng tập dữ liệu.")
]

for i, (title, desc) in enumerate(q_points):
    p_t = tf_q6.paragraphs[0] if i == 0 else tf_q6.add_paragraph()
    p_t.text = f"• {title}:"
    p_t.font.name = FONT_HEADING
    p_t.font.size = Pt(8.5)
    p_t.font.bold = True
    p_t.font.color.rgb = EMERALD_700 if "104.72" in title else BLUE_700
    p_t.space_before = Pt(2)
    
    p_b = tf_q6.add_paragraph()
    p_b.text = f"  {desc}"
    p_b.font.name = FONT_BODY
    p_b.font.size = Pt(7.8)
    p_b.font.color.rgb = SLATE_600

# Right Side: Figures 6 & 7
add_card(s13, Inches(7.7), Inches(1.6), Inches(4.833), Inches(5.25), bg_color=WHITE, border_color=SLATE_200)
fig6_path = FIGS_DIR / "rq3_train_ms.png"
fig7_path = FIGS_DIR / "rq3_training_memory.png"

if fig6_path.exists():
    s13.shapes.add_picture(str(fig6_path), Inches(7.85), Inches(1.75), width=Inches(4.533), height=Inches(2.35))
if fig7_path.exists():
    s13.shapes.add_picture(str(fig7_path), Inches(7.85), Inches(4.35), width=Inches(4.533), height=Inches(2.35))


# ==========================================================
# SLIDE 14: Quality Assurance & Decoder Hardening
# ==========================================================
s14 = prs.slides.add_slide(blank_layout)
add_bg(s14)
add_header(s14, "KIỂM THỬ HỆ THỐNG", "Kiểm thử Phần mềm Toàn diện & Gia cố Bộ Giải mã (Hardening)", "761 Pytest Passed 100% · Xử lý trường hợp biên cực trị và phát hiện dữ liệu lỗi")
add_footer(s14, 14)

# 4 Testing Pillars
pillars = [
    ("761 / 761 Pytest Passed", "Toàn diện & Tự động hóa", EMERALD_600, [
        "100% bộ kiểm thử tự động vượt qua trong 28.26 giây.",
        "Bao phủ toàn bộ các module: RLE, Huffman, LZW, BPE Trainer (3 biến thể), Codec Container và Analysis Scripts.",
        "Kiểm thử tính tương đương (Equivalence Oracle): Khẳng định Naive, Noheap và Inc sinh cùng danh sách merge trên mọi tập input."
    ]),
    ("Gia cố Decoder (Hardening)", "Bảo mật & Tính mạnh mẽ", BLUE_600, [
        "LZW Hardening: Kiểm tra và từ chối nghiêm ngặt 15/15 giá trị padding bẩn ở nibble cuối; từ chối mã vượt dải [0, 4095].",
        "Huffman Hardening: Phát hiện và ném ngoại lệ khi cây mã vượt khả năng biểu diễn (oversubscribed code lengths), payload thừa hoặc bit padding khác 0.",
        "BPE Hardening: Kiểm tra định dạng bảng merge, ID token ngoài từ điển, khớp kích thước gốc."
    ]),
    ("Trường hợp Biên Cực trị (Edge Cases)", "Độ bền bỉ của Codec", INDIGO_600, [
        "Đầu vào rỗng (Empty stream, 0 byte): Trả về container tối thiểu, giải nén ra 0 byte mà không crash.",
        "Đầu vào 1 byte & 64 KiB cùng 1 byte: Kiểm tra giới hạn co giãn của RLE và cây suy biến của Huffman.",
        "Chuỗi 256 byte đầy đủ: Kiểm tra phân bố đều tuyệt đối.",
        "Chuỗi có chu kỳ phức tạp: 'ABABABA' và 'aaabdaaabac' với K=3 kiểm tra cơ chế giải quyết xung đột tần suất (tie-breaking)."
    ]),
    ("Toàn vẹn Dữ liệu (Integrity)", "Đối chiếu Mã băm SHA-256", CYAN_600, [
        "Mọi lượt đo timing và đo memory đều đối chiếu SHA-256 đầy đủ sau khi giải nén.",
        "Hồi quy bộ nhớ nghiêm ngặt: Nếu chỉ riêng lượt đo tracemalloc bị sai giải nén, pipeline lập tức báo lỗi và dừng toàn bộ hệ thống.",
        "Tự động giải phóng tài nguyên: Đảm bảo dừng tracemalloc ngay cả khi codec ném ngoại lệ."
    ])
]

for idx, (title, sub, col, items) in enumerate(pillars):
    col_idx = idx % 2
    row_idx = idx // 2
    c_left = Inches(0.8 + col_idx * 6.0)
    c_top = Inches(1.6 + row_idx * 2.7)
    
    card = add_card(s14, c_left, c_top, Inches(5.733), Inches(2.5), bg_color=WHITE, border_color=SLATE_200)
    
    # Header badge
    pb = s14.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left + Inches(0.18), c_top + Inches(0.15), Inches(5.373), Inches(0.38))
    pb.fill.solid()
    pb.fill.fore_color.rgb = col
    pb.line.fill.background()
    tf_pb = pb.text_frame
    tf_pb.word_wrap = True
    tf_pb.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf_pb.paragraphs[0]
    p.text = f"{title} — {sub}"
    p.font.name = FONT_HEADING
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER
    
    # Text items
    tx_items = s14.shapes.add_textbox(c_left + Inches(0.18), c_top + Inches(0.6), Inches(5.373), Inches(1.8))
    tf_it = tx_items.text_frame
    tf_it.word_wrap = True
    tf_it.margin_left = tf_it.margin_right = tf_it.margin_top = tf_it.margin_bottom = 0
    for i_idx, item in enumerate(items):
        p_it = tf_it.paragraphs[0] if i_idx == 0 else tf_it.add_paragraph()
        p_it.text = f"• {item}"
        p_it.font.name = FONT_BODY
        p_it.font.size = Pt(8.3)
        p_it.font.color.rgb = NAVY_900 if i_idx == 0 else SLATE_600
        p_it.space_before = Pt(3)


# ==========================================================
# SLIDE 15: Limitations & Scientific Integrity
# ==========================================================
s15 = prs.slides.add_slide(blank_layout)
add_bg(s15)
add_header(s15, "THẢO LUẬN & GIỚI HẠN", "Giới hạn Nghiên cứu & Tính Trung thực Khoa học", "Minh bạch về phạm vi thực nghiệm, điều kiện môi trường và các giả định phương pháp luận")
add_footer(s15, 15)

# 4 Limitations in 2x2 layout
limits = [
    ("1. Ngữ liệu V1/E1 Không Song Song (Non-parallel)", ROSE_600, [
        "V1 và E1 được lấy từ các bài viết độc lập trên Wikipedia Tiếng Việt và Tiếng Anh.",
        "Hệ quả: Khác biệt về số token giữa hai ngôn ngữ phản ánh đồng thời cả cấu trúc ngôn ngữ lẫn chủ đề nội dung của bài viết.",
        "Kết luận thận trọng: Không thể suy rộng thành khẳng định tiếng Việt luôn tốn token hơn tiếng Anh cho cùng một ngữ nghĩa."
    ]),
    ("2. Cỡ Mẫu V1 trong RQ1 & Sai số Môi trường", AMBER_600, [
        "RQ1 chỉ thu thập 1 mẫu prefix Wikipedia tiếng Việt cho mỗi quy mô kích thước.",
        "Dải seed của dữ liệu tổng hợp C1-C3 chỉ phản ánh biến thiên giữa các mẫu dữ liệu, không phải khoảng tin cậy của cùng một input.",
        "Nhiễu tải hệ thống: Một số phép đo thực hiện ở các phiên khác nhau, sai khác tải nền hệ điều hành có thể tạo sai số nhỏ."
    ]),
    ("3. Huấn luyện Naive Chỉ Đo Một Lượt", BLUE_600, [
        "Do biến thể Naive chạy rất lâu ở K=3840 (lên tới hơn 3 phút), nhóm chỉ đo 1 lượt thay vì lấy trung vị 3 lượt.",
        "Tính trung thực: Nhóm giữ nguyên số đo thực tế, không nội suy hay 'làm đẹp' dữ liệu để tạo khoảng tin cậy giả.",
        "Tỷ số tăng tốc (17.76× – 104.72×) là kết quả quan sát thực nghiệm, không phải cam kết phổ quát cho mọi cấu hình."
    ]),
    ("4. Chi phí Bộ nhớ của Huffman là do Cài đặt Python", CYAN_600, [
        "Đỉnh cấp phát 275 MB của Huffman là do biểu diễn chuỗi bit trung gian dạng ký tự trong Python (`bitstring`), không phải giới hạn của thuật toán.",
        "Nếu được cài đặt bằng C hoặc đóng gói bitmask mảng byte trực tiếp, mức tiêu thụ bộ nhớ của Huffman sẽ thấp hơn rất nhiều.",
        "Bộ nhớ `tracemalloc` chỉ phản ánh heap Python, không đo toàn bộ footprint RAM hệ điều hành."
    ])
]

for idx, (title, col, bullets) in enumerate(limits):
    col_idx = idx % 2
    row_idx = idx // 2
    c_left = Inches(0.8 + col_idx * 6.0)
    c_top = Inches(1.6 + row_idx * 2.7)
    
    card = add_card(s15, c_left, c_top, Inches(5.733), Inches(2.5), bg_color=WHITE, border_color=SLATE_200)
    
    # Title
    tx_t = s15.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.15), Inches(5.333), Inches(0.35))
    tf_t = tx_t.text_frame
    p_t = tf_t.paragraphs[0]
    p_t.text = title
    p_t.font.name = FONT_HEADING
    p_t.font.size = Pt(11)
    p_t.font.bold = True
    p_t.font.color.rgb = col
    
    # Bullets
    tx_b = s15.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.55), Inches(5.333), Inches(1.85))
    tf_b = tx_b.text_frame
    tf_b.word_wrap = True
    tf_b.margin_left = tf_b.margin_right = tf_b.margin_top = tf_b.margin_bottom = 0
    for b_idx, bullet in enumerate(bullets):
        p = tf_b.paragraphs[0] if b_idx == 0 else tf_b.add_paragraph()
        p.text = f"• {bullet}"
        p.font.name = FONT_BODY
        p.font.size = Pt(8.3)
        p.font.color.rgb = SLATE_700
        p.space_before = Pt(3)


# ==========================================================
# SLIDE 16: Conclusions & Key Contributions
# ==========================================================
s16 = prs.slides.add_slide(blank_layout)
add_bg(s16)
add_header(s16, "TỔNG KẾT", "Kết luận & 3 Đóng góp Cốt lõi của Đề tài", "Học phần CSD203 — Data Structures and Algorithms with Python · Đề tài 4")
add_footer(s16, 16)

# 3 Major Contributions
contribs = [
    ("ĐÓNG GÓP 1 — LÝ THUYẾT NÉN & CẤU TRÚC DỮ LIỆU", BLUE_600, [
        "Xác nhận thực nghiệm sự phụ thuộc mật thiết giữa bản chất dư thừa và thuật toán nén: RLE tối ưu cho run dài, Huffman bất biến với hoán vị thứ tự, LZW phụ thuộc chuỗi.",
        "Chứng minh H₀/8 không phải là cận dưới tuyệt đối cho mọi codec; LZW hoàn toàn có thể vượt qua H₀/8 khi dữ liệu có tương quan chuỗi bậc cao.",
        "Chỉ ra và giải mã hiện tượng đóng băng từ điển (frozen dictionary) khiến LZW bị phình to (>1.0) khi gặp run byte quá sớm trên tệp lớn."
    ]),
    ("ĐÓNG GÓP 2 — ĐÁNH GIÁ TOKENIZER LLM & ĐA NGỮ", ROSE_600, [
        "Tách bạch rõ ràng giữa hai vai trò của BPE: Codec nén độc lập (chịu overhead bảng merge) và Tokenizer chia sẻ từ điển (chỉ tính payload token).",
        "Chứng minh tại K=3840, BPE cùng ngôn ngữ nén tốt hơn LZW tới 32.6% trên Tiếng Việt và 13.7% trên Tiếng Anh.",
        "Cảnh báo định lượng hiện tượng lạm phát token gấp 3.54 lần khi áp dụng tokenizer tiếng Anh lên tiếng Việt; nhấn mạnh tầm quan trọng của việc xây dựng tokenizer tiếng Việt bản địa cho LLM."
    ]),
    ("ĐÓNG GÓP 3 — THIẾT KẾ CẤU TRÚC DỮ LIỆU TỐI ƯU", EMERALD_600, [
        "Hiện thực thành công biến thể Incremental Heap với kỹ thuật Lazy Deletion, giảm độ phức tạp chọn cực đại từ O(Pₜ) xuống O(log H).",
        "Đạt tỷ số tăng tốc ngoạn mục lên tới 104.72× so với Naive và 17.06× so với Noheap trên ngữ liệu 1 MiB.",
        "Bảo đảm 100% tính tương đương toán học về danh sách merge và vượt qua toàn bộ 761/761 ca kiểm thử phần mềm nghiêm ngặt."
    ])
]

for idx, (title, col, items) in enumerate(contribs):
    c_top = Inches(1.6 + idx * 1.72)
    card = add_card(s16, Inches(0.8), c_top, Inches(11.733), Inches(1.58), bg_color=WHITE, border_color=SLATE_200)
    
    # Left colored bar
    bar = s16.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), c_top, Inches(0.2), Inches(1.58))
    bar.fill.solid()
    bar.fill.fore_color.rgb = col
    bar.line.fill.background()
    
    # Title
    tx_t = s16.shapes.add_textbox(Inches(1.2), c_top + Inches(0.1), Inches(11.1), Inches(0.3))
    tf_t = tx_t.text_frame
    p_t = tf_t.paragraphs[0]
    p_t.text = title
    p_t.font.name = FONT_HEADING
    p_t.font.size = Pt(10.5)
    p_t.font.bold = True
    p_t.font.color.rgb = col
    
    # Items
    tx_i = s16.shapes.add_textbox(Inches(1.2), c_top + Inches(0.38), Inches(11.1), Inches(1.1))
    tf_i = tx_i.text_frame
    tf_i.word_wrap = True
    tf_i.margin_left = tf_i.margin_right = tf_i.margin_top = tf_i.margin_bottom = 0
    for i_idx, it in enumerate(items):
        p = tf_i.paragraphs[0] if i_idx == 0 else tf_i.add_paragraph()
        p.text = f"• {it}"
        p.font.name = FONT_BODY
        p.font.size = Pt(8.2)
        p.font.color.rgb = SLATE_700
        p.space_before = Pt(2)


# ==========================================================
# SLIDE 17: Thank You & Q&A (Dark Navy Closing Slide)
# ==========================================================
s17 = prs.slides.add_slide(blank_layout)
add_bg(s17, NAVY_900)

# Center Box
tx_c = s17.shapes.add_textbox(Inches(1.5), Inches(1.5), Inches(10.333), Inches(2.2))
tf_c = tx_c.text_frame
tf_c.word_wrap = True
tf_c.margin_left = tf_c.margin_right = tf_c.margin_top = tf_c.margin_bottom = 0

p1 = tf_c.paragraphs[0]
p1.text = "CẢM ƠN THẦY CÔ VÀ CÁC BẠN ĐÃ LẮNG NGHE!"
p1.font.name = FONT_HEADING
p1.font.size = Pt(28)
p1.font.bold = True
p1.font.color.rgb = WHITE
p1.alignment = PP_ALIGN.CENTER

p2 = tf_c.add_paragraph()
p2.text = "PHIÊN HỎI & ĐÁP — QUESTIONS & ANSWERS (Q&A)"
p2.font.name = FONT_HEADING
p2.font.size = Pt(16)
p2.font.bold = True
p2.font.color.rgb = BLUE_500
p2.alignment = PP_ALIGN.CENTER
p2.space_before = Pt(8)

p3 = tf_c.add_paragraph()
p3.text = "Học phần CSD203 — Data Structures and Algorithms with Python · Đề tài 4: Nén Dữ Liệu & BPE Tokenizer"
p3.font.name = FONT_BODY
p3.font.size = Pt(11)
p3.font.color.rgb = SLATE_400
p3.alignment = PP_ALIGN.CENTER
p3.space_before = Pt(6)

# Bottom Info Cards
info_cards = [
    ("Kho Lưu Trữ & Tái Lập", [
        "Mã nguồn đầy đủ: RLE, Huffman, LZW, BPE (3 trainers)",
        "Kiểm thử: python -m pytest -q (761 passed)",
        "Báo cáo & Phân tích: python -m rq3.analyze_rq3"
    ]),
    ("Nhóm Thực Hiện — Nhóm 4 (AI21B)", [
        "Trần Châu Hoàng Nam (Trưởng nhóm) — QE210145",
        "Nguyễn Trí Viễn — QE210041 · Phạm Minh Tiến — QE210079",
        "Hoàng Đức Khánh — SE180114 · Trương Đình Tân — QE210065 · Dương Quốc Thịnh — QE210121"
    ])
]

for idx, (card_title, lines) in enumerate(info_cards):
    c_left = Inches(1.8 + idx * 5.0)
    card = s17.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left, Inches(4.2), Inches(4.7), Inches(2.3))
    card.fill.solid()
    card.fill.fore_color.rgb = SLATE_800
    card.line.color.rgb = SLATE_700
    card.line.width = Pt(1)
    
    txbox = s17.shapes.add_textbox(c_left + Inches(0.2), Inches(4.35), Inches(4.3), Inches(2.0))
    tf = txbox.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    
    p_t = tf.paragraphs[0]
    p_t.text = card_title
    p_t.font.name = FONT_HEADING
    p_t.font.size = Pt(11)
    p_t.font.bold = True
    p_t.font.color.rgb = CYAN_600
    
    for l_idx, line in enumerate(lines):
        p_l = tf.add_paragraph()
        p_l.text = f"• {line}"
        p_l.font.name = FONT_BODY
        p_l.font.size = Pt(8.5)
        p_l.font.color.rgb = WHITE if idx == 1 and l_idx == 0 else SLATE_300
        p_l.space_before = Pt(4)


# Save presentation
prs.save(str(OUTPUT_PPTX))
print(f"Presentation successfully created at: {OUTPUT_PPTX}")
