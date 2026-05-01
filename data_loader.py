"""
DOMME — Data Loader
Lê Catálogo Laszlo, Base MP e Check_Retirada do arquivo xlsx.
Em produção: substituir por queries SQL (Supabase/Postgres).
"""
import functools
from pathlib import Path
from typing import Optional
import pandas as pd

# Caminho relativo ao diretório do app
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_XLSX = _DATA_DIR / "DOMME_Motor_v4.xlsx"


@functools.lru_cache(maxsize=1)
def carregar_catalogo() -> pd.DataFrame:
    """Carrega a aba 'Catálogo Laszlo' do xlsx."""
    df = pd.read_excel(_XLSX, sheet_name="Catálogo Laszlo")
    # Normaliza nomes de colunas
    df.columns = [c.strip() for c in df.columns]
    return df


@functools.lru_cache(maxsize=1)
def carregar_base_mp() -> pd.DataFrame:
    """Carrega a aba 'Base cadastro MP'."""
    df = pd.read_excel(_XLSX, sheet_name="Base cadastro MP")
    df.columns = [c.strip() for c in df.columns]
    return df


@functools.lru_cache(maxsize=1)
def carregar_check_retirada() -> pd.DataFrame:
    """Carrega a aba 'Check_Retirada'."""
    df = pd.read_excel(_XLSX, sheet_name="Check_Retirada")
    df.columns = [c.strip() for c in df.columns]
    return df


def listar_skus_disponiveis() -> list[str]:
    """Retorna lista de nomes de SKUs disponíveis para WL."""
    cat = carregar_catalogo()
    disp = cat[cat["Status WL"].str.contains("Disponível", na=False)]
    return sorted(disp["Nome do Produto"].dropna().tolist())


def buscar_sku(nome: str) -> Optional[dict]:
    """Busca um SKU por nome exato (ou substring) no catálogo."""
    cat = carregar_catalogo()
    # Tenta match exato primeiro
    match = cat[cat["Nome do Produto"] == nome]
    if match.empty:
        # Tenta substring
        match = cat[cat["Nome do Produto"].str.contains(nome, case=False, na=False)]
    if match.empty:
        return None
    row = match.iloc[0]
    return {
        "nome": str(row["Nome do Produto"]),
        "codigo": int(row["Código"]),
        "cvu_mp": float(row["CVU (R$)"]),
        "ticket_medio": float(row["Ticket Médio (R$)"]),
        "vendas_2024": int(row.get("Vendas 2024", 0) or 0),
        "mc_real": float(row.get("% MC Real", 0) or 0),
        "status_wl": str(row.get("Status WL", "")),
        "volume_ml": int(row.get("Volume (ml)", 0) or 0),
        "ranking": row.get("Ranking", ""),
    }


def sku_em_retirada(codigo: int) -> bool:
    """Verifica se um código Laszlo está na lista de retirada."""
    try:
        ret = carregar_check_retirada()
        return codigo in ret["Código Laszlo"].values
    except Exception:
        return False


def kpis_dashboard() -> dict:
    """Retorna KPIs do portfólio para o dashboard."""
    cat = carregar_catalogo()
    total = len(cat)
    disp = cat["Status WL"].str.contains("Disponível", na=False).sum()
    risco = cat["Status WL"].str.contains("Risco", na=False).sum()

    # Ticket médio do catálogo
    tickets = cat["Ticket Médio (R$)"].dropna()
    ticket_medio = float(tickets.mean()) if len(tickets) > 0 else 0.0

    # Vendas totais 2024
    vendas_col = cat.get("Vendas 2024")
    vendas_total = int(vendas_col.sum()) if vendas_col is not None else 0

    return {
        "total_skus": total,
        "skus_disponiveis": disp,
        "skus_risco": risco,
        "ticket_medio_catalogo": ticket_medio,
        "vendas_totais_2024": vendas_total,
    }
