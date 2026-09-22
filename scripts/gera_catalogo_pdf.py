from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "catalogo_atomos_confusao_systemverilog.pdf"
TITLE = "Catálogo de Átomos de Confusão em SystemVerilog"


def read_case(path: Path) -> tuple[list[str], list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    marker = next(i for i, line in enumerate(lines) if line.strip().startswith("// Gabarito:"))
    code = lines[:marker]
    while code and not code[-1].strip():
        code.pop()
    inline_answer = lines[marker].split("// Gabarito:", 1)[1].strip()
    answer = ([part.strip() for part in inline_answer.split(";")] if inline_answer else []) + [
        line.strip() for line in lines[marker + 1:] if line.strip()
    ]
    return code, answer


def changed_lines(left: list[str], right: list[str]) -> tuple[set[int], set[int]]:
    left_changed: set[int] = set()
    right_changed: set[int] = set()
    matcher = SequenceMatcher(a=left, b=right)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            left_changed.update(range(i1, i2))
            right_changed.update(range(j1, j2))
    return left_changed, right_changed


def draw_code_column(
    pdf: canvas.Canvas,
    x: float,
    top: float,
    width: float,
    label: str,
    lines: list[str],
    changed: set[int],
    answer: list[str],
    highlight: colors.Color,
) -> None:
    pdf.setFillColor(colors.HexColor("#526B7E"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawCentredString(x + width / 2, top, label)

    font_size = 8.4 if len(lines) <= 22 else 7.7
    leading = font_size + 2.1
    code_top = top - 25
    pdf.setFont("Courier", font_size)
    for index, line in enumerate(lines):
        y = code_top - index * leading
        if index in changed:
            text_width = min(width - 14, stringWidth(line or " ", "Courier", font_size) + 10)
            pdf.setFillColor(highlight)
            pdf.roundRect(x + 5, y - 2.2, text_width, leading, 4, fill=1, stroke=0)
        pdf.setFillColor(colors.HexColor("#27313A"))
        pdf.drawString(x + 10, y, line)

    answer_y = code_top - len(lines) * leading - 17
    answer_lines = answer or ["-"]
    box_height = 18 + 12 * (len(answer_lines) + 1)
    pdf.setFillColor(colors.HexColor("#F2F6F8"))
    pdf.roundRect(x + 4, answer_y - box_height + 17, width - 8, box_height, 6, fill=1, stroke=0)
    pdf.setFillColor(colors.HexColor("#304B5E"))
    pdf.setFont("Helvetica-Bold", 8.5)
    pdf.drawString(x + 12, answer_y + 2, "Gabarito:")
    for line_index, line in enumerate(answer_lines):
        pdf.drawString(x + 12, answer_y - 10 - line_index * 12, line)


def build() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    page_width, page_height = landscape(A4)
    pdf = canvas.Canvas(str(OUTPUT), pagesize=(page_width, page_height))
    pdf.setTitle(TITLE)
    pdf.setAuthor("Experimento HDL")

    for page_number, number in enumerate((1, 2, 4, 5), start=1):
        left, left_answer = read_case(ROOT / "lambda" / "vscode-pages-Smell" / f"pagina-{number}.sv")
        right, right_answer = read_case(ROOT / "omega" / "vscode-pages-NoSmell" / f"pagina-{number}.sv")
        left_changed, right_changed = changed_lines(left, right)

        pdf.setFillColor(colors.HexColor("#1E2933"))
        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawCentredString(page_width / 2, page_height - 43, TITLE)
        pdf.setStrokeColor(colors.HexColor("#C8D4DC"))
        pdf.line(42, page_height - 60, page_width - 42, page_height - 60)

        pdf.setFillColor(colors.HexColor("#526B7E"))
        pdf.setFont("Helvetica-Bold", 24)
        pdf.drawString(43, page_height - 88, f"{number}.")

        margin = 75
        gap = 48
        column_width = (page_width - 2 * margin - gap) / 2
        top = page_height - 93
        draw_code_column(
            pdf, margin, top, column_width, "Lambda - com smell", left,
            left_changed, left_answer, colors.HexColor("#FBE4E2")
        )
        draw_code_column(
            pdf, margin + column_width + gap, top, column_width, "Omega - sem smell", right,
            right_changed, right_answer, colors.HexColor("#E3F2E9")
        )

        center_x = page_width / 2
        center_y = page_height / 2 + 5
        pdf.setStrokeColor(colors.HexColor("#526B7E"))
        pdf.setFillColor(colors.HexColor("#526B7E"))
        pdf.setLineWidth(3)
        pdf.line(center_x - 16, center_y, center_x + 12, center_y)
        path = pdf.beginPath()
        path.moveTo(center_x + 12, center_y + 7)
        path.lineTo(center_x + 22, center_y)
        path.lineTo(center_x + 12, center_y - 7)
        path.close()
        pdf.drawPath(path, fill=1, stroke=0)

        pdf.setFillColor(colors.HexColor("#7A8994"))
        pdf.setFont("Helvetica", 7.5)
        pdf.drawRightString(page_width - 42, 22, f"Página {page_number} de 4 - Caso {number}")
        pdf.showPage()

    pdf.save()


if __name__ == "__main__":
    build()
