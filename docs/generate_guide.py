"""
BTU Virtual University – Working Guide PDF Generator
Run: python docs/generate_guide.py
Outputs: BTU_Working_Guide.pdf
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    HRFlowable,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.colors import HexColor, Color
from reportlab.platypus import KeepTogether

# ── Brand palette ─────────────────────────────────────────────────────────────
NAVY       = HexColor("#0D1B2A")   # deep navy – cover bg
INDIGO     = HexColor("#1B3A6B")   # section headers
ELECTRIC   = HexColor("#3D8EF0")   # accents / links
TEAL       = HexColor("#00BFA5")   # highlights
AMBER      = HexColor("#FFB300")   # badges / warnings
CORAL      = HexColor("#FF5C5C")   # danger / important
WHITE      = HexColor("#FFFFFF")
LIGHT_BG   = HexColor("#F4F7FC")   # light section backgrounds
LIGHT_GRAY = HexColor("#E8EDF4")
MID_GRAY   = HexColor("#8899AA")
DARK_TEXT  = HexColor("#1A2740")

# Code block colours (VS Code Dark+ inspired)
CODE_BG    = HexColor("#1E1E2E")
CODE_KW    = HexColor("#569CD6")   # keywords (blue)
CODE_STR   = HexColor("#CE9178")   # strings (orange)
CODE_COMM  = HexColor("#6A9955")   # comments (green)
CODE_FN    = HexColor("#DCDCAA")   # function names (yellow)
CODE_NUM   = HexColor("#B5CEA8")   # numbers (light green)
CODE_TEXT  = HexColor("#D4D4D4")   # default text (light gray)
CODE_HL    = HexColor("#264F78")   # highlighted line bg

W, H = A4


# ── Helper: rounded coloured box Flowable ─────────────────────────────────────
class ColorBox(Flowable):
    def __init__(self, width, height, fill_color, radius=6):
        super().__init__()
        self.width = width
        self.height = height
        self.fill_color = fill_color
        self.radius = radius

    def draw(self):
        self.canv.setFillColor(self.fill_color)
        self.canv.roundRect(0, 0, self.width, self.height, self.radius, fill=1, stroke=0)


class SectionDivider(Flowable):
    """Decorative horizontal rule with dot accent."""
    def __init__(self, width, color=ELECTRIC, thickness=2):
        super().__init__()
        self.width = width
        self.height = thickness + 8
        self.color = color
        self.thickness = thickness

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.thickness / 2, self.width * 0.6, self.thickness / 2)
        self.canv.setFillColor(self.color)
        self.canv.circle(self.width * 0.6 + 4, self.thickness / 2, 3, fill=1, stroke=0)


class TOCAnchor(Flowable):
    """Zero-height invisible flowable that registers a TOC entry via afterFlowable."""
    def __init__(self, text: str, level: int = 0):
        Flowable.__init__(self)
        self._toc_text  = text
        self._toc_level = level
        self._toc_key   = "toc_" + text[:50].replace(" ", "_").replace(".", "")
        self.width  = 0
        self.height = 0

    def draw(self):
        self.canv.bookmarkPage(self._toc_key)


# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["cover_title"] = ParagraphStyle(
        "cover_title",
        fontName="Helvetica-Bold",
        fontSize=34,
        textColor=WHITE,
        alignment=TA_CENTER,
        leading=42,
        spaceAfter=10,
    )
    styles["cover_subtitle"] = ParagraphStyle(
        "cover_subtitle",
        fontName="Helvetica",
        fontSize=15,
        textColor=HexColor("#A0C4FF"),
        alignment=TA_CENTER,
        leading=22,
        spaceAfter=6,
    )
    styles["cover_tag"] = ParagraphStyle(
        "cover_tag",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=TEAL,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    styles["h1"] = ParagraphStyle(
        "h1",
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=WHITE,
        alignment=TA_LEFT,
        leading=28,
        spaceBefore=18,
        spaceAfter=6,
    )
    styles["h2"] = ParagraphStyle(
        "h2",
        fontName="Helvetica-Bold",
        fontSize=15,
        textColor=INDIGO,
        leading=20,
        spaceBefore=14,
        spaceAfter=4,
        borderPad=(0, 0, 2, 0),
    )
    styles["h3"] = ParagraphStyle(
        "h3",
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=ELECTRIC,
        leading=16,
        spaceBefore=10,
        spaceAfter=3,
    )
    styles["body"] = ParagraphStyle(
        "body",
        fontName="Helvetica",
        fontSize=10,
        textColor=DARK_TEXT,
        leading=16,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
    )
    styles["body_left"] = ParagraphStyle(
        "body_left",
        fontName="Helvetica",
        fontSize=10,
        textColor=DARK_TEXT,
        leading=16,
        spaceAfter=4,
    )
    styles["bullet"] = ParagraphStyle(
        "bullet",
        fontName="Helvetica",
        fontSize=10,
        textColor=DARK_TEXT,
        leading=15,
        leftIndent=14,
        spaceAfter=3,
        bulletIndent=4,
        bulletText="•",
    )
    styles["note"] = ParagraphStyle(
        "note",
        fontName="Helvetica-Oblique",
        fontSize=9,
        textColor=MID_GRAY,
        leading=13,
        spaceAfter=4,
    )
    styles["code_label"] = ParagraphStyle(
        "code_label",
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=TEAL,
        spaceAfter=2,
    )
    styles["caption"] = ParagraphStyle(
        "caption",
        fontName="Helvetica-Oblique",
        fontSize=8,
        textColor=MID_GRAY,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    styles["tag_text"] = ParagraphStyle(
        "tag_text",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=NAVY,
    )
    return styles


# ── Code block builder ────────────────────────────────────────────────────────
def code_block(code: str, label: str = "", styles: dict = None,
               chunk_lines: int = 38) -> list:
    """Returns a list of flowables representing a styled code block.

    Large blocks are automatically split into chunks of ``chunk_lines`` lines
    so they can span page breaks (single-row Tables cannot be split by
    reportlab's layout engine).
    """
    content_w = W - 4 * cm

    pre_style = ParagraphStyle(
        "code_pre",
        fontName="Courier-Bold",
        fontSize=9,
        textColor=WHITE,
        leading=14,
        leftIndent=0,
        rightIndent=0,
        spaceBefore=0,
        spaceAfter=0,
    )

    def _make_table(chunk: str, is_first: bool, is_last: bool) -> Table:
        pre = Preformatted(chunk, pre_style)
        t = Table([[pre]], colWidths=[content_w])
        top_pad    = 10 if is_first else 2
        bottom_pad = 10 if is_last  else 2
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), CODE_BG),
            ("TOPPADDING",    (0, 0), (-1, -1), top_pad),
            ("BOTTOMPADDING", (0, 0), (-1, -1), bottom_pad),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
            ("LINECOLOR",     (0, 0), (-1, -1), HexColor("#3A3A5C")),
            ("BOX",           (0, 0), (-1, -1), 1, HexColor("#3A3A5C")),
        ]))
        return t

    items = []
    if label and styles:
        items.append(Paragraph(label, styles["code_label"]))

    lines = code.split("\n")
    chunks = [lines[i:i + chunk_lines] for i in range(0, len(lines), chunk_lines)]
    total  = len(chunks)
    for idx, chunk in enumerate(chunks):
        items.append(_make_table("\n".join(chunk), idx == 0, idx == total - 1))

    items.append(Spacer(1, 6))
    return items


# ── Inline badge ──────────────────────────────────────────────────────────────
def badge(text: str, bg: HexColor = ELECTRIC, fg: HexColor = WHITE) -> str:
    """Returns HTML-like markup for a small inline badge (Paragraph only)."""
    return (
        f'<font color="#{bg.hexval()[2:]}" size="9"><b> {text} </b></font>'
    )


# ── Table helpers ─────────────────────────────────────────────────────────────
def styled_table(data: list[list], col_widths: list[float], header=True) -> Table:
    t = Table(data, colWidths=col_widths)
    ts = [
        ("BACKGROUND", (0, 0), (-1, 0 if header else -1), INDIGO if header else LIGHT_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE if header else DARK_TEXT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, LIGHT_GRAY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, HexColor("#EEF3FB")]),
    ]
    t.setStyle(TableStyle(ts))
    return t


# ── Page templates ────────────────────────────────────────────────────────────
class BTUDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2 * cm,
        )
        self.page_templates_setup()

    def page_templates_setup(self):
        content_w = W - 4 * cm

        # ── Cover page ────────────────────────────────────────────
        cover_frame = Frame(0, 0, W, H, leftPadding=0, bottomPadding=0,
                            rightPadding=0, topPadding=0)
        cover_template = PageTemplate(
            id="cover",
            frames=[cover_frame],
            onPage=self._draw_cover_bg,
        )

        # ── Content pages ─────────────────────────────────────────
        content_frame = Frame(
            2 * cm, 2 * cm,
            content_w, H - 4.8 * cm,
            leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0,
        )
        content_template = PageTemplate(
            id="content",
            frames=[content_frame],
            onPage=self._draw_content_header_footer,
        )
        self.addPageTemplates([cover_template, content_template])

    def afterFlowable(self, flowable):
        """Hook called after each flowable is drawn – used to register TOC entries."""
        if isinstance(flowable, TOCAnchor):
            self.notify(
                "TOCEntry",
                (flowable._toc_level, flowable._toc_text, self.page, flowable._toc_key),
            )

    def _draw_cover_bg(self, canvas, doc):
        canvas.saveState()
        # Deep navy background
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, W, H, fill=1, stroke=0)
        # Electric gradient bar – top
        canvas.setFillColor(INDIGO)
        canvas.rect(0, H - 1.2 * cm, W, 1.2 * cm, fill=1, stroke=0)
        # Teal accent left strip
        canvas.setFillColor(TEAL)
        canvas.rect(0, 0, 0.5 * cm, H, fill=1, stroke=0)
        # Electric bottom bar
        canvas.setFillColor(ELECTRIC)
        canvas.rect(0, 0, W, 0.8 * cm, fill=1, stroke=0)
        # Decorative circles (design element)
        canvas.setFillColor(HexColor("#1B3A6B"))
        canvas.circle(W - 3 * cm, H - 4 * cm, 5 * cm, fill=1, stroke=0)
        canvas.setFillColor(HexColor("#0D2444"))
        canvas.circle(W - 2 * cm, H - 5 * cm, 3.5 * cm, fill=1, stroke=0)
        canvas.restoreState()

    def _draw_content_header_footer(self, canvas, doc):
        canvas.saveState()
        # Header bar
        canvas.setFillColor(INDIGO)
        canvas.rect(0, H - 1.8 * cm, W, 1.8 * cm, fill=1, stroke=0)
        # Teal left accent
        canvas.setFillColor(TEAL)
        canvas.rect(0, H - 1.8 * cm, 0.5 * cm, 1.8 * cm, fill=1, stroke=0)
        # Header text
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(WHITE)
        canvas.drawString(1.2 * cm, H - 1.1 * cm, "BTU Virtual University")
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(HexColor("#A0C4FF"))
        canvas.drawRightString(W - 2 * cm, H - 1.1 * cm, "End-to-End Working Guide")

        # Footer
        canvas.setFillColor(LIGHT_GRAY)
        canvas.rect(0, 0, W, 1.2 * cm, fill=1, stroke=0)
        canvas.setFillColor(ELECTRIC)
        canvas.rect(0, 0, 0.5 * cm, 1.2 * cm, fill=1, stroke=0)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MID_GRAY)
        canvas.drawString(1.2 * cm, 0.45 * cm,
                          "Multi-Agentic AI Framework  •  FastAPI + Anthropic Claude")
        canvas.drawRightString(W - 2 * cm, 0.45 * cm, f"Page {doc.page}")
        canvas.restoreState()


# ── Section header (coloured band) ───────────────────────────────────────────
def section_header(title: str, styles: dict, sub: str = "") -> list:
    """A full-width indigo banner for major sections."""
    items = [Spacer(1, 8)]
    # Build as a 1-row table (gives us background fill across full width)
    content_w = W - 4 * cm
    title_para = Paragraph(title, styles["h1"])
    sub_para = Paragraph(sub, ParagraphStyle(
        "sh_sub", fontName="Helvetica", fontSize=10,
        textColor=HexColor("#A0C4FF"), spaceAfter=0,
    )) if sub else Spacer(1, 0)

    t = Table([[title_para], [sub_para]], colWidths=[content_w])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), INDIGO),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ]))
    items.append(t)
    items.append(Spacer(1, 10))
    return items


# ── Info box ──────────────────────────────────────────────────────────────────
def info_box(text: str, styles: dict, color: HexColor = ELECTRIC, icon: str = "ℹ") -> list:
    content_w = W - 4 * cm
    p = Paragraph(f"<b>{icon}</b>  {text}", ParagraphStyle(
        "ib", fontName="Helvetica", fontSize=9.5,
        textColor=DARK_TEXT, leading=14,
    ))
    t = Table([[p]], colWidths=[content_w - 0.4 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#EBF5FB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINECOLOR", (0, 0), (0, -1), color),
        ("LINEBEFORE", (0, 0), (0, -1), 4, color),
    ]))
    return [t, Spacer(1, 6)]


# ── Build PDF ─────────────────────────────────────────────────────────────────
def build_pdf(output_path: str):
    doc = BTUDoc(output_path)
    styles = make_styles()
    content_w = W - 4 * cm
    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(NextPageTemplate("cover"))
    story.append(Spacer(1, 4.5 * cm))
    story.append(Paragraph("BTU Virtual University", styles["cover_title"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("End-to-End Working Guide", ParagraphStyle(
        "cov2", fontName="Helvetica-Bold", fontSize=20,
        textColor=TEAL, alignment=TA_CENTER, spaceAfter=6,
    )))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(
        "Multi-Agentic AI Framework  ·  3-Tier Architecture",
        styles["cover_subtitle"],
    ))
    story.append(Spacer(1, 1.6 * cm))

    # Feature tags row
    tags_data = [
        [
            Paragraph("AGENTIC RAG", styles["cover_tag"]),
            Paragraph("LIBRARY", styles["cover_tag"]),
            Paragraph("DOUBT CLEARING", styles["cover_tag"]),
            Paragraph("GAMIFICATION", styles["cover_tag"]),
        ]
    ]
    tags_table = Table(tags_data, colWidths=[4 * cm] * 4)
    tags_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#112244")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINECOLOR", (0, 0), (-1, -1), HexColor("#1B3A6B")),
        ("BOX", (0, 0), (-1, -1), 1, TEAL),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#1B3A6B")),
    ]))
    story.append(tags_table)

    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph(
        "FastAPI  ·  Anthropic Claude  ·  sentence-transformers  ·  FAISS  ·  PostgreSQL  ·  Vercel",
        ParagraphStyle("tech", fontName="Helvetica", fontSize=10,
                       textColor=MID_GRAY, alignment=TA_CENTER),
    ))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("v2.1  —  2026", ParagraphStyle(
        "ver", fontName="Helvetica", fontSize=9,
        textColor=HexColor("#445566"), alignment=TA_CENTER,
    )))

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 2 – TABLE OF CONTENTS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(NextPageTemplate("content"))
    story.append(PageBreak())

    cw = W - 4 * cm

    # TOC header banner
    toc_title_para = Paragraph("Table of Contents", ParagraphStyle(
        "toc_banner_title", fontName="Helvetica-Bold", fontSize=22,
        textColor=WHITE, alignment=TA_CENTER, leading=28,
    ))
    toc_banner = Table([[toc_title_para]], colWidths=[cw])
    toc_banner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), INDIGO),
        ("TOPPADDING",    (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("LINEBELOW",     (0, -1), (-1, -1), 4, TEAL),
    ]))
    story.append(toc_banner)
    story.append(Spacer(1, 14))

    # Auto-generated TOC (filled by multiBuild second pass)
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOCLevel0",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=DARK_TEXT,
            leading=18,
            leftIndent=0,
            spaceBefore=6,
            spaceAfter=2,
        ),
        ParagraphStyle(
            "TOCLevel1",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=MID_GRAY,
            leading=14,
            leftIndent=16,
            spaceBefore=2,
            spaceAfter=1,
        ),
    ]
    toc.dotsMinLevel = 0
    toc.rightColumnWidth = 1 * cm
    story.append(toc)

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 – ARCHITECTURE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(TOCAnchor("1. System Architecture", level=0))

    story += section_header(
        "1. System Architecture",
        styles,
        sub="3-Tier Agentic Pipeline with Agentic RAG"
    )

    story.append(Paragraph(
        "BTU Virtual University is a <b>3-tier multi-agentic AI backend</b> built on FastAPI "
        "and the Anthropic Claude API. Every student message flows through three specialised "
        "agent tiers before a response is returned.",
        styles["body"],
    ))

    story += code_block("""\
Student Message
      │
      ▼
┌────────────────────────────────────────┐
│  TIER 1 – Dean Morgan (Orchestrator)  │
│  • Intent classification (Haiku)      │
│  • Ceremony triggers                  │
│  • Quality gate on responses          │
└──────────────────┬─────────────────────┘
                   │ HandoffPacket1
                   ▼
┌────────────────────────────────────────┐
│  TIER 2 – Elias Vance (Coach)         │
│  • nav / sprint / wheel / motivation  │
│  • Library scenario (cross-chapter)   │
│  • Routes domain/doubt → professors   │
│  • Agentic RAG pre-retrieval          │
└──────────────────┬─────────────────────┘
                   │ HandoffPacket2
                   ▼
┌────────────────────────────────────────┐
│  TIER 3 – 10 Specialist Professors    │
│  P1  Prof. Priya Place      Ch.1-3 ✅ │
│  P2  Prof. Maya People      Ch.4-6 🔒 │
│  ...  (8 more dormant)                │
└────────────────────────────────────────┘
                   │
                   ▼  AgentResponse
""", label="Pipeline Flow", styles=styles)

    story.append(Spacer(1, 6))

    story.append(Paragraph("Intent Types", styles["h2"]))
    intent_data = [
        ["Intent", "Trigger Example", "Handler"],
        ["domain", "\"How do I choose a location?\"", "Professor (Tier 3)"],
        ["cross_p", "\"Compare pricing vs positioning\"", "Professor + RAG"],
        ["nav", "\"What chapter am I on?\"", "Coach direct"],
        ["motivation", "\"I feel like giving up...\"", "Coach direct"],
        ["ceremony", "First login / 30 chapters done", "Dean ceremony"],
        ["sprint", "\"How many hours left?\"", "Coach direct"],
        ["wheel", "\"Spin the wheel\"", "Coach direct"],
        ["library", "\"Take me to the library\"", "Coach library handler"],
        ["doubt", "\"I have a doubt about pricing\"", "Professor doubt session"],
    ]
    story.append(styled_table(intent_data, [3 * cm, 7 * cm, 5.5 * cm]))
    story.append(Spacer(1, 8))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 – THE AGENT HANDOFF JOURNEY
    # ══════════════════════════════════════════════════════════════════════════
    story.append(TOCAnchor("2. The Agent Handoff Journey", level=0))
    story += section_header(
        "2. The Agent Handoff Journey",
        styles,
        sub="Dean → Coach → Professor: a student's first interaction"
    )

    story.append(Paragraph(
        "Every student message travels through three agents in sequence. Each agent "
        "reads only what they need to know — a context-narrowing pyramid — before "
        "passing a structured <b>HandoffPacket</b> to the next tier.",
        styles["body"],
    ))
    story.append(Spacer(1, 10))

    # ── Agent cards helper ────────────────────────────────────────────────────
    def agent_card(
        name: str, title: str, tier: str,
        avatar_color: HexColor, border_color: HexColor,
        role_lines: list[str], says: str, styles: dict,
    ) -> Table:
        cw = W - 4 * cm

        # Avatar circle drawn via a tiny 1-row table acting as a pill
        avatar_para = Paragraph(
            f'<font color="white"><b>{name[0]}</b></font>',
            ParagraphStyle("av", fontName="Helvetica-Bold", fontSize=22,
                           textColor=WHITE, alignment=TA_CENTER, leading=28),
        )
        avatar_cell = Table([[avatar_para]], colWidths=[1.4 * cm])
        avatar_cell.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), avatar_color),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ]))

        # Name + title block
        name_para  = Paragraph(f"<b>{name}</b>", ParagraphStyle(
            "cn", fontName="Helvetica-Bold", fontSize=13,
            textColor=border_color, leading=17))
        title_para = Paragraph(title, ParagraphStyle(
            "ct", fontName="Helvetica", fontSize=9,
            textColor=MID_GRAY, leading=12))
        tier_para  = Paragraph(tier, ParagraphStyle(
            "ctr", fontName="Helvetica-Bold", fontSize=8,
            textColor=WHITE, leading=11))
        tier_bg = Table([[tier_para]], colWidths=[3 * cm])
        tier_bg.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), avatar_color),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ]))
        header_inner = Table(
            [[name_para], [title_para], [Spacer(1, 4)], [tier_bg]],
            colWidths=[cw - 2.4 * cm],
        )
        header_inner.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ]))

        header_row = Table([[avatar_cell, header_inner]],
                           colWidths=[1.8 * cm, cw - 1.8 * cm])
        header_row.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))

        # Role bullets
        role_paras = [Paragraph(
            f"<font color='#{border_color.hexval()[2:]}'>▸</font>  {line}",
            ParagraphStyle("rb", fontName="Helvetica", fontSize=9.5,
                           textColor=DARK_TEXT, leading=14, leftIndent=6),
        ) for line in role_lines]

        # Speech bubble – what the agent says
        speech = Paragraph(
            f'<i>"{says}"</i>',
            ParagraphStyle("sp", fontName="Helvetica-Oblique", fontSize=9.5,
                           textColor=DARK_TEXT, leading=14),
        )
        speech_cell = Table([[speech]], colWidths=[cw - 1.2 * cm])
        speech_cell.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), HexColor("#F0F8FF")),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LINECOLOR",     (0, 0), (0, -1),  border_color),
            ("LINEBEFORE",    (0, 0), (0, -1),  3, border_color),
        ]))

        # Assemble header block (with top accent border)
        header_block = Table([[header_row]], colWidths=[cw])
        header_block.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), WHITE),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
            ("LINEABOVE",     (0, 0), (-1, 0),  4, border_color),
            ("LINEBEFORE",    (0, 0), (0, -1),  2, border_color),
            ("LINEAFTER",     (0, 0), (-1, -1), 2, border_color),
        ]))

        # Bullets block
        bullets_table = Table([[p] for p in role_paras], colWidths=[cw])
        bullets_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), WHITE),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 18),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
            ("LINEBEFORE",    (0, 0), (0, -1),  2, border_color),
            ("LINEAFTER",     (0, 0), (-1, -1), 2, border_color),
        ]))

        # Speech bubble block (bottom border closes the card)
        speech_outer = Table([[speech_cell]], colWidths=[cw])
        speech_outer.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), WHITE),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
            ("LINEBEFORE",    (0, 0), (0, -1),  2, border_color),
            ("LINEAFTER",     (0, 0), (-1, -1), 2, border_color),
            ("LINEBELOW",     (0, -1), (-1, -1), 2, border_color),
        ]))

        return [header_block, bullets_table, speech_outer]

    # ── Handoff arrow helper ──────────────────────────────────────────────────
    def handoff_arrow(label: str, sub: str, styles: dict) -> list:
        cw = W - 4 * cm
        arrow_para = Paragraph(
            f"<b>↓  {label}</b>",
            ParagraphStyle("ha", fontName="Helvetica-Bold", fontSize=10,
                           textColor=WHITE, alignment=TA_CENTER, leading=14),
        )
        sub_para = Paragraph(sub, ParagraphStyle(
            "hs", fontName="Helvetica", fontSize=8.5,
            textColor=HexColor("#C8E6FF"), alignment=TA_CENTER, leading=12))
        t = Table([[arrow_para], [sub_para]], colWidths=[cw])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), INDIGO),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        return [Spacer(1, 6), t, Spacer(1, 6)]

    # ── DEAN MORGAN card ──────────────────────────────────────────────────────
    story += agent_card(
        name="Dean Morgan",
        title="Master Orchestrator  ·  Tier 1",
        tier="TIER 1  –  ORCHESTRATOR",
        avatar_color=HexColor("#7C3AED"),   # violet
        border_color=HexColor("#7C3AED"),
        role_lines=[
            "Receives every student message first — no professor ever sees a raw message.",
            "Classifies intent (domain / library / doubt / sprint / ...) using claude-haiku.",
            "Triggers Onboarding ceremony on first login; Graduation ceremony on chapter 30.",
            "Writes a diagnostic note (gaps, urgency, emotional cues) for the Coach.",
            "Runs a quality gate on the final response before it reaches the student.",
        ],
        says=(
            "Welcome to BTU Virtual University! I'm Dean Morgan. "
            "I've read your question, classified it as a domain query about location strategy, "
            "and I'm handing you to your AI Coach Elias Vance with my diagnostic note. "
            "He'll take it from here."
        ),
        styles=styles,
    )

    story += handoff_arrow(
        "HandoffPacket1  →  Coach Elias Vance",
        "student_id · raw_message · intent_type=domain · target_module=place · dean_note · student_context",
        styles,
    )

    # ── COACH ELIAS card ──────────────────────────────────────────────────────
    story += agent_card(
        name="Elias Vance",
        title="AI Coach & Bridge Agent  ·  Tier 2",
        tier="TIER 2  –  COACH",
        avatar_color=HexColor("#0891B2"),   # cyan
        border_color=HexColor("#0891B2"),
        role_lines=[
            "Handles navigation, motivation, sprint status, and wheel-of-fortune directly.",
            "Manages the Library scenario — runs Agentic RAG across all 30 chapters.",
            "For domain/doubt queries: runs Agentic RAG at coach level, refines the query,",
            "  builds a ProfessorBriefingPacket, and forwards to the right professor.",
            "Fetches recent session history so the professor has conversation context.",
        ],
        says=(
            "Hi! I'm Elias, your AI Coach. Dean told me you're asking about retail location strategy. "
            "I've run a multi-round Agentic RAG search across all 30 chapters and found 4 relevant "
            "curriculum excerpts. I'm briefing Prof. Priya Place now — she owns Chapters 1-3 "
            "on Location & Footprint Strategy. She'll give you the deep answer."
        ),
        styles=styles,
    )

    story += handoff_arrow(
        "HandoffPacket2  →  Prof. Priya Place",
        "professor_id=place · briefing_packet · rag_chapters=[1,2,3] · rag_pre_query · session_history · mode=normal",
        styles,
    )

    # ── PROFESSOR card ────────────────────────────────────────────────────────
    story += agent_card(
        name="Prof. Priya Place",
        title="Specialist Professor – Location & Footprint Strategy  ·  Tier 3",
        tier="TIER 3  –  PROFESSOR  (Chapters 1-3)",
        avatar_color=HexColor("#059669"),   # emerald
        border_color=HexColor("#059669"),
        role_lines=[
            "Runs Agentic RAG scoped to her own 3 chapters only — no noise from other domains.",
            "Uses claude-opus-4-6 with adaptive thinking (up to 8 000 thinking tokens).",
            "In DOUBT CLEARING mode: adopts Socratic style, returns explanation + follow-up questions.",
            "Returns a ProfessorResponse: answer text + thinking trace + RAG chunks used.",
            "Response passes back through Dean's quality gate before reaching the student.",
        ],
        says=(
            "Hello! I'm Prof. Priya Place, your Location & Footprint Strategy specialist. "
            "Based on Chapter 2's footfall analysis framework and Chapter 3's site scoring model, "
            "here is what you should consider when choosing a retail location: "
            "footfall volume, catchment demographics, competitor proximity, and lease flexibility... "
            "[full answer continues]"
        ),
        styles=styles,
    )

    story.append(Spacer(1, 10))

    # Full handoff data flow summary
    story.append(Paragraph("Complete Handoff Data Flow", styles["h2"]))
    story += code_block("""\
Student: "What should I consider when choosing a retail location?"
   │
   │  ┌─────────────────── TIER 1: Dean Morgan ──────────────────────┐
   │  │  1. classify_intent()  →  intent=DOMAIN, target=place        │
   │  │  2. _diagnostic_note() →  "Student on Ch.1, gap in site      │
   │  │                            selection knowledge, eager tone"   │
   │  │  3. Return HandoffPacket1                                     │
   │  └──────────────────────────────────────────────────────────────┘
   │                              │
   │                    HandoffPacket1 {
   │                      student_id, raw_message,
   │                      intent_type = "domain",
   │                      target_module = "place",
   │                      confidence = 0.94,
   │                      student_context { chapter=1, sprint_hours=3.5 },
   │                      dean_note = "Student on Ch.1, gap in site..."
   │                    }
   │
   │  ┌─────────────────── TIER 2: Coach Elias Vance ────────────────┐
   │  │  1. agentic_retrieve(query, chapters=1..30)                  │
   │  │     Round 1: ["retail location factors",                     │
   │  │               "site selection criteria",                     │
   │  │               "footfall analysis"]  →  8 chunks              │
   │  │     Evaluate: sufficient=True                                │
   │  │  2. Build ProfessorBriefingPacket                            │
   │  │  3. Fetch last 10 messages (session_history)                 │
   │  │  4. Return HandoffPacket2                                    │
   │  └──────────────────────────────────────────────────────────────┘
   │                              │
   │                    HandoffPacket2 {
   │                      professor_id = "place",
   │                      briefing_packet {
   │                        student_name, current_chapter=1,
   │                        coach_note = "8 RAG chunks retrieved | conf=0.94",
   │                      },
   │                      rag_chapters = [1, 2, 3],
   │                      rag_pre_query = "retail location ...",
   │                      session_history = [...last 10 msgs],
   │                      mode = "normal"
   │                    }
   │
   │  ┌─────────────────── TIER 3: Prof. Priya Place ────────────────┐
   │  │  1. agentic_retrieve(query, chapters=[1,2,3])                │
   │  │     Round 1: 4 relevant chunks from Ch.2 & Ch.3             │
   │  │     Evaluate: sufficient=True                                │
   │  │  2. _build_messages() with RAG context + session history     │
   │  │  3. claude-opus-4-6 call (adaptive thinking=8000 tokens)     │
   │  │  4. Return ProfessorResponse { text, thinking, latency_ms }  │
   │  └──────────────────────────────────────────────────────────────┘
   │                              │
   │  ┌─────────────────── TIER 1: Dean quality_gate() ─────────────┐
   │  │  • Check latency (warn if > 15 s)                           │
   │  │  • Future: confidence scoring, content safety               │
   │  └──────────────────────────────────────────────────────────────┘
   │
   ▼
AgentResponse {
  text           = "When choosing a retail location, consider...",
  source_agent   = "place",
  latency_ms     = 1840,
  rag_chunks_used = 4
}
""", label="End-to-End Handoff Trace", styles=styles)

    story.append(Spacer(1, 8))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 – PERSONALISED GREETING SYSTEM
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(TOCAnchor("3. Personalised Greeting System", level=0))
    story += section_header(
        "3. Personalised Greeting System",
        styles,
        sub="Dean Morgan greets every student by name"
    )

    story.append(Paragraph(
        "Before any academic content is delivered, Dean Morgan personalises the "
        "experience with a warm greeting. The system detects whether this is the "
        "student's <b>first message</b> after onboarding or a <b>returning session</b>, "
        "and generates an appropriate greeting via Haiku.",
        styles["body"],
    ))

    story.append(Paragraph("How It Works", styles["h2"]))
    story += code_block("""\
Student sends first message after onboarding
  → Dean counts total messages (≤3 = first real message)
  → Haiku generates: "Welcome, Alice! Great to have you at BTU..."
  → greeting rides on HandoffPacket1.greeting
  → Engine prepends it to the professor/coach response

Returning student (>3 messages)
  → Dean detects returning session
  → Haiku: "Welcome back, Alice! You're on Chapter 3..."
  → Same prepend mechanism
""", label="Greeting Flow", styles=styles)

    story.append(Paragraph("Code – Dean._maybe_greet()", styles["h2"]))
    story += code_block("""\
# agents/dean.py
async def _maybe_greet(self, student_id, context) -> str | None:
    msg_count = await self.memory.total_message_count(student_id)

    if msg_count <= 3:   # first real message after onboarding
        prompt = (
            f"The student {context.full_name} just completed "
            "onboarding... Write a warm 1-2 sentence greeting "
            "from Dean Morgan. Keep it under 40 words."
        )
    elif msg_count > 3:  # returning student
        prompt = (
            f"Student {context.full_name} is back. "
            f"Chapter {context.current_chapter}, "
            f"{context.completion_pct*100:.0f}% complete. "
            "Write a 1-sentence welcome-back. Under 30 words."
        )
    else:
        return None

    result = await self._call_llm(
        system=DEAN_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100, model=settings.HAIKU_MODEL,
    )
    return result["text"]
""", label="Python – agents/dean.py", styles=styles)

    story.append(Paragraph("Code – Engine prepends greeting", styles["h2"]))
    story += code_block("""\
# agents/engine.py
@staticmethod
def _prepend_greeting(greeting: str | None, text: str) -> str:
    if greeting:
        return f"{greeting}\\n\\n{text}"
    return text

# Used in both chat() and stream_chat():
response = AgentResponse(
    text=self._prepend_greeting(tier1.greeting, prof_resp.response_text),
    ...
)
""", label="Python – agents/engine.py", styles=styles)

    story += info_box(
        "The greeting uses <b>Haiku</b> (not Opus) for speed — adds only ~200ms latency. "
        "It is generated once per session and stored on HandoffPacket1.",
        styles, color=TEAL, icon="⚡"
    )

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4 – AGENTIC RAG
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(TOCAnchor("4. Agentic RAG Pipeline", level=0))
    story += section_header(
        "4. Agentic RAG Pipeline",
        styles,
        sub="LLM-Guided Multi-Round Retrieval"
    )

    story.append(Paragraph(
        "The <b>AgenticRAGPipeline</b> (rag/agentic_pipeline.py) replaces the old single-shot "
        "passive retrieval. A Haiku agent actively drives retrieval in up to 3 rounds, "
        "evaluating whether the collected context is sufficient before each round ends.",
        styles["body"],
    ))

    story += code_block("""\
Query
  │
  ▼  ROUND 1 ──────────────────────────────────────
  │  Haiku: decompose query → 2-3 sub-queries
  │  e.g. "pricing strategy" →
  │       ["competitive pricing models",
  │        "cost-plus pricing",
  │        "price elasticity"]
  │  Embed each sub-query → search FAISS
  │  Collect & deduplicate chunks
  │
  ▼  EVALUATE ─────────────────────────────────────
  │  Haiku: "Is context sufficient to answer?"
  │  YES → done (return chunks + trace)
  │  NO  → generate follow-up queries
  │
  ▼  ROUND 2/3 ────────────────────────────────────
     Retrieve for follow-up queries
     Add new chunks (deduplicated by text prefix)
     Re-evaluate → return top-K by score
""", label="Agentic RAG Flow (up to 3 rounds)", styles=styles)

    story.append(Paragraph("Core API", styles["h3"]))
    story += code_block("""\
from rag.agentic_pipeline import AgenticRAGPipeline

rag = AgenticRAGPipeline()
await rag.init()

# Drop-in compatible with old RAGPipeline
chunks = await rag.retrieve(query, chapters=[1, 2, 3])

# Full agentic mode – returns trace + metadata
result = await rag.agentic_retrieve(
    query       = "How does footfall analysis work?",
    chapters    = [1, 2, 3],          # chapter-scoped (professor mode)
    max_rounds  = 3,
)

print(result.chunks)          # list[RagChunk]  ranked by score
print(result.rounds_used)     # 1, 2, or 3
print(result.sufficient)      # True if Haiku confirmed sufficiency
print(result.trace)           # per-round query + evaluation details
""", label="Python Usage", styles=styles)

    story += info_box(
        "AgenticRAGPipeline is a drop-in replacement for RAGPipeline — "
        "the retrieve() method signature is identical. All professors, "
        "the coach, and the library pipeline use it automatically.",
        styles, TEAL, "✓"
    )

    story.append(Paragraph("AgenticRagResult Fields", styles["h3"]))
    rag_fields = [
        ["Field", "Type", "Description"],
        ["chunks", "list[RagChunk]", "Deduplicated, re-ranked chunks (top-K)"],
        ["sub_queries", "list[str]", "Sub-queries generated in round 1"],
        ["rounds_used", "int", "How many retrieval rounds were needed (1-3)"],
        ["sufficient", "bool", "Whether Haiku confirmed context was sufficient"],
        ["trace", "list[dict]", "Per-round: queries, chunks_found, reason, follow_ups"],
    ]
    story.append(styled_table(rag_fields, [3 * cm, 3.5 * cm, 9 * cm]))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4 – HOW THE CODE WORKS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(TOCAnchor("5. How the Code Works — End-to-End", level=0))
    story += section_header(
        "5. How the Code Works — End-to-End Request Lifecycle",
        styles,
        sub="From student message to professor response: every function call traced"
    )

    story.append(Paragraph(
        "This section walks through a single student message end-to-end, showing exactly which "
        "class, method, and file handles each step. Every tier of the pipeline is explained "
        "with the actual production code it runs.",
        styles["body"],
    ))
    story.append(Spacer(1, 8))

    # ── Step 1: FastAPI entry point ───────────────────────────────────────────
    story.append(Paragraph("Step 1 — FastAPI Receives the Request", styles["h2"]))
    story.append(Paragraph(
        "The student's message arrives at <b>POST /chat</b> defined in "
        "<b>api/routes/chat.py</b>. The route extracts the <i>student_id</i> from the "
        "JWT session token, then calls <b>PipelineEngine.chat()</b>.",
        styles["body"],
    ))
    story += code_block("""\
# api/routes/chat.py
@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    student_id: str = Depends(get_current_student),
    engine: PipelineEngine = Depends(get_pipeline_engine),
):
    response = await engine.chat(student_id, body.message)
    return ChatResponse(
        text=response.text,
        source_agent=response.source_agent,
        latency_ms=response.latency_ms,
        rag_chunks_used=response.rag_chunks_used,
    )
