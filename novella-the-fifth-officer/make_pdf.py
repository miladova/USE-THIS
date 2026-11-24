#!/usr/bin/env python3
"""
Typeset THE FIFTH OFFICER as a 6x9in PDF from the markdown chapters.

Deps:  pip install reportlab
Run:   python3 make_pdf.py
Out:   The-Fifth-Officer.pdf
"""

import pathlib
import re

from reportlab.lib.colors import Color, black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch as IN
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = pathlib.Path(__file__).parent
FONTS = ROOT / "fonts"

PAGE_W, PAGE_H = 6 * IN, 9 * IN
M_TOP, M_BOT = 0.85 * IN, 0.80 * IN
M_SIDE = 0.80 * IN
TEXT_W = PAGE_W - 2 * M_SIDE

INK = Color(0.10, 0.09, 0.08)
FAINT = Color(0.45, 0.43, 0.40)

# ---------------------------------------------------------------- fonts
pdfmetrics.registerFont(TTFont("EBG", FONTS / "EBGaramond-Regular.ttf"))
pdfmetrics.registerFont(TTFont("EBG-Bold", FONTS / "EBGaramond-SemiBold.ttf"))
pdfmetrics.registerFont(TTFont("EBG-Italic", FONTS / "EBGaramond-Italic.ttf"))
pdfmetrics.registerFont(TTFont("EBG-BoldItalic", FONTS / "EBGaramond-SemiBoldItalic.ttf"))
pdfmetrics.registerFontFamily("EBG", normal="EBG", bold="EBG-Bold",
                              italic="EBG-Italic", boldItalic="EBG-BoldItalic")

BODY = ParagraphStyle("body", fontName="EBG", fontSize=11.4, leading=16.2,
                      alignment=TA_JUSTIFY, firstLineIndent=13, textColor=INK,
                      spaceBefore=0, spaceAfter=0)
BODY_FIRST = ParagraphStyle("body1", parent=BODY, firstLineIndent=0)
SCENE = ParagraphStyle("scene", parent=BODY, alignment=TA_CENTER, firstLineIndent=0,
                       textColor=FAINT, spaceBefore=9, spaceAfter=9)
QUOTE = ParagraphStyle("quote", parent=BODY, leftIndent=22, rightIndent=22,
                       firstLineIndent=0, fontName="EBG-Italic", fontSize=10.6,
                       leading=15, textColor=INK, spaceBefore=7, spaceAfter=7)
NUMERAL = ParagraphStyle("num", fontName="EBG", fontSize=15, leading=18,
                         alignment=TA_CENTER, textColor=FAINT, spaceAfter=10)
CH_TITLE = ParagraphStyle("cht", fontName="EBG", fontSize=16.5, leading=21,
                          alignment=TA_CENTER, textColor=INK, spaceAfter=2)
CH_DATE = ParagraphStyle("chd", fontName="EBG-Italic", fontSize=9.6, leading=13,
                         alignment=TA_CENTER, textColor=FAINT, spaceBefore=8)
FRONT_TITLE = ParagraphStyle("ft", fontName="EBG", fontSize=31, leading=36,
                             alignment=TA_CENTER, textColor=INK)
FRONT_SUB = ParagraphStyle("fs", fontName="EBG-Italic", fontSize=12.5, leading=17,
                           alignment=TA_CENTER, textColor=FAINT)
EPI = ParagraphStyle("epi", fontName="EBG-Italic", fontSize=11.5, leading=17,
                     alignment=TA_CENTER, textColor=INK)
EPI_ATT = ParagraphStyle("epia", fontName="EBG", fontSize=9.2, leading=13,
                         alignment=TA_CENTER, textColor=FAINT)
TOCH = ParagraphStyle("toch", fontName="EBG", fontSize=17, leading=22,
                      alignment=TA_CENTER, spaceAfter=26, textColor=INK)


