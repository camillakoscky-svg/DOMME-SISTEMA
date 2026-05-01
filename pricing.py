"""
DOMME × LASZLO — Motor de Precificação v3
Implementa Motor v3 + Renda Garantida DOMME.

Regras consolidadas:
- Fator de Escala Envase: lote ≤100un → kit 2x; >100 → kit 1x
- Fee de Ativação dinâmico (T1=1500, T2=2500, T3=max(5000; 5%*lote))
- Tiers: T1 ≤500 (+20%), T2 501-2000 (+10%), T3 >2000 (0%)
- MIL 40% sobre CVU; trava MC mínima 20% no PI Laszlo
- Selo Laszlo 3% sobre PFC
- Markup Export 8x sobre CVU (sem MIL/MD locais)
- ROI conservador: -15% Receita Bruta (impostos + frete)
- Trava Pro Labore: alerta se Renda Bruta DOMME < R$ 2.000
- IV verde <0.55 / amarelo 0.55-0.70 / vermelho >0.70
"""
from dataclasses import dataclass, field, asdict
from typing import Optional


# ----------------------------- PARÂMETROS GLOBAIS ----------------------------- #
@dataclass
class Parametros:
    # Margens
    mil: float = 0.40
    md: float = 0.20
    selo_laszlo: float = 0.03
    mc_minima_laszlo: float = 0.20

    # Tiers de markup por volume
    tier1_markup: float = 0.20     # ≤500 un
    tier2_markup: float = 0.10     # 501-2000 un
    tier3_markup: float = 0.00     # >2000 un

    # Envase
    kit_envase_base: float = 5.50
    desconto_kit: float = 0.05
    limite_fator_2x: int = 100
    fator_escala_pequeno: float = 2.0

    # Fee de ativação dinâmico
    fee_t1: float = 1500.0       # ≤500 un
    fee_t2: float = 2500.0       # 501-2000 un
    fee_t3_minimo: float = 5000.0
    fee_t3_pct: float = 0.05     # 5% do valor do lote

    # Trava de pro labore
    pro_labore_minimo: float = 2000.0

    # Viabilidade
    iv_verde: float = 0.55
    iv_amarelo: float = 0.70

    # Exportação
    markup_export: float = 8.0
    cotacao_usd: float = 5.0
    cotacao_eur: float = 5.5
    frete_internacional_usd: float = 0.0

    # ROI conservador
    desc_impostos_frete: float = 0.15


# ----------------------------- RESULTADO ----------------------------- #
@dataclass
class ResultadoPricing:
    # Identificação
    sku: str = ""
    volume: int = 0
    mercado: str = "Brasil"

    # Custos
    cvu_mp: float = 0.0
    custo_envase_unit: float = 0.0
    cvu_total_unit: float = 0.0
    fator_escala: float = 1.0

    # Pricing
    pi_laszlo_unit: float = 0.0
    markup_volume: float = 0.0
    tier_nome: str = ""
    fee_ativacao_total: float = 0.0
    fee_unitario: float = 0.0
    pfc_final_unit: float = 0.0

    # Viabilidade
    ticket_medio_laszlo: float = 0.0
    iv: Optional[float] = None
    iv_cor: str = "neutro"
    iv_status: str = ""

    # ROI do cliente
    preco_venda: float = 0.0
    investimento_total: float = 0.0
    receita_bruta: float = 0.0
    lucro_liquido_lote: Optional[float] = None
    roi_pct: Optional[float] = None
    break_even_un: Optional[int] = None
    margem_liquida_unit: Optional[float] = None

    # Renda Garantida DOMME (visão interna)
    repasse_fabrica: float = 0.0
    renda_bruta_domme: float = 0.0
    renda_pct_sobre_lote: float = 0.0
    pro_labore_ok: bool = True

    # Alertas
    alertas: list = field(default_factory=list)