""", label="api/routes/chat.py", styles=styles)

    # ── Step 2: PipelineEngine.chat() ────────────────────────────────────────
    story.append(Paragraph("Step 2 — PipelineEngine Orchestrates the 3-Tier Chain", styles["h2"]))
    story.append(Paragraph(
        "<b>agents/engine.py → PipelineEngine.chat()</b> is the central coordinator. "
        "It first persists the user message to PostgreSQL via MemoryStore, then invokes "
        "each tier in sequence, short-circuiting early if a tier can answer directly "
        "(e.g. a ceremony or a sprint status query).",
        styles["body"],
    ))
    story += code_block("""\
# agents/engine.py  –  PipelineEngine.chat()
async def chat(self, student_id: str, message: str) -> AgentResponse:
    start = time.monotonic()

    # Persist student message to PostgreSQL (messages table)
    await self.memory.save_message(student_id, role="user", content=message)

    # ── TIER 1: Dean Morgan ──────────────────────────────────────────────
    tier1 = await self.dean.orchestrate(student_id, message)

    if isinstance(tier1, CeremonyResponse):          # onboarding / graduation
        response = AgentResponse(text=tier1.ceremony_script, ...)
        await self._persist_and_maybe_summarise(...)
        return response                              # short-circuit here

    # ── TIER 2: Coach Elias Vance ────────────────────────────────────────
    tier2 = await self.coach.bridge(tier1)

    if isinstance(tier2, CoachResponse):             # nav / sprint / library
        response = AgentResponse(text=tier2.response_text, ...)
        await self._persist_and_maybe_summarise(...)
        return response                              # short-circuit here

    # ── TIER 3: Specialist Professor ─────────────────────────────────────
    professor = self.registry.get_professor(tier2.professor_id)
    prof_resp  = await professor.respond(tier2)

    # Quality gate (Dean post-check on latency & confidence)
    response = AgentResponse(
        text=prof_resp.response_text,
        source_agent=tier2.professor_id,
        latency_ms=int((time.monotonic() - start) * 1000),
        rag_chunks_used=prof_resp.rag_chunks_used,
    )
    response = await self.dean.quality_gate(response, tier1.student_context)

    await self._persist_and_maybe_summarise(student_id, response, tier2.professor_id)
    return response