# ---------------------------------------------------------------- markup
def smart(text: str) -> str:
    text = re.sub(r"(?<=[\s(\[*\u2014\u2013])'(\d\d)", "\u2019\\1", text)
    text = re.sub(r'(^|[\s(\[*\u2014\u2013])"', "\\1\u201c", text)
    text = text.replace('"', "\u201d")
    text = re.sub(r"(^|[\s(\[*\u2014\u2013])'", "\\1\u2018", text)
    return text.replace("'", "\u2019")


def inline(text: str) -> str:
    text = smart(text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text, flags=re.S)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text, flags=re.S)
    return text


def spaced_caps(s: str) -> str:
    out = []
    for ch in s.upper():
        out.append("\u2009" if ch != " " else "\u2002\u2002")
        out.append(ch)
    return "".join(out)


# ---------------------------------------------------------------- parsing
def load_chapters():
    out = []
    for p in sorted((ROOT / "chapters").glob("*.md")):
        lines = p.read_text(encoding="utf-8").splitlines()
        numeral = lines[0].lstrip("# ").strip()
        title = lines[2].lstrip("# ").strip()
        datel = lines[4].lstrip("# ").strip() if len(lines) > 4 else ""
        body = "\n".join(lines[5:]).strip()
        blocks = [b.strip() for b in re.split(r"\n\s*\n", body) if b.strip()]
        out.append((numeral, title, datel, blocks))
    return out


# ---------------------------------------------------------------- template
class Book(BaseDocTemplate):
    def __init__(self, filename, **kw):
        super().__init__(filename, pagesize=(PAGE_W, PAGE_H),
                         leftMargin=M_SIDE, rightMargin=M_SIDE,
                         topMargin=M_TOP, bottomMargin=M_BOT,
                         title="The Fifth Officer",
                         author="A Novella of the Titanic",
                         subject="A historical novella of the Titanic, 1912", **kw)
        frame = Frame(M_SIDE, M_BOT, TEXT_W, PAGE_H - M_TOP - M_BOT,
                      id="main", leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(id="page", frames=[frame], onPage=self.decorate)])
        self.chapter = ""
        self.opener_pages = set()
        self.body_start = None

    def decorate(self, canv, doc):
        page = canv.getPageNumber()
        if self.body_start is None or page < self.body_start:
            return
        # running head
        if page not in self.opener_pages:
            canv.saveState()
            canv.setFillColor(FAINT)
            head = (self.chapter if page % 2 else "The Fifth Officer").upper()
            t = canv.beginText()
            t.setFont("EBG", 7.6)
            t.setCharSpace(1.35)
            w = pdfmetrics.stringWidth(head, "EBG", 7.6) + 1.35 * max(len(head) - 1, 0)
            t.setTextOrigin((PAGE_W - w) / 2, PAGE_H - M_TOP + 26)
            t.textOut(head)
            canv.drawText(t)
            canv.setStrokeColor(Color(0.80, 0.78, 0.74))
            canv.setLineWidth(0.4)
            canv.line(M_SIDE + 1.1 * IN, PAGE_H - M_TOP + 18,
                      PAGE_W - M_SIDE - 1.1 * IN, PAGE_H - M_TOP + 18)
            canv.restoreState()
        # folio
        canv.saveState()
        canv.setFont("EBG", 9)
        canv.setFillColor(FAINT)
        canv.drawCentredString(PAGE_W / 2, M_BOT - 30, str(page))
        canv.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            name = flowable.style.name
            if name == "cht":
                self.chapter = flowable.getPlainText()
                self.opener_pages.add(self.page)
                num = getattr(flowable, "numeral", "")
                self.notify("TOCEntry", (0, num + ". " + getattr(flowable, "chaptertitle", ""), self.page))
                if self.body_start is None:
                    self.body_start = self.page


