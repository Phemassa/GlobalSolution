#!/usr/bin/env python3
"""
gerar_pdf_evidencias.py
-----------------------
Gera o PDF academico completo a partir do docs/EVIDENCIAS.md,
embutindo todas as screenshots de assets/evidencias/.

Uso:
    source .venv/bin/activate
    python scripts/gerar_pdf_evidencias.py
    # PDF gerado em: docs/GS2026_EVIDENCIAS.pdf
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
MD_PATH   = ROOT / "docs" / "EVIDENCIAS.md"
IMG_DIR   = ROOT / "assets" / "evidencias"
PDF_PATH  = ROOT / "docs" / "GS2026_EVIDENCIAS.pdf"

# ─── compatibilidade de encoding ────────────────────────────────────────────

def c(text: str) -> str:
    """Normaliza caracteres para latin-1 (fpdf2 built-in fonts)."""
    replacements = {
        "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2192": "->", "\u2190": "<-",
        "\u00b7": ".", "\u2022": "-", "\u2026": "...",
        "\u00b0": "o", "\u00b9": "1", "\u00b2": "2", "\u00b3": "3",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", errors="replace").decode("latin-1")


# ─── parser simples de markdown ─────────────────────────────────────────────

def parse_md(path: Path) -> list[dict]:
    """Retorna lista de blocos: {type, content, level}."""
    blocks: list[dict] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    in_code = False
    code_buf: list[str] = []

    while i < len(lines):
        line = lines[i]

        # bloco de codigo
        if line.startswith("```"):
            if in_code:
                blocks.append({"type": "code", "content": "\n".join(code_buf)})
                code_buf = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # headings
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            blocks.append({"type": "heading", "level": len(m.group(1)), "content": m.group(2)})
            i += 1
            continue

        # imagem  ![alt](path)
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", line)
        if m:
            blocks.append({"type": "image", "alt": m.group(1), "src": m.group(2)})
            i += 1
            continue

        # legenda italica *texto*
        m = re.match(r"^\*([^*]+)\*\s*$", line)
        if m:
            blocks.append({"type": "caption", "content": m.group(1)})
            i += 1
            continue

        # blockquote >
        if line.startswith("> "):
            blocks.append({"type": "quote", "content": line[2:]})
            i += 1
            continue

        # linha horizontal
        if re.match(r"^-{3,}$", line.strip()):
            blocks.append({"type": "hr"})
            i += 1
            continue

        # tabela (linha com |)
        if "|" in line and line.strip().startswith("|"):
            table_lines = []
            while i < len(lines) and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1
            # filtrar linhas de separador (---|---)
            rows = [
                [cell.strip() for cell in r.strip().strip("|").split("|")]
                for r in table_lines
                if not re.match(r"^\|[-| :]+\|$", r.strip())
            ]
            blocks.append({"type": "table", "rows": rows})
            continue

        # lista
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)", line)
        if m:
            indent = len(m.group(1))
            blocks.append({"type": "list_item", "content": m.group(3), "indent": indent})
            i += 1
            continue

        # linha vazia
        if line.strip() == "":
            blocks.append({"type": "blank"})
            i += 1
            continue

        # paragrafo
        blocks.append({"type": "paragraph", "content": line})
        i += 1

    return blocks


# ─── gerador PDF ────────────────────────────────────────────────────────────

def remove_md_inline(text: str) -> str:
    """Remove bold (**) e backticks do texto inline."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    return text


