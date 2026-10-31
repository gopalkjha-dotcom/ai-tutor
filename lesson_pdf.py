"""Turn a tutor conversation into a textbook-style PDF.

Displayed equations ($$ ... $$) are drawn as real formulas with matplotlib's maths
renderer; inline maths ($ ... $) becomes readable text such as x² or 6×2.
"""
import io
import os
import re
from datetime import date

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from fpdf import FPDF  # noqa: E402

FONT_DIR = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
INK = (20, 42, 67)        # matches the app's text colour
ACCENT = (22, 140, 145)   # matches the app's primary colour
GREY = (110, 120, 130)

SUPERSCRIPT = str.maketrans("0123456789+-=()niax", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱᵃˣ")
SUBSCRIPT = str.maketrans("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")
SYMBOLS = {
    r"\times": "×", r"\cdot": "·", r"\div": "÷", r"\pm": "±", r"\le": "≤", r"\leq": "≤",
    r"\ge": "≥", r"\geq": "≥", r"\ne": "≠", r"\neq": "≠", r"\approx": "≈", r"\infty": "∞",
    r"\pi": "π", r"\theta": "θ", r"\alpha": "α", r"\beta": "β", r"\Delta": "Δ", r"\delta": "δ",
    r"\sigma": "σ", r"\mu": "μ", r"\lambda": "λ", r"\to": "→", r"\rightarrow": "→",
    r"\Rightarrow": "⇒", r"\sum": "Σ", r"\sqrt": "√", r"\%": "%", r"\,": " ", r"\;": " ",
    r"\quad": "  ", r"\left": "", r"\right": "", r"\text": "", r"\mathrm": "",
}


def inline_to_text(tex):
    """Best-effort conversion of short inline LaTeX to readable Unicode text."""
    s = tex
    for _ in range(3):
        s = re.sub(r"\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", s)
    s = re.sub(r"\\sqrt\{([^{}]*)\}", r"√(\1)", s)
    for name in sorted(SYMBOLS, key=len, reverse=True):
        s = s.replace(name, SYMBOLS[name])
    s = re.sub(r"\^\{([^{}]*)\}", lambda m: _script(m.group(1), SUPERSCRIPT, "^"), s)
    s = re.sub(r"\^(\w)", lambda m: _script(m.group(1), SUPERSCRIPT, "^"), s)
    s = re.sub(r"_\{([^{}]*)\}", lambda m: _script(m.group(1), SUBSCRIPT, "_"), s)
    s = re.sub(r"_(\w)", lambda m: _script(m.group(1), SUBSCRIPT, "_"), s)
    s = s.replace("{", "").replace("}", "").replace("\\", "")
    s = re.sub(r"\(([A-Za-z0-9.]+)\)/\(([A-Za-z0-9.]+)\)", r"\1/\2", s)  # (a)/(b) -> a/b
    return s


def _script(text, table, marker):
    """Use real superscript/subscript characters when every character has one."""
    if text and all(ord(c) in table for c in text):
        return text.translate(table)
    return marker + "(" + text + ")" if len(text) > 1 else marker + text


def _mathtext_safe(tex):
    """Adjust LaTeX into the subset matplotlib can draw."""
    # Full-size fractions, as in a printed textbook.
    s = tex.replace(r"\tfrac", r"\frac").replace(r"\dfrac", r"\frac").replace(r"\frac", r"\dfrac")
    s = s.replace(r"\left", "").replace(r"\right", "")
    s = re.sub(r"(\d),(\d{3})", r"\1{,}\2", s)  # thousands separator without a stray space
    s = re.sub(r"\\text\{([^{}]*)\}", lambda m: r"\mathrm{" + m.group(1).replace(" ", r"\ ") + "}", s)
    s = s.replace(r"\,", r"\ ").replace(r"\;", r"\ ").replace(r"\!", "")
    return s.strip()


def equation_rows(tex):
    """Split an aligned/gathered block into separate rows, keeping the '=' alignment marker."""
    body = re.sub(r"\\begin\{(aligned|align\*?|gathered|array|cases|split)\}(\{[^}]*\})?", "", tex)
    body = re.sub(r"\\end\{(aligned|align\*?|gathered|array|cases|split)\}", "", body)
    rows = [r.strip() for r in re.split(r"\\\\", body) if r.strip()]
    return rows or [tex.strip()]


def render_equation(tex, fontsize=15):
    """Return PNG bytes of one equation row, or None if matplotlib cannot draw it."""
    fig = plt.figure(figsize=(0.01, 0.01))
    try:
        fig.text(0, 0, f"${_mathtext_safe(tex)}$", fontsize=fontsize, color=[c / 255 for c in INK])
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=220, bbox_inches="tight", pad_inches=0.04, transparent=True)
        return buf.getvalue()
    except Exception:
        return None
    finally:
        plt.close(fig)


class LessonPDF(FPDF):
    def __init__(self, title):
        super().__init__(format="A4")
        self.lesson_title = title
        self.set_margins(20, 18, 20)
        self.set_auto_page_break(True, margin=18)
        self.add_font("Body", "", os.path.join(FONT_DIR, "DejaVuSans.ttf"))
        self.add_font("Body", "B", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"))
        self.add_font("Body", "I", os.path.join(FONT_DIR, "DejaVuSans-Oblique.ttf"))
        self.add_font("Mono", "", os.path.join(FONT_DIR, "DejaVuSansMono.ttf"))

    def header(self):
        self.set_font("Body", "B", 9)
        self.set_text_color(*ACCENT)
        self.cell(0, 6, "GJ AI Tutor · GJ Perspective", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*ACCENT)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-13)
        self.set_font("Body", "", 8)
        self.set_text_color(*GREY)
        self.cell(0, 6, f"AI-generated study support; check important answers against your course material.   Page {self.page_no()}", align="C")