""", label="agents/engine.py", styles=styles)

    # ── Step 3: Dean Agent ────────────────────────────────────────────────────
    story.append(Paragraph("Step 3 — Dean Morgan: Intent Classification & Ceremony", styles["h2"]))
    story.append(Paragraph(
        "<b>agents/dean.py → DeanAgent.orchestrate()</b> does three things in order: "
        "(1) checks if a ceremony is due, (2) classifies the intent via Haiku LLM, "
        "(3) writes a 1-2 sentence diagnostic note for downstream agents.",
        styles["body"],
    ))
    story += code_block("""\
# agents/dean.py  –  DeanAgent.orchestrate()
async def orchestrate(self, student_id: str, message: str):
    context = await self.memory.get_student_context(student_id)
    # StudentContext: current_chapter, completion_pct, sprint_hours, badges ...

    # 1. Ceremony checks  ─────────────────────────────────────────────────
    if context.completion_pct == 0.0 and not await self.memory.is_onboarded(student_id):
        return await self._ceremony(context, MilestoneType.ONBOARDING)

    if context.completion_pct >= 1.0 and not await self.memory.is_graduated(student_id):
        return await self._ceremony(context, MilestoneType.GRADUATION)

    # 2. Classify intent via claude-haiku  ────────────────────────────────
    #    IntentRouter calls Haiku with a structured routing prompt.
    #    Returns: (intent, target_module, confidence)
    #    e.g.  (IntentType.DOMAIN, "place", 0.94)
    intent, target_module, confidence = await self.router.classify(message, context)

    # 3. Fallback: inactive professor in POC → reroute to "place"
    if intent == IntentType.DOMAIN and target_module not in POC_ACTIVE_PROFESSORS:
        target_module = POC_ACTIVE_PROFESSORS[0]

    # 4. Diagnostic note (Haiku, 128 tokens max)
    dean_note = await self._diagnostic_note(message, context, intent)

    return HandoffPacket1(
        student_id=student_id,
        raw_message=message,
        intent_type=intent,        # domain | library | doubt | sprint | ...
        target_module=target_module,
        confidence=confidence,
        student_context=context,
        dean_note=dean_note,       # e.g. "Student is behind on sprint, eager tone"
    )