# ----------------------------- LÓGICA DE CÁLCULO ----------------------------- #
def _tier_info(volume: int, p: Parametros) -> tuple[str, float]:
    """Retorna (nome_tier, markup) com base no volume."""
    if volume <= 500:
        return "Tier 1 (≤500 un)", p.tier1_markup
    elif volume <= 2000:
        return "Tier 2 (501-2000 un)", p.tier2_markup
    else:
        return "Tier 3 (>2000 un)", p.tier3_markup


def _fee_ativacao(volume: int, valor_lote: float, p: Parametros) -> float:
    """Fee de ativação dinâmico por tier."""
    if volume <= 500:
        return p.fee_t1
    elif volume <= 2000:
        return p.fee_t2
    else:
        return max(p.fee_t3_minimo, p.fee_t3_pct * valor_lote)


def _fator_escala(volume: int, p: Parametros) -> float:
    """Fator de escala do kit de envase."""
    return p.fator_escala_pequeno if volume <= p.limite_fator_2x else 1.0


def _iv_classificar(iv: float, p: Parametros) -> tuple[str, str]:
    """Retorna (cor, status) do IV."""
    if iv < p.iv_verde:
        return "verde", "Altamente Viável"
    elif iv < p.iv_amarelo:
        return "amarelo", "Viável com atenção"
    else:
        return "vermelho", "Markup elevado — risco de churn"