def _paragraph(pdf, text):
    """Write a paragraph with **bold** support and inline maths converted to text."""
    text = re.sub(r"(?<!\$)\$([^$\n]+?)\$(?!\$)", lambda m: inline_to_text(m.group(1)), text)
    text = re.sub(r"^#{1,6}\s*", "", text)  # headings become bold lines
    bullet = re.match(r"^\s*(?:[-*+]|(\d+)[.)])\s+(.*)$", text)
    pdf.set_font("Body", "", 11)
    pdf.set_text_color(*INK)
    if bullet:
        marker = (bullet.group(1) + ".") if bullet.group(1) else "•"
        pdf.set_x(pdf.l_margin + 4)
        pdf.cell(6, 6, marker)
        pdf.multi_cell(0, 6, bullet.group(2), markdown=True, new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.multi_cell(0, 6, text, markdown=True, new_x="LMARGIN", new_y="NEXT")


MM_PER_PX = 25.4 / 220


def _image(png):
    """Return (png, width_mm, height_mm) for rendered equation bytes."""
    from PIL import Image
    img = Image.open(io.BytesIO(png))
    return png, img.width * MM_PER_PX, img.height * MM_PER_PX


def _equation(pdf, tex):
    """Draw a displayed equation centred; multi-row working is aligned on the '&' (=) column."""
    usable = pdf.w - pdf.l_margin - pdf.r_margin
    rows = []
    for row in equation_rows(tex):
        left, _, right = row.partition("&") if "&" in row else ("", "", row)
        left_img = _image(p) if left.strip() and (p := render_equation(left)) else None
        right_png = render_equation(right.replace("&", ""))
        if right_png is None or (left.strip() and left_img is None):
            rows.append(("code", row))  # readable fallback rather than failing the whole PDF
        else:
            rows.append(("eq", left_img, _image(right_png)))

    eq_rows = [r for r in rows if r[0] == "eq"]
    lw = max((r[1][1] for r in eq_rows if r[1]), default=0)
    rw = max((r[2][1] for r in eq_rows), default=0)
    scale = min(1.0, usable / (lw + rw)) if (lw + rw) else 1.0
    total_h = sum(max(r[2][2], r[1][2] if r[1] else 0) * scale + 2.2 for r in eq_rows) + 6 * (len(rows) - len(eq_rows))
    if pdf.get_y() + min(total_h, pdf.h * 0.6) > pdf.h - pdf.b_margin:
        pdf.add_page()  # keep a block of working together on one page
    column = pdf.l_margin + (usable - (lw + rw) * scale) / 2 + lw * scale  # x of the '=' column

    for r in rows:
        if r[0] == "code":
            pdf.set_font("Mono", "", 10)
            pdf.set_text_color(*INK)
            pdf.multi_cell(0, 5.5, r[1], align="C", new_x="LMARGIN", new_y="NEXT")
            continue
        _, left_img, (rpng, rw_mm, rh_mm) = r
        h = max(rh_mm, left_img[2] if left_img else 0) * scale
        y = pdf.get_y() + 1
        if left_img:
            lpng, lw_mm, lh_mm = left_img
            pdf.image(io.BytesIO(lpng), x=column - lw_mm * scale, y=y + (h - lh_mm * scale) / 2, w=lw_mm * scale)
            x = column
        else:
            x = pdf.l_margin + (usable - rw_mm * scale) / 2 if lw == 0 else column
        pdf.image(io.BytesIO(rpng), x=x, y=y + (h - rh_mm * scale) / 2, w=rw_mm * scale)
        pdf.set_y(y + h + 1.2)
    pdf.ln(1.5)


def _message_body(pdf, content):
    lines = content.split("\n")
    i, para = 0, []

    def flush():
        if para:
            _paragraph(pdf, " ".join(p.strip() for p in para))
            pdf.ln(1.5)
            para.clear()

    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("$$"):
            flush()
            body = stripped[2:]
            while "$$" not in body and i + 1 < len(lines):
                i += 1
                body += "\n" + lines[i].strip()
            eq, _, after = body.partition("$$")
            _equation(pdf, eq.strip())
            if after.strip():
                para.append(after.strip())
        elif not stripped:
            flush()
        elif re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", lines[i]) or stripped.startswith("#"):
            flush()
            para.append(stripped)
            flush()
        else:
            para.append(stripped)
        i += 1
    flush()


def lesson_pdf(messages, subject, mode):
    """Build the PDF and return it as bytes."""
    pdf = LessonPDF(f"{subject} · {mode}")
    pdf.add_page()
    pdf.set_font("Body", "B", 18)
    pdf.set_text_color(*INK)
    pdf.multi_cell(0, 9, f"{subject} · {mode}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Body", "", 9)
    pdf.set_text_color(*GREY)
    pdf.cell(0, 6, f"Lesson notes · {date.today():%d %B %Y}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    for m in messages:
        is_tutor = m["role"] == "assistant"
        pdf.set_font("Body", "B", 10)
        pdf.set_text_color(*(ACCENT if is_tutor else GREY))
        pdf.cell(0, 7, "Tutor" if is_tutor else "You", new_x="LMARGIN", new_y="NEXT")
        if is_tutor:
            _message_body(pdf, m["content"])
        else:
            pdf.set_font("Body", "I", 10.5)
            pdf.set_text_color(*GREY)
            question = m["content"].replace("📷 *(photo attached)*", "[photo attached]").strip()
            question = re.sub(r"\$+([^$]+?)\$+", lambda q: inline_to_text(q.group(1)), question)
            pdf.multi_cell(0, 5.5, question, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
    return bytes(pdf.output())