""", label="agents/dean.py", styles=styles)

    # ── Step 4: Coach Agent ───────────────────────────────────────────────────
    story.append(Paragraph("Step 4 — Coach Elias Vance: Agentic RAG + Professor Briefing", styles["h2"]))
    story.append(Paragraph(
        "<b>agents/coach.py → CoachAgent.bridge()</b> branches based on intent. "
        "For domain/doubt queries it runs Agentic RAG across all 30 chapters at the coach level "
        "(broad context sweep), then builds a <i>ProfessorBriefingPacket</i> and "
        "<i>HandoffPacket2</i> to pass to the professor.",
        styles["body"],
    ))
    story += code_block("""\
# agents/coach.py  –  CoachAgent.bridge()
async def bridge(self, packet: HandoffPacket1) -> HandoffPacket2 | CoachResponse:
    intent = packet.intent_type

    # ── Direct handlers (no professor needed) ────────────────────────────
    if intent == IntentType.NAVIGATION:  return await self._handle_navigation(packet)
    if intent == IntentType.MOTIVATION:  return await self._handle_motivation(packet)
    if intent == IntentType.SPRINT:      return await self._handle_sprint(packet.student_id)
    if intent == IntentType.WHEEL:       return await self._handle_wheel(packet.student_id)
    if intent == IntentType.LIBRARY:     return await self._handle_library(packet)

    # ── DOMAIN / CROSS_P / DOUBT → forward to professor ─────────────────
    professor_id = packet.target_module or "place"
    chapters     = PROFESSOR_CHAPTERS.get(professor_id, [1, 2, 3])
    mode         = "doubt_clearing" if intent == IntentType.DOUBT else "normal"

    # Broad Agentic RAG sweep (all 30 chapters) at coach level
    rag_result   = await self.rag.agentic_retrieve(
        packet.raw_message, chapters=list(range(1, 31))
    )
    rag_pre_query = self._refine_query(packet.raw_message, packet.dean_note)

    # Build the briefing packet the professor will receive
    briefing = ProfessorBriefingPacket(
        student_name=ctx.full_name,
        current_chapter=ctx.current_chapter,
        completion_pct=ctx.completion_pct,
        sprint_context=f"Week {ctx.sprint_week}: {ctx.sprint_hours}/{ctx.sprint_target}hrs",
        recent_summaries=ctx.recent_summaries,   # cross-agent memory summaries
        coach_note=self._build_coach_note(packet, rag_result.chunks),
    )

    # Fetch last 10 messages for conversation context
    history = await self.memory.get_recent_messages(packet.student_id, limit=10)

    return HandoffPacket2(
        professor_id=professor_id,          # e.g. "place"
        briefing_packet=briefing,
        rag_chapters=chapters,              # professor's own chapters [1,2,3]
        rag_pre_query=rag_pre_query,        # refined query for chapter-scoped RAG
        session_history=history,
        thinking_budget=settings.THINKING_BUDGET,  # 8000 tokens
        mode=mode,                          # "normal" or "doubt_clearing"
    )
