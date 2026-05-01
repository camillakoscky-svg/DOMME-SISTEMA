"""
DOMME — Motor de Recomendações
Classificação aromática, enriquecimento de SKUs, kits pré-curados e matching.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


# ----------------------------- CONSTANTES ----------------------------- #
CANAIS = ["Varejo físico", "E-commerce", "Marketplace", "Profissional (B2B)", "Exportação"]
CANAIS_ICONES = {
    "Varejo físico": "🏪",
    "E-commerce": "🛒",
    "Marketplace": "📦",
    "Profissional (B2B)": "🏢",
    "Exportação": "🌍",
}
TICKETS = ["economico", "intermediario", "premium"]
TICKETS_LABEL = {
    "economico": "💚 Econômico (até R$ 80)",
    "intermediario": "💛 Intermediário (R$ 80-200)",
    "premium": "💎 Premium (acima R$ 200)",
}
OBJETIVOS = ["margem", "volume", "diferenciacao", "sazonalidade"]
OBJETIVOS_LABEL = {
    "margem": "📈 Maximizar margem",
    "volume": "📦 Volume e escala",
    "diferenciacao": "✨ Diferenciação de portfólio",
    "sazonalidade": "🗓 Tendência sazonal",
}

SELO_ALIMENTOS = "🍃 Linha Alimentos"
TOOLTIP_ALIMENTOS = (
    "Registrado como Aroma Natural (Alimentos). "
    "Go-to-market imediato — uso por ingestão sem ANVISA cosmético."
)


# ----------------------------- CLASSIFICAÇÃO ----------------------------- #
FAMILIAS = {
    "Cítrica": {
        "keywords": ["LARANJA", "LIMAO", "LIMÃO", "BERGAMOTA", "TORANJA",
                     "GRAPEFRUIT", "TANGERINA", "MANDARINA", "YUZU", "COMBAVA"],
        "desc": "Notas frescas e estimulantes — energia e vitalidade.",
    },
    "Floral": {
        "keywords": ["ROSA", "JASMIM", "YLANG", "GERANIO", "GERÂNIO", "NEROLI",
                     "CAMOMILA", "LAVANDA", "MIMOSA", "ACACIA", "ACÁCIA",
                     "MAGNOLIA", "MAGNÓLIA", "PALMAROSA", "LÓTUS"],
        "desc": "Notas delicadas e femininas — sofisticação e suavidade.",
    },
    "Amadeirada": {
        "keywords": ["SANDALO", "SÂNDALO", "CEDRO", "VETIVER", "PATCHOULI",
                     "GUAIAC", "AMYRIS", "HINOKI", "CIPRESTE"],
        "desc": "Notas quentes e profundas — grounding e sofisticação.",
    },
    "Herbácea": {
        "keywords": ["ALECRIM", "HORTELA", "HORTELÃ", "MANJERICAO", "MANJERICÃO",
                     "TOMILHO", "SÁLVIA", "SALVIA", "EUCALIPTO", "MENTA",
                     "MELISSA", "LEMONGRASS", "CAPIM"],
        "desc": "Notas verdes e revigorantes — frescor e clareza.",
    },
    "Oriental": {
        "keywords": ["BENJOIM", "BAUNILHA", "INCENSO", "OLIBANO", "OLÍBANO",
                     "MIRRA", "OPOPANAX", "SIAM"],
        "desc": "Notas profundas e envolventes — meditação e rituais.",
    },
    "Resinosa": {
        "keywords": ["COPAIBA", "COPAÍBA", "ELEMI", "BREU", "LABDANO",
                     "LADANO", "ESTORAQUE"],
        "desc": "Notas balsâmicas e reparadoras — tradição brasileira.",
    },
    "Especiada": {
        "keywords": ["CRAVO", "CANELA", "CARDAMOMO", "GENGIBRE", "PIMENTA",
                     "COMINHO", "NOZ-MOSCADA", "ANIS", "FUNCHO", "AÇAFRÃO"],
        "desc": "Notas quentes e gastronômicas — sabor e intensidade.",
    },
    "Aquática": {
        "keywords": ["ALGAS", "TEA TREE", "TEA-TREE", "MELALEUCA"],
        "desc": "Notas purificantes e frescas — clean beauty.",
    },
}

EFEITOS = {
    "Relaxante": ["LAVANDA", "CAMOMILA", "VETIVER", "YLANG", "BERGAMOTA", "CEDRO"],
    "Energizante": ["LARANJA", "LIMAO", "LIMÃO", "HORTELA", "HORTELÃ", "ALECRIM",
                    "TORANJA", "GRAPEFRUIT", "MENTA"],
    "Afrodisíaco": ["JASMIM", "ROSA", "YLANG", "PATCHOULI", "SANDALO", "SÂNDALO",
                    "NEROLI"],
    "Concentração": ["ALECRIM", "HORTELA", "HORTELÃ", "LIMAO", "LIMÃO", "EUCALIPTO",
                     "MENTA"],
    "Imunidade": ["TEA TREE", "MELALEUCA", "EUCALIPTO", "CRAVO", "TOMILHO"],
    "Ansiedade": ["LAVANDA", "BERGAMOTA", "CAMOMILA", "NEROLI", "VETIVER"],
    "Sono": ["LAVANDA", "VETIVER", "CEDRO", "CAMOMILA", "BENJOIM"],
    "Purificação": ["TEA TREE", "MELALEUCA", "LIMAO", "LIMÃO", "EUCALIPTO", "CRAVO"],
    "Culinário": ["BAUNILHA", "LARANJA", "LIMAO", "LIMÃO", "CANELA", "CARDAMOMO",
                  "GENGIBRE", "CACAU", "MENTA", "CRAVO", "AÇAFRÃO"],
}

NICHOS = {
    "Spa & Bem-estar": ["LAVANDA", "YLANG", "BERGAMOTA", "CAMOMILA", "VETIVER", "CEDRO"],
    "Gastronomia & Confeitaria": ["BAUNILHA", "LARANJA", "LIMAO", "LIMÃO", "CANELA",
                                   "CARDAMOMO", "GENGIBRE", "CACAU", "MENTA"],
    "Perfumaria Natural": ["ROSA", "JASMIM", "NEROLI", "SANDALO", "SÂNDALO",
                           "PATCHOULI", "VETIVER", "BERGAMOTA"],
    "Aromaterapia Clínica": ["LAVANDA", "TEA TREE", "MELALEUCA", "EUCALIPTO",
                             "ALECRIM", "CAMOMILA"],
    "Cosméticos & Skincare": ["ROSA", "LAVANDA", "COPAIBA", "COPAÍBA", "TEA TREE",
                              "MELALEUCA", "GERANIO", "GERÂNIO"],
    "Bebidas & Drinks": ["GENGIBRE", "LIMAO", "LIMÃO", "HORTELA", "HORTELÃ",
                         "BERGAMOTA", "LARANJA"],
    "Rituais & Meditação": ["INCENSO", "OLIBANO", "OLÍBANO", "MIRRA", "CEDRO",
                            "SANDALO", "SÂNDALO", "BENJOIM"],
}


# ----------------------------- SKU ENRIQUECIDO ----------------------------- #
@dataclass
class SkuEnriquecido:
    nome: str = ""
    codigo: int = 0
    cvu_mp: float = 0.0
    ticket_medio: float = 0.0
    vendas_2024: int = 0
    mc_real: float = 0.0
    status_wl: str = ""
    familia: str = "Outros"
    familia_desc: str = ""
    efeitos: list = field(default_factory=list)
    nichos: list = field(default_factory=list)
    is_alimentos: bool = False
    bestseller_score: float = 0.0
    is_bestseller: bool = False
    is_novidade: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _classificar_familia(nome: str) -> tuple[str, str]:
    """Retorna (familia, descricao) baseado em keywords no nome."""
    nome_upper = nome.upper()
    for fam, info in FAMILIAS.items():
        for kw in info["keywords"]:
            if kw in nome_upper:
                return fam, info["desc"]
    # Se tem ABS/ABSOLUTO mas não caiu em nenhuma família
    if "ABS " in nome_upper or "ABSOLUTO" in nome_upper:
        return "Exótica", "Notas raras e absolutas — exclusividade para blends premium."
    return "Outros", "Não classificado automaticamente."


def _classificar_efeitos(nome: str) -> list[str]:
    """Retorna lista de efeitos (max 3) baseado em keywords."""
    nome_upper = nome.upper()
    matched = []
    for efeito, keywords in EFEITOS.items():
        for kw in keywords:
            if kw in nome_upper:
                matched.append(efeito)
                break
    return matched[:3]


def _classificar_nichos(nome: str) -> list[str]:
    """Retorna lista de nichos baseado em keywords."""
    nome_upper = nome.upper()
    matched = []
    for nicho, keywords in NICHOS.items():
        for kw in keywords:
            if kw in nome_upper:
                matched.append(nicho)
                break
    return matched[:3]


def _is_alimentos(nome: str) -> bool:
    """Verifica se o SKU pertence à linha de alimentos (aromas naturais)."""
    nome_upper = nome.upper()
    keywords_alimentos = [
        "BAUNILHA", "LARANJA", "LIMAO", "LIMÃO", "CANELA", "CARDAMOMO",
        "GENGIBRE", "CACAU", "MENTA", "CRAVO", "AÇAFRÃO", "ANIS",
        "FUNCHO", "COMINHO", "PIMENTA", "NOZ-MOSCADA", "HORTELÃ", "HORTELA",
        "BERGAMOTA", "TORANJA",
    ]
    return any(kw in nome_upper for kw in keywords_alimentos)


def enriquecer_skus(dados: list[dict]) -> list[SkuEnriquecido]:
    """Enriquece lista de dicts de SKUs com classificação aromática."""
    if not dados:
        return []

    # Determinar bestsellers (top 10% por vendas)
    vendas_vals = sorted(
        [d.get("vendas_2024", 0) or 0 for d in dados], reverse=True
    )
    corte_bestseller = vendas_vals[max(0, len(vendas_vals) // 10)] if vendas_vals else 0

    enriched = []
    for d in dados:
        nome = d.get("nome", "")
        vendas = d.get("vendas_2024", 0) or 0
        mc = d.get("mc_real", 0) or 0
        familia, familia_desc = _classificar_familia(nome)
        efeitos = _classificar_efeitos(nome)
        nichos = _classificar_nichos(nome)
        alimentos = _is_alimentos(nome)

        # Score composto: 40% vendas normalizadas + 40% MC + 20% flag alimentos
        v_max = max(vendas_vals) if vendas_vals and max(vendas_vals) > 0 else 1
        score = (vendas / v_max) * 0.4 + mc * 0.4 + (0.2 if alimentos else 0)

        enriched.append(SkuEnriquecido(
            nome=nome,
            codigo=d.get("codigo", 0),
            cvu_mp=d.get("cvu_mp", 0),
            ticket_medio=d.get("ticket_medio", 0),
            vendas_2024=vendas,
            mc_real=mc,
            status_wl=d.get("status_wl", ""),
            familia=familia,
            familia_desc=familia_desc,
            efeitos=efeitos,
            nichos=nichos,
            is_alimentos=alimentos,
            bestseller_score=score,
            is_bestseller=vendas >= corte_bestseller and vendas > 0,
            is_novidade=d.get("is_novidade", False),
        ))
    return enriched


# ----------------------------- KITS PRÉ-CURADOS ----------------------------- #
@dataclass
class KitTemplate:
    name: str = ""
    tagline: str = ""
    niche: str = ""
    target_client: str = ""
    mercado: str = "Brasil"
    food_line: bool = False
    seasonal: str = ""
    sku_keywords: list = field(default_factory=list)
    components: list = field(default_factory=list)  # [(keyword, qty_default)]


@dataclass
class MatchedKit:
    kit: KitTemplate = field(default_factory=KitTemplate)
    score: float = 0.0


KITS_PRECURADOS: list[KitTemplate] = [
    KitTemplate(
        name="Kit Spa Premium",
        tagline="Relaxamento profundo com notas florais e amadeiradas",
        niche="Spa & Bem-estar",
        target_client="Spas, clínicas de estética, hotéis boutique",
        sku_keywords=["LAVANDA", "YLANG", "BERGAMOTA", "CEDRO"],
        components=[("LAVANDA", 100), ("YLANG", 100), ("BERGAMOTA", 100), ("CEDRO", 100)],
    ),
    KitTemplate(
        name="Kit Confeitaria Artesanal",
        tagline="Aromas para doces, chocolates e panificação",
        niche="Gastronomia & Confeitaria",
        target_client="Confeitarias, chocolaterias, padarias artesanais",
        food_line=True,
        sku_keywords=["BAUNILHA", "LARANJA", "CANELA", "CARDAMOMO"],
        components=[("BAUNILHA", 100), ("LARANJA", 100), ("CANELA", 100), ("CARDAMOMO", 100)],
    ),
    KitTemplate(
        name="Kit Drinks & Bartender",
        tagline="Essências naturais para coquetéis e bebidas premium",
        niche="Bebidas & Drinks",
        target_client="Bares, bartenders, produtores de kombucha e tônicos",
        food_line=True,
        sku_keywords=["GENGIBRE", "LIMAO", "HORTELA", "BERGAMOTA"],
        components=[("GENGIBRE", 100), ("LIMAO", 100), ("HORTELA", 100), ("BERGAMOTA", 100)],
    ),
    KitTemplate(
        name="Kit Perfumaria Natural",
        tagline="Base aromática para perfumes sem sintéticos",
        niche="Perfumaria Natural",
        target_client="Perfumistas artesanais, marcas indie de fragrâncias",
        sku_keywords=["ROSA", "JASMIM", "SANDALO", "PATCHOULI", "VETIVER"],
        components=[("ROSA", 50), ("JASMIM", 50), ("SANDALO", 100), ("PATCHOULI", 100), ("VETIVER", 100)],
    ),
    KitTemplate(
        name="Kit Imunidade & Respiratório",
        tagline="Proteção natural com óleos antivirais e expectorantes",
        niche="Aromaterapia Clínica",
        target_client="Terapeutas, farmácias de manipulação, clínicas integrativas",
        seasonal="Inverno",
        sku_keywords=["EUCALIPTO", "TEA TREE", "ALECRIM", "CRAVO"],
        components=[("EUCALIPTO", 200), ("TEA TREE", 200), ("ALECRIM", 100), ("CRAVO", 100)],
    ),
    KitTemplate(
        name="Kit Meditação & Rituais",
        tagline="Incenso, mirra e cedro — a tradição milenar em óleos puros",
        niche="Rituais & Meditação",
        target_client="Estúdios de yoga, retiros, lojas esotéricas, templos",
        sku_keywords=["INCENSO", "MIRRA", "CEDRO", "SANDALO"],
        components=[("INCENSO", 100), ("MIRRA", 100), ("CEDRO", 100), ("SANDALO", 50)],
    ),
    KitTemplate(
        name="Kit Skincare Botânico",
        tagline="Óleos reparadores e anti-inflamatórios para cosméticos naturais",
        niche="Cosméticos & Skincare",
        target_client="Marcas indie de skincare, farmácias de manipulação",
        sku_keywords=["COPAIBA", "ROSA", "LAVANDA", "TEA TREE", "GERANIO"],
        components=[("COPAIBA", 100), ("ROSA", 50), ("LAVANDA", 100), ("TEA TREE", 100), ("GERANIO", 100)],
    ),
    KitTemplate(
        name="Kit Export Premium",
        tagline="Brazilian botanicals for the international luxury market",
        niche="Exportação Premium",
        target_client="Distribuidores internacionais, marcas europeias e asiáticas",
        mercado="Internacional",
        sku_keywords=["COPAIBA", "ROSA", "PATCHOULI", "BAUNILHA", "VETIVER"],
        components=[("COPAIBA", 200), ("ROSA", 50), ("PATCHOULI", 100), ("BAUNILHA", 100), ("VETIVER", 100)],
    ),
]


# ----------------------------- MATCHING ----------------------------- #
def recomendar_kits(
    canal: str,
    ticket: str,
    objetivo: str,
    enriched_skus: list[SkuEnriquecido],
) -> list[MatchedKit]:
    """Pontua cada kit pré-curado baseado nos filtros selecionados."""
    nomes_disponiveis = {s.nome.upper() for s in enriched_skus}
    resultados = []

    for kit in KITS_PRECURADOS:
        score = 0.0

        # Score de disponibilidade: quantos SKUs do kit existem no catálogo
        matched_skus = 0
        for kw in kit.sku_keywords:
            for nome in nomes_disponiveis:
                if kw.upper() in nome:
                    matched_skus += 1
                    break
        if len(kit.sku_keywords) > 0:
            disponibilidade = matched_skus / len(kit.sku_keywords)
        else:
            disponibilidade = 0
        score += disponibilidade * 4  # max 4 pontos

        # Score de canal
        if canal == "Exportação" and kit.mercado == "Internacional":
            score += 3
        elif canal == "E-commerce" and kit.food_line:
            score += 2
        elif canal == "Profissional (B2B)" and kit.niche in ("Aromaterapia Clínica", "Spa & Bem-estar"):
            score += 2.5
        elif canal == "Marketplace":
            score += 1.5  # generalista
        elif canal == "Varejo físico":
            score += 1.5

        # Score de ticket
        if ticket == "premium":
            if kit.niche in ("Perfumaria Natural", "Exportação Premium"):
                score += 2
        elif ticket == "economico":
            if kit.niche in ("Gastronomia & Confeitaria", "Bebidas & Drinks"):
                score += 2
        else:
            score += 1  # intermediario — neutro

        # Score de objetivo
        if objetivo == "margem" and kit.food_line:
            score += 2
        elif objetivo == "diferenciacao" and kit.niche in ("Perfumaria Natural", "Rituais & Meditação"):
            score += 2
        elif objetivo == "volume" and kit.niche in ("Gastronomia & Confeitaria", "Aromaterapia Clínica"):
            score += 2
        elif objetivo == "sazonalidade" and kit.seasonal:
            score += 3

        resultados.append(MatchedKit(kit=kit, score=score))

    resultados.sort(key=lambda m: m.score, reverse=True)
    return resultados


def expandir_kit(
    kit: KitTemplate,
    catalogo_nomes: list[str],
    buscar_sku_fn,
) -> list[tuple[dict, int]]:
    """Resolve os sku_keywords de um kit contra o catálogo real.
    Retorna lista de (dados_sku, quantidade)."""
    items = []
    for i, kw in enumerate(kit.sku_keywords):
        qty = kit.components[i][1] if i < len(kit.components) else 100
        # Tenta encontrar no catálogo
        for nome in catalogo_nomes:
            if kw.upper() in nome.upper():
                dados = buscar_sku_fn(nome)
                if dados:
                    items.append((dados, qty))
                    break
    return items


# ----------------------------- SAZONALIDADE ----------------------------- #
def tendencia_sazonal() -> tuple[str, str]:
    """Retorna (titulo, descricao) da tendência sazonal atual."""
    mes = datetime.now().month
    if mes in (12, 1, 2):
        return (
            "🌴 Verão — Frescor & Energia",
            "Cítricos e mentolados lideram. Kits refrescantes para o calor."
        )
    elif mes in (3, 4, 5):
        return (
            "🍂 Outono — Aconchego & Transição",
            "Amadeirados e orientais ganham força. Ideal para lançar kits de bem-estar."
        )
    elif mes in (6, 7, 8):
        return (
            "❄️ Inverno — Imunidade & Proteção",
            "Eucalipto, Tea Tree e especiados em alta. Kits respiratórios e de imunidade."
        )
    else:
        return (
            "🌸 Primavera — Renovação & Florais",
            "Rosa, Jasmim e Lavanda em alta. Kits florais e skincare botânico."
        )


# ----------------------------- INSIGHTS ----------------------------- #
@dataclass
class Insights:
    top5_vendas: list = field(default_factory=list)
    melhor_familia_margem: list = field(default_factory=list)  # [(familia, mc_media, count)]
    qtd_alimentos: int = 0
    novidades: list = field(default_factory=list)


def gerar_insights(enriched: list[SkuEnriquecido]) -> Insights:
    """Gera insights do catálogo enriquecido."""
    ins = Insights()

    # Top 5 vendas
    por_vendas = sorted(enriched, key=lambda s: s.vendas_2024, reverse=True)
    ins.top5_vendas = por_vendas[:5]

    # Melhor família por margem
    fam_mc: dict[str, list[float]] = {}
    for s in enriched:
        fam_mc.setdefault(s.familia, []).append(s.mc_real)
    familias_margem = []
    for fam, mcs in fam_mc.items():
        media = sum(mcs) / len(mcs) if mcs else 0
        familias_margem.append((fam, media, len(mcs)))
    familias_margem.sort(key=lambda x: x[1], reverse=True)
    ins.melhor_familia_margem = familias_margem[:5]

    # Quantidade de alimentos
    ins.qtd_alimentos = sum(1 for s in enriched if s.is_alimentos)

    # Novidades
    ins.novidades = [s for s in enriched if s.is_novidade]

    return ins