# ---------------------------------------------------------------- build
def main():
    chaps = load_chapters()
    story = []

    # half title
    story += [Spacer(1, 2.9 * IN),
              Paragraph(spaced_caps("The Fifth Officer"), ParagraphStyle(
                  "ht", parent=FRONT_SUB, fontSize=13)),
              PageBreak()]

    # title page
    story += [Spacer(1, 2.15 * IN),
              Paragraph("THE FIFTH<br/>OFFICER", FRONT_TITLE),
              Spacer(1, 22),
              Rule(),
              Spacer(1, 22),
              Paragraph("A Novella of the <i>Titanic</i>", FRONT_SUB),
              Spacer(1, 2.35 * IN),
              Paragraph(spaced_caps("MCMXII"), ParagraphStyle(
                  "yr", parent=EPI_ATT, fontSize=9.6)),
              PageBreak()]

    # epigraph
    story += [Spacer(1, 2.6 * IN),
              Paragraph("&#8220;I am a seaman.&#8221;", EPI),
              Spacer(1, 22),
              Paragraph("Harold Godfrey Lowe, Fifth Officer, R.M.S. <i>Titanic</i>,<br/>"
                        "before the United States Senate Inquiry, April 1912", EPI_ATT),
              Spacer(1, 0.9 * IN),
              Paragraph("&#183; &#183; &#183;", EPI_ATT),
              PageBreak(),
              Spacer(1, 3.35 * IN),
              Paragraph("For everyone who has ever said a thing<br/>"
                        "twelve years too late", EPI_ATT),
              PageBreak()]

    # contents
    story += [Spacer(1, 0.55 * IN), Paragraph(spaced_caps("Contents"), TOCH)]
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("toc1", fontName="EBG", fontSize=10.6, leading=21,
                                      textColor=INK, firstLineIndent=0, leftIndent=0,
                                      rightIndent=8)]
    toc.dotsMinLevel = 0
    story += [toc, PageBreak()]

    # chapters
    for numeral, title, datel, blocks in chaps:
        cht = Paragraph(spaced_caps(title), CH_TITLE)
        cht.numeral = numeral
        cht.chaptertitle = title
        story += [Spacer(1, 1.30 * IN),
                  Paragraph(numeral, NUMERAL),
                  cht,
                  Spacer(1, 12),
                  Rule(width=1.15 * IN),
                  Paragraph(datel, CH_DATE),
                  Spacer(1, 34)]

        first = True
        for b in blocks:
            if b.strip() == "---":
                story.append(Paragraph("&#183; &#183; &#183;", SCENE))
                first = True
                continue
            if b.startswith("> "):
                txt = " ".join(l.lstrip("> ").strip() for l in b.splitlines())
                story.append(Paragraph(inline(txt), QUOTE))
                first = False
                continue
            txt = " ".join(b.split())
            story.append(Paragraph(inline(txt), BODY_FIRST if first else BODY))
            first = False
        story.append(PageBreak())

    # colophon
    story += [Spacer(1, 2.4 * IN),
              Paragraph(spaced_caps("The End"), ParagraphStyle(
                  "end", parent=FRONT_SUB, fontSize=11)),
              Spacer(1, 1.5 * IN),
              Paragraph("Set in EB Garamond.<br/>"
                        "The record is real; the woman is not.", EPI_ATT)]

    doc = Book(str(ROOT / "The-Fifth-Officer.pdf"))
    doc.multiBuild(story)
    print("pages:", doc.page)
    print("wrote", ROOT / "The-Fifth-Officer.pdf")


class Rule(Spacer):
    def __init__(self, width=2.0 * IN, thickness=0.6):
        super().__init__(1, 1)
        self.w, self.t = width, thickness
        self.hAlign = "CENTER"

    def wrap(self, aw, ah):
        return (self.w, self.t)

    def draw(self):
        c = self.canv
        c.saveState()
        c.setStrokeColor(Color(0.62, 0.58, 0.50))
        c.setLineWidth(self.t)
        c.line(0, 0, self.w, 0)
        c.restoreState()


if __name__ == "__main__":
    main()
