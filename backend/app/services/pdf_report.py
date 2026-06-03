"""Render a diagnostic report to PDF using ReportLab.

Aesthetic mirrors the on-screen ReportCard (Hatana style): deep-green brand,
orange accent, Fraunces display + Geist body, editorial layout, A4 page size.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor, Color
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ───────────────────── paths ─────────────────────

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
FONTS_DIR = TEMPLATES_DIR / "fonts"

# ───────────────────── tokens ─────────────────────

GREEN = HexColor("#1F4E3D")
GREEN_DEEP = HexColor("#163A2D")
GREEN_MID = HexColor("#2C6B55")
GREEN_SOFT = HexColor("#E8EFE9")
ORANGE = HexColor("#E07B1F")
ORANGE_SOFT = HexColor("#FCEEDC")
CREAM = HexColor("#F5F2EA")
CREAM_SOFT = HexColor("#FBF9F4")
INK = HexColor("#161616")
MUTED = HexColor("#6B6B6B")
MUTED_SOFT = HexColor("#9A9591")
LINE = Color(22 / 255, 22 / 255, 22 / 255, alpha=0.10)
LINE_LIGHT = Color(245 / 255, 242 / 255, 234 / 255, alpha=0.18)

# ───────────────────── fonts ─────────────────────

_FONTS_REGISTERED = False


def _register_fonts() -> None:
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    try:
        pdfmetrics.registerFont(TTFont("Fraunces", str(FONTS_DIR / "fraunces.ttf")))
        pdfmetrics.registerFont(TTFont("Geist", str(FONTS_DIR / "geist.ttf")))
        # Variable fonts: register the same file twice so the bold style maps
        # to the same file (visually identical; weights can't be varied per-style
        # without separate static masters, but the lookup must succeed).
        pdfmetrics.registerFont(TTFont("Fraunces-Bold", str(FONTS_DIR / "fraunces.ttf")))
        pdfmetrics.registerFont(TTFont("Geist-Bold", str(FONTS_DIR / "geist.ttf")))
        pdfmetrics.registerFontFamily(
            "Fraunces", normal="Fraunces", bold="Fraunces-Bold",
            italic="Fraunces", boldItalic="Fraunces-Bold",
        )
        pdfmetrics.registerFontFamily(
            "Geist", normal="Geist", bold="Geist-Bold",
            italic="Geist", boldItalic="Geist-Bold",
        )
    except Exception:
        # Fall back to built-ins if font files are missing or corrupted.
        pass
    _FONTS_REGISTERED = True


def _font(family: str, fallback: str) -> str:
    """Return registered family name if available, else a built-in fallback."""
    return family if family in pdfmetrics.getRegisteredFontNames() else fallback


# ───────────────────── helpers ─────────────────────

DOMAIN_ORDER = ("strategy", "customers", "money", "operations", "talent")
DOMAIN_LABELS = {
    "strategy": "Strategy",
    "customers": "Customers",
    "money": "Money",
    "operations": "Operations",
    "talent": "Talent",
}
BAND_TONE_COLOR = {
    "A": (GREEN, CREAM, GREEN),       # bg, fg, border
    "B": (CREAM_SOFT, GREEN, GREEN),
    "C": (ORANGE_SOFT, ORANGE, ORANGE),
    "—": (CREAM_SOFT, MUTED, LINE),
}
MUSPER = {
    "address": "KN 12, Nyarugenge, Kigali, Rwanda",
    "phone": "+250 788 300 840",
    "email": "muspersolutions@musper.com",
}


def _slug(text: str) -> str:
    out = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_")
    return out or "report"


def _format_date(dt: datetime | None) -> str:
    dt = dt or datetime.now(timezone.utc)
    return dt.strftime("%d %B %Y")


def _tone_color(score: float) -> Color:
    if score >= 80:
        return GREEN
    if score >= 60:
        return GREEN_MID
    return ORANGE


# ───────────────────── custom flowables ─────────────────────

class HRule(Flowable):
    def __init__(self, width: float, color: Color = LINE, thickness: float = 0.4):
        super().__init__()
        self.width = width
        self.color = color
        self.thickness = thickness

    def wrap(self, _aw: float, _ah: float):
        return self.width, self.thickness

    def draw(self) -> None:
        c = self.canv
        c.setStrokeColor(self.color)
        c.setLineWidth(self.thickness)
        c.line(0, 0, self.width, 0)


class DomainBar(Flowable):
    """Single domain row: label + numeric on top, coloured bar underneath."""

    HEIGHT = 22

    def __init__(self, width: float, label: str, score: float):
        super().__init__()
        self.width = width
        self.label = label
        self.score = score

    def wrap(self, _aw: float, _ah: float):
        return self.width, self.HEIGHT

    def draw(self) -> None:
        c = self.canv
        sans = _font("Geist", "Helvetica")
        sans_b = _font("Geist-Bold", "Helvetica-Bold")
        serif = _font("Fraunces", "Times-Roman")
        # Label
        c.setFillColor(INK)
        c.setFont(sans_b, 9.5)
        c.drawString(0, 14, self.label)
        # Score on right
        score_int = int(round(self.score))
        score_text = str(score_int)
        c.setFillColor(INK)
        c.setFont(serif, 12)
        c.drawRightString(self.width - 24, 14, score_text)
        c.setFillColor(MUTED)
        c.setFont(sans, 8)
        c.drawRightString(self.width, 14, " / 100")
        # Bar background
        bar_y = 4
        bar_h = 4
        c.setFillColor(LINE)
        c.roundRect(0, bar_y, self.width, bar_h, bar_h / 2, stroke=0, fill=1)
        # Bar fill
        pct = max(0.0, min(1.0, self.score / 100.0))
        if pct > 0:
            c.setFillColor(_tone_color(self.score))
            c.roundRect(0, bar_y, max(bar_h, self.width * pct), bar_h, bar_h / 2, stroke=0, fill=1)


class BandBadgeWithScore(Flowable):
    """Round band badge (A/B/C) + large score number, used for headline."""

    HEIGHT = 50

    def __init__(self, width: float, band: str, score: float):
        super().__init__()
        self.width = width
        self.band = band
        self.score = score

    def wrap(self, _aw: float, _ah: float):
        return self.width, self.HEIGHT

    def draw(self) -> None:
        c = self.canv
        serif = _font("Fraunces", "Times-Roman")
        serif_b = _font("Fraunces-Bold", "Times-Bold")
        sans = _font("Geist", "Helvetica")
        bg, fg, border = BAND_TONE_COLOR.get(self.band or "—", BAND_TONE_COLOR["—"])

        # Badge circle
        r = 18
        cx, cy = r, self.HEIGHT / 2
        c.setFillColor(bg)
        c.setStrokeColor(border)
        c.setLineWidth(0.6)
        c.circle(cx, cy, r, stroke=1, fill=1)
        c.setFillColor(fg)
        c.setFont(serif_b, 18)
        c.drawCentredString(cx, cy - 6.5, self.band or "—")

        # Number + " / 100"
        score_int = int(round(self.score or 0))
        c.setFillColor(INK)
        c.setFont(serif, 26)
        x_num = cx + r + 14
        c.drawString(x_num, cy - 8, str(score_int))
        # Compute approx width of the number to place " / 100" right after
        num_w = pdfmetrics.stringWidth(str(score_int), serif, 26)
        c.setFillColor(MUTED)
        c.setFont(sans, 9)
        c.drawString(x_num + num_w + 3, cy - 6, " / 100")


class Sparkline(Flowable):
    """Hand-built revenue-trend sparkline. Expects a list of {period, revenue_mrwf}."""

    HEIGHT = 70

    def __init__(self, width: float, trend: list[dict[str, Any]]):
        super().__init__()
        self.width = width
        self.trend = trend or []

    def wrap(self, _aw: float, _ah: float):
        return self.width, self.HEIGHT

    def draw(self) -> None:
        if len(self.trend) < 2:
            return
        c = self.canv
        sans = _font("Geist", "Helvetica")
        sans_b = _font("Geist-Bold", "Helvetica-Bold")
        values = [float(p.get("revenue_mrwf", 0)) for p in self.trend]
        labels = [str(p.get("period", "")) for p in self.trend]
        v_max, v_min = max(values), min(values)
        v_range = (v_max - v_min) or 1
        pad_t, pad_b, pad_l, pad_r = 12, 18, 26, 14
        iw = self.width - pad_l - pad_r
        ih = self.HEIGHT - pad_t - pad_b
        n = len(values)

        coords = []
        for i, v in enumerate(values):
            x = pad_l + (i / (n - 1)) * iw
            y = pad_b + ((v - v_min) / v_range) * ih
            coords.append((x, y))

        # Gridline (midpoint)
        mid_y = pad_b + ih / 2
        c.setStrokeColor(Color(0.086, 0.086, 0.086, alpha=0.06))
        c.setDash(2, 3)
        c.setLineWidth(0.4)
        c.line(pad_l, mid_y, self.width - pad_r, mid_y)
        c.setDash()

        # Area fill (polygon)
        c.setFillColor(Color(31 / 255, 78 / 255, 61 / 255, alpha=0.08))
        path = c.beginPath()
        path.moveTo(coords[0][0], pad_b)
        for x, y in coords:
            path.lineTo(x, y)
        path.lineTo(coords[-1][0], pad_b)
        path.close()
        c.drawPath(path, stroke=0, fill=1)

        # Line
        c.setStrokeColor(GREEN)
        c.setLineWidth(1.6)
        c.setLineJoin(1)
        c.setLineCap(1)
        for i in range(len(coords) - 1):
            x1, y1 = coords[i]
            x2, y2 = coords[i + 1]
            c.line(x1, y1, x2, y2)

        # Dots
        for x, y in coords:
            c.setFillColor(CREAM)
            c.circle(x, y, 2.6, stroke=0, fill=1)
            c.setFillColor(ORANGE)
            c.circle(x, y, 2.0, stroke=0, fill=1)

        # Max / min value labels
        max_idx = values.index(v_max)
        min_idx = values.index(v_min)
        mx, my = coords[max_idx]
        c.setFillColor(GREEN)
        c.setFont(sans_b, 6.5)
        c.drawCentredString(mx, my + 6, f"{int(v_max)}M")
        mnx, mny = coords[min_idx]
        c.setFillColor(MUTED_SOFT)
        c.setFont(sans, 6.5)
        c.drawCentredString(mnx, mny - 9, f"{int(v_min)}M")

        # Period labels
        c.setFillColor(MUTED_SOFT)
        c.setFont(sans, 6.5)
        for i, lbl in enumerate(labels):
            x = pad_l + (i / (n - 1)) * iw
            c.drawCentredString(x, 4, lbl)


# ───────────────────── paragraph styles ─────────────────────


def _styles() -> dict[str, ParagraphStyle]:
    sans = _font("Geist", "Helvetica")
    sans_b = _font("Geist-Bold", "Helvetica-Bold")
    serif = _font("Fraunces", "Times-Roman")
    serif_b = _font("Fraunces-Bold", "Times-Bold")
    return {
        "eyebrow": ParagraphStyle(
            "Eyebrow", fontName=sans_b, fontSize=8, textColor=GREEN,
            leading=10, spaceAfter=0,
        ),
        "h2": ParagraphStyle(
            "H2", fontName=serif, fontSize=18, leading=22, textColor=INK,
            spaceBefore=4, spaceAfter=10,
        ),
        "h3": ParagraphStyle(
            "H3", fontName=serif, fontSize=13, leading=16, textColor=INK,
            spaceBefore=0, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "Body", fontName=sans, fontSize=10, leading=14, textColor=INK,
            spaceAfter=4,
        ),
        "body-soft": ParagraphStyle(
            "BodySoft", fontName=sans, fontSize=9.5, leading=14, textColor=MUTED,
        ),
        "label": ParagraphStyle(
            "Label", fontName=sans_b, fontSize=7.5, leading=10, textColor=MUTED,
        ),
        "label-on-dark": ParagraphStyle(
            "LabelDark", fontName=sans_b, fontSize=7.5, leading=10,
            textColor=Color(0.96, 0.95, 0.92, alpha=0.55),
        ),
        "value": ParagraphStyle(
            "Value", fontName=sans_b, fontSize=10.5, leading=13, textColor=INK,
        ),
        "value-sub": ParagraphStyle(
            "ValueSub", fontName=sans, fontSize=8.5, leading=11, textColor=MUTED_SOFT,
        ),
        "note": ParagraphStyle(
            "Note", fontName=sans, fontSize=8.5, leading=12, textColor=MUTED,
        ),
        "summary": ParagraphStyle(
            "Summary", fontName=sans, fontSize=11, leading=16, textColor=INK,
        ),
        "flag": ParagraphStyle(
            "Flag", fontName=sans, fontSize=10.5, leading=15, textColor=INK,
        ),
        "action-title": ParagraphStyle(
            "ActionTitle", fontName=serif, fontSize=13, leading=16, textColor=INK,
        ),
        "action-detail": ParagraphStyle(
            "ActionDetail", fontName=sans, fontSize=10, leading=14, textColor=MUTED,
        ),
        "action-meta": ParagraphStyle(
            "ActionMeta", fontName=sans, fontSize=8.5, leading=12, textColor=MUTED,
        ),
        "pill": ParagraphStyle(
            "Pill", fontName=sans, fontSize=9.5, leading=13, textColor=INK,
        ),
        "close": ParagraphStyle(
            "Close", fontName=sans, fontSize=8.5, leading=13, textColor=MUTED,
        ),
    }


# ───────────────────── cover + chrome ─────────────────────


def _draw_cover(
    canvas, doc, *, client: dict, issued_date: str, report_ref: str
) -> None:
    w, h = A4
    serif = _font("Fraunces", "Times-Roman")
    serif_b = _font("Fraunces-Bold", "Times-Bold")
    sans = _font("Geist", "Helvetica")
    sans_b = _font("Geist-Bold", "Helvetica-Bold")

    # Background
    canvas.setFillColor(GREEN)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)

    # Decorative rings (top right)
    canvas.setStrokeColor(Color(0.96, 0.95, 0.92, alpha=0.10))
    canvas.setLineWidth(0.6)
    canvas.circle(w + 5, h + 5, 200, fill=0, stroke=1)
    canvas.setStrokeColor(Color(0.88, 0.48, 0.12, alpha=0.45))
    canvas.setLineWidth(0.8)
    canvas.circle(w + 5, h + 5, 140, fill=0, stroke=1)

    # Wordmark (top left)
    badge_x, badge_y = 22 * mm, h - 30 * mm
    canvas.setFillColor(CREAM)
    canvas.circle(badge_x + 8, badge_y + 8, 9, stroke=0, fill=1)
    canvas.setFillColor(GREEN)
    canvas.setFont(serif_b, 14)
    canvas.drawCentredString(badge_x + 8, badge_y + 4, "M")
    # Orange dot accent
    canvas.setFillColor(ORANGE)
    canvas.circle(badge_x + 16, badge_y + 16, 2.4, stroke=0, fill=1)
    # Wordmark text
    canvas.setFillColor(CREAM)
    canvas.setFont(serif, 14)
    canvas.drawString(badge_x + 24, badge_y + 4, "Musper Solutions")

    # Eyebrow
    eyebrow_y = h - 110 * mm
    canvas.setFillColor(ORANGE)
    canvas.circle(24 * mm, eyebrow_y + 3, 1.4, stroke=0, fill=1)
    canvas.setFillColor(ORANGE)
    canvas.setFont(sans_b, 8)
    canvas.drawString(28 * mm, eyebrow_y, "INTEGRATED  DIAGNOSTIC  REPORT")

    # Title
    canvas.setFillColor(CREAM)
    canvas.setFont(serif, 32)
    title_lines = [
        "Where the business stands today,",
        "and the moves that matter next.",
    ]
    ty = eyebrow_y - 18
    for line in title_lines:
        ty -= 34
        canvas.drawString(22 * mm, ty, line)

    # Prepared-for block
    block_y = ty - 50
    canvas.setFillColor(Color(0.96, 0.95, 0.92, alpha=0.7))
    canvas.setFont(sans, 10)
    canvas.drawString(22 * mm, block_y, "Prepared for")
    canvas.setFillColor(CREAM)
    canvas.setFont(serif, 22)
    canvas.drawString(22 * mm, block_y - 26, client.get("business_name", "—"))
    canvas.setFillColor(Color(0.96, 0.95, 0.92, alpha=0.85))
    canvas.setFont(sans, 10)
    sub_line = client.get("contact_name") or "Founder & Owner"
    location = client.get("location") or ""
    sector = client.get("sector") or ""
    sub2 = f"{location}{' · ' if location and sector else ''}{sector}"
    canvas.drawString(22 * mm, block_y - 42, sub_line)
    if sub2:
        canvas.drawString(22 * mm, block_y - 56, sub2)

    # Footer meta row
    foot_y = 24 * mm
    canvas.setStrokeColor(Color(0.96, 0.95, 0.92, alpha=0.18))
    canvas.setLineWidth(0.4)
    canvas.line(22 * mm, foot_y + 16, w - 22 * mm, foot_y + 16)
    canvas.setFillColor(Color(0.96, 0.95, 0.92, alpha=0.55))
    canvas.setFont(sans_b, 7.5)
    canvas.drawString(22 * mm, foot_y + 6, "ISSUED")
    canvas.drawRightString(w - 22 * mm, foot_y + 6, "REFERENCE")
    canvas.setFillColor(CREAM)
    canvas.setFont(sans, 9.5)
    canvas.drawString(22 * mm, foot_y - 6, issued_date)
    canvas.drawRightString(w - 22 * mm, foot_y - 6, report_ref)


def _draw_main_chrome(canvas, doc, *, business_name: str) -> None:
    w, h = A4
    sans = _font("Geist", "Helvetica")
    # Footer: confidential + page numbers
    y = 12 * mm
    canvas.setFillColor(MUTED_SOFT)
    canvas.setFont(sans, 7.5)
    canvas.drawString(
        18 * mm, y,
        f"Confidential — prepared solely for {business_name}",
    )
    canvas.drawRightString(
        w - 18 * mm, y,
        f"Page {canvas.getPageNumber()}",
    )


# ───────────────────── main render ─────────────────────


def render_report_pdf(
    *,
    client: dict[str, Any],
    report: dict[str, Any],
) -> tuple[bytes, str]:
    _register_fonts()
    styles = _styles()

    issued_dt = report.get("created_at") or datetime.now(timezone.utc)
    if isinstance(issued_dt, str):
        try:
            issued_dt = datetime.fromisoformat(issued_dt.replace("Z", "+00:00"))
        except ValueError:
            issued_dt = datetime.now(timezone.utc)

    report_id = str(report.get("id", uuid.uuid4()))
    report_ref = f"MS-{report_id[:8].upper()}"
    issued_date = _format_date(issued_dt)
    business_name = client.get("business_name", "—")

    # Document setup
    buffer = BytesIO()
    page_w, page_h = A4
    margin = 18 * mm
    frame_x, frame_y = margin, 22 * mm
    frame_w = page_w - 2 * margin
    frame_h = page_h - 22 * mm - 22 * mm  # top + bottom

    main_frame = Frame(frame_x, frame_y, frame_w, frame_h, id="main", showBoundary=0)
    empty_frame = Frame(0, 0, page_w, page_h, id="cover", showBoundary=0)

    def on_cover(c, d):
        _draw_cover(c, d, client=client, issued_date=issued_date, report_ref=report_ref)

    def on_main(c, d):
        _draw_main_chrome(c, d, business_name=business_name)

    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        title=f"Musper Diagnostic Report — {business_name}",
        author="Musper Solutions",
        subject="Integrated Diagnostic Report",
        leftMargin=margin,
        rightMargin=margin,
        topMargin=22 * mm,
        bottomMargin=22 * mm,
    )
    doc.addPageTemplates(
        [
            PageTemplate(id="cover", frames=[empty_frame], onPage=on_cover),
            PageTemplate(id="main", frames=[main_frame], onPage=on_main),
        ]
    )

    flow: list[Any] = []
    # Cover page is emitted by the first PageTemplate. We add a Spacer + PageBreak
    # to commit it, then switch to the main template for the content.
    flow.append(Spacer(0, 1))
    flow.append(NextPageTemplate("main"))
    flow.append(PageBreak())

    # ── Business snapshot section ─────────────────────────────
    flow.append(_section_eyebrow_title("Business snapshot", "The business at a glance.", styles))
    flow.append(_snapshot_table(client, styles, frame_w))
    flow.append(Spacer(0, 12))

    # Revenue trend
    if client.get("revenue_trend"):
        flow.append(_revenue_card(client["revenue_trend"], styles, frame_w))
        flow.append(Spacer(0, 16))

    # ── Headline scores ─────────────────────────────
    flow.append(_section_eyebrow_title("Headline scores", "The numbers, in two views.", styles))
    flow.append(_headline_table(report.get("headline", {}), styles, frame_w))
    flow.append(Spacer(0, 18))

    # ── Domain breakdown (next page) ─────────────────────────────
    flow.append(PageBreak())
    flow.append(_section_eyebrow_title(
        "Domain breakdown", "Where the business is strong, where it is stretched.", styles,
    ))
    for d in DOMAIN_ORDER:
        s = float(report.get("domains", {}).get(d, 0))
        flow.append(DomainBar(frame_w, DOMAIN_LABELS[d], s))
        flow.append(Spacer(0, 8))
    flow.append(Spacer(0, 8))

    # ── Summary ─────────────────────────────
    if report.get("summary"):
        flow.append(_section_eyebrow_title("Summary", "The picture, in plain language.", styles))
        flow.append(_summary_card(report["summary"], styles, frame_w))
        flow.append(Spacer(0, 18))

    # ── Red flags (next page) ─────────────────────────────
    red_flags = report.get("red_flags") or []
    if red_flags:
        flow.append(PageBreak())
        flow.append(_section_eyebrow_title(
            "Red flags", "Issues worth surfacing now.", styles, eyebrow_color=ORANGE,
        ))
        for f in red_flags:
            flow.append(_flag_box(f, styles, frame_w))
            flow.append(Spacer(0, 8))
        flow.append(Spacer(0, 10))

    # ── Priority actions ─────────────────────────────
    actions = report.get("priority_actions") or []
    if actions:
        flow.append(_section_eyebrow_title(
            "Priority actions", "What to do in the next 90 days.", styles,
        ))
        for i, a in enumerate(actions, 1):
            flow.append(_action_block(i, a, styles, frame_w))
            flow.append(Spacer(0, 10))
        flow.append(Spacer(0, 8))

    # ── Coaching topics ─────────────────────────────
    topics = report.get("suggested_topics") or []
    if topics:
        flow.append(_section_eyebrow_title(
            "Suggested coaching topics", "Where Musper can go deeper.", styles,
        ))
        flow.append(_pill_row(topics, styles, frame_w))
        flow.append(Spacer(0, 18))

    # ── Closing footer line ─────────────────────────────
    flow.append(HRule(frame_w))
    flow.append(Spacer(0, 6))
    closing = (
        f"<b>Musper Solutions Ltd.</b> &nbsp;·&nbsp; {MUSPER['address']} &nbsp;·&nbsp; "
        f"{MUSPER['phone']} &nbsp;·&nbsp; {MUSPER['email']}<br/>"
        f"This report was prepared confidentially for {business_name} on {issued_date}. "
        "Please do not share without consent."
    )
    flow.append(Paragraph(closing, styles["close"]))

    doc.build(flow)

    business_slug = _slug(business_name)
    date_slug = issued_dt.strftime("%Y-%m-%d")
    filename = f"Musper_Diagnostic_{business_slug}_{date_slug}.pdf"
    return buffer.getvalue(), filename


# ───────────────────── small builders ─────────────────────


def _section_eyebrow_title(
    eyebrow: str, title: str, styles: dict, eyebrow_color: Color | None = None
) -> Table:
    eb = styles["eyebrow"]
    if eyebrow_color is not None:
        eb = ParagraphStyle("EyebrowCustom", parent=eb, textColor=eyebrow_color)
    rows = [
        [Paragraph(f"●  {eyebrow.upper()}", eb)],
        [Paragraph(title, styles["h2"])],
    ]
    t = Table(rows, colWidths=["*"])
    t.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, 0), 0),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                ("TOPPADDING", (0, 1), (-1, 1), 0),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
            ]
        )
    )
    return t


def _snapshot_table(client: dict, styles: dict, frame_w: float) -> Table:
    def cell(label: str, value: str, sub: str = "") -> list:
        items = [
            Paragraph(label.upper(), styles["label"]),
            Paragraph(value, styles["value"]),
        ]
        if sub:
            items.append(Paragraph(sub, styles["value-sub"]))
        return items

    rows = [
        [
            cell("Sector", client.get("sector") or "—"),
            cell("Location", client.get("location") or "—"),
        ],
        [
            cell(
                "Headcount",
                str(client.get("employee_count")) if client.get("employee_count") is not None else "—",
                f"{client.get('business_size').capitalize()} business" if client.get("business_size") else "",
            ),
            cell(
                "Founded",
                str(client.get("founded_year") or "—"),
                client.get("revenue_band") or "",
            ),
        ],
    ]
    col_w = frame_w / 2
    t = Table(rows, colWidths=[col_w, col_w])
    t.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 0), (-1, 0), 0.5, LINE),
                ("LINEBELOW", (0, -1), (-1, -1), 0.5, LINE),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, LINE),
                ("LINEAFTER", (0, 0), (0, -1), 0.5, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return t


def _revenue_card(trend: list[dict], styles: dict, frame_w: float) -> Table:
    eb = Paragraph("●  REVENUE TREND", styles["eyebrow"])
    right = Paragraph(
        "Quarterly · millions of RWF",
        ParagraphStyle("RightSmall", parent=styles["body-soft"], fontSize=8.5,
                       alignment=2, textColor=MUTED),
    )
    head = Table([[eb, right]], colWidths=[frame_w / 2 - 18, frame_w / 2 - 18])
    head.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    spark = Sparkline(frame_w - 36, trend)

    card = Table([[head], [spark]], colWidths=[frame_w])
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CREAM_SOFT),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return card


def _headline_card(label: str, band: str, score: float, note: str, styles: dict, w: float) -> Table:
    badge = BandBadgeWithScore(w - 32, band, score)
    rows = [
        [Paragraph(label.upper(), styles["label"])],
        [badge],
        [Paragraph(note, styles["note"])],
    ]
    card = Table(rows, colWidths=[w - 32])
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CREAM),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, 0), 16),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 12),
        ("TOPPADDING", (0, 2), (-1, 2), 0),
        ("BOTTOMPADDING", (0, 2), (-1, 2), 16),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return card


def _headline_table(headline: dict, styles: dict, frame_w: float) -> Table:
    grow = _headline_card(
        "GROW Overall",
        headline.get("grow_band", "—"),
        float(headline.get("grow_overall", 0)),
        "Composite across Strategy, Customers, Money, Operations, Talent.",
        styles, frame_w / 2,
    )
    finance = _headline_card(
        "Finance Readiness",
        headline.get("finance_band", "—"),
        float(headline.get("finance_readiness", 0)),
        "Weighted toward Money, Operations, and Strategy.",
        styles, frame_w / 2,
    )
    t = Table([[grow, finance]], colWidths=[frame_w / 2, frame_w / 2])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 6),
        ("LEFTPADDING", (1, 0), (1, 0), 6),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _summary_card(text: str, styles: dict, frame_w: float) -> Table:
    p = Paragraph(text, styles["summary"])
    t = Table([[p]], colWidths=[frame_w])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GREEN_SOFT),
        ("LINEBEFORE", (0, 0), (0, -1), 2, GREEN),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _flag_box(text: str, styles: dict, frame_w: float) -> Table:
    p = Paragraph(text, styles["flag"])
    t = Table([[p]], colWidths=[frame_w])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ORANGE_SOFT),
        ("BOX", (0, 0), (-1, -1), 0.5, Color(0.88, 0.48, 0.12, alpha=0.30)),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _action_block(num: int, a: dict, styles: dict, frame_w: float) -> KeepTogether:
    head = Table(
        [
            [
                Paragraph(f"0{num}",
                          ParagraphStyle(
                              "ActionNum", parent=styles["label"],
                              fontName=_font("Geist", "Helvetica"),
                              fontSize=9, textColor=MUTED, leading=12,
                          )),
                Paragraph(a.get("title", ""), styles["action-title"]),
            ]
        ],
        colWidths=[24, frame_w - 24 - 28],
    )
    head.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    rows: list[Any] = [head]
    if a.get("detail"):
        d = Paragraph(a["detail"], styles["action-detail"])
        d_wrap = Table([[d]], colWidths=[frame_w - 28])
        d_wrap.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 24),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        rows.append(d_wrap)

    if a.get("owner") or a.get("horizon"):
        meta_html = []
        if a.get("owner"):
            meta_html.append(
                f'<font color="#9A9591">Owner</font>  '
                f'<b><font color="#161616">{a["owner"]}</font></b>'
            )
        if a.get("horizon"):
            meta_html.append(
                f'<font color="#9A9591">Horizon</font>  '
                f'<b><font color="#161616">{a["horizon"]}</font></b>'
            )
        meta = Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;".join(meta_html), styles["action-meta"])
        m_wrap = Table([[meta]], colWidths=[frame_w - 28])
        m_wrap.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 24),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        rows.append(m_wrap)

    body = Table([[r] for r in rows], colWidths=[frame_w - 28])
    body.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CREAM),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (0, 0), 12),
        ("TOPPADDING", (0, 1), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -2), 0),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return KeepTogether(body)


def _pill_row(topics: list[str], styles: dict, frame_w: float) -> Table:
    """Render coaching topics as little pill-shaped boxes wrapping to multiple rows."""
    # Simple approach: build rows of pills as separate Tables, packed greedily by width.
    sans = _font("Geist", "Helvetica")
    estimate_w = lambda t: pdfmetrics.stringWidth(t, sans, 9.5) + 22  # padding
    rows: list[list[Any]] = [[]]
    used = 0.0
    gap = 6
    for t in topics:
        w = estimate_w(t)
        if used + w + gap > frame_w and rows[-1]:
            rows.append([])
            used = 0.0
        rows[-1].append(t)
        used += w + gap

    pills_per_row: list[Table] = []
    for row in rows:
        if not row:
            continue
        cells = []
        widths = []
        for txt in row:
            p = Paragraph(txt, styles["pill"])
            cells.append(p)
            widths.append(estimate_w(txt))
        # Pad row to full width
        cells.append(Paragraph("", styles["pill"]))
        widths.append(max(0, frame_w - sum(widths) - gap * (len(row) - 1) - gap))
        inner = Table([cells], colWidths=widths)
        styles_row = []
        for i in range(len(row)):
            styles_row.extend([
                ("BACKGROUND", (i, 0), (i, 0), CREAM),
                ("BOX", (i, 0), (i, 0), 0.5, LINE),
                ("LEFTPADDING", (i, 0), (i, 0), 11),
                ("RIGHTPADDING", (i, 0), (i, 0), 11),
                ("TOPPADDING", (i, 0), (i, 0), 4),
                ("BOTTOMPADDING", (i, 0), (i, 0), 4),
            ])
        styles_row.append(("LEFTPADDING", (len(row), 0), (len(row), 0), 0))
        styles_row.append(("RIGHTPADDING", (len(row), 0), (len(row), 0), 0))
        styles_row.append(("VALIGN", (0, 0), (-1, -1), "TOP"))
        inner.setStyle(TableStyle(styles_row))
        pills_per_row.append(inner)

    outer = Table([[r] for r in pills_per_row], colWidths=[frame_w])
    outer.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return outer