""", label="agents/coach.py", styles=styles)

    # ── Step 5: Professor ─────────────────────────────────────────────────────
    story.append(Paragraph("Step 5 — Specialist Professor: Chapter-Scoped RAG + LLM Response", styles["h2"]))
    story.append(Paragraph(
        "<b>agents/professors/base_professor.py → BaseProfessor.respond()</b> runs a "
        "second, narrower Agentic RAG pass scoped only to the professor's own chapters "
        "(e.g. chapters 1-3 for Prof. Priya Place). This precise context is injected into "
        "the system prompt before calling <i>claude-opus-4-6</i> with extended thinking.",
        styles["body"],
    ))
    story += code_block("""\
# agents/professors/base_professor.py  –  BaseProfessor.respond()
async def respond(self, packet: HandoffPacket2) -> ProfessorResponse:

    # Step 1: Chapter-scoped Agentic RAG (professor's own 3 chapters)
    rag_result  = await self.rag.agentic_retrieve(
        query    = packet.rag_pre_query,
        chapters = packet.rag_chapters,    # e.g. [1, 2, 3]
        top_k    = settings.RAG_TOP_K,
    )
    rag_context = self._format_rag(rag_result.chunks)
    # _format_rag() → "[1] Ch.2 – <first 400 chars of chunk text>\\n\\n[2] ..."

    # Step 2: Build messages list with full context
    messages = self._build_messages(packet, rag_context)
    # Injects: student briefing, coach note, RAG context, session history,
    #          mode note ("doubt_clearing" → Socratic instructions)

    # Step 3: Call claude-opus-4-6 with adaptive thinking (up to 8000 tokens)
    result = await self._call_llm(
        system     = self._system,    # professor persona + domain instructions
        messages   = messages,
        max_tokens = 2048,
        use_thinking = True,          # extended thinking enabled
    )

    return ProfessorResponse(
        response_text  = result["text"],
        thinking       = result["thinking"],   # internal reasoning trace
        latency_ms     = result["latency_ms"],
        rag_chunks_used = len(rag_result.chunks),
    )
""", label="agents/professors/base_professor.py", styles=styles)

    # ── Step 6: Summariser ────────────────────────────────────────────────────
    story.append(Paragraph("Step 6 — Upward Summarisation (Every 5 Messages)", styles["h2"]))
    story.append(Paragraph(
        "After every response is persisted, <b>PipelineEngine._maybe_summarise()</b> checks "
        "whether 5 or more new messages have accumulated since the last summary. If so, "
        "<b>memory/summariser.py → Summariser.summarise_and_store()</b> calls Haiku to condense "
        "the conversation and stores it in the <i>cross_agent_summaries</i> table. "
        "These summaries are injected into every future professor briefing via "
        "<i>student_context.recent_summaries</i>.",
        styles["body"],
    ))
    story += code_block("""\
# agents/engine.py  –  _maybe_summarise()
async def _maybe_summarise(self, student_id: str, professor_id: str) -> None:
    count = await self.memory.message_count_since_last_summary(student_id, professor_id)
    if count >= settings.SUMMARISE_EVERY_N:          # default: 5
        recent = await self.memory.get_recent_messages(student_id, limit=5)
        await self.summariser.summarise_and_store(student_id, professor_id, recent)
        # Haiku condenses the last 5 messages into 2-3 sentences
        # → stored in cross_agent_summaries table
        # → injected into next HandoffPacket2 via student_context.recent_summaries
""", label="agents/engine.py", styles=styles)

    # ── Library & Doubt flows ─────────────────────────────────────────────────
    story.append(Paragraph("Alternative Flows — Library & Doubt Clearing", styles["h2"]))
    story.append(Paragraph(
        "Two additional pipelines run independently of the main 3-tier chain:",
        styles["body"],
    ))

    story += info_box(
        "LIBRARY FLOW  (POST /library/search)\n"
        "engine.library_search() → AgenticRAGPipeline.agentic_retrieve(chapters=1-30) "
        "→ Coach LLM synthesises cross-chapter answer → LibraryResponse "
        "{answer, resources[], chapters_searched, rag_rounds_used, retrieval_trace}",
        styles, ELECTRIC, "📚"
    )

    story += info_box(
        "DOUBT CLEARING FLOW  (POST /doubt)\n"
        "engine.doubt_chat() → resolves professor from chapter_hint → "
        "professor.clear_doubt(DoubtPacket) → Agentic RAG on professor chapters → "
        "claude-opus with SOCRATIC system prompt → JSON response "
        "{explanation, follow_up_questions[], suggested_chapters[]}",
        styles, TEAL, "❓"
    )

    story += code_block("""\
# engine.py  –  doubt_chat()  (skips Dean & Coach entirely)
async def doubt_chat(self, student_id, doubt_question, professor_id=None,
                     chapter_hint=None) -> DoubtResponse:

    context = await self.memory.get_student_context(student_id)

    # Auto-resolve professor from chapter hint
    resolved = professor_id or "place"
    if chapter_hint:
        resolved = CHAPTER_TO_PROFESSOR.get(chapter_hint, resolved)

    professor = self.registry.get_professor(resolved)

    packet = DoubtPacket(
        student_id      = student_id,
        student_context = context,
        professor_id    = resolved,
        doubt_question  = doubt_question,
        chapter_hint    = chapter_hint,
    )
    doubt_response = await professor.clear_doubt(packet)
    # → returns DoubtResponse:
    #   explanation           – Socratic, step-by-step
    #   follow_up_questions   – ["Why does X matter?", "What would happen if Y?"]
    #   suggested_chapters    – [2, 3]
    #   rag_chunks_used       – 4

    await self.memory.save_message(student_id, role="assistant",
                                   content=doubt_response.explanation,
                                   source_agent=resolved)
    return doubt_response
