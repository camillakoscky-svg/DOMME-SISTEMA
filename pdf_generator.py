"""
DOMME — Gerador de Proposta PDF
Gera PDFs camuflados (cliente nunca vê CVU, MIL, MD, Markup).
"""
import io
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable,
)


# ----------------------------- ESTILOS ----------------------------- #
_GOLD = colors.HexColor("#A88B5C")
_DARK = colors.HexColor("#0E0E0E")
_LIGHT = colors.HexColor("#FAFAF7")
_GRAY = colors.HexColor("#6B6B6B")


def _styles():
    ss = getSampleStyleSheet()
    s = {}
    s["titulo"] = ParagraphStyle(
        "titulo", parent=ss["Title"],
        fontName="Helvetica-Bold", fontSize=22,
        textColor=_DARK, spaceAfter=4,
    )
    s["subtitulo"] = ParagraphStyle(
        "subtitulo", parent=ss["Normal"],
        fontName="Helvetica", fontSize=11,
        textColor=_GOLD, spaceAfter=12,
    )
    s["secao"] = ParagraphStyle(
        "secao", parent=ss["Heading2"],
        fontName="Helvetica-Bold", fontSize=13,
        textColor=_DARK, spaceBefore=16, spaceAfter=6,
    )
    s["corpo"] = ParagraphStyle(
        "corpo", parent=ss["Normal"],
        fontName="Helvetica", fontSize=10,
        textColor=_DARK, leading=14, spaceAfter=4,
    )
    s["rodape"] = ParagraphStyle(
        "rodape", parent=ss["Normal"],
        fontName="Helvetica", fontSize=8,
        textColor=_GRAY, alignment=1,
    )
    return s


def _fmt_brl(valor) -> str:
    if valor is None:
        return "—"
    return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(valor) -> str:
    if valor is None:
        return "—"
    return f"{float(valor) * 100:.1f}%"