def calcular_pricing(
    sku: str,
    volume: int,
    cvu_mp: float,
    ticket_medio_laszlo: float,
    mercado: str = "Brasil",
    preco_venda_input: Optional[float] = None,
    em_retirada: bool = False,
    parametros: Optional[Parametros] = None,
) -> ResultadoPricing:
    """Calcula pricing completo de um SKU."""
    p = parametros or Parametros()
    r = ResultadoPricing(sku=sku, volume=volume, mercado=mercado, cvu_mp=cvu_mp)
    r.ticket_medio_laszlo = ticket_medio_laszlo

    if em_retirada:
        r.alertas.append("⛔ SKU em retirada de linha — não prosseguir.")
        return r

    # --- EXPORTAÇÃO ---
    if mercado == "Internacional":
        r.fator_escala = _fator_escala(volume, p)
        r.custo_envase_unit = p.kit_envase_base * r.fator_escala
        r.cvu_total_unit = cvu_mp + r.custo_envase_unit
        r.pfc_final_unit = r.cvu_total_unit * p.markup_export
        r.pi_laszlo_unit = r.cvu_total_unit * (1 + p.mil)
        r.tier_nome = f"Export ({p.markup_export:.0f}x)"
        r.markup_volume = 0.0
        r.fee_ativacao_total = 0.0
        r.fee_unitario = 0.0
        r.investimento_total = r.pfc_final_unit * volume

        # IV export
        if ticket_medio_laszlo > 0:
            r.iv = r.pfc_final_unit / ticket_medio_laszlo
            r.iv_cor, r.iv_status = _iv_classificar(r.iv, p)

        # Renda export: Laszlo recebe PI normal + 50% do excedente
        excedente_unit = r.pfc_final_unit - r.pi_laszlo_unit
        repasse_excedente = excedente_unit * 0.5 * volume
        r.repasse_fabrica = r.pi_laszlo_unit * volume + repasse_excedente
        r.renda_bruta_domme = (r.pfc_final_unit * volume) - r.repasse_fabrica
        lote_total = r.pfc_final_unit * volume
        r.renda_pct_sobre_lote = r.renda_bruta_domme / lote_total if lote_total else 0
        r.pro_labore_ok = r.renda_bruta_domme >= p.pro_labore_minimo

        # ROI
        if preco_venda_input and preco_venda_input > 0:
            r.preco_venda = preco_venda_input
            r.receita_bruta = preco_venda_input * volume
            receita_liq = r.receita_bruta * (1 - p.desc_impostos_frete)
            r.lucro_liquido_lote = receita_liq - r.investimento_total
            if r.investimento_total > 0:
                r.roi_pct = r.lucro_liquido_lote / r.investimento_total
            r.margem_liquida_unit = r.lucro_liquido_lote / volume if volume > 0 else 0
            if r.margem_liquida_unit and r.margem_liquida_unit > 0:
                r.break_even_un = int(
                    -(-r.investimento_total // r.margem_liquida_unit)
                )
        return r

    # --- BRASIL ---
    r.fator_escala = _fator_escala(volume, p)
    r.custo_envase_unit = p.kit_envase_base * r.fator_escala
    r.cvu_total_unit = cvu_mp + r.custo_envase_unit

    # PI Laszlo (preço industrial)
    r.pi_laszlo_unit = r.cvu_total_unit * (1 + p.mil)

    # Trava MC mínima
    if ticket_medio_laszlo > 0:
        mc_real = 1 - (r.pi_laszlo_unit / ticket_medio_laszlo)
        if mc_real < p.mc_minima_laszlo:
            r.alertas.append(
                f"⚠ MC Laszlo ({mc_real:.1%}) abaixo do mínimo ({p.mc_minima_laszlo:.0%}). "
                f"PI ajustado automaticamente."
            )
            r.pi_laszlo_unit = ticket_medio_laszlo * (1 - p.mc_minima_laszlo)

    # Tier de volume
    r.tier_nome, r.markup_volume = _tier_info(volume, p)

    # PFC sem fee
    pfc_sem_fee = (
        r.pi_laszlo_unit
        * (1 + p.md)
        * (1 + r.markup_volume)
        * (1 + p.selo_laszlo)
    )

    # Fee de ativação
    valor_lote_estimado = pfc_sem_fee * volume
    r.fee_ativacao_total = _fee_ativacao(volume, valor_lote_estimado, p)
    r.fee_unitario = r.fee_ativacao_total / max(volume, 1)

    # PFC final
    r.pfc_final_unit = pfc_sem_fee + r.fee_unitario
    r.investimento_total = r.pfc_final_unit * volume

    # IV
    if ticket_medio_laszlo > 0:
        r.iv = r.pfc_final_unit / ticket_medio_laszlo
        r.iv_cor, r.iv_status = _iv_classificar(r.iv, p)

    # Renda Garantida DOMME
    selo_unit = p.selo_laszlo * pfc_sem_fee
    r.repasse_fabrica = (r.pi_laszlo_unit * volume) + (selo_unit * volume)
    r.renda_bruta_domme = (r.pfc_final_unit * volume) - r.repasse_fabrica
    lote_total = r.pfc_final_unit * volume
    r.renda_pct_sobre_lote = r.renda_bruta_domme / lote_total if lote_total else 0
    r.pro_labore_ok = r.renda_bruta_domme >= p.pro_labore_minimo

    if not r.pro_labore_ok:
        r.alertas.append(
            f"⚠ Renda DOMME (R$ {r.renda_bruta_domme:,.2f}) abaixo do "
            f"mínimo R$ {p.pro_labore_minimo:,.2f}. Considere up-sell de volume."
        )

    # ROI do cliente
    if preco_venda_input and preco_venda_input > 0:
        r.preco_venda = preco_venda_input
        r.receita_bruta = preco_venda_input * volume
        receita_liq = r.receita_bruta * (1 - p.desc_impostos_frete)
        r.lucro_liquido_lote = receita_liq - r.investimento_total
        if r.investimento_total > 0:
            r.roi_pct = r.lucro_liquido_lote / r.investimento_total
        r.margem_liquida_unit = r.lucro_liquido_lote / volume if volume > 0 else 0
        if r.margem_liquida_unit and r.margem_liquida_unit > 0:
            r.break_even_un = int(
                -(-r.investimento_total // r.margem_liquida_unit)
            )
    else:
        # Estima com ticket médio como preço de venda
        r.preco_venda = ticket_medio_laszlo
        r.receita_bruta = ticket_medio_laszlo * volume
        receita_liq = r.receita_bruta * (1 - p.desc_impostos_frete)
        r.lucro_liquido_lote = receita_liq - r.investimento_total
        if r.investimento_total > 0:
            r.roi_pct = r.lucro_liquido_lote / r.investimento_total
        r.margem_liquida_unit = r.lucro_liquido_lote / volume if volume > 0 else 0
        if r.margem_liquida_unit and r.margem_liquida_unit > 0:
            r.break_even_un = int(
                -(-r.investimento_total // r.margem_liquida_unit)
            )

    return r


def comparar_cenarios(
    sku: str,
    cvu_mp: float,
    ticket_medio: float,
    volumes: list[int] = None,
    parametros: Optional[Parametros] = None,
) -> list[dict]:
    """Compara pricing em múltiplos volumes."""
    if volumes is None:
        volumes = [50, 200, 500, 1000, 3000]
    resultados = []
    for vol in volumes:
        r = calcular_pricing(
            sku=sku, volume=vol, cvu_mp=cvu_mp,
            ticket_medio_laszlo=ticket_medio,
            parametros=parametros,
        )
        resultados.append({
            "volume": vol,
            "pfc_final_unit": r.pfc_final_unit,
            "investimento_total": r.investimento_total,
            "tier_nome": r.tier_nome,
            "iv": r.iv,
            "iv_cor": r.iv_cor,
            "fee_ativacao_total": r.fee_ativacao_total,
            "lucro_liquido_lote": r.lucro_liquido_lote,
            "roi_pct": r.roi_pct,
            "renda_bruta_domme": r.renda_bruta_domme,
        })
    return resultados


# ----------------------------- MIX / KIT COMPOSTO ----------------------------- #
@dataclass
class MixItem:
    sku: str = ""
    quantidade: int = 0
    cvu_mp: float = 0.0
    ticket_medio: float = 0.0
    pfc_individual: float = 0.0
    tier_individual: str = ""


@dataclass
class MixResult:
    # Blendados
    cvu_blendado: float = 0.0
    custo_envase_unit: float = 0.0
    cvu_total_unit: float = 0.0
    pi_laszlo_unit: float = 0.0
    markup_volume: float = 0.0
    tier_nome: str = ""
    fator_escala: float = 1.0
    fee_ativacao_total: float = 0.0
    fee_unitario: float = 0.0
    mix_pfc_unit: float = 0.0
    ticket_medio_blendado: float = 0.0

    # Totais
    total_unidades: int = 0
    total_skus: int = 0
    investimento_total: float = 0.0

    # Viabilidade
    iv: Optional[float] = None
    iv_cor: str = "neutro"
    iv_status: str = ""

    # ROI
    lucro_liquido_lote: Optional[float] = None
    roi_pct: Optional[float] = None
    break_even_un: Optional[int] = None
    margem_liquida_unit: Optional[float] = None

    # Renda DOMME
    repasse_fabrica: float = 0.0
    renda_bruta_domme: float = 0.0
    renda_pct_sobre_lote: float = 0.0
    pro_labore_ok: bool = True

    # Economia vs lotes separados
    avg_pfc_individual_ponderado: float = 0.0
    economia_por_unidade: float = 0.0
    economia_total_lote: float = 0.0

    # Itens detalhados
    itens: list = field(default_factory=list)

    # Alertas
    alertas: list = field(default_factory=list)


def calcular_mix(
    itens: list[tuple[dict, int]],
    mercado: str = "Brasil",
    skus_em_retirada: list[int] = None,
    parametros: Optional[Parametros] = None,
) -> MixResult:
    """
    Calcula pricing de kit composto.
    itens: lista de (dados_sku_dict, quantidade)
    dados_sku_dict deve ter: nome, cvu_mp, ticket_medio, codigo
    """
    p = parametros or Parametros()
    if skus_em_retirada is None:
        skus_em_retirada = []

    if len(itens) < 2:
        raise ValueError("Mix requer pelo menos 2 SKUs.")

    result = MixResult()

    # Calcular totais e blendados
    total_un = sum(qty for _, qty in itens)
    result.total_unidades = total_un
    result.total_skus = len(itens)

    # CVU blendado ponderado
    cvu_blend = sum(d["cvu_mp"] * qty for d, qty in itens) / max(total_un, 1)
    ticket_blend = sum(d["ticket_medio"] * qty for d, qty in itens) / max(total_un, 1)

    result.cvu_blendado = cvu_blend
    result.ticket_medio_blendado = ticket_blend

    # Fator de escala e envase pelo TOTAL do kit
    result.fator_escala = _fator_escala(total_un, p)
    result.custo_envase_unit = p.kit_envase_base * result.fator_escala
    result.cvu_total_unit = cvu_blend + result.custo_envase_unit

    # PI Laszlo
    result.pi_laszlo_unit = result.cvu_total_unit * (1 + p.mil)

    # Tier pelo TOTAL de unidades
    result.tier_nome, result.markup_volume = _tier_info(total_un, p)

    # PFC sem fee
    pfc_sem_fee = (
        result.pi_laszlo_unit
        * (1 + p.md)
        * (1 + result.markup_volume)
        * (1 + p.selo_laszlo)
    )

    # Fee ÚNICO por lote
    valor_lote_est = pfc_sem_fee * total_un
    result.fee_ativacao_total = _fee_ativacao(total_un, valor_lote_est, p)
    result.fee_unitario = result.fee_ativacao_total / max(total_un, 1)

    # PFC mix unitário
    result.mix_pfc_unit = pfc_sem_fee + result.fee_unitario
    result.investimento_total = result.mix_pfc_unit * total_un

    # IV blendado
    if ticket_blend > 0:
        result.iv = result.mix_pfc_unit / ticket_blend
        result.iv_cor, result.iv_status = _iv_classificar(result.iv, p)

    # Renda DOMME
    selo_unit = p.selo_laszlo * pfc_sem_fee
    result.repasse_fabrica = (result.pi_laszlo_unit * total_un) + (selo_unit * total_un)
    result.renda_bruta_domme = result.investimento_total - result.repasse_fabrica
    result.renda_pct_sobre_lote = (
        result.renda_bruta_domme / result.investimento_total
        if result.investimento_total else 0
    )
    result.pro_labore_ok = result.renda_bruta_domme >= p.pro_labore_minimo

    # ROI (usando ticket blendado como proxy de preço de venda)
    receita = ticket_blend * total_un
    receita_liq = receita * (1 - p.desc_impostos_frete)
    result.lucro_liquido_lote = receita_liq - result.investimento_total
    if result.investimento_total > 0:
        result.roi_pct = result.lucro_liquido_lote / result.investimento_total
    result.margem_liquida_unit = result.lucro_liquido_lote / total_un if total_un > 0 else 0
    if result.margem_liquida_unit and result.margem_liquida_unit > 0:
        result.break_even_un = int(-(-result.investimento_total // result.margem_liquida_unit))

    # Calcular PFC individual de cada SKU (se fosse comprado isolado)
    mix_items = []
    soma_pfc_ind_ponderado = 0.0
    for dados, qty in itens:
        r_ind = calcular_pricing(
            sku=dados["nome"], volume=qty,
            cvu_mp=dados["cvu_mp"],
            ticket_medio_laszlo=dados["ticket_medio"],
            parametros=p,
        )
        item = MixItem(
            sku=dados["nome"],
            quantidade=qty,
            cvu_mp=dados["cvu_mp"],
            ticket_medio=dados["ticket_medio"],
            pfc_individual=r_ind.pfc_final_unit,
            tier_individual=r_ind.tier_nome,
        )
        mix_items.append(item)
        soma_pfc_ind_ponderado += r_ind.pfc_final_unit * qty

    result.itens = mix_items
    result.avg_pfc_individual_ponderado = soma_pfc_ind_ponderado / max(total_un, 1)
    result.economia_por_unidade = result.avg_pfc_individual_ponderado - result.mix_pfc_unit
    result.economia_total_lote = result.economia_por_unidade * total_un

    return result