""", label="agents/engine.py", styles=styles)

    # ── File map ──────────────────────────────────────────────────────────────
    story.append(Paragraph("Key File Map", styles["h2"]))
    file_map_data = [
        ["File", "Class / Function", "Responsibility"],
        ["api/routes/chat.py",          "POST /chat",                    "HTTP entry point for normal chat"],
        ["api/routes/library.py",       "POST /library/search",          "HTTP entry for library queries"],
        ["api/routes/doubt.py",         "POST /doubt",                   "HTTP entry for doubt clearing"],
        ["agents/engine.py",            "PipelineEngine.chat()",         "3-tier orchestration + persist"],
        ["agents/dean.py",              "DeanAgent.orchestrate()",       "Intent classify, ceremonies, quality gate"],
        ["agents/router.py",            "IntentRouter.classify()",       "Haiku prompt → intent + target_module"],
        ["agents/coach.py",             "CoachAgent.bridge()",           "Agentic RAG (broad) + HandoffPacket2"],
        ["agents/professors/base_professor.py", "BaseProfessor.respond()", "RAG (scoped) + claude-opus call"],
        ["agents/professors/base_professor.py", "BaseProfessor.clear_doubt()", "Socratic mode + JSON response"],
        ["rag/agentic_pipeline.py",     "AgenticRAGPipeline.agentic_retrieve()", "Multi-round Haiku-driven retrieval"],
        ["memory/store.py",             "MemoryStore.*",                 "PostgreSQL: messages, sessions, summaries"],
        ["memory/summariser.py",        "Summariser.summarise_and_store()", "Haiku condensation every 5 messages"],
        ["gamification/sprint_engine.py", "SprintEngine.get_status()",  "Weekly 15-hr sprint tracking"],
        ["gamification/wheel_of_fortune.py", "WheelOfFortune.spin()",   "Reward spins on sprint completion"],
    ]
    story.append(styled_table(file_map_data, [5 * cm, 5.5 * cm, 5.5 * cm]))
    story.append(Spacer(1, 12))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 5 – SETUP
    # ══════════════════════════════════════════════════════════════════════════
    story.append(TOCAnchor("6. Setup & Installation", level=0))
    story += section_header(
        "6. Setup & Installation",
        styles,
        sub="From zero to running server"
    )

    story.append(Paragraph("Prerequisites", styles["h2"]))
    prereq_data = [
        ["Tool", "Version", "Purpose"],
        ["Python", "3.11+", "Runtime"],
        ["PostgreSQL", "16+", "Student memory, messages, sessions"],
        ["Anthropic API Key", "—", "Claude Opus (professors) + Haiku (routing/RAG)"],
    ]
    story.append(styled_table(prereq_data, [4 * cm, 2.5 * cm, 9 * cm]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Step 1 – Virtual Environment", styles["h3"]))
    story += code_block("""\
# Create and activate
python -m venv venv

# Windows
venv\\Scripts\\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
""", label="bash", styles=styles)

    story.append(Paragraph("Step 2 – Environment Variables", styles["h3"]))
    story += code_block("""\
# .env  (minimum required keys)
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_REAL_KEY
JWT_SECRET=a-long-random-string-at-least-32-characters

# PostgreSQL (database: BTU_VU)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YOUR_POSTGRES_PASSWORD
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/BTU_VU

# Embeddings (free, local – no API key needed)
EMBEDDING_MODEL=all-MiniLM-L6-v2
FAISS_PERSIST_DIR=.faiss_store

# Optional tuning
CLAUDE_MODEL=claude-opus-4-6
HAIKU_MODEL=claude-haiku-4-5
RAG_TOP_K=5
RAG_THRESHOLD=0.30
""", label=".env", styles=styles)

    story.append(Paragraph("Step 3 – Create the Database", styles["h3"]))
    story += code_block("""\
# Option A: Terminal
psql -U postgres -c "CREATE DATABASE \\"BTU_VU\\";"

# Option B: pgAdmin (GUI)
# Right-click Databases > Create > Database > Name: BTU_VU > Save

# That's it! All 14 tables are auto-created on first
# python main.py via init_db() -> Base.metadata.create_all()

# Optional: for production (CHECK constraints + indexes):
psql -U postgres -d BTU_VU -f schema.sql
""", label="bash", styles=styles)

    story.append(Paragraph("Step 5 – Ingest Chapter Content", styles["h3"]))
    story += code_block("""\
# Place chapter files in data/chapters/
# File names must contain the chapter number, e.g.:
#   chapter_01.md, chapter_02.md, ..., chapter_30.md

python -m rag.ingest --source data/chapters/

# The ingester:
#   1. Chunks each file into 512-token overlapping chunks
#   2. Embeds with sentence-transformers (all-MiniLM-L6-v2)
#   3. Stores vectors in FAISS (.faiss_store/)
""", label="bash", styles=styles)

    story.append(Paragraph("Step 6 – Start the Server", styles["h3"]))
    story += code_block("""\
python main.py

# Server starts at:  http://localhost:8080
# Interactive docs:  http://localhost:8080/docs
# OpenAPI schema:    http://localhost:8080/openapi.json
""", label="bash", styles=styles)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 6 – API REFERENCE: AUTH & CHAT
    # ══════════════════════════════════════════════════════════════════════════
    story.append(TOCAnchor("7. API Reference – Auth & Chat", level=0))
    story += section_header(
        "7. API Reference – Auth & Chat",
        styles,
        sub="Authentication, standard chat, and streaming"
    )

    story.append(Paragraph("Register a Student", styles["h2"]))
    story += code_block("""\
curl -X POST http://localhost:8080/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "alice@example.com",
    "full_name": "Alice Johnson",
    "password": "securepassword"
  }'
""", label="bash – POST /auth/register", styles=styles)
    story += code_block("""\
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "student_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "full_name": "Alice Johnson"
}
""", label="Response", styles=styles)

    story.append(Paragraph("Login", styles["h2"]))
    story += code_block("""\
curl -X POST http://localhost:8080/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"email": "alice@example.com", "password": "securepassword"}'
""", label="bash – POST /auth/login", styles=styles)

    story.append(Paragraph("Standard Chat", styles["h2"]))
    story.append(Paragraph(
        "The main chat endpoint routes through all 3 tiers. "
        "The Agentic RAG pipeline is invoked at both the Coach (Tier 2) and Professor (Tier 3) levels.",
        styles["body"],
    ))
    story += code_block("""\
curl -X POST http://localhost:8080/chat \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"message": "What should I consider when choosing a retail location?"}'
""", label="bash – POST /chat", styles=styles)
    story += code_block("""\
{
  "text": "When selecting a retail location, footfall analysis is your...",
  "source_agent": "place",
  "latency_ms": 1840,
  "rag_chunks_used": 4,
  "ceremony": null,
  "sprint_status": null,
  "wheel_prize": null
}
""", label="Response", styles=styles)

    story.append(Paragraph("Streaming Chat (SSE)", styles["h2"]))
    story += code_block("""\
curl -N "http://localhost:8080/chat/stream?message=Explain+site+selection" \\
  -H "Authorization: Bearer YOUR_TOKEN"

# Returns Server-Sent Events:
data: {"text": "When"}
data: {"text": " selecting"}
data: {"text": " a site, the first..."}
data: [DONE]
""", label="bash – GET /chat/stream", styles=styles)

    story.append(Paragraph("Upload a File for Analysis", styles["h2"]))
    story += code_block("""\
curl -X POST http://localhost:8080/chat/upload \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -F "file=@my_business_plan.txt"
""", label="bash – POST /chat/upload", styles=styles)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 7 – LIBRARY
    # ══════════════════════════════════════════════════════════════════════════
    story.append(TOCAnchor("8. BTU Digital Library", level=0))
    story += section_header(
        "8. BTU Digital Library",
        styles,
        sub="Full Knowledge Hub — Curriculum RAG + Papers, Videos, Articles"
    )

    story.append(Paragraph(
        "The Library lets students explore content across <b>all 30 chapters</b> regardless "
        "of which professor they are currently assigned to. Unlike domain chat (scoped to one "
        "professor's 3 chapters), the library runs Agentic RAG across the full curriculum and "
        "synthesises a curated answer.",
        styles["body"],
    ))

    story.append(Paragraph("Two Ways to Access the Library", styles["h2"]))
    lib_ways = [
        ["Method", "How", "Notes"],
        ["Via main chat", "Say \"I want to go to the library\" or\n\"search library for pricing\"",
         "IntentType.LIBRARY → Coach._handle_library()"],
        ["Direct API", "POST /library/search", "Full LibraryResponse with trace"],
    ]
    story.append(styled_table(lib_ways, [3.5 * cm, 6 * cm, 6 * cm]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Search the Library", styles["h2"]))
    story += code_block("""\
curl -X POST http://localhost:8080/library/search \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "How do I price my product competitively?"}'
""", label="bash – POST /library/search", styles=styles)
    story += code_block("""\
{
  "answer": "Competitive pricing requires balancing your cost structure with...",
  "resources": [
    {
      "chapter": 19,
      "excerpt": "Pricing strategy starts with understanding value...",
      "score": 0.87,
      "source": "chapter_19.md",
      "professor": "pricing"
    },
    {
      "chapter": 7,
      "excerpt": "Process efficiency directly impacts your unit cost...",
      "score": 0.72,
      "source": "chapter_07.md",
      "professor": "process"
    }
  ],
  "chapters_searched": [7, 13, 19, 20],
  "rag_rounds_used": 2,
  "retrieval_trace": [
    {
      "round": 1,
      "queries": ["competitive pricing models", "price positioning", "market rate"],
      "chunks_collected": 8,
      "sufficient": false,
      "reason": "Missing cost-side pricing context",
      "follow_up_queries": ["cost-plus pricing", "margin analysis"]
    },
    {
      "round": 2,
      "queries": ["cost-plus pricing", "margin analysis"],
      "chunks_collected": 12,
      "sufficient": true,
      "reason": "Context now covers value, cost, and market perspectives"
    }
  ],
  "latency_ms": 2350
}
""", label="Response", styles=styles)

    story.append(Paragraph("Browse Library Topics", styles["h2"]))
    story += code_block("""\
curl http://localhost:8080/library/topics \\
  -H "Authorization: Bearer YOUR_TOKEN"
""", label="bash – GET /library/topics", styles=styles)
    story += code_block("""\
{
  "topics": [
    {
      "professor_id": "place",
      "professor_name": "Prof. Priya Place",
      "domain": "Location & Footprint Strategy",
      "chapters": [1, 2, 3],
      "active": true
    },
    {
      "professor_id": "pricing",
      "professor_name": "Prof. Marcus Pricing",
      "domain": "Financial Planning & Pricing",
      "chapters": [19, 20, 21],
      "active": false
    }
  ]
}
""", label="Response (abridged)", styles=styles)

    story += info_box(
        "The retrieval_trace field is your window into how the Agentic RAG agent "
        "navigated the curriculum. Use it to understand why certain chapters were "
        "selected and how many retrieval rounds were needed.",
        styles, ELECTRIC, "💡"
    )

    story.append(Paragraph("External Resource Catalog", styles["h2"]))
    story.append(Paragraph(
        "Beyond curriculum chapters, the library includes <b>external resources</b>: "
        "research papers, videos, articles, case studies, and books. Students and instructors "
        "can contribute resources, which are linked to chapters and professor modules "
        "for discoverability. Library search automatically includes matching external resources.",
        styles["body"],
    ))

    story.append(Paragraph("Resource Types", styles["h3"]))
    res_types = [
        ["Type", "Examples"],
        ["paper", "Research papers, academic publications, DOI links"],
        ["video", "YouTube lectures, TED talks, course recordings"],
        ["article", "Blog posts, industry reports, news analysis"],
        ["case_study", "Harvard Business cases, real-world examples"],
        ["book", "Textbooks, reference books, recommended reading"],
    ]
    story.append(styled_table(res_types, [3 * cm, 12.5 * cm]))

    story += code_block("""\