# ----------------------------- PROPOSTA INDIVIDUAL ----------------------------- #
def gerar_proposta_pdf(
    resultado,
    cliente_nome: str,
    usuario_nome: str = "DOMME",
    proposta_num: str = "",
) -> bytes:
    """Gera PDF da proposta para um SKU individual."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )
    s = _styles()
    story = []

    # Header
    story.append(Paragraph("DOMME × LASZLO", s["titulo"]))
    story.append(Paragraph("Proposta Comercial — White Label", s["subtitulo"]))
    if proposta_num:
        story.append(Paragraph(f"Proposta #{proposta_num}", s["corpo"]))
    story.append(Paragraph(
        f"Data: {datetime.now().strftime('%d/%m/%Y')} · "
        f"Preparada por: {usuario_nome}",
        s["corpo"],
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=_GOLD, spaceAfter=12))

    # Cliente
    story.append(Paragraph("CLIENTE", s["secao"]))
    story.append(Paragraph(f"<b>{cliente_nome}</b>", s["corpo"]))
    story.append(Spacer(1, 0.5 * cm))

    # Produto
    story.append(Paragraph("PRODUTO", s["secao"]))
    story.append(Paragraph(f"<b>{resultado.sku}</b>", s["corpo"]))
    story.append(Paragraph(
        f"Volume do lote: <b>{resultado.volume:,} unidades</b>".replace(",", "."),
        s["corpo"],
    ))
    story.append(Paragraph(f"Mercado: <b>{resultado.mercado}</b>", s["corpo"]))
    story.append(Spacer(1, 0.5 * cm))

    # Investimento — CAMUFLADO (sem CVU, MIL, MD)
    story.append(Paragraph("INVESTIMENTO", s["secao"]))

    data = [
        ["Descrição", "Valor"],
        ["Preço unitário full-service", _fmt_brl(resultado.pfc_final_unit)],
        ["Volume do lote", f"{resultado.volume:,} un".replace(",", ".")],
        ["Faixa de volume", resultado.tier_nome],
        ["Valor global do projeto", _fmt_brl(resultado.investimento_total)],
    ]
    t = Table(data, colWidths=[10 * cm, 6 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _GOLD),
        ("TEXTCOLOR", (0, 0), (-1, 0), _LIGHT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_LIGHT, colors.white]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    # Viabilidade
    if resultado.iv is not None:
        story.append(Paragraph("ANÁLISE DE VIABILIDADE", s["secao"]))
        story.append(Paragraph(
            f"Índice de Viabilidade: <b>{resultado.iv:.3f}</b> — "
            f"<b>{resultado.iv_status}</b>",
            s["corpo"],
        ))
        if resultado.roi_pct is not None:
            story.append(Paragraph(
                f"ROI projetado: <b>{_fmt_pct(resultado.roi_pct)}</b>",
                s["corpo"],
            ))
        if resultado.break_even_un:
            story.append(Paragraph(
                f"Break-even: <b>{resultado.break_even_un:,} unidades</b>".replace(",", "."),
                s["corpo"],
            ))
        story.append(Spacer(1, 0.5 * cm))

    # Selo Laszlo
    story.append(Paragraph("SELO LASZLO", s["secao"]))
    story.append(Paragraph(
        "Este projeto inclui o <b>Selo de Qualidade Laszlo</b> — "
        "garantia de rastreabilidade, pureza e compliance regulatório. "
        "Licenciamento de 3% sobre o PFC já incluído no preço acima.",
        s["corpo"],
    ))
    story.append(Spacer(1, 0.5 * cm))

    # Notas
    story.append(Paragraph("OBSERVAÇÕES", s["secao"]))
    story.append(Paragraph(
        "<b>Full-service:</b> inclui matéria-prima, envase, embalagem padrão "
        "(frasco, tampa, gotejador, rótulo técnico) e fee de ativação.",
        s["corpo"],
    ))
    story.append(Paragraph(
        "<b>Compliance:</b> verso técnico do rótulo é imutável (dados regulatórios). "
        "Foco regulatório em Aromas Naturais / Alimentos para Go-to-Market imediato.",
        s["corpo"],
    ))
    story.append(Paragraph(
        "<b>Não incluído:</b> design gráfico exclusivo · tecnologias especiais de envase · "
        "fotografia de produto. Disponíveis via parceiros DOMME sob demanda.",
        s["corpo"],
    ))

    # Rodapé
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph(
        "DOMME — Inteligência em White Label · contato@domme.com",
        s["rodape"],
    ))

    doc.build(story)
    return buf.getvalue()


# ----------------------------- PROPOSTA KIT ----------------------------- #
def gerar_proposta_kit_pdf(
    resultado,
    cliente_nome: str,
    kit_nome: str = "Kit Composto",
    usuario_nome: str = "DOMME",
    proposta_num: str = "",
) -> bytes:
    """Gera PDF da proposta para um Kit/Mix composto."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )
    s = _styles()
    story = []

    # Header
    story.append(Paragraph("DOMME × LASZLO", s["titulo"]))
    story.append(Paragraph(f"Proposta Comercial — {kit_nome}", s["subtitulo"]))
    if proposta_num:
        story.append(Paragraph(f"Proposta #{proposta_num}", s["corpo"]))
    story.append(Paragraph(
        f"Data: {datetime.now().strftime('%d/%m/%Y')} · "
        f"Preparada por: {usuario_nome}",
        s["corpo"],
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=_GOLD, spaceAfter=12))

    # Cliente
    story.append(Paragraph("CLIENTE", s["secao"]))
    story.append(Paragraph(f"<b>{cliente_nome}</b>", s["corpo"]))
    story.append(Spacer(1, 0.5 * cm))

    # Composição do kit
    story.append(Paragraph("COMPOSIÇÃO DO KIT", s["secao"]))

    data = [["Produto", "Quantidade"]]
    for item in resultado.itens:
        data.append([
            item.sku[:50],
            f"{item.quantidade:,} un".replace(",", "."),
        ])
    data.append(["TOTAL", f"{resultado.total_unidades:,} un".replace(",", ".")])

    t = Table(data, colWidths=[12 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _GOLD),
        ("TEXTCOLOR", (0, 0), (-1, 0), _LIGHT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [_LIGHT, colors.white]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F5F1EA")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    # Investimento
    story.append(Paragraph("INVESTIMENTO", s["secao"]))

    data2 = [
        ["Descrição", "Valor"],
        ["PFC unitário (kit blendado)", _fmt_brl(resultado.mix_pfc_unit)],
        ["Total de unidades", f"{resultado.total_unidades:,}".replace(",", ".")],
        ["Faixa de volume", resultado.tier_nome],
        ["Valor global do projeto", _fmt_brl(resultado.investimento_total)],
    ]
    if resultado.economia_por_unidade > 0:
        data2.append([
            "Economia vs. lotes separados",
            _fmt_brl(resultado.economia_total_lote),
        ])

    t2 = Table(data2, colWidths=[10 * cm, 6 * cm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _GOLD),
        ("TEXTCOLOR", (0, 0), (-1, 0), _LIGHT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, _GRAY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_LIGHT, colors.white]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t2)
    story.append(Spacer(1, 0.5 * cm))

    # Viabilidade
    if resultado.iv is not None:
        story.append(Paragraph("VIABILIDADE", s["secao"]))
        story.append(Paragraph(
            f"IV blendado: <b>{resultado.iv:.3f}</b> — "
            f"<b>{resultado.iv_status}</b>",
            s["corpo"],
        ))

    # Notas
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("OBSERVAÇÕES", s["secao"]))
    story.append(Paragraph(
        "<b>Kit consolidado:</b> fee de ativação cobrado uma única vez sobre o lote. "
        "Tier de volume calculado pelo total de unidades do kit.",
        s["corpo"],
    ))
    story.append(Paragraph(
        "<b>Selo Laszlo:</b> licenciamento de 3% incluído.",
        s["corpo"],
    ))
    story.append(Paragraph(
        "<b>Não incluído:</b> design gráfico exclusivo · tecnologias especiais de envase.",
        s["corpo"],
    ))

    # Rodapé
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph(
        "DOMME — Inteligência em White Label · contato@domme.com",
        s["rodape"],
    ))

    doc.build(story)
    return buf.getvalue()
