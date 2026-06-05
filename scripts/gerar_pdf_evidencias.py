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

    pdf = FPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(18, 18, 18)
    UW = pdf.w - pdf.l_margin - pdf.r_margin  # usable width

    ACCENT   = (124, 92, 255)
    DARK     = (20, 26, 51)
    MUTED    = (100, 110, 140)
    BLACK    = (30, 30, 30)
    CODE_BG  = (15, 20, 40)

    blank_count = 0

    def new_page():
        pdf.add_page()
        # faixa de cabecalho discreta
        pdf.set_fill_color(*DARK)
        pdf.rect(0, 0, pdf.w, 8, "F")
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(*MUTED)
        pdf.set_xy(pdf.l_margin, 1.5)
        pdf.cell(0, 5, c("FIAP · Global Solution 2026.1 · Monitoramento Climatico Espacial"))
        pdf.set_xy(pdf.l_margin, 12)

    def ln(h: float = 3.0):
        pdf.ln(h)

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

            if level == 1:
                if pdf.get_y() > 30:
                    new_page()
                # bloco de titulo nivel 1
                pdf.set_fill_color(*DARK)
                pdf.rect(pdf.l_margin - 2, pdf.get_y() - 1, UW + 4, 14, "F")
                pdf.set_font("Helvetica", "B", 18)
                pdf.set_text_color(255, 255, 255)
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(UW, 9, c(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                ln(3)

            elif level == 2:
                if pdf.get_y() > pdf.h - 50:
                    new_page()
                ln(4)
                pdf.set_fill_color(*ACCENT)
                pdf.rect(pdf.l_margin - 2, pdf.get_y(), 3, 8, "F")
                pdf.set_font("Helvetica", "B", 14)
                pdf.set_text_color(*DARK)
                pdf.set_x(pdf.l_margin + 4)
                pdf.multi_cell(UW - 4, 8, c(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                ln(2)

            elif level == 3:
                if pdf.get_y() > pdf.h - 40:
                    new_page()
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
            pdf.set_fill_color(230, 225, 255)
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(*DARK)
            pdf.set_x(pdf.l_margin)
            # barra lateral roxa
            y0 = pdf.get_y()
            pdf.multi_cell(UW, 5.5, c(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            y1 = pdf.get_y()
            pdf.set_fill_color(*ACCENT)
            pdf.rect(pdf.l_margin - 3, y0, 2, y1 - y0, "F")
            pdf.set_text_color(*BLACK)
            ln(2)

        elif t == "code":
            lines_code = blk["content"].splitlines() or [""]
            pdf.set_fill_color(*CODE_BG)
            pdf.set_text_color(180, 220, 255)
            pdf.set_font("Courier", "", 8)
            wrap = 100
            y0 = pdf.get_y()
            # fundo
            estimated_h = len(lines_code) * 4.2 + 6
            if pdf.get_y() + estimated_h > pdf.h - 20:
                new_page()
                y0 = pdf.get_y()
            pdf.set_fill_color(*CODE_BG)
            # renderiza linhas
            for raw in lines_code:
                if not raw:
                    pdf.ln(4.2)
                    continue
                for chunk_i in range(0, len(raw), wrap):
                    chunk = raw[chunk_i: chunk_i + wrap]
                    pdf.set_x(pdf.l_margin + 3)
                    pdf.multi_cell(UW - 3, 4.2, c(chunk), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            y1 = pdf.get_y()
            # retangulo de fundo (desenhado sobre o texto — colocar antes)
            # em fpdf2 nao ha z-index; desenhamos o box antes do texto
            # solucao: redesenhar com borda visivel ao redor
            pdf.set_draw_color(*ACCENT)
            pdf.set_line_width(0.3)
            pdf.rect(pdf.l_margin - 2, y0 - 2, UW + 4, y1 - y0 + 4)
            pdf.set_line_width(0.2)
            pdf.set_text_color(*BLACK)
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
                    fill = (235, 232, 255) if r_idx % 2 == 0 else (245, 245, 255)
                    pdf.set_fill_color(*fill)
                    pdf.set_text_color(*BLACK)
                    pdf.set_font("Helvetica", "", 9)
                for ci, cell in enumerate(row):
                    pdf.set_x(pdf.l_margin + ci * col_w)
                    text = remove_md_inline(cell)
                    pdf.cell(col_w, 6, c(text), border=0, fill=True)
                pdf.ln(6)
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

            # largura maxima: 75% da pagina; altura proporcional
            img_w = UW * 0.92
            pdf.set_x(pdf.l_margin + (UW - img_w) / 2)
            try:
                pdf.image(str(img_path), x=pdf.get_x(), y=pdf.get_y(), w=img_w)
                # avanca Y manualmente (fpdf2 avanca apos image)
                ln(2)
            except Exception as exc:
                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(*MUTED)
                pdf.multi_cell(UW, 5, c(f"[erro ao carregar imagem: {exc}]"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_text_color(*BLACK)

            skip_next_blank = True

        elif t == "caption":
            text = blk["content"]
            pdf.set_font("Helvetica", "I", 8.5)
            pdf.set_text_color(*MUTED)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(UW, 5, c(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            pdf.set_text_color(*BLACK)
            ln(3)

    # rodape nas paginas
    for page_num in range(1, pdf.page + 1):
        pdf.page = page_num
        pdf.set_y(pdf.h - 12)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*MUTED)
        pdf.set_x(pdf.l_margin)
        pdf.cell(UW / 2, 5, c("FIAP · Global Solution 2026.1 · Analise e Desenvolvimento de Sistemas"))
        pdf.cell(UW / 2, 5, c(f"Pagina {page_num}"), align="R")

    pdf.page = pdf.pages
    pdf.output(str(PDF_PATH))
    n_pages = len(pdf.pages)
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