# Add a research paper to the library
curl -X POST http://localhost:8080/library/resources \\
  -H "Authorization: Bearer TOKEN" \\
  -d '{
    "title": "Porter Five Forces in Retail",
    "resource_type": "paper",
    "url": "https://doi.org/10.1234/example",
    "author": "Michael Porter",
    "chapters": [10, 11],
    "tags": ["strategy", "positioning"]
  }'

# Browse videos for Chapter 2
curl "http://localhost:8080/library/resources?resource_type=video&chapter=2" \\
  -H "Authorization: Bearer TOKEN"

# Full-text search across all resources
curl "http://localhost:8080/library/resources?search=marketing+strategy" \\
  -H "Authorization: Bearer TOKEN"
""", label="bash – Library Resources API", styles=styles)

    story += info_box(
        "When a student runs POST /library/search, the response now includes an "
        "<b>external_resources</b> field alongside RAG chunks — giving students both "
        "curriculum content and real-world reading material in one response.",
        styles, TEAL, "📚"
    )

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 8 – DOUBT CLEARING
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(TOCAnchor("9. Doubt Clearing Sessions", level=0))
    story += section_header(
        "9. Doubt Clearing Sessions",
        styles,
        sub="Direct 1-on-1 with the concerned professor"
    )

    story.append(Paragraph(
        "A doubt clearing session lets students raise a specific question directly with "
        "the professor responsible for that chapter. The session <b>bypasses Tiers 1 and 2</b> "
        "for speed and goes straight to the professor with a Socratic teaching prompt. "
        "The professor uses Agentic RAG on their own chapter scope, then responds with a "
        "structured explanation plus follow-up questions to guide deeper understanding.",
        styles["body"],
    ))

    story += code_block("""\
Student POST /doubt  →  Engine.doubt_chat()
                            │
                            │  Resolves professor from chapter_hint
                            │  (no Dean/Coach overhead)
                            │
                            ▼
                   BaseProfessor.clear_doubt(DoubtPacket)
                            │
                   ┌────────┴──────────────────────────────┐
                   │  1. AgenticRAG on professor chapters  │
                   │  2. Socratic LLM prompt               │
                   │  3. Parse structured JSON response    │
                   └────────┬──────────────────────────────┘
                            │
                            ▼
                   DoubtResponse {
                     explanation,
                     follow_up_questions[],
                     suggested_chapters[]
                   }
""", label="Doubt Clearing Flow", styles=styles)

    story.append(Paragraph("Auto-Detect Professor (via chapter_hint)", styles["h2"]))
    story += code_block("""\
curl -X POST http://localhost:8080/doubt \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "doubt_question": "I don'\''t understand footfall analysis. How does it work?",
    "chapter_hint": 2
  }'
""", label="bash – POST /doubt", styles=styles)
    story += code_block("""\
{
  "explanation": "Footfall analysis measures the number of people who walk past "
                 "or enter your store in a given period. Here is how it works step-by-step:\\n"
                 "1. Data Collection: sensors or cameras count visitors...\\n"
                 "2. Conversion Rate: divide actual buyers by total footfall...\\n"
                 "3. Peak Times: identify hours/days with highest traffic...",
  "follow_up_questions": [
    "If your store gets 500 daily visitors but only 40 buy, what is the conversion rate "
    "and what two things would you investigate first?",
    "How would footfall analysis differ between a high-street boutique and an "
    "out-of-town retail park?"
  ],
  "suggested_chapters": [2, 3],
  "professor_id": "place",
  "rag_chunks_used": 4,
  "latency_ms": 1920
}
""", label="Response", styles=styles)

    story.append(Paragraph("Target a Specific Professor Directly", styles["h2"]))
    story += code_block("""\
curl -X POST http://localhost:8080/doubt/professor \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "doubt_question": "What is contribution margin and how do I calculate it?",
    "professor_id": "profit"
  }'
""", label="bash – POST /doubt/professor", styles=styles)

    story.append(Paragraph("DoubtRequest Schema", styles["h3"]))
    doubt_schema = [
        ["Field", "Type", "Required", "Description"],
        ["doubt_question", "string (1-2000)", "Yes", "The student's doubt question"],
        ["chapter_hint", "int (1-30)", "No", "Chapter the doubt is about; used to auto-select professor"],
    ]
    story.append(styled_table(doubt_schema, [3.5 * cm, 3 * cm, 2 * cm, 7 * cm]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("ProfessorDoubtRequest Schema", styles["h3"]))
    pdr_schema = [
        ["Field", "Type", "Required", "Description"],
        ["doubt_question", "string (1-2000)", "Yes", "The student's doubt question"],
        ["professor_id", "string", "Yes", "e.g. 'place', 'pricing', 'people', 'profit'"],
        ["chapter_hint", "int (1-30)", "No", "Optional chapter context"],
    ]
    story.append(styled_table(pdr_schema, [3.5 * cm, 3 * cm, 2 * cm, 7 * cm]))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 10 – GROUP DISCUSSION
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(TOCAnchor("10. Group Discussion (Campus & Library)", level=0))
    story += section_header(
        "10. Group Discussion",
        styles,
        sub="Campus & Library Rooms — AI-Moderated by Coach Elias"
    )

    story.append(Paragraph(
        "Students can create or join <b>discussion rooms</b> tied to specific chapters, "
        "professor modules, or research topics. Coach Elias serves as an AI moderator — "
        "synthesising key points, correcting misconceptions, and asking follow-up questions.",
        styles["body"],
    ))

    story.append(Paragraph("Room Types", styles["h2"]))
    room_types_data = [
        ["Type", "Scope", "Example"],
        ["campus", "Tied to a chapter or professor module",
         "Ch.2 — Distribution Channels discussion"],
        ["library", "Cross-chapter study group",
         "Marketing vs Pricing: a comparison"],
    ]
    story.append(styled_table(room_types_data, [2.5 * cm, 5.5 * cm, 7.5 * cm]))

    story.append(Paragraph("Create a discussion room", styles["h2"]))
    story += code_block("""\
curl -X POST http://localhost:8080/discuss/create \\
  -H "Authorization: Bearer TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "Distribution Channels Deep Dive",
    "room_type": "campus",
    "chapter_hint": 2,
    "topic": "Comparing direct vs indirect distribution"
  }'
""", label="bash – POST /discuss/create", styles=styles)

    story.append(Paragraph("Post a message & ask AI to moderate", styles["h2"]))
    story += code_block("""\
# Post a message in the room
curl -X POST http://localhost:8080/discuss/{room_id}/msg \\
  -H "Authorization: Bearer TOKEN" \\
  -d '{"content": "I think omnichannel is the future!"}'

# Ask Coach Elias to moderate
curl -X POST http://localhost:8080/discuss/{room_id}/ai \\
  -H "Authorization: Bearer TOKEN" \\
  -d '{"prompt": "summarise and ask a follow-up"}'
""", label="bash – Discussion interaction", styles=styles)

    story.append(Paragraph("AI Moderation Flow", styles["h2"]))
    story += code_block("""\
POST /discuss/{room_id}/ai
  │
  ▼
Engine.discuss_ai(room_id, nudge)
  ├── Load last 30 messages from room
  ├── Build room context (title, chapter, module)
  ├── Optional RAG from linked chapter
  └── Coach Elias → synthesis / correction / follow-up
        │
        ▼
AI message persisted in the room (visible to all)
""", label="AI Moderation Pipeline", styles=styles)

    story.append(Paragraph("Discussion Endpoints", styles["h2"]))
    discuss_endpoints = [
        ["Method", "Endpoint", "Description"],
        ["POST", "/discuss/create", "Create a room (campus or library)"],
        ["GET", "/discuss/rooms", "List rooms (filter by type/chapter)"],
        ["POST", "/discuss/{room_id}/join", "Join a room"],
        ["POST", "/discuss/{room_id}/msg", "Post a message"],
        ["GET", "/discuss/{room_id}/msgs", "Get room messages"],
        ["GET", "/discuss/{room_id}/members", "List room members"],
        ["POST", "/discuss/{room_id}/ai", "Ask Coach Elias to moderate"],
    ]
    story.append(styled_table(discuss_endpoints, [2 * cm, 5.5 * cm, 8 * cm]))

    story += info_box(
        "Coach Elias reads the room's linked chapter via RAG for curriculum-grounded moderation. "
        "Without a nudge prompt, he automatically synthesises, corrects, and asks a follow-up question.",
        styles, color=ELECTRIC, icon="💬"
    )

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 11 – SPRINT & WHEEL
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(TOCAnchor("11. Sprint & Wheel of Fortune", level=0))
    story += section_header(
        "11. Sprint & Wheel of Fortune",
        styles,
        sub="Gamification Layer"
    )

    story.append(Paragraph("Sprint (15 hrs / week target)", styles["h2"]))
    story += code_block("""\
# Check sprint status
curl http://localhost:8080/sprint/{student_id} \\
  -H "Authorization: Bearer YOUR_TOKEN"
""", label="bash – GET /sprint/{student_id}", styles=styles)
    story += code_block("""\
{
  "week": 3,
  "logged": 9.5,
  "target": 15.0,
  "status": "active",
  "pct": 63
}
""", label="Response", styles=styles)
    story += code_block("""\
# Log study hours
curl -X POST http://localhost:8080/sprint/{student_id}/log \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"hours": 2.5}'
""", label="bash – POST /sprint/{student_id}/log", styles=styles)

    story.append(Paragraph("Wheel of Fortune", styles["h2"]))
    story += code_block("""\
# Spin the wheel (requires 100% sprint completion this week)
curl -X POST http://localhost:8080/wheel/{student_id}/spin \\
  -H "Authorization: Bearer YOUR_TOKEN"