def generate(blocks: list[dict]) -> None:
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    ACCENT = (99, 87, 232)
    DARK = (20, 26, 51)
    MUTED = (88, 100, 132)
    BLACK = (35, 40, 52)
    CODE_BG = (243, 246, 255)
    CODE_TEXT = (56, 66, 92)

    class EvidencePDF(FPDF):
        def header(self) -> None:
            self.set_fill_color(*DARK)
            self.rect(0, 0, self.w, 8, "F")
            self.set_font("Helvetica", "I", 7)
            self.set_text_color(*MUTED)
            self.set_xy(self.l_margin, 1.5)
            self.cell(0, 5, c("FIAP . Global Solution 2026.1 . Monitoramento Climatico Espacial"))
            self.set_text_color(*BLACK)
            if self.get_y() < 12:
                self.set_y(12)

        def footer(self) -> None:
            self.set_y(-12)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(*MUTED)
            uw = self.w - self.l_margin - self.r_margin
            self.set_x(self.l_margin)
            self.cell(uw / 2, 5, c("FIAP . Global Solution 2026.1 . Analise e Desenvolvimento de Sistemas"))
            self.cell(uw / 2, 5, c(f"Pagina {self.page_no()}"), align="R")

    pdf = EvidencePDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(18, 18, 18)
    UW = pdf.w - pdf.l_margin - pdf.r_margin  # usable width

    blank_count = 0
    figure_count = 0
    pending_figure_number: int | None = None

    def new_page():
        pdf.add_page()
        if pdf.get_y() < 12:
            pdf.set_y(12)

    def ln(h: float = 3.0):
        pdf.ln(h)

    def wrap_by_width(text: str, width: float) -> list[str]:
        normalized = remove_md_inline(text).strip()
        if not normalized:
            return [""]
        words = normalized.split()
        lines: list[str] = []
        cur = words[0]
        for w in words[1:]:
            candidate = f"{cur} {w}"
            if pdf.get_string_width(c(candidate)) <= width:
                cur = candidate
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        return lines

    def next_meaningful_block(start_idx: int) -> dict | None:
        for j in range(start_idx + 1, len(blocks)):
            bt = blocks[j]["type"]
            if bt in {"blank", "hr"}:
                continue
            return blocks[j]
        return None

    def min_space_for_heading(level: int, next_blk: dict | None) -> float:
        heading_base = {1: 28.0, 2: 18.0, 3: 14.0}.get(level, 12.0)
        if next_blk is None:
            return heading_base

        next_type = next_blk.get("type", "")
        next_need = {
            "image": 88.0,
            "table": 30.0,
            "code": 24.0,
            "paragraph": 14.0,
            "list_item": 12.0,
            "quote": 14.0,
            "heading": 12.0,
            "caption": 10.0,
        }.get(next_type, 12.0)
        return heading_base + next_need

    new_page()

    skip_next_blank = False

    for idx, blk in enumerate(blocks):
        t = blk["type"]

        if t == "blank":
            blank_count += 1
            if blank_count <= 1 and not skip_next_blank:
                ln(3)
            skip_next_blank = False
            continue
        blank_count = 0
        skip_next_blank = False

        if t == "hr":
            ln(1)
            pdf.set_draw_color(*ACCENT)
            pdf.set_line_width(0.4)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + UW, pdf.get_y())
            pdf.set_line_width(0.2)
            ln(4)

        elif t == "heading":
            level = blk["level"]
            text  = remove_md_inline(blk["content"])

            # Regra de paginação (ABNT): evita título isolado no fim da página.
            next_blk = next_meaningful_block(idx)
            remaining = pdf.h - pdf.b_margin - pdf.get_y()
            if remaining < min_space_for_heading(level, next_blk):
                new_page()

            if level == 1:
                if pdf.get_y() > 30:
                    new_page()
                # bloco de titulo nivel 1
                pdf.set_fill_color(*DARK)
                pdf.rect(pdf.l_margin - 2, pdf.get_y() - 1, UW + 4, 13, "F")
                pdf.set_font("Helvetica", "B", 18)
                pdf.set_text_color(255, 255, 255)
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(UW, 9, c(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                ln(3)

            elif level == 2:
                ln(4)
                pdf.set_fill_color(*ACCENT)
                pdf.rect(pdf.l_margin - 2, pdf.get_y(), 3, 8, "F")
                pdf.set_font("Helvetica", "B", 14)
                pdf.set_text_color(*DARK)
                pdf.set_x(pdf.l_margin + 4)
                pdf.multi_cell(UW - 4, 8, c(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                ln(2)

            elif level == 3:
                ln(3)
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(*ACCENT)
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(UW, 7, c(remove_md_inline(text)), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                ln(1)

            else:
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(*BLACK)
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(UW, 6, c(remove_md_inline(text)), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_text_color(*BLACK)

        elif t == "paragraph":
            text = remove_md_inline(blk["content"])
            if not text.strip():
                continue
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*BLACK)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(UW, 5.5, c(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            ln(1)

        elif t == "list_item":
            text   = remove_md_inline(blk["content"])
            indent = min(blk.get("indent", 0), 8)
            bullet = "-"
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*BLACK)
            pdf.set_x(pdf.l_margin + 4 + indent)
            pdf.cell(5, 5.5, bullet)
            pdf.set_x(pdf.l_margin + 9 + indent)
            pdf.multi_cell(UW - 9 - indent, 5.5, c(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        elif t == "quote":
            text = remove_md_inline(blk["content"])
            pdf.set_fill_color(240, 237, 255)
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(*DARK)
            pdf.set_x(pdf.l_margin)
            # barra lateral de destaque
            y0 = pdf.get_y()
            pdf.multi_cell(UW, 5.5, c(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            y1 = pdf.get_y()
            pdf.set_fill_color(*ACCENT)
            pdf.rect(pdf.l_margin - 3, y0, 2, y1 - y0, "F")
            pdf.set_text_color(*BLACK)
            ln(2)

        elif t == "code":
            raw_lines = blk["content"].splitlines() or [""]
            wrapped_lines: list[str] = []
            wrap = 96
            for raw in raw_lines:
                if not raw:
                    wrapped_lines.append("")
                    continue
                for i in range(0, len(raw), wrap):
                    wrapped_lines.append(raw[i : i + wrap])

            line_h = 4.3
            box_h = max(10.0, len(wrapped_lines) * line_h + 4)
            if pdf.get_y() + box_h > pdf.h - pdf.b_margin:
                new_page()

            y0 = pdf.get_y()
            pdf.set_fill_color(*CODE_BG)
            pdf.set_draw_color(*ACCENT)
            pdf.set_line_width(0.25)
            pdf.rect(pdf.l_margin - 1.5, y0 - 1.2, UW + 3.0, box_h + 2.4, "DF")

            pdf.set_font("Courier", "", 8)
            pdf.set_text_color(*CODE_TEXT)
            pdf.set_y(y0 + 1.0)
            for line in wrapped_lines:
                pdf.set_x(pdf.l_margin + 1.2)
                pdf.cell(UW - 2.4, line_h, c(line))
                pdf.ln(line_h)

            pdf.set_text_color(*BLACK)
            pdf.set_draw_color(0, 0, 0)
            ln(4)

        elif t == "table":
            rows = blk["rows"]
            if not rows:
                continue
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*BLACK)
            n_cols = max(len(r) for r in rows)
            if n_cols == 0:
                continue
            col_w = UW / n_cols
            for r_idx, row in enumerate(rows):
                if r_idx == 0:
                    pdf.set_fill_color(*DARK)
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font("Helvetica", "B", 9)
                else:
                    fill = (232, 230, 246) if r_idx % 2 == 0 else (242, 242, 250)
                    pdf.set_fill_color(*fill)
                    pdf.set_text_color(*BLACK)
                    pdf.set_font("Helvetica", "", 9)

                padded_row = list(row) + [""] * (n_cols - len(row))
                max_text_w = col_w - 3.0
                wrapped_cells = [wrap_by_width(cell, max_text_w) for cell in padded_row]
                row_h = max(len(lines) for lines in wrapped_cells) * 4.5 + 2.2

                if pdf.get_y() + row_h > pdf.h - pdf.b_margin:
                    new_page()

                y0 = pdf.get_y()
                for ci, lines_cell in enumerate(wrapped_cells):
                    x0 = pdf.l_margin + ci * col_w
                    pdf.rect(x0, y0, col_w, row_h, "F")
                    txt_color = (255, 255, 255) if r_idx == 0 else BLACK
                    pdf.set_text_color(*txt_color)
                    y_text = y0 + 1.3
                    for line in lines_cell:
                        pdf.set_xy(x0 + 1.5, y_text)
                        pdf.cell(col_w - 3.0, 4.5, c(line))
                        y_text += 4.5
                pdf.set_y(y0 + row_h)

            pdf.set_text_color(*BLACK)
            ln(3)

        elif t == "image":
            src = blk["src"]
            # normaliza caminho relativo ao MD (docs/)
            img_path = (ROOT / "docs" / src).resolve()
            if not img_path.exists():
                # tenta direto
                img_path = (ROOT / src.lstrip("../")).resolve()
            if not img_path.exists():
                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(*MUTED)
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(UW, 5, c(f"[imagem nao encontrada: {src}]"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_text_color(*BLACK)
                continue

            # inserir imagem em nova pagina se necessario
            if pdf.get_y() > pdf.h - 80:
                new_page()

            # dimensiona imagem para caber na pagina e evita sobreposicao
            target_w = UW * 0.92
            reserve_h = 12  # margem para legenda/respiracao
            available_h = pdf.h - pdf.b_margin - pdf.get_y() - reserve_h

            if available_h < 40:
                new_page()
                available_h = pdf.h - pdf.b_margin - pdf.get_y() - reserve_h

            img_w = target_w
            img_h = target_w * 0.56

            img_mat = cv2.imread(str(img_path))
            if img_mat is not None:
                h_px, w_px = img_mat.shape[:2]
                if w_px > 0 and h_px > 0:
                    ratio = h_px / w_px
                    img_h = target_w * ratio
                    if img_h > available_h:
                        img_h = available_h
                        img_w = img_h / ratio

            pdf.set_x(pdf.l_margin + (UW - img_w) / 2)
            try:
                y_before = pdf.get_y()
                pdf.image(str(img_path), x=pdf.get_x(), y=y_before, w=img_w, h=img_h)
                pdf.set_y(y_before + img_h + 2)
                figure_count += 1
                pending_figure_number = figure_count
            except Exception as exc:
                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(*MUTED)
                pdf.multi_cell(UW, 5, c(f"[erro ao carregar imagem: {exc}]"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_text_color(*BLACK)

            skip_next_blank = True

        elif t == "caption":
            text = blk["content"]
            if pending_figure_number is not None:
                caption_text = f"Figura {pending_figure_number} - {text}"
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(*BLACK)
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(UW, 5, c(caption_text), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                pdf.set_font("Helvetica", "I", 8.5)
                pdf.set_text_color(*MUTED)
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(UW, 4.6, c("Fonte: Elaboracao propria (2026)."), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                pending_figure_number = None
            else:
                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(*MUTED)
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(UW, 5, c(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            pdf.set_text_color(*BLACK)
            ln(3)

    pdf.output(str(PDF_PATH))
    n_pages = pdf.page_no()
    print(f"[OK] PDF gerado: {PDF_PATH.relative_to(ROOT)} ({PDF_PATH.stat().st_size // 1024} KB, {n_pages} paginas)")


def main():
    print("=== gerar_pdf_evidencias.py ===")
    if not MD_PATH.exists():
        print(f"[ERRO] Nao encontrado: {MD_PATH}")
        sys.exit(1)

    print(f"Lendo {MD_PATH.relative_to(ROOT)} ...")
    blocks = parse_md(MD_PATH)
    print(f"Blocos parsed: {len(blocks)}")
    print("Gerando PDF ...")
    generate(blocks)


if __name__ == "__main__":
    main()