""", label="bash – POST /wheel/{student_id}/spin", styles=styles)
    story += code_block("""\
{
  "prize": {
    "prize_label": "Double XP Weekend",
    "prize_type": "double_xp",
    "value": 2
  }
}
""", label="Response", styles=styles)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 10 – DATABASE SCHEMA
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(TOCAnchor("12. Database Schema", level=0))
    story += section_header(
        "12. Database Schema",
        styles,
        sub="14 PostgreSQL tables"
    )

    _tc = ParagraphStyle("_tc", fontName="Helvetica", fontSize=8,
                          textColor=DARK_TEXT, leading=11)
    _th = ParagraphStyle("_th", fontName="Helvetica-Bold", fontSize=9,
                          textColor=WHITE, leading=12)
    def _r(row, hdr=False):
        s = _th if hdr else _tc
        return [Paragraph(c, s) for c in row]

    tables_data = [
        _r(["Table", "Key Columns", "Purpose"], hdr=True),
        _r(["students", "student_id, email, full_name, onboarded, graduated",
            "Student accounts and progress flags"]),
        _r(["sessions", "session_id, student_id, last_active", "Auth sessions"]),
        _r(["messages", "role, content, source_agent, thinking, latency_ms",
            "Full chat history (user + assistant)"]),
        _r(["cross_agent_summaries", "professor_id, summary_text, msg_count",
            "Upward summaries every 5 messages"]),
        _r(["sprints", "week_number, hours_logged, target_hours, status",
            "15 hr/week sprint tracking"]),
        _r(["wheel_spins", "prize, prize_type, spun_at", "Wheel of Fortune history"]),
        _r(["ceremonies", "milestone, script, triggered_at",
            "Onboarding / graduation scripts"]),
        _r(["chapter_progress", "chapter_number, status, started_at, completed_at",
            "Per-chapter progress (locked / in_progress / completed)"]),
        _r(["library_sessions", "query, answer, chapters_hit, rag_rounds",
            "Library search log with retrieval metadata"]),
        _r(["doubt_sessions", "professor_id, doubt_question, explanation, "
            "follow_up_questions (JSONB), suggested_chapters",
            "Doubt clearing exchange log"]),
        _r(["discussion_rooms", "room_id, title, room_type, chapter_hint, "
            "professor_id, topic, created_by",
            "Group discussion rooms (campus / library)"]),
        _r(["discussion_members", "room_id, student_id, joined_at",
            "Room membership"]),
        _r(["discussion_messages", "room_id, student_id, content, is_ai",
            "Messages in rooms (student + AI)"]),
        _r(["library_resources", "title, resource_type, url, author, "
            "chapters, tags, added_by",
            "External resources (papers, videos, articles)"]),
    ]
    story.append(styled_table(tables_data, [3.2 * cm, 6.2 * cm, 6.2 * cm]))

    story.append(Paragraph("library_sessions DDL", styles["h3"]))
    story += code_block("""\
CREATE TABLE IF NOT EXISTS library_sessions (
    session_id   BIGSERIAL PRIMARY KEY,
    student_id   UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    query        TEXT NOT NULL,
    answer       TEXT NOT NULL,
    chapters_hit INT[] NOT NULL DEFAULT '{}',
    rag_rounds   INT NOT NULL DEFAULT 1,
    latency_ms   INT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
""", label="SQL", styles=styles)

    story.append(Paragraph("doubt_sessions DDL", styles["h3"]))
    story += code_block("""\
CREATE TABLE IF NOT EXISTS doubt_sessions (
    doubt_id              BIGSERIAL PRIMARY KEY,
    student_id            UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    professor_id          TEXT NOT NULL,
    doubt_question        TEXT NOT NULL,
    explanation           TEXT NOT NULL,
    follow_up_questions   JSONB NOT NULL DEFAULT '[]',
    suggested_chapters    INT[] NOT NULL DEFAULT '{}',
    rag_chunks_used       INT NOT NULL DEFAULT 0,
    chapter_hint          INT,
    latency_ms            INT,
    created_at            TIMESTAMPTZ DEFAULT NOW()
);
""", label="SQL", styles=styles)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 11 – CONFIGURATION
    # ══════════════════════════════════════════════════════════════════════════
    story.append(TOCAnchor("13. Configuration Reference", level=0))
    story += section_header(
        "13. Configuration Reference",
        styles,
        sub="All .env variables"
    )

    config_data = [
        ["Variable", "Default", "Description"],
        ["ANTHROPIC_API_KEY", "required", "Anthropic Console → API Keys"],
        ["CLAUDE_MODEL", "claude-opus-4-6", "Main agent model (professors)"],
        ["HAIKU_MODEL", "claude-haiku-4-5", "Fast ops: routing, RAG planning, summaries"],
        ["THINKING_BUDGET", "8000", "Adaptive thinking token budget"],
        ["EMBEDDING_MODEL", "all-MiniLM-L6-v2", "sentence-transformers model (free, local)"],
        ["DATABASE_URL", "postgresql+asyncpg://postgres:pw@localhost:5432/BTU_VU", "PostgreSQL async connection string"],
        ["FAISS_PERSIST_DIR", ".faiss_store", "Directory for FAISS index files"],
        ["JWT_SECRET", "required", "Secret for signing JWT tokens"],
        ["JWT_EXPIRE_MINUTES", "1440", "Token expiry (24 hours)"],
        ["RAG_CHUNK_SIZE", "512", "Words per RAG chunk (ingestion)"],
        ["RAG_CHUNK_OVERLAP", "64", "Overlap between consecutive chunks"],
        ["RAG_TOP_K", "5", "Max chunks returned per retrieval query"],
        ["RAG_THRESHOLD", "0.30", "Min cosine similarity score (0.0–1.0)"],
        ["SPRINT_TARGET_HOURS", "15.0", "Weekly learning sprint target"],
        ["SUMMARISE_EVERY_N", "5", "Messages between upward summaries"],
        ["APP_ENV", "development", "development enables uvicorn hot-reload"],
    ]
    story.append(styled_table(config_data, [5 * cm, 4.5 * cm, 6 * cm]))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 12 – ACTIVATING A PROFESSOR
    # ══════════════════════════════════════════════════════════════════════════
    story.append(TOCAnchor("14. Activating a Dormant Professor", level=0))
    story += section_header(
        "14. Activating a Dormant Professor",
        styles,
        sub="No code changes required"
    )

    story.append(Paragraph(
        "Only Prof. Priya Place (Ch. 1–3) is active in the POC. To unlock the next professor:",
        styles["body"],
    ))
    story += code_block("""\
# Step 1 – Set active: True in config/agent_config.py
PROFESSOR_META = {
    "people": {
        "name": "Prof. Maya People",
        "domain": "Team & Talent Strategy",
        "active": True,    # ← change False to True
    },
    ...
}
""", label="config/agent_config.py", styles=styles)
    story += code_block("""\
# Step 2 – Add chapter files (4, 5, 6 for 'people')
data/chapters/
├── chapter_04.md   ← new
├── chapter_05.md   ← new
└── chapter_06.md   ← new

# Step 3 – Ingest
python -m rag.ingest --source data/chapters/

# Step 4 – Restart
python main.py
""", label="bash", styles=styles)

    story += info_box(
        "The registry, pipeline, and router all update automatically when active=True is set. "
        "The intent router will start routing 'people' domain questions to Prof. Maya People.",
        styles, AMBER, "★"
    )

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 13 – TROUBLESHOOTING
    # ══════════════════════════════════════════════════════════════════════════
    story.append(TOCAnchor("15. Troubleshooting", level=0))
    story += section_header(
        "15. Troubleshooting",
        styles,
        sub="Common issues and solutions"
    )

    issues = [
        ("ModuleNotFoundError",
         "Activate venv and run from the btu-virtual-university/ directory."),
        ("PostgreSQL connection error",
         "Check DATABASE_URL in .env. Server starts without it (graceful mode)."),
        ("No RAG results / 0 chunks",
         "FAISS index is empty. Run: python -m rag.ingest --source data/chapters/"),
        ("Slow first startup (~20s)",
         "sentence-transformers downloads the model (~80MB) on first run. Cached after that."),
        ("Doubt response is plain text (not structured)",
         "LLM returned non-JSON. The system falls back to raw text as explanation — no data lost."),
        ("401 Unauthorized",
         "Register first (POST /auth/register), then pass the returned access_token as Bearer."),
        ("Rate limit from Anthropic",
         "SDK auto-retries with exponential backoff. Reduce concurrent users or add queuing."),
        ("Library returns no resources",
         "No chapters ingested yet, or RAG_THRESHOLD is too high. Try lowering to 0.20."),
        ("Vercel bundle too large",
         "sentence-transformers + torch can be large. Consider Vercel Pro plan or lighter model."),
    ]

    for problem, solution in issues:
        story.append(Paragraph(f"<b>{problem}</b>", styles["h3"]))
        story.append(Paragraph(solution, styles["body_left"]))
        story.append(Spacer(1, 2))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 14 – QUICK REFERENCE CARD
    # ══════════════════════════════════════════════════════════════════════════
    story.append(TOCAnchor("16. Quick Reference Card", level=0))
    story += section_header(
        "16. Quick Reference Card",
        styles,
        sub="All endpoints at a glance"
    )

    endpoints = [
        ["Method", "Endpoint", "Auth", "Description"],
        ["GET",  "/health", "No",  "Health check"],
        ["POST", "/auth/register", "No", "Register a new student"],
        ["POST", "/auth/login", "No", "Login → access_token"],
        ["GET",  "/auth/me", "Yes", "Current student profile"],
        ["POST", "/chat", "Yes", "Standard chat (3-tier pipeline)"],
        ["GET",  "/chat/stream", "Yes", "SSE streaming chat"],
        ["POST", "/chat/upload", "Yes", "Upload file for analysis"],
        ["GET",  "/library/topics", "Yes", "Browse library topic areas"],
        ["POST", "/library/search", "Yes", "RAG search + external resources"],
        ["GET",  "/library/resources", "Yes", "Browse/filter external resources"],
        ["POST", "/library/resources", "Yes", "Add a resource (paper/video/etc.)"],
        ["POST", "/doubt", "Yes", "Doubt session (auto-detect professor)"],
        ["POST", "/doubt/professor", "Yes", "Doubt session (specific professor)"],
        ["POST", "/discuss/create", "Yes", "Create a discussion room"],
        ["GET",  "/discuss/rooms", "Yes", "List open discussion rooms"],
        ["POST", "/discuss/{id}/join", "Yes", "Join a discussion room"],
        ["POST", "/discuss/{id}/msg", "Yes", "Post a discussion message"],
        ["GET",  "/discuss/{id}/msgs", "Yes", "Get room messages"],
        ["POST", "/discuss/{id}/ai", "Yes", "Ask Coach Elias to moderate"],
        ["GET",  "/sprint/{id}", "Yes", "Sprint status"],
        ["POST", "/sprint/{id}/log", "Yes", "Log study hours"],
        ["POST", "/wheel/{id}/spin", "Yes", "Spin wheel (100% sprint)"],
        ["GET",  "/agents", "Yes", "List all agents"],
        ["GET",  "/agents/chapter-map", "Yes", "Chapter → professor mapping"],
        ["POST", "/ingest/chapters", "Yes", "Trigger chapter ingestion"],
    ]
    story.append(styled_table(endpoints, [1.8 * cm, 5 * cm, 1.5 * cm, 7.2 * cm]))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.multiBuild(story)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    out = Path(__file__).parent.parent / "BTU_Working_Guide.pdf"
    build_pdf(str(out))
