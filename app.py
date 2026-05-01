"""
DOMME × LASZLO — Hub de Marcas Premium
App Streamlit single-file com RBAC para 3 perfis (ADMIN/FABRICA/CLIENTE).

Run:
    streamlit run app.py
"""
import inspect
import time
from typing import Optional
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import altair as alt
from datetime import datetime
from pathlib import Path

# Detecta em runtime se este Streamlit suporta o parâmetro `shortcut` em
# st.button (adicionado em Streamlit 1.50+; este projeto roda em 1.57).
# Em versões mais antigas o atalho é silenciosamente omitido em vez de
# quebrar o app.
_BUTTON_SUPPORTS_SHORTCUT = "shortcut" in inspect.signature(st.button).parameters

from core.auth import autenticar, pode, Usuario
from core.pricing import (
    calcular_pricing, comparar_cenarios, Parametros, calcular_mix, MixResult,
)
from core.pdf_generator import gerar_proposta_pdf, gerar_proposta_kit_pdf
from core.data_loader import (
    carregar_catalogo, carregar_base_mp, carregar_check_retirada,
    buscar_sku, sku_em_retirada, listar_skus_disponiveis, kpis_dashboard,
)
from core.recommendations import (
    KITS_PRECURADOS, KitTemplate, MatchedKit, SkuEnriquecido,
    CANAIS, CANAIS_ICONES, TICKETS, TICKETS_LABEL,
    OBJETIVOS, OBJETIVOS_LABEL,
    SELO_ALIMENTOS, TOOLTIP_ALIMENTOS,
    enriquecer_skus, recomendar_kits, expandir_kit,
    tendencia_sazonal, gerar_insights,
)


# -------------------------------- CONFIG ---------------------------------- #
st.set_page_config(
    page_title="DOMME · Hub de Marcas Premium",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -------------------------------- ESTILOS --------------------------------- #
def aplicar_estilos():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, sans-serif;
            color: #0E0E0E;
        }
        h1, .titulo-serif {
            font-family: 'Cormorant Garamond', Georgia, serif !important;
            font-weight: 500 !important;
            font-size: 2.6rem !important;
            letter-spacing: 1px !important;
            line-height: 1.1 !important;
            margin-bottom: 0.3rem !important;
        }
        h2 {
            font-family: 'Cormorant Garamond', Georgia, serif !important;
            font-weight: 500 !important;
            font-size: 2.1rem !important;
            letter-spacing: 0.8px !important;
        }
        h3 {
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important;
            font-size: 0.85rem !important;
            text-transform: uppercase !important;
            letter-spacing: 3px !important;
            color: #6B6B6B !important;
            margin-top: 1.2rem !important;
            margin-bottom: 0.6rem !important;
        }
        .stApp {
            background: #FAFAF7;
        }
        .block-container {
            padding-top: 2.4rem !important;
            padding-bottom: 5.5rem !important;
            max-width: 1400px;
        }

        /* ---------- SIDEBAR ---------- */
        section[data-testid="stSidebar"] {
            background: #0E0E0E;
            border-right: 1px solid #1c1c1c;
        }
        section[data-testid="stSidebar"] * {
            color: #F5F1EA;
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #A88B5C !important;
        }
        /* Sidebar nav buttons */
        section[data-testid="stSidebar"] .stButton > button {
            background: transparent !important;
            color: #C9C2B5 !important;
            border: none !important;
            border-left: 3px solid transparent !important;
            border-radius: 0 !important;
            padding: 0.55rem 0.9rem 0.55rem 1rem !important;
            text-align: left !important;
            justify-content: flex-start !important;
            text-transform: none !important;
            letter-spacing: 0.3px !important;
            font-weight: 400 !important;
            font-size: 0.88rem !important;
            transition: all 0.15s ease;
            box-shadow: none !important;
        }
        section[data-testid="stSidebar"] .stButton > button:hover {
            background: rgba(168,139,92,0.08) !important;
            color: #F5F1EA !important;
            border-left-color: rgba(168,139,92,0.5) !important;
        }
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: rgba(168,139,92,0.12) !important;
            color: #A88B5C !important;
            border-left: 3px solid #A88B5C !important;
            font-weight: 500 !important;
        }
        .sidebar-divider {
            height: 1px;
            background: linear-gradient(to right, transparent, #A88B5C44, transparent);
            margin: 1rem 0;
        }
        .sidebar-section-label {
            font-size: 0.65rem;
            letter-spacing: 2.5px;
            text-transform: uppercase;
            color: #6B6256 !important;
            margin: 0.6rem 0 0.4rem 1rem;
        }

        /* ---------- LOGOS ---------- */
        .domme-logo {
            font-family: 'Cormorant Garamond', serif;
            font-size: 2.4rem;
            letter-spacing: 8px;
            font-weight: 500;
            color: #A88B5C;
            text-align: center;
            margin: 1rem 0 0.2rem 0;
        }
        .domme-tagline {
            font-size: 0.7rem;
            letter-spacing: 3px;
            color: #6B6B6B;
            text-align: center;
            text-transform: uppercase;
            margin-bottom: 1.5rem;
        }
        /* Dashboard hero (cabeçalho enxuto da tela inicial) */
        .dashboard-hero {
            margin: 0.2rem 0 1.4rem 0;
            padding-bottom: 1rem;
            border-bottom: 1px solid #E8E2D5;
        }
        .dashboard-hello {
            font-family: 'Cormorant Garamond', Georgia, serif !important;
            font-weight: 500 !important;
            font-size: 2.4rem !important;
            color: #0E0E0E !important;
            line-height: 1.1 !important;
            margin: 0 0 0.5rem 0 !important;
            letter-spacing: 0.5px !important;
        }
        .dashboard-hello span {
            color: #A88B5C;
            font-style: italic;
        }
        .dashboard-subtitle {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.55rem;
            font-size: 0.78rem;
            color: #6B6B6B;
            letter-spacing: 0.4px;
        }
        .dashboard-subtitle .ds-chip {
            display: inline-block;
            padding: 0.18rem 0.6rem;
            border: 1px solid #A88B5C;
            border-radius: 999px;
            color: #A88B5C;
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 1.4px;
            font-weight: 500;
            background: rgba(168,139,92,0.06);
        }
        .dashboard-subtitle .ds-sep { color: #C9C2B5; }
        .dashboard-subtitle .ds-org {
            color: #0E0E0E;
            font-weight: 500;
        }
        .dashboard-subtitle .ds-tagline {
            color: #8A8273;
            text-transform: uppercase;
            letter-spacing: 1.6px;
            font-size: 0.66rem;
        }
        .sidebar-mini-logo {
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.55rem;
            letter-spacing: 6px;
            font-weight: 500;
            color: #A88B5C !important;
            text-align: center;
            margin: 0.4rem 0 0.1rem 0;
        }
        .sidebar-mini-tag {
            font-size: 0.6rem;
            letter-spacing: 2.5px;
            color: #6B6256 !important;
            text-align: center;
            text-transform: uppercase;
            margin-bottom: 1.2rem;
        }

        /* ---------- METRIC CARDS ---------- */
        .metric-card {
            background: white;
            padding: 1.4rem 1.6rem 1.3rem 1.6rem;
            border: 1px solid #E5DFD3;
            border-top: 3px solid #A88B5C;
            border-radius: 4px;
            position: relative;
            animation: fadeUp 0.45s ease both;
            transition: box-shadow 0.2s ease, transform 0.2s ease;
            min-height: 110px;
        }
        .metric-card:hover {
            box-shadow: 0 6px 18px rgba(14,14,14,0.06);
            transform: translateY(-1px);
        }
        .metric-card.iv-verde    { border-top-color: #2D6A4F; }
        .metric-card.iv-amarelo  { border-top-color: #C49B0B; }
        .metric-card.iv-vermelho { border-top-color: #9E2A2B; }
        .metric-card.iv-neutro   { border-top-color: #A88B5C; }
        .metric-label {
            font-size: 0.68rem;
            letter-spacing: 2.2px;
            text-transform: uppercase;
            color: #6B6B6B;
            margin-bottom: 0.45rem;
        }
        .metric-value {
            font-family: 'Cormorant Garamond', serif;
            font-size: 2rem;
            font-weight: 500;
            color: #0E0E0E;
            display: flex;
            align-items: baseline;
            gap: 0.4rem;
            line-height: 1.05;
        }
        .metric-arrow {
            font-size: 0.95rem;
            font-weight: 600;
        }
        .arrow-up    { color: #2D6A4F; }
        .arrow-down  { color: #9E2A2B; }
        .arrow-flat  { color: #A88B5C; }
        .metric-sub {
            font-size: 0.76rem;
            color: #6B6B6B;
            margin-top: 0.45rem;
        }
        @keyframes fadeUp {
            0%   { opacity: 0; transform: translateY(8px); }
            100% { opacity: 1; transform: translateY(0); }
        }

        /* ---------- WIZARD STEP INDICATOR ---------- */
        .stepper {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0;
            margin: 0.5rem 0 2rem 0;
        }
        .step {
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }
        .step-circle {
            width: 34px;
            height: 34px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.1rem;
            font-weight: 600;
            border: 1.5px solid #D8D2C4;
            background: white;
            color: #9A9484;
        }
        .step.active .step-circle {
            border-color: #A88B5C;
            background: #A88B5C;
            color: #FAFAF7;
            box-shadow: 0 0 0 4px rgba(168,139,92,0.15);
        }
        .step.done .step-circle {
            border-color: #A88B5C;
            color: #A88B5C;
            background: #FAFAF7;
        }
        .step-label {
            font-size: 0.72rem;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #9A9484;
        }
        .step.active .step-label,
        .step.done   .step-label {
            color: #A88B5C;
        }
        .step-bar {
            width: 60px;
            height: 1px;
            background: #D8D2C4;
            margin: 0 0.7rem;
        }
        .step.done + .step-bar,
        .step.active + .step-bar {
            background: #A88B5C;
        }

        /* ---------- EMPTY STATE ---------- */
        .empty-state {
            background: #FFFFFF;
            border: 1px dashed #D8D2C4;
            border-radius: 6px;
            padding: 3.5rem 1.5rem;
            text-align: center;
            margin: 1.5rem 0;
            animation: fadeUp 0.4s ease both;
        }
        .empty-state .es-icon {
            font-family: 'Cormorant Garamond', serif;
            font-size: 3rem;
            color: #A88B5C;
            line-height: 1;
            margin-bottom: 0.6rem;
        }
        .empty-state .es-title {
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.5rem;
            color: #0E0E0E;
            margin-bottom: 0.4rem;
        }
        .empty-state .es-sub {
            font-size: 0.85rem;
            color: #6B6B6B;
            letter-spacing: 0.5px;
        }

        /* ---------- PRODUCT CARD ---------- */
        .product-card {
            background: white;
            border: 1px solid #E5DFD3;
            border-left: 3px solid #A88B5C;
            border-radius: 4px;
            padding: 1.4rem 1.6rem;
            margin: 0.5rem 0 1rem 0;
            animation: fadeUp 0.45s ease both;
        }
        .product-card .pc-name {
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.4rem;
            color: #0E0E0E;
            margin-bottom: 0.6rem;
        }
        .product-card .pc-row {
            display: flex;
            gap: 2.2rem;
            flex-wrap: wrap;
        }
        .product-card .pc-cell .pc-label {
            font-size: 0.65rem;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #6B6B6B;
        }
        .product-card .pc-cell .pc-value {
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.25rem;
            color: #0E0E0E;
            margin-top: 0.15rem;
        }
        .pc-status-badge {
            display: inline-block;
            padding: 0.2rem 0.7rem;
            border-radius: 999px;
            font-size: 0.7rem;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            font-weight: 500;
        }
        .pc-status-ok    { background: #E6F0EA; color: #2D6A4F; }
        .pc-status-warn  { background: #FFF3CD; color: #8A6D0B; }
        .pc-status-block { background: #FBE4E5; color: #9E2A2B; }

        /* ---------- DASHBOARD: AÇÕES PANEL ---------- */
        .actions-panel {
            background: white;
            border: 1px solid #E5DFD3;
            border-radius: 4px;
            padding: 1.2rem 1.4rem;
            animation: fadeUp 0.45s ease both;
        }
        .actions-panel .ap-title {
            font-size: 0.75rem;
            letter-spacing: 2.5px;
            text-transform: uppercase;
            color: #6B6B6B;
            margin-bottom: 0.9rem;
        }
        .action-item {
            display: flex;
            gap: 0.8rem;
            padding: 0.7rem 0;
            border-bottom: 1px solid #F0EBE0;
        }
        .action-item:last-child { border-bottom: none; }
        .action-icon {
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.4rem;
            color: #A88B5C;
            line-height: 1.2;
            min-width: 1.8rem;
        }
        .action-text { font-size: 0.88rem; color: #0E0E0E; }
        .action-meta { font-size: 0.75rem; color: #6B6B6B; margin-top: 0.15rem; }

        /* ---------- LEGACY (Cenários etc) ---------- */
        .iv-badge {
            padding: 1.2rem 1.6rem;
            border-radius: 4px;
            color: white;
            font-weight: 500;
            margin: 0.5rem 0;
        }
        .iv-verde-bg { background: #2D6A4F; }
        .iv-amarelo-bg { background: #C49B0B; }
        .iv-vermelho-bg { background: #9E2A2B; }
        .iv-neutro-bg { background: #6B6B6B; }
        .alerta-box {
            background: #FFF8E1;
            border-left: 3px solid #C49B0B;
            padding: 0.8rem 1.2rem;
            margin: 0.5rem 0;
            font-size: 0.9rem;
        }
        .alerta-critico {
            background: #FFEBEE;
            border-left-color: #9E2A2B;
        }
        div[data-testid="stMetricValue"] {
            font-family: 'Cormorant Garamond', serif;
            font-size: 2rem;
        }

        /* Default (non-sidebar) buttons */
        .stButton > button {
            background: #0E0E0E;
            color: #F5F1EA;
            border: none;
            border-radius: 2px;
            padding: 0.6rem 1.4rem;
            font-weight: 500;
            letter-spacing: 1px;
            text-transform: uppercase;
            font-size: 0.78rem;
            transition: all 0.15s ease;
        }
        .stButton > button:hover {
            background: #A88B5C;
            color: #FAFAF7;
        }
        .stDownloadButton > button {
            background: #A88B5C;
            color: #FAFAF7;
            border: none;
            border-radius: 2px;
            padding: 0.55rem 1.3rem;
            font-weight: 500;
            letter-spacing: 1px;
            text-transform: uppercase;
            font-size: 0.78rem;
        }
        .stDownloadButton > button:hover { background: #0E0E0E; }
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(to right, transparent 0%, #A88B5C55 18%, #A88B5C55 82%, transparent 100%);
            margin: 2.5rem 0;
        }
        .gold-divider {
            height: 1px;
            background: linear-gradient(to right, transparent 0%, #A88B5C55 18%, #A88B5C55 82%, transparent 100%);
            margin: 2.5rem 0;
        }

        /* ---------- BREADCRUMB ---------- */
        .breadcrumb {
            font-size: 0.62rem;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: #A88B5C;
            margin: 0 0 0.6rem 0;
            font-weight: 500;
        }
        .breadcrumb .crumb-sep { color: #6B6256; margin: 0 0.5rem; }
        .breadcrumb .crumb-current { color: #0E0E0E; }

        /* ---------- METRIC CARD: TOOLTIP + COUNT-UP REVEAL ---------- */
        .metric-tip {
            display: inline-block;
            margin-left: 0.35rem;
            color: #A88B5C;
            cursor: help;
            font-size: 0.78rem;
            position: relative;
            opacity: 0.65;
            transition: opacity 0.15s ease;
        }
        .metric-tip:hover { opacity: 1; }
        .metric-tip .tip-bubble {
            visibility: hidden;
            opacity: 0;
            position: absolute;
            bottom: 130%;
            left: 50%;
            transform: translateX(-50%);
            background: #0E0E0E;
            color: #F5F1EA;
            font-family: 'Inter', sans-serif;
            font-size: 0.7rem;
            letter-spacing: 0.3px;
            text-transform: none;
            line-height: 1.35;
            padding: 0.55rem 0.75rem;
            border-radius: 4px;
            border-top: 2px solid #A88B5C;
            min-width: 180px;
            max-width: 240px;
            text-align: center;
            white-space: normal;
            z-index: 60;
            box-shadow: 0 6px 18px rgba(14,14,14,0.18);
            transition: opacity 0.15s ease;
        }
        .metric-tip:hover .tip-bubble {
            visibility: visible;
            opacity: 1;
        }
        .metric-card .metric-value {
            animation: countReveal 0.7s cubic-bezier(0.2, 0.8, 0.2, 1) both;
        }
        @keyframes countReveal {
            0%   { opacity: 0; transform: translateY(6px) scale(0.92); filter: blur(2px); }
            60%  { opacity: 1; filter: blur(0); }
            100% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
        }
        .metric-delta {
            display: inline-block;
            margin-left: 0.4rem;
            font-family: 'Inter', sans-serif;
            font-size: 0.72rem;
            font-weight: 500;
            letter-spacing: 0.3px;
        }
        .metric-delta.delta-up   { color: #2D6A4F; }
        .metric-delta.delta-down { color: #9E2A2B; }
        .metric-delta.delta-flat { color: #A88B5C; }

        /* ---------- FOCUS RINGS / GOLD BOTTOM-BORDER ON FORM FIELDS ---------- */
        .stButton > button:focus-visible,
        .stDownloadButton > button:focus-visible,
        a:focus-visible {
            outline: 2px solid #A88B5C !important;
            outline-offset: 2px !important;
            box-shadow: 0 0 0 4px rgba(168,139,92,0.18) !important;
        }
        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="select"]:focus-within,
        div[data-baseweb="textarea"]:focus-within {
            border-bottom: 2px solid #A88B5C !important;
            box-shadow: 0 1px 0 0 #A88B5C !important;
        }
        input[type="text"]:focus,
        input[type="number"]:focus,
        input[type="password"]:focus,
        textarea:focus {
            outline: none !important;
            border-bottom: 2px solid #A88B5C !important;
            box-shadow: 0 1px 0 0 #A88B5C !important;
        }

        /* ---------- IV STATUS ICON BADGES ---------- */
        .iv-status-line {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            font-size: 0.85rem;
            margin-top: 0.2rem;
        }
        .iv-status-icon {
            width: 22px; height: 22px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            font-weight: 700;
            font-size: 0.78rem;
            color: white;
        }
        .iv-status-icon.iv-verde    { background: #2D6A4F; }
        .iv-status-icon.iv-amarelo  { background: #C49B0B; }
        .iv-status-icon.iv-vermelho { background: #9E2A2B; }
        .iv-status-icon.iv-neutro   { background: #6B6B6B; }

        /* ---------- IV THERMOMETER SUB-LABELS + EXPLANATION ---------- */
        .iv-tick-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: -0.4rem;
            padding: 0 2px;
            font-size: 0.62rem;
            letter-spacing: 1.8px;
            text-transform: uppercase;
            color: #6B6B6B;
        }
        .iv-tick-row .iv-tick-num { color: #0E0E0E; font-weight: 500; }
        .iv-explain {
            margin-top: 0.6rem;
            font-size: 0.85rem;
            color: #0E0E0E;
            line-height: 1.4;
            font-style: italic;
        }

        /* ---------- THREE-PANEL MOTOR LAYOUT ---------- */
        .panel-title {
            font-size: 0.66rem;
            letter-spacing: 2.6px;
            text-transform: uppercase;
            color: #A88B5C;
            margin: 0.2rem 0 0.8rem 0;
            font-weight: 500;
        }
        .alert-card {
            background: #FFF8E1;
            border-left: 3px solid #C49B0B;
            padding: 0.7rem 1rem;
            margin: 0.4rem 0;
            font-size: 0.82rem;
            border-radius: 0 3px 3px 0;
        }
        .alert-card.alert-critical {
            background: #FBE4E5;
            border-left-color: #9E2A2B;
        }
        .alert-card.alert-info {
            background: #F5F1EA;
            border-left-color: #A88B5C;
        }

        /* ---------- SUGESTÕES DE MIX (recomendações) ---------- */
        .reco-banner {
            background: linear-gradient(90deg, #F5F1EA 0%, #FFFFFF 100%);
            border-left: 3px solid #A88B5C;
            border-radius: 0 4px 4px 0;
            padding: 0.9rem 1.2rem;
            margin: 0.4rem 0 1.2rem 0;
            animation: fadeUp 0.5s ease both;
        }
        .reco-banner .rb-title {
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.15rem;
            color: #0E0E0E;
            margin-bottom: 0.15rem;
        }
        .reco-banner .rb-sub {
            font-size: 0.82rem;
            color: #6B6256;
        }
        .reco-kit-card {
            background: #FFFFFF;
            border: 1px solid #E5DFD3;
            border-left: 3px solid #A88B5C;
            border-radius: 4px;
            padding: 1.1rem 1.3rem 1.2rem 1.3rem;
            margin: 0.4rem 0 0.8rem 0;
            min-height: 232px;
            display: flex;
            flex-direction: column;
            animation: fadeUp 0.4s ease both;
        }
        .reco-kit-card .rk-name {
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.45rem;
            color: #0E0E0E;
            margin-bottom: 0.25rem;
            line-height: 1.15;
        }
        .reco-kit-card .rk-tag {
            font-size: 0.82rem;
            color: #6B6256;
            font-style: italic;
            margin-bottom: 0.7rem;
        }
        .reco-kit-card .rk-niche {
            font-size: 0.7rem;
            letter-spacing: 1.6px;
            text-transform: uppercase;
            color: #A88B5C;
            margin-bottom: 0.5rem;
        }
        .reco-kit-card .rk-row {
            display: flex; gap: 1.4rem; flex-wrap: wrap;
            margin: 0.35rem 0 0.5rem 0;
        }
        .reco-kit-card .rk-cell .rk-label {
            font-size: 0.62rem;
            letter-spacing: 1.6px;
            text-transform: uppercase;
            color: #6B6B6B;
        }
        .reco-kit-card .rk-cell .rk-value {
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.1rem;
            color: #0E0E0E;
        }
        .reco-kit-card .rk-target {
            font-size: 0.75rem;
            color: #4A4A4A;
            margin-top: 0.4rem;
            line-height: 1.45;
        }
        .reco-chip {
            display: inline-block;
            font-size: 0.65rem;
            letter-spacing: 1.4px;
            text-transform: uppercase;
            background: #F5F1EA;
            color: #6B6256;
            padding: 0.18rem 0.55rem;
            border-radius: 999px;
            margin: 0.15rem 0.25rem 0.15rem 0;
            border: 1px solid #E5DFD3;
        }
        .reco-chip.reco-chip-food {
            background: #E6F0EA; color: #2D6A4F;
            border-color: #C7E0D0;
        }
        .reco-chip.reco-chip-best {
            background: #FFF7E0; color: #8A6D0B;
            border-color: #F0E2A8;
        }
        .reco-chip.reco-chip-novo {
            background: #FBE9E7; color: #B53B23;
            border-color: #F4C7BD;
        }
        .reco-chip.reco-chip-season {
            background: #EAE7F5; color: #4B3F8A;
            border-color: #D4CDEB;
        }
        .reco-sku-card {
            background: #FFFFFF;
            border: 1px solid #E5DFD3;
            border-radius: 4px;
            padding: 0.9rem 1rem;
            margin: 0.35rem 0;
            animation: fadeUp 0.35s ease both;
        }
        .reco-sku-card .rs-name {
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.05rem;
            color: #0E0E0E;
            margin-bottom: 0.25rem;
            line-height: 1.2;
        }
        .reco-sku-card .rs-meta {
            font-size: 0.72rem;
            color: #6B6B6B;
            margin-top: 0.15rem;
        }
        .reco-stars {
            color: #C49B0B; letter-spacing: 1px;
            font-size: 0.85rem;
        }
        .reco-empty {
            font-size: 0.85rem;
            color: #6B6256;
            font-style: italic;
            padding: 0.8rem 0;
        }
        .reco-shortlist-bar {
            background: #F5F1EA;
            border: 1px solid #E5DFD3;
            border-left: 3px solid #A88B5C;
            border-radius: 4px;
            padding: 0.7rem 1rem;
            margin: 0.6rem 0 1rem 0;
            font-size: 0.85rem;
            color: #0E0E0E;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.8rem;
            flex-wrap: wrap;
        }
        .reco-insight-card {
            background: #FFFFFF;
            border: 1px solid #E5DFD3;
            border-radius: 4px;
            padding: 1rem 1.2rem;
            margin: 0.4rem 0;
            min-height: 168px;
            animation: fadeUp 0.4s ease both;
        }
        .reco-insight-card .ri-title {
            font-size: 0.66rem;
            letter-spacing: 2.6px;
            text-transform: uppercase;
            color: #A88B5C;
            margin-bottom: 0.6rem;
        }
        .reco-insight-card .ri-row {
            font-size: 0.85rem;
            color: #0E0E0E;
            padding: 0.25rem 0;
            border-bottom: 1px solid #F0EBE0;
        }
        .reco-insight-card .ri-row:last-child { border-bottom: none; }
        .reco-insight-card .ri-row .ri-num {
            color: #6B6256;
            font-size: 0.78rem;
            margin-right: 0.4rem;
        }
        .reco-insight-card .ri-big {
            font-family: 'Cormorant Garamond', serif;
            font-size: 2.4rem;
            color: #A88B5C;
            line-height: 1;
            margin: 0.2rem 0 0.3rem 0;
        }

        /* ---------- PAGE FADE ON SECTION TRANSITION ---------- */
        .block-container {
            animation: pageFade 0.22s ease-out both;
        }
        @keyframes pageFade {
            from { opacity: 0; }
            to   { opacity: 1; }
        }

        /* ---------- 40px section spacing ---------- */
        .section-gap { height: 40px; }

        /* ---------- Botões ocultos para atalhos de teclado ---------- */
        /* Renderizados por _render_hidden_kbd_buttons; nunca devem ser
           visíveis nem capturar eventos do mouse — apenas o handler JS
           os aciona programaticamente via .click(). */
        .st-key-domme-kbd-buttons,
        [class*="st-key-_kbd_"] {
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            margin: -1px !important;
            padding: 0 !important;
            border: 0 !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }

        /* ---------- PDF success badge (transição ~2s) ---------- */
        .pdf-success-badge {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            background: linear-gradient(135deg, #2E7D32, #43A047);
            color: #FFF;
            font-size: 0.92rem;
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
            padding: 0.65rem 1rem;
            margin: 0.4rem 0 0.6rem 0;
            border-radius: 6px;
            box-shadow: 0 4px 14px rgba(46,125,50,0.28);
            animation: pdfSuccessFlash 2.0s ease forwards;
            transform-origin: center;
        }
        .pdf-success-badge .check-circle {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.4rem;
            height: 1.4rem;
            border-radius: 50%;
            background: rgba(255,255,255,0.18);
            font-size: 1rem;
            line-height: 1;
            animation: pdfCheckPop 0.45s cubic-bezier(0.18,0.89,0.32,1.28);
        }
        @keyframes pdfSuccessFlash {
            0%   { opacity: 0; transform: scale(0.92) translateY(-4px); }
            12%  { opacity: 1; transform: scale(1.02) translateY(0); }
            22%  { transform: scale(1) translateY(0); }
            80%  { opacity: 1; transform: scale(1) translateY(0); }
            100% { opacity: 0.55; transform: scale(0.99) translateY(0); }
        }
        @keyframes pdfCheckPop {
            0%   { transform: scale(0); }
            70%  { transform: scale(1.25); }
            100% { transform: scale(1); }
        }


        /* ---------- FOOTER ---------- */
        .domme-footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            text-align: center;
            padding: 0.6rem 1rem;
            font-size: 0.7rem;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: #A88B5C;
            background: linear-gradient(to top, rgba(250,250,247,0.95), rgba(250,250,247,0.0));
            pointer-events: none;
            z-index: 50;
        }

        /* ---------- RESPONSIVE (mobile / narrow viewports) ---------- */
        @media (max-width: 900px) {
            h1, .stMarkdown h1 { font-size: 1.9rem !important; }
            h2, .stMarkdown h2 { font-size: 1.4rem !important; }
            .stepper { flex-wrap: wrap; gap: 0.4rem 0; }
            .step-bar { width: 24px; margin: 0 0.3rem; }
            .step-label { display: none; }
            .step { gap: 0.3rem; }
            .metric-card {
                padding: 1.1rem 1.0rem;
                margin-bottom: 0.6rem;
            }
            .metric-card .metric-value { font-size: 1.5rem !important; }
            .product-card { padding: 1.1rem 1.0rem; }
            .actions-panel { padding: 1.1rem 1.1rem; }
            .domme-footer {
                font-size: 0.6rem;
                letter-spacing: 2px;
                padding: 0.5rem 0.6rem;
            }
        }
        /* Bottom-nav: por padrão escondido (desktop); mostrado em mobile */
        .st-key-domme-mobile-botnav { display: none; }

        @media (max-width: 768px) {
            .block-container {
                padding-top: 1.4rem !important;
                padding-bottom: 5.5rem !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
            h1, .stMarkdown h1, .titulo-serif { font-size: 2rem !important; }
            .metric-card .metric-value { font-size: 1.5rem !important; }
            .metric-card { min-height: 95px; }
            div[data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
            }
            div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
                flex: 1 1 100% !important;
                min-width: 100% !important;
                margin-bottom: 0.8rem;
            }
            /* Mobile bottom-nav: container st.button posicionado fixo */
            .st-key-domme-mobile-botnav {
                display: block !important;
                position: fixed !important;
                left: 0; right: 0; bottom: 0;
                background: #0E0E0E;
                border-top: 2px solid #A88B5C;
                z-index: 100;
                padding: 0.45rem 0.6rem 0.55rem 0.6rem;
                box-shadow: 0 -4px 18px rgba(14,14,14,0.18);
            }
            /* Dentro do container, força colunas a NÃO quebrar (override
               da regra de stack vertical acima). */
            .st-key-domme-mobile-botnav div[data-testid="stHorizontalBlock"] {
                flex-wrap: nowrap !important;
                gap: 0.3rem !important;
            }
            .st-key-domme-mobile-botnav div[data-testid="stHorizontalBlock"]
                > div[data-testid="column"] {
                flex: 1 1 0 !important;
                min-width: 0 !important;
                margin-bottom: 0 !important;
            }
            .st-key-domme-mobile-botnav .stButton > button {
                background: transparent !important;
                color: #A88B5C !important;
                border: none !important;
                padding: 0.35rem 0.1rem !important;
                line-height: 1 !important;
                letter-spacing: 0 !important;
                text-transform: none !important;
                min-height: 2.8rem !important;
                box-shadow: none !important;
                gap: 0 !important;
            }
            /* Icons-only no mobile: oculta o <p> de label (Streamlit
               renderiza o texto do botão dentro de um <p>), preservando
               apenas o ícone Material. */
            .st-key-domme-mobile-botnav .stButton > button p,
            .st-key-domme-mobile-botnav .stButton > button div p {
                display: none !important;
            }
            .st-key-domme-mobile-botnav .stButton > button
                [data-testid="stIconMaterial"] {
                font-size: 1.65rem !important;
                line-height: 1 !important;
                margin: 0 !important;
            }
            .st-key-domme-mobile-botnav .stButton > button:hover {
                background: rgba(168,139,92,0.12) !important;
                color: #F5F1EA !important;
            }
            .st-key-domme-mobile-botnav .stButton > button[kind="primary"] {
                color: #F5F1EA !important;
                background: rgba(168,139,92,0.18) !important;
            }
            .st-key-domme-mobile-botnav .stButton > button[kind="primary"]
                [data-testid="stIconMaterial"] {
                color: #F5F1EA !important;
            }
            .domme-footer {
                bottom: 56px;
                font-size: 0.55rem;
                letter-spacing: 1.6px;
                padding: 0.35rem 0.6rem;
                background: transparent;
            }
        }
        @media (max-width: 560px) {
            .step-circle { width: 28px; height: 28px; font-size: 0.95rem; }
            .step-bar { width: 12px; }
        }
    </style>
    """, unsafe_allow_html=True)


# -------------------------------- HELPERS --------------------------------- #
def fmt_brl(valor) -> str:
    if valor is None or pd.isna(valor):
        return "—"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(valor) -> str:
    if valor is None or pd.isna(valor):
        return "—"
    return f"{valor:.1%}"


def metric_card(label: str, value: str, sub: str = ""):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>
    """, unsafe_allow_html=True)


def metric_card_iv(
    label: str,
    value: str,
    sub: str = "",
    iv_cor: str = "neutro",
    arrow: str = "",
    tooltip: str = "",
    delta_label: str = "",
    delta_dir: str = "",
    value_num: float | None = None,
    value_format: str = "text",
):
    """Metric card com top-border colorido, tooltip ⓘ, contagem
    progressiva real (count-up via JS quando value_num é informado),
    seta de tendência e delta vs. simulação anterior.

    Parâmetros opcionais para count-up numérico:
      value_num    — valor numérico de destino para animação.
      value_format — 'brl' (R$ pt-BR), 'pct' (xx,x%), 'int' (milhar pt-BR),
                     'iv' (3 casas) ou 'text' (sem animação)."""
    arrow_html = ""
    if arrow == "up":
        arrow_html = '<span class="metric-arrow arrow-up">▲</span>'
    elif arrow == "down":
        arrow_html = '<span class="metric-arrow arrow-down">▼</span>'
    elif arrow == "flat":
        arrow_html = '<span class="metric-arrow arrow-flat">→</span>'

    tip_html = ""
    if tooltip:
        tip_html = (
            f'<span class="metric-tip" tabindex="0">ⓘ'
            f'<span class="tip-bubble">{tooltip}</span></span>'
        )

    delta_html = ""
    if delta_label and delta_dir in ("up", "down", "flat"):
        delta_html = f'<span class="metric-delta delta-{delta_dir}">{delta_label}</span>'

    # Count-up: emite atributos lidos pelo handler JS injetado uma vez
    # por render (ver _inject_metric_countup). Sem value_num, render
    # textual idêntico ao anterior.
    if value_num is not None and value_format != "text":
        value_inner = (
            f'<span class="metric-countup" '
            f'data-target="{float(value_num)}" '
            f'data-format="{value_format}" '
            f'data-final="{value}">{value}</span>'
        )
    else:
        value_inner = value

    st.markdown(f"""
        <div class="metric-card iv-{iv_cor}">
            <div class="metric-label">{label}{tip_html}</div>
            <div class="metric-value">{value_inner} {arrow_html}</div>
            <div class="metric-sub">{sub}{delta_html}</div>
        </div>
    """, unsafe_allow_html=True)


def _inject_metric_countup():
    """Injeta uma única vez o handler JS de contagem progressiva
    (~700 ms) para todos os spans .metric-countup da página."""
    components.html(
        """
<script>
(function () {
  const win = window.parent;
  if (!win || !win.document) return;
  const doc = win.document;
  const DURATION = 700;
  function fmt(v, kind) {
    if (kind === "brl") {
      return "R$ " + v.toLocaleString("pt-BR",
        { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    if (kind === "pct") {
      return v.toLocaleString("pt-BR",
        { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + "%";
    }
    if (kind === "int") {
      return Math.round(v).toLocaleString("pt-BR");
    }
    if (kind === "iv") {
      return v.toLocaleString("pt-BR",
        { minimumFractionDigits: 3, maximumFractionDigits: 3 });
    }
    return String(v);
  }
  function animate(el) {
    if (el.dataset.countupDone === "1") return;
    el.dataset.countupDone = "1";
    const target = parseFloat(el.dataset.target);
    const kind = el.dataset.format || "text";
    const finalText = el.dataset.final || el.textContent;
    if (!isFinite(target)) { el.textContent = finalText; return; }
    const start = performance.now();
    function tick(now) {
      const t = Math.min(1, (now - start) / DURATION);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = fmt(target * eased, kind);
      if (t < 1) {
        win.requestAnimationFrame(tick);
      } else {
        el.textContent = finalText;
      }
    }
    win.requestAnimationFrame(tick);
  }
  function scan() {
    const els = doc.querySelectorAll(".metric-countup");
    els.forEach(animate);
  }
  scan();
  // Observa novas adições (Streamlit re-renderiza com frequência).
  if (!doc.__dommeCountupObserver) {
    const obs = new win.MutationObserver(function () { scan(); });
    obs.observe(doc.body, { childList: true, subtree: true });
    doc.__dommeCountupObserver = obs;
  }
})();
</script>
""",
        height=0,
    )


def render_empty_state(titulo: str, subtitulo: str = "", icone: str = "◆"):
    st.markdown(f"""
        <div class="empty-state">
            <div class="es-icon">{icone}</div>
            <div class="es-title">{titulo}</div>
            <div class="es-sub">{subtitulo}</div>
        </div>
    """, unsafe_allow_html=True)


def render_breadcrumb(pagina: str):
    """Pequeno breadcrumb dourado uppercase no topo de cada tela."""
    st.markdown(
        f'<div class="breadcrumb">DOMME'
        f'<span class="crumb-sep">›</span>'
        f'<span class="crumb-current">{pagina}</span></div>',
        unsafe_allow_html=True,
    )


def render_divider():
    """Divisor decorativo dourado fino."""
    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)


def render_step_indicator(produto_done: bool, lote_done: bool, resultado_done: bool):
    """Indicador passivo de 3 etapas — destaca em ouro conforme cada
    seção recebe dados.

    - 'done' (ouro pleno) quando a etapa já foi preenchida.
    - 'active' (ouro com halo) na primeira etapa ainda não concluída.
    - cinza nas etapas futuras.
    """
    etapas = [
        (1, "Produto", produto_done),
        (2, "Lote", lote_done),
        (3, "Resultado", resultado_done),
    ]
    classes: list[str] = []
    primeira_pendente_marcada = False
    for _, _, done in etapas:
        if done:
            classes.append("done")
        elif not primeira_pendente_marcada:
            classes.append("active")
            primeira_pendente_marcada = True
        else:
            classes.append("")

    html = ['<div class="stepper">']
    for i, ((num, label, _), cls) in enumerate(zip(etapas, classes)):
        html.append(
            f'<div class="step {cls}">'
            f'<div class="step-circle">{num}</div>'
            f'<div class="step-label">{label}</div>'
            f'</div>'
        )
        if i < len(etapas) - 1:
            html.append('<div class="step-bar"></div>')
    html.append('</div>')
    st.markdown("".join(html), unsafe_allow_html=True)


def render_iv_gauge(iv: float | None):
    """Altair horizontal gradient gauge (verde→amarelo→vermelho) com agulha no IV.

    Constrói segmentos contíguos não sobrepostos (x → x2) cobrindo o domínio
    [0.30, 1.00]. Cores interpoladas linearmente entre 3 stops:
        0.30 verde (#2D6A4F) → 0.625 amarelo (#C49B0B) → 1.00 vermelho (#9E2A2B).
    """
    if iv is None:
        st.caption("Sem benchmark de varejo Laszlo — IV indisponível.")
        return

    lo, hi = 0.30, 1.00
    iv_clip = max(lo, min(hi, iv))

    def hex_to_rgb(h: str):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def rgb_to_hex(rgb):
        return "#{:02X}{:02X}{:02X}".format(*[max(0, min(255, int(c))) for c in rgb])

    g, y, r = hex_to_rgb("#2D6A4F"), hex_to_rgb("#C49B0B"), hex_to_rgb("#9E2A2B")
    mid = 0.625

    def color_at(x: float) -> str:
        if x <= mid:
            t = (x - lo) / (mid - lo)
            rgb = tuple(g[i] + (y[i] - g[i]) * t for i in range(3))
        else:
            t = (x - mid) / (hi - mid)
            rgb = tuple(y[i] + (r[i] - y[i]) * t for i in range(3))
        return rgb_to_hex(rgb)

    n_seg = 60
    step = (hi - lo) / n_seg
    rows = []
    for i in range(n_seg):
        x_start = lo + i * step
        x_end = x_start + step
        rows.append({
            "x": x_start,
            "x2": x_end,
            "cor": color_at((x_start + x_end) / 2.0),
        })
    df_bar = pd.DataFrame(rows)

    bar = (
        alt.Chart(df_bar)
        .mark_rect(height=22)
        .encode(
            x=alt.X("x:Q",
                    scale=alt.Scale(domain=[lo, hi]),
                    axis=alt.Axis(title=None,
                                  values=[0.30, 0.55, 0.70, 0.85, 1.00],
                                  format=".2f", labelFontSize=10,
                                  labelColor="#6B6B6B")),
            x2="x2:Q",
            color=alt.Color("cor:N", scale=None, legend=None),
        )
        .properties(height=70)
    )

    # Linha vertical sutil ainda ajuda a ancorar o losango ao ponto exato.
    needle_line = (
        alt.Chart(pd.DataFrame({"iv": [iv_clip]}))
        .mark_rule(color="#0E0E0E", strokeWidth=1.2, opacity=0.55)
        .encode(x=alt.X("iv:Q", scale=alt.Scale(domain=[lo, hi])))
    )
    # Marcador em losango (diamond) sobre a barra.
    diamond = (
        alt.Chart(pd.DataFrame({"iv": [iv_clip]}))
        .mark_point(shape="diamond", size=260, filled=True,
                    color="#0E0E0E", stroke="#FAFAF7", strokeWidth=2)
        .encode(x=alt.X("iv:Q", scale=alt.Scale(domain=[lo, hi])))
    )
    needle_top = (
        alt.Chart(pd.DataFrame({"iv": [iv_clip], "label": [f"{iv:.2f}"]}))
        .mark_text(dy=-22, fontSize=13, fontWeight="bold", color="#0E0E0E",
                   font="Cormorant Garamond")
        .encode(x=alt.X("iv:Q", scale=alt.Scale(domain=[lo, hi])), text="label:N")
    )

    chart = (bar + needle_line + diamond + needle_top).properties(height=80)
    st.altair_chart(chart, use_container_width=True)

    # Tick labels abaixo da barra: Viável · 0.55 · Atenção · 0.70 · Inviável
    st.markdown(
        '<div class="iv-tick-row">'
        '<span>Viável</span>'
        '<span class="iv-tick-num">0.55</span>'
        '<span>Atenção</span>'
        '<span class="iv-tick-num">0.70</span>'
        '<span>Inviável</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Frase explicativa em linguagem de cliente.
    pct = int(round(iv * 100))
    st.markdown(
        f'<div class="iv-explain">Seu produto custa <b>{pct}%</b> do '
        'preço de referência Laszlo.</div>',
        unsafe_allow_html=True,
    )


def render_health_gauge(score: float, titulo: str = "Saúde do Portfólio"):
    """Gauge circular (arco) 0-100 em gold, renderizado com Altair."""
    score = max(0.0, min(100.0, float(score)))
    valor = score / 100.0
    df_full = pd.DataFrame({"v": [1.0]})
    df_score = pd.DataFrame({"v": [valor]})
    base = alt.Chart(df_full).mark_arc(
        innerRadius=70, outerRadius=95, color="#EFEAE0",
    ).encode(
        theta=alt.Theta("v:Q", scale=alt.Scale(domain=[0, 1])),
    )
    arc = alt.Chart(df_score).mark_arc(
        innerRadius=70, outerRadius=95, color="#A88B5C",
        cornerRadius=8,
    ).encode(
        theta=alt.Theta("v:Q", scale=alt.Scale(domain=[0, 1])),
    )
    txt_value = alt.Chart(pd.DataFrame({"t": [f"{int(score)}"]})).mark_text(
        font="Cormorant Garamond", fontSize=46, color="#0E0E0E", fontWeight=500,
        dy=-4,
    ).encode(text="t:N")
    txt_unit = alt.Chart(pd.DataFrame({"t": ["/ 100"]})).mark_text(
        font="Inter", fontSize=10, color="#6B6B6B", dy=24,
    ).encode(text="t:N")
    chart = (base + arc + txt_value + txt_unit).properties(height=240)
    st.markdown(f"<div style='text-align:center;'><div class='metric-label'>{titulo}</div></div>",
                unsafe_allow_html=True)
    st.altair_chart(chart, use_container_width=True)


def render_footer():
    st.markdown(
        '<div class="domme-footer">DOMME × LASZLO · Motor v3 · © 2025</div>',
        unsafe_allow_html=True,
    )


_PLACEHOLDER_SKU = "— selecione um SKU —"


def selector_sku_busca(label: str, key: str):
    """Searchable SKU selector: text filter + selectbox with a placeholder
    first option so the result starts unselected (returns None)."""
    skus = listar_skus_disponiveis()
    busca = st.text_input(
        "🔍 Buscar SKU",
        key=f"{key}_busca",
        placeholder="digite parte do nome para filtrar...",
    )
    if busca:
        opcoes = [s for s in skus if busca.lower() in str(s).lower()]
    else:
        opcoes = skus

    if not opcoes:
        st.warning("Nenhum SKU encontrado com esse filtro.")
        return None

    st.caption(f"{len(opcoes)} SKU(s) correspondente(s)")
    options_with_placeholder = [_PLACEHOLDER_SKU] + opcoes
    selected = st.selectbox(label, options=options_with_placeholder, index=0, key=key)
    if selected == _PLACEHOLDER_SKU:
        return None
    return selected


# ------------------------------ TELA LOGIN -------------------------------- #
def tela_login():
    st.markdown('<div class="domme-logo">D O M M E</div>', unsafe_allow_html=True)
    st.markdown('<div class="domme-tagline">Inteligência em White Label</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Acesso ao Hub")
        u = st.text_input("Usuário", placeholder="seu usuário")
        s = st.text_input("Senha", type="password", placeholder="••••••••")
        if st.button("Entrar", use_container_width=True):
            user = autenticar(u, s)
            if user:
                st.session_state["usuario"] = user
                st.rerun()
            else:
                st.error("Credenciais inválidas")

        with st.expander("Credenciais de demonstração (apagar em produção)"):
            st.code("""
camilla / domme2025      → ADMIN (vê tudo)
laszlo  / laszlo2025     → FÁBRICA (só Catálogo + MP + Retirada)
cliente_demo / demo2025  → CLIENTE (só Motor + Proposta)
            """)


# ---------------------------- TELA: MOTOR v3 ------------------------------ #
def _motor_emit_alerts(alertas: list[str]):
    """Emite alertas como toast com dedup por fingerprint. Reseta quando
    a lista esvazia, permitindo o mesmo alerta re-disparar se reaparecer."""
    fingerprint = tuple(alertas)
    if not fingerprint:
        st.session_state["_motor_last_toast"] = None
        return
    if fingerprint == st.session_state.get("_motor_last_toast"):
        return
    st.session_state["_motor_last_toast"] = fingerprint
    for a in alertas:
        icon = "⛔" if "INVIÁVEL" in a or "⛔" in a else "⚠"
        st.toast(a, icon=icon)


def _trend(curr: float, prev) -> str:
    """Direção da variação para setas/deltas. 'flat' se variação < 0.5%."""
    if prev is None or prev == 0:
        return "flat"
    delta = curr - prev
    if abs(delta) / max(abs(prev), 1e-9) < 0.005:
        return "flat"
    return "up" if delta > 0 else "down"


def _delta_label(curr: float, prev) -> str:
    """Texto curto de delta vs. simulação anterior (pode ser R$ ou pp)."""
    if prev is None:
        return ""
    diff = curr - prev
    sign = "+" if diff >= 0 else "−"
    return f"{sign}{fmt_brl(abs(diff)).replace('R$ ', 'R$ ')}"


def _delta_pct_label(curr: float, prev) -> str:
    if prev is None:
        return ""
    diff = curr - prev
    sign = "+" if diff >= 0 else "−"
    return f"{sign}{abs(diff) * 100:.1f}pp"


def tela_motor(usuario: Usuario):
    render_breadcrumb("Motor de Precificação")
    st.markdown("# Motor de Precificação")
    st.caption("Workspace ao vivo · escolha o produto, ajuste o lote, veja o impacto na hora")

    ss = st.session_state
    ss.setdefault("motor_sku", None)
    ss.setdefault("motor_volume", 200)
    ss.setdefault("motor_mercado", "Brasil")
    ss.setdefault("motor_preco", 0.0)
    ss.setdefault("motor_compare", False)
    ss.setdefault("motor_history", [])
    ss.setdefault("_motor_last_toast", None)
    ss.setdefault("_motor_last_risky_sku", None)

    # Indicador passivo: cada etapa fica dourada conforme recebe dados.
    sku_atual = ss.get("motor_sku")
    produto_done = bool(sku_atual)
    lote_done = produto_done and int(ss["motor_volume"]) > 0
    resultado_done = produto_done and lote_done  # compute happens live abaixo
    render_step_indicator(produto_done, lote_done, resultado_done)

    # ============================================================
    # PAINEL TRIPLO — esquerdo (inputs) · centro (métricas) · direito (IV + alertas + PDF)
    # ============================================================
    col_left, col_mid, col_right = st.columns([3, 4, 3], gap="large")

    # ---------- PAINEL ESQUERDO: ENTRADAS ----------
    with col_left:
        st.markdown('<div class="panel-title">Entradas</div>', unsafe_allow_html=True)

        sku_input = selector_sku_busca("SKU", key="motor_sku_picker")
        if sku_input != sku_atual:
            ss["motor_sku"] = sku_input
            ss["_motor_last_toast"] = None
            sku_atual = sku_input

        if not sku_atual:
            render_empty_state(
                "Selecione um produto para começar",
                "A análise carrega instantaneamente a cada ajuste.",
                icone="✦",
            )

        dados_sku = buscar_sku(sku_atual) if sku_atual else None
        em_retirada = bool(dados_sku) and sku_em_retirada(dados_sku["codigo"])

        if dados_sku:
            status_wl = str(dados_sku.get("status_wl", "—"))
            if em_retirada:
                status_html = '<span class="pc-status-badge pc-status-block">⛔ Em retirada</span>'
            elif "disponível" in status_wl.lower():
                status_html = f'<span class="pc-status-badge pc-status-ok">✓ {status_wl}</span>'
            elif "risco" in status_wl.lower():
                status_html = f'<span class="pc-status-badge pc-status-warn">⚠ {status_wl}</span>'
            else:
                status_html = f'<span class="pc-status-badge pc-status-warn">⚠ {status_wl}</span>'

            # Toast: alerta quando o SKU selecionado for de risco (uma vez por SKU).
            if "risco" in status_wl.lower() and ss.get("_motor_last_risky_sku") != sku_atual:
                st.toast(
                    f"⚠ Atenção: o SKU '{dados_sku['nome'][:40]}' está em risco de estoque.",
                    icon="⚠",
                )
                ss["_motor_last_risky_sku"] = sku_atual
            elif "risco" not in status_wl.lower():
                ss["_motor_last_risky_sku"] = None

            st.markdown(f"""
                <div class="product-card">
                    <div class="pc-name">{dados_sku['nome']}</div>
                    <div class="pc-row">
                        <div class="pc-cell">
                            <div class="pc-label">CVU MP</div>
                            <div class="pc-value">{fmt_brl(dados_sku['cvu_mp'])}</div>
                        </div>
                        <div class="pc-cell">
                            <div class="pc-label">Ticket Laszlo</div>
                            <div class="pc-value">{fmt_brl(dados_sku['ticket_medio'])}</div>
                        </div>
                        <div class="pc-cell">
                            <div class="pc-label">Volume</div>
                            <div class="pc-value">{dados_sku.get('volume_ml', '—')} ml</div>
                        </div>
                        <div class="pc-cell">
                            <div class="pc-label">Status WL</div>
                            <div class="pc-value">{status_html}</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if em_retirada:
                st.error("⛔ SKU em retirada de linha — cálculo bloqueado.")

            # Volume: slider para os tiers comuns + number_input para faixa
            # completa de negócio (1–50 000). on_change callbacks mantêm
            # ss["motor_volume"] como fonte única de verdade.
            vol_atual = min(max(int(ss["motor_volume"]), 1), 50000)

            def _sync_vol_from_slider():
                ss["motor_volume"] = int(ss["motor_volume_slider"])

            def _sync_vol_from_input():
                ss["motor_volume"] = int(ss["motor_volume_input"])

            # Pré-semeia os valores dos widgets a partir da fonte de verdade.
            ss["motor_volume_slider"] = min(max(vol_atual, 50), 5000)
            ss["motor_volume_input"] = vol_atual

            st.slider(
                "Volume do lote (un)",
                min_value=50, max_value=5000,
                step=50,
                key="motor_volume_slider",
                on_change=_sync_vol_from_slider,
                help="Arraste para ajustar dentro dos tiers comerciais "
                     "(50–5 000). Use o campo abaixo para volumes fora "
                     "dessa faixa.",
            )
            st.caption(
                "▎ Tier 1 ≤500 (+20%) · Tier 2 501–2000 (+10%) · Tier 3 >2000 (0%)"
            )
            st.number_input(
                "Volume exato (1–50 000)",
                min_value=1, max_value=50000,
                step=50,
                key="motor_volume_input",
                on_change=_sync_vol_from_input,
                help="Para volumes fora da faixa do slider (ex.: 10, 25 000).",
            )

            ss["motor_mercado"] = st.radio(
                "Mercado",
                options=["Brasil", "Internacional"],
                index=0 if ss["motor_mercado"] == "Brasil" else 1,
                horizontal=True,
                key="motor_mercado_radio",
            )

            ss["motor_preco"] = st.number_input(
                "Preço de venda alvo (R$) — opcional",
                min_value=0.0,
                value=float(ss["motor_preco"]),
                step=10.0,
                key="motor_preco_input",
                help=f"Deixe 0 para usar o ticket médio Laszlo "
                     f"({fmt_brl(dados_sku['ticket_medio'])}).",
            )

            ss["motor_compare"] = st.toggle(
                "Comparar com simulação anterior",
                value=ss["motor_compare"],
                key="motor_compare_toggle",
                help="Mostra ↑ / ↓ e a diferença vs. a simulação anterior do histórico.",
            )

    # Sem SKU válido (ou em retirada) → painéis centro/direita ficam vazios.
    if not (dados_sku and not em_retirada):
        with col_mid:
            st.markdown('<div class="panel-title">Resultado</div>', unsafe_allow_html=True)
            render_empty_state(
                "Aguardando produto",
                "Os indicadores aparecem assim que um SKU válido for selecionado.",
                icone="◆",
            )
        with col_right:
            st.markdown('<div class="panel-title">Viabilidade</div>', unsafe_allow_html=True)
            render_empty_state(
                "Termômetro inativo",
                "Selecione um produto à esquerda.",
                icone="✦",
            )
        return

    # ---------- CÁLCULO LIVE ----------
    volume = int(ss["motor_volume"])
    mercado = ss["motor_mercado"]
    preco_venda = float(ss["motor_preco"])

    resultado = calcular_pricing(
        sku=dados_sku["nome"],
        volume=volume,
        cvu_mp=dados_sku["cvu_mp"],
        ticket_medio_laszlo=dados_sku["ticket_medio"],
        mercado=mercado,
        preco_venda_input=preco_venda if preco_venda > 0 else None,
        em_retirada=False,
    )

    # ---------- HISTÓRICO ----------
    nova_entrada = {
        "Hora": datetime.now().strftime("%H:%M:%S"),
        "SKU": str(sku_atual)[:40],
        "Volume": int(volume),
        "Mercado": mercado,
        "Preço Venda (R$)": float(preco_venda) if preco_venda > 0
                            else float(dados_sku["ticket_medio"]),
        "PFC Unit (R$)": float(resultado.pfc_final_unit),
        "Investimento (R$)": float(resultado.investimento_total),
        "Lucro Lote (R$)": float(resultado.lucro_liquido_lote)
                            if resultado.lucro_liquido_lote else 0.0,
        "ROI": float(resultado.roi_pct) if resultado.roi_pct else 0.0,
        "IV": float(resultado.iv) if resultado.iv else 0.0,
        "Tier": resultado.tier_nome,
    }
    hist = ss["motor_history"]
    if not hist or {k: v for k, v in nova_entrada.items() if k != "Hora"} != \
       {k: v for k, v in hist[-1].items() if k != "Hora"}:
        hist.append(nova_entrada)

    prev_entry = hist[-2] if len(hist) >= 2 else None
    compare_on = bool(ss["motor_compare"])

    def _arrow_and_delta(curr_val, prev_key, label_fn=_delta_label):
        if not prev_entry:
            return "", "", ""
        prev_val = prev_entry[prev_key]
        direction = _trend(curr_val, prev_val)
        if not compare_on:
            return direction, "", ""
        return direction, label_fn(curr_val, prev_val), direction

    arr_pfc, dlt_pfc, dir_pfc = _arrow_and_delta(
        resultado.pfc_final_unit, "PFC Unit (R$)")
    arr_inv, dlt_inv, dir_inv = _arrow_and_delta(
        resultado.investimento_total, "Investimento (R$)")
    arr_luc, dlt_luc, dir_luc = _arrow_and_delta(
        resultado.lucro_liquido_lote or 0.0, "Lucro Lote (R$)")
    arr_roi, dlt_roi, dir_roi = _arrow_and_delta(
        resultado.roi_pct or 0.0, "ROI",
        label_fn=lambda c, p: f"{(c - p) * 100:+.1f} pp")
    arr_iv, dlt_iv, dir_iv = _arrow_and_delta(
        resultado.iv or 0.0, "IV",
        label_fn=lambda c, p: f"{(c - p):+.3f}")

    iv_cor = resultado.iv_cor or "neutro"
    iv_icon_map = {"verde": "✓", "amarelo": "⚠", "vermelho": "✗", "neutro": "·"}

    # ---------- PAINEL CENTRO: MÉTRICAS LIVE ----------
    with col_mid:
        st.markdown('<div class="panel-title">Resultado · ao vivo</div>',
                    unsafe_allow_html=True)
        m_a, m_b = st.columns(2)
        with m_a:
            metric_card_iv(
                "Preço Unitário (PFC)",
                fmt_brl(resultado.pfc_final_unit),
                resultado.tier_nome,
                iv_cor=iv_cor, arrow=arr_pfc,
                tooltip="PFC = Preço Final ao Cliente. Inclui produto Laszlo, "
                        "envase full-service, selo e fee diluído.",
                delta_label=dlt_pfc, delta_dir=dir_pfc,
                value_num=float(resultado.pfc_final_unit or 0.0),
                value_format="brl",
            )
            be = f"{resultado.break_even_un} un" if resultado.break_even_un else "Inviável"
            metric_card_iv(
                "Ponto de Equilíbrio",
                be,
                "Para cobrir o investimento",
                iv_cor=iv_cor,
                tooltip="Quantas unidades o cliente precisa vender para "
                        "recuperar o investimento total no lote.",
                value_num=(float(resultado.break_even_un)
                           if resultado.break_even_un else None),
                value_format="text" if not resultado.break_even_un else "int",
            )
        with m_b:
            metric_card_iv(
                "Investimento Total",
                fmt_brl(resultado.investimento_total),
                f"{resultado.volume:,} unidades".replace(",", "."),
                iv_cor=iv_cor, arrow=arr_inv,
                tooltip="Valor global do projeto: PFC × volume. "
                        "Tudo incluso, sem decomposição visível ao cliente.",
                delta_label=dlt_inv, delta_dir=dir_inv,
                value_num=float(resultado.investimento_total or 0.0),
                value_format="brl",
            )
            metric_card_iv(
                "Lucro Líquido no Lote",
                fmt_brl(resultado.lucro_liquido_lote),
                f"ROI {fmt_pct(resultado.roi_pct)}",
                iv_cor=iv_cor, arrow=arr_luc,
                tooltip="Receita bruta do lote − impostos/frete (15%) − investimento. "
                        "ROI conservador.",
                delta_label=dlt_luc, delta_dir=dir_luc,
                value_num=float(resultado.lucro_liquido_lote or 0.0),
                value_format="brl",
            )

        m_c, m_d = st.columns(2)
        with m_c:
            metric_card_iv(
                "ROI",
                fmt_pct(resultado.roi_pct),
                "Lucro líquido / Investimento",
                iv_cor=iv_cor, arrow=arr_roi,
                tooltip="Retorno sobre Investimento conservador, calculado "
                        "após impostos/frete. Quanto maior, melhor o "
                        "atrativo financeiro do lote.",
                delta_label=dlt_roi, delta_dir=dir_roi,
                value_num=float((resultado.roi_pct or 0.0) * 100),
                value_format="pct",
            )
        with m_d:
            iv_val_str = f"{resultado.iv:.3f}" if resultado.iv else "—"
            # Para IV, MENOR é melhor (relação CVU vs ticket). Por isso
            # invertemos a direção da seta/delta: queda do IV = positivo.
            _iv_flip = {"up": "down", "down": "up"}
            arr_iv_inv = _iv_flip.get(arr_iv, arr_iv)
            dir_iv_inv = _iv_flip.get(dir_iv, dir_iv)
            metric_card_iv(
                "IV — Viabilidade",
                iv_val_str,
                resultado.iv_status,
                iv_cor=iv_cor, arrow=arr_iv_inv,
                tooltip="Índice de Viabilidade DOMME — quanto MENOR, melhor. "
                        "Verde < 0,55 · Amarelo 0,55–0,70 · Vermelho > 0,70. "
                        "Combina CVU, tier e ticket médio.",
                delta_label=dlt_iv, delta_dir=dir_iv_inv,
                value_num=float(resultado.iv or 0.0) if resultado.iv else None,
                value_format="iv" if resultado.iv else "text",
            )

    # ---------- PAINEL DIREITO: TERMÔMETRO IV + ALERTAS + PDF ----------
    with col_right:
        st.markdown('<div class="panel-title">Viabilidade</div>',
                    unsafe_allow_html=True)
        render_iv_gauge(resultado.iv)

        # Resumo IV com ícone (não depende só de cor).
        iv_str = f"{resultado.iv:.3f}" if resultado.iv else "—"
        icon = iv_icon_map.get(iv_cor, "·")
        st.markdown(
            f'<div class="iv-status-line">'
            f'<span class="iv-status-icon iv-{iv_cor}">{icon}</span>'
            f'<div><b>{resultado.iv_status}</b> · IV {iv_str}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Alertas dentro do painel direito (visualmente integrados).
        if resultado.alertas:
            st.markdown('<div class="panel-title" style="margin-top:1.2rem;">'
                        'Alertas</div>', unsafe_allow_html=True)
            for a in resultado.alertas:
                critical = "INVIÁVEL" in a or "⛔" in a
                cls = "alert-critical" if critical else ""
                st.markdown(
                    f'<div class="alert-card {cls}">{a}</div>',
                    unsafe_allow_html=True,
                )

        # Toasts (dedup): IV vermelho + alertas.
        _motor_emit_alerts(resultado.alertas or [])
        if iv_cor == "vermelho" and ss.get("_motor_last_iv_red") != iv_str:
            st.toast("✗ Índice de Viabilidade no vermelho — produto inviável a este preço.",
                     icon="✗")
            ss["_motor_last_iv_red"] = iv_str
        elif iv_cor != "vermelho":
            ss["_motor_last_iv_red"] = None

        # Botão PDF (com spinner + toast de sucesso).
        if pode(usuario, "proposta"):
            st.markdown('<div class="panel-title" style="margin-top:1.2rem;">'
                        'Proposta</div>', unsafe_allow_html=True)
            cliente_nome = st.text_input(
                "Nome do cliente",
                value=usuario.empresa if usuario.perfil == "CLIENTE" else "Cliente Premium",
                key="motor_cliente_nome",
            )
            if st.button("📄 Gerar Proposta em PDF",
                         use_container_width=True, key="motor_gerar_pdf"):
                ss.setdefault("_proposta_seq", 0)
                ss["_proposta_seq"] += 1
                proposta_num = (
                    f"DOMME-{datetime.now().year}-{ss['_proposta_seq']:03d}"
                )
                with st.spinner("Montando proposta…"):
                    pdf_bytes = gerar_proposta_pdf(
                        resultado, cliente_nome,
                        usuario_nome=usuario.nome,
                        proposta_num=proposta_num,
                    )
                ss["_motor_pdf_bytes"] = pdf_bytes
                ss["_motor_pdf_num"] = proposta_num
                ss["_motor_pdf_filename"] = (
                    f"{proposta_num}_{cliente_nome.replace(' ', '_')}.pdf"
                )
                # Marca timestamp da geração para exibir o badge animado
                # (~2s) somente no rerun imediato após clicar.
                ss["_motor_pdf_just_generated_at"] = time.time()
                st.toast("✓ Proposta gerada com sucesso!", icon="✅")
            if ss.get("_motor_pdf_bytes"):
                # Badge animado verde com check (~2s) renderizado apenas se
                # o PDF acabou de ser gerado nesta sessão (≤ 4s).
                _just_at = ss.get("_motor_pdf_just_generated_at") or 0
                _is_fresh = (time.time() - _just_at) < 4.0
                if _is_fresh:
                    st.markdown(
                        f"<div class='pdf-success-badge'>"
                        f"<span class='check-circle'>✓</span>"
                        f"<span>PDF gerado · "
                        f"<b>{ss.get('_motor_pdf_num', '')}</b></span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div style='text-align:center; color:#2E7D32; "
                        f"font-size:0.85rem; margin:0.3rem 0 0.4rem 0; "
                        f"letter-spacing:0.5px;'>✓ Proposta "
                        f"<b>{ss.get('_motor_pdf_num', '')}</b> pronta</div>",
                        unsafe_allow_html=True,
                    )
                st.download_button(
                    "⬇ Baixar Proposta (PDF)",
                    data=ss["_motor_pdf_bytes"],
                    file_name=ss.get("_motor_pdf_filename", "Proposta_DOMME.pdf"),
                    mime="application/pdf",
                    use_container_width=True,
                )

    # ============================================================
    # SEÇÕES INFERIORES (full-width)
    # ============================================================

    # ---------- VISÃO INTERNA — APENAS ADMIN ----------
    if pode(usuario, "visao_caixa"):
        render_divider()
        st.markdown("### Visão Interna · Gestão de Caixa DOMME")
        st.caption("⚡ Confidencial · Não exibido a Cliente nem Fábrica")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("Repasse à Fábrica", fmt_brl(resultado.repasse_fabrica),
                        "PI Laszlo + Selo")
        with c2:
            metric_card("Renda Bruta DOMME", fmt_brl(resultado.renda_bruta_domme),
                        f"{fmt_pct(resultado.renda_pct_sobre_lote)} do lote")
        with c3:
            metric_card("Fee de Ativação", fmt_brl(resultado.fee_ativacao_total),
                        f"Diluído: {fmt_brl(resultado.fee_unitario)}/un")
        with c4:
            status_pl = "✓ OK" if resultado.pro_labore_ok else "⚠ ABAIXO"
            metric_card("Pro Labore Mínimo", status_pl,
                        f"Mín. R$ 2.000 · Atual {fmt_brl(resultado.renda_bruta_domme)}")

        with st.expander("Decomposição completa de custos (não compartilhar)"):
            decomp = pd.DataFrame({
                "Componente": [
                    "CVU Matéria-Prima",
                    "Custo Envase (kit + fator escala)",
                    "CVU Total Unitário",
                    "MIL — Margem Industrial Laszlo (40%)",
                    "PI Laszlo (preço atacado)",
                    "MD — Margem Comercial DOMME (20%)",
                    "Markup de Volume (tier)",
                    "Selo Laszlo (3%)",
                    "Fee Ativação Diluído",
                    "PFC Unitário FINAL",
                ],
                "Valor Unitário (R$)": [
                    resultado.cvu_mp,
                    resultado.custo_envase_unit,
                    resultado.cvu_total_unit,
                    resultado.cvu_total_unit * 0.40,
                    resultado.pi_laszlo_unit,
                    resultado.pi_laszlo_unit * 0.20,
                    f"+{resultado.markup_volume:.0%}",
                    resultado.pi_laszlo_unit * 1.20 * (1 + resultado.markup_volume) * 0.03,
                    resultado.fee_unitario,
                    resultado.pfc_final_unit,
                ],
            })
            st.dataframe(decomp, hide_index=True, use_container_width=True)

    # ---------- HISTÓRICO ----------
    render_divider()
    st.markdown("### Histórico de Simulações nesta Sessão")
    if hist:
        df_hist = pd.DataFrame(reversed(hist))
        df_view = df_hist.copy()
        df_view["Preço Venda (R$)"] = df_view["Preço Venda (R$)"].map(fmt_brl)
        df_view["PFC Unit (R$)"] = df_view["PFC Unit (R$)"].map(fmt_brl)
        df_view["Investimento (R$)"] = df_view["Investimento (R$)"].map(fmt_brl)
        df_view["Lucro Lote (R$)"] = df_view["Lucro Lote (R$)"].map(fmt_brl)
        df_view["ROI"] = df_view["ROI"].map(fmt_pct)
        df_view["IV"] = df_view["IV"].map(lambda v: f"{v:.3f}" if v else "—")
        st.dataframe(df_view, hide_index=True, use_container_width=True)

        col_a, col_b = st.columns([1, 5])
        with col_a:
            if st.button("🗑 Limpar histórico"):
                ss["motor_history"] = []
                st.rerun()
        with col_b:
            csv = pd.DataFrame(hist).to_csv(index=False).encode("utf-8")
            st.download_button("⬇ Exportar CSV", data=csv,
                               file_name="motor_historico.csv", mime="text/csv")
    else:
        st.caption("Nenhuma simulação registrada ainda nesta sessão.")


# --------------------------- TELA: CENÁRIOS ------------------------------- #
def tela_cenarios(usuario: Usuario):
    render_breadcrumb("Análise de Cenários")
    st.markdown("# Análise de Cenários")
    st.caption("Comparativo automático: 'E se eu produzir mais?'")

    sku = selector_sku_busca("SKU", key="cenarios_sku")
    if not sku:
        render_empty_state(
            "Selecione um produto para comparar cenários",
            "Veja como o lote impacta tier, IV e lucro líquido.",
            icone="✦",
        )
        return
    dados = buscar_sku(sku)
    if not dados:
        return

    cenarios = comparar_cenarios(
        sku, dados["cvu_mp"], dados["ticket_medio"],
        volumes=[50, 200, 500, 1000, 3000],
    )

    st.markdown("### Comparativo PFC × Margem por Volume")
    st.caption("Barras agrupadas: PFC unitário (preto) e margem unitária (ouro) lado a lado.")

    # Construir DataFrame longo (PFC × Margem) por volume.
    rows = []
    for c in cenarios:
        vol_label = f"{c['volume']:,} un".replace(",", ".")
        pfc = float(c["pfc_final_unit"] or 0)
        # Margem unitária = lucro líquido lote / volume (proxy claro p/ usuário).
        lucro_lote = float(c["lucro_liquido_lote"] or 0)
        vol = max(int(c["volume"]), 1)
        margem_un = lucro_lote / vol
        rows.append({
            "Volume": vol_label, "VolumeOrdem": c["volume"],
            "Métrica": "PFC unitário (R$)", "Valor": pfc,
        })
        rows.append({
            "Volume": vol_label, "VolumeOrdem": c["volume"],
            "Métrica": "Margem unitária (R$)", "Valor": margem_un,
        })
    df_long = pd.DataFrame(rows)

    chart = (
        alt.Chart(df_long)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Volume:N", sort=alt.SortField("VolumeOrdem"),
                    title=None, axis=alt.Axis(labelAngle=0)),
            xOffset=alt.XOffset("Métrica:N"),
            y=alt.Y("Valor:Q", title="R$ por unidade"),
            color=alt.Color(
                "Métrica:N",
                scale=alt.Scale(
                    domain=["PFC unitário (R$)", "Margem unitária (R$)"],
                    range=["#0E0E0E", "#A88B5C"],
                ),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[
                "Volume", "Métrica",
                alt.Tooltip("Valor:Q", format=",.2f", title="R$/un"),
            ],
        )
        .properties(height=340)
    )
    st.altair_chart(chart, use_container_width=True)

    # Auto-insight: compara o menor e o maior volume.
    if len(cenarios) >= 2:
        c_lo = cenarios[0]
        c_hi = cenarios[-1]
        vol_lo = int(c_lo["volume"])
        vol_hi = int(c_hi["volume"])
        pfc_lo = float(c_lo["pfc_final_unit"] or 0)
        pfc_hi = float(c_hi["pfc_final_unit"] or 0)
        lucro_lo = float(c_lo["lucro_liquido_lote"] or 0)
        lucro_hi = float(c_hi["lucro_liquido_lote"] or 0)
        d_pfc = pfc_lo - pfc_hi
        d_lucro = lucro_hi - lucro_lo
        sentido_pfc = "cai" if d_pfc > 0 else "sobe"
        sentido_lucro = "sobe" if d_lucro >= 0 else "cai"
        # Apenas as quantidades inteiras vão a milhar pt-BR; preserva o
        # formato de moeda do fmt_brl (que já usa vírgula decimal).
        vol_lo_fmt = f"{vol_lo:,}".replace(",", ".")
        vol_hi_fmt = f"{vol_hi:,}".replace(",", ".")
        st.info(
            f"💡 **Insight automático:** ao subir de **{vol_lo_fmt} un** para "
            f"**{vol_hi_fmt} un**, o PFC unitário {sentido_pfc} "
            f"**{fmt_brl(abs(d_pfc))}** e o lucro do lote {sentido_lucro} "
            f"**{fmt_brl(abs(d_lucro))}**. O Fee de Ativação se dilui e o "
            f"markup de volume reduz, mas a Renda DOMME cresce em valor "
            f"absoluto pelo Fee escalonado (T3 = 5%)."
        )


# --------------------------- TELA: MIX & KITS ----------------------------- #
# Limites do construtor de kit
_MIX_MIN_SKUS = 2
_MIX_MAX_SKUS = 10
_MIX_DEFAULT_QTY = 200
_MIX_TOTAL_ALERTA = 50  # alerta se total < 50un (lote raso)


def _mix_init_state():
    """Inicializa o estado do construtor de kit. Cada slot guarda
    o nome do SKU e a quantidade. Slots vazios = SKU None."""
    ss = st.session_state
    if "mix_slots" not in ss:
        ss["mix_slots"] = [
            {"sku": None, "qty": _MIX_DEFAULT_QTY},
            {"sku": None, "qty": _MIX_DEFAULT_QTY},
        ]
    ss.setdefault("mix_kit_nome", "Kit Composto DOMME")
    ss.setdefault("mix_cliente", "Cliente Premium")
    ss.setdefault("mix_pdf_bytes", None)
    ss.setdefault("mix_pdf_proposta_num", None)
    # Versão monotônica usada como sufixo nas `key=` dos widgets dos slots.
    # Toda mutação que reembaralha o significado dos índices (remover,
    # limpar, adicionar) incrementa esta versão — assim o Streamlit
    # vê widgets totalmente novos e não há "vazamento" de estado de
    # uma renderização para outra. A lista `mix_slots` permanece como
    # fonte única da verdade.
    ss.setdefault("mix_widget_ver", 0)


def _mix_bump_widget_version():
    st.session_state["mix_widget_ver"] = st.session_state.get("mix_widget_ver", 0) + 1


def _mix_slot_picker(slot_idx: int, opcoes: list[str], usado: set[str]):
    """Seletor de SKU para um slot do kit. Filtra SKUs já escolhidos
    em outros slots para evitar duplicidade. Retorna (sku, qty)."""
    slot = st.session_state["mix_slots"][slot_idx]
    sku_atual = slot.get("sku")

    # Permite manter o SKU atual mesmo que esteja no `usado` (não auto-removê-lo).
    candidatos = [_PLACEHOLDER_SKU] + [
        s for s in opcoes if (s == sku_atual) or (s not in usado)
    ]
    try:
        idx = candidatos.index(sku_atual) if sku_atual in candidatos else 0
    except ValueError:
        idx = 0

    # Sufixo de versão garante que widgets sejam recriados após qualquer
    # mutação estrutural (remover/adicionar/limpar) — evita o vazamento
    # de valor entre slots quando os índices deslizam.
    ver = st.session_state.get("mix_widget_ver", 0)
    col_sku, col_qty, col_rm = st.columns([6, 2, 1], gap="small")
    with col_sku:
        novo_sku = st.selectbox(
            f"Produto {slot_idx + 1}",
            options=candidatos,
            index=idx,
            key=f"mix_slot_sku_v{ver}_{slot_idx}",
            label_visibility="collapsed",
        )
        if novo_sku == _PLACEHOLDER_SKU:
            novo_sku = None
    with col_qty:
        nova_qty = st.number_input(
            "qty",
            min_value=0, max_value=50000, step=50,
            value=int(slot.get("qty", _MIX_DEFAULT_QTY)),
            key=f"mix_slot_qty_v{ver}_{slot_idx}",
            label_visibility="collapsed",
        )
    with col_rm:
        # Permite remover o slot a qualquer momento; o construtor reaplica
        # o mínimo de 2 ao listar slots após a interação.
        if st.button("✕", key=f"mix_slot_rm_v{ver}_{slot_idx}",
                     help="Remover este produto do kit",
                     use_container_width=True):
            st.session_state["mix_slots"].pop(slot_idx)
            _mix_bump_widget_version()
            st.session_state["mix_pdf_bytes"] = None
            st.rerun()

    # Persiste mudanças no slot
    if novo_sku != slot["sku"] or int(nova_qty) != int(slot["qty"]):
        st.session_state["mix_slots"][slot_idx] = {"sku": novo_sku, "qty": int(nova_qty)}
        st.session_state["mix_pdf_bytes"] = None  # invalida cache de PDF


def _mix_load_check_retirada_codes() -> list[int]:
    """Lê os códigos Laszlo em retirada via data_loader. Tolerante a
    ausência da coluna ou de erros de leitura — retorna lista vazia."""
    try:
        df = carregar_check_retirada()
        if df is None or df.empty:
            return []
        # tenta colunas usuais
        for col in ("codigo", "codigo_laszlo", "Código", "cod"):
            if col in df.columns:
                return [int(c) for c in df[col].dropna().astype(int).tolist()]
        return []
    except Exception:
        return []


def tela_mix(usuario: Usuario):
    render_breadcrumb("Mix & Kits — Simulador de Kit Composto")
    st.markdown("# Mix & Kits")
    st.caption(
        "Combine de 2 a 10 SKUs em um único lote · CVU e ticket blendados · "
        "Tier escalado pelo TOTAL · Fee único · Termômetro de Viabilidade do kit"
    )

    _mix_init_state()
    ss = st.session_state

    skus = listar_skus_disponiveis()
    em_retirada_codes = _mix_load_check_retirada_codes()

    # Permissão: ADMIN e CLIENTE podem gerar PDF; FABRICA é read-only.
    pode_gerar_pdf = pode(usuario, "proposta") or usuario.perfil == "ADMIN"

    if usuario.perfil == "FABRICA":
        st.info(
            "Você está em modo de consulta. A simulação fica disponível, "
            "mas a geração da proposta é restrita a ADMIN e clientes."
        )

    # ============================================================
    # PAINEL TRIPLO: composição · resultado blendado · viabilidade
    # ============================================================
    col_left, col_mid, col_right = st.columns([3, 4, 3], gap="large")

    # ---------------- PAINEL ESQUERDO: COMPOSIÇÃO --------------- #
    with col_left:
        st.markdown('<div class="panel-title">Composição do kit</div>',
                    unsafe_allow_html=True)

        kit_nome = st.text_input(
            "Nome do kit",
            value=ss["mix_kit_nome"],
            key="mix_kit_nome_input",
            placeholder="Ex.: Coleção Mediterrâneo",
        )
        if kit_nome != ss["mix_kit_nome"]:
            ss["mix_kit_nome"] = kit_nome
            ss["mix_pdf_bytes"] = None

        cliente = st.text_input(
            "Cliente / projeto",
            value=ss["mix_cliente"],
            key="mix_cliente_input",
        )
        if cliente != ss["mix_cliente"]:
            ss["mix_cliente"] = cliente
            ss["mix_pdf_bytes"] = None

        st.markdown(
            f"<div style='font-size:0.78rem; color:#6B6256; "
            f"letter-spacing:1px; text-transform:uppercase; margin-top:0.4rem;'>"
            f"Produtos · {len(ss['mix_slots'])}/{_MIX_MAX_SKUS}</div>",
            unsafe_allow_html=True,
        )

        # Garante mínimo visual de 2 slots (mesmo após remover).
        while len(ss["mix_slots"]) < _MIX_MIN_SKUS:
            ss["mix_slots"].append({"sku": None, "qty": _MIX_DEFAULT_QTY})

        usados = {s["sku"] for s in ss["mix_slots"] if s.get("sku")}
        for i in range(len(ss["mix_slots"])):
            _mix_slot_picker(i, skus, usados)

        col_add, col_clear = st.columns(2, gap="small")
        with col_add:
            disabled_add = len(ss["mix_slots"]) >= _MIX_MAX_SKUS
            if st.button(
                "+ Adicionar produto",
                key="mix_add_slot",
                use_container_width=True,
                disabled=disabled_add,
                help=(f"Limite de {_MIX_MAX_SKUS} produtos por kit"
                      if disabled_add else "Adicionar mais um SKU ao kit"),
            ):
                ss["mix_slots"].append({"sku": None, "qty": _MIX_DEFAULT_QTY})
                # Não estritamente necessário (o índice novo é fresco),
                # mas mantemos a versão monotônica para consistência.
                _mix_bump_widget_version()
                ss["mix_pdf_bytes"] = None
                st.rerun()
        with col_clear:
            if st.button("Limpar kit",
                         key="mix_clear",
                         use_container_width=True,
                         help="Reinicia o construtor com 2 slots vazios"):
                ss["mix_slots"] = [
                    {"sku": None, "qty": _MIX_DEFAULT_QTY},
                    {"sku": None, "qty": _MIX_DEFAULT_QTY},
                ]
                # Garante que NENHUM widget de slot herde valor anterior.
                _mix_bump_widget_version()
                ss["mix_pdf_bytes"] = None
                st.rerun()

    # Materializa os itens válidos para cálculo
    itens_validos: list[tuple[dict, int]] = []
    skus_em_retirada_no_kit: list[str] = []
    for slot in ss["mix_slots"]:
        sku_nome = slot.get("sku")
        qty = int(slot.get("qty", 0))
        if not sku_nome or qty <= 0:
            continue
        dados = buscar_sku(sku_nome)
        if not dados:
            continue
        itens_validos.append((dados, qty))
        if sku_em_retirada(int(dados.get("codigo") or 0)):
            skus_em_retirada_no_kit.append(str(dados.get("nome", "—")))

    # Se composição insuficiente: mostra empty state nos painéis direitos
    if len(itens_validos) < _MIX_MIN_SKUS:
        with col_mid:
            st.markdown('<div class="panel-title">Resultado consolidado</div>',
                        unsafe_allow_html=True)
            render_empty_state(
                "Selecione ao menos 2 produtos com quantidade > 0",
                "O simulador roda ao vivo conforme você monta o kit.",
                icone="✦",
            )
        with col_right:
            st.markdown('<div class="panel-title">Viabilidade do kit</div>',
                        unsafe_allow_html=True)
            render_empty_state(
                "Aguardando composição",
                "Termômetro IV blendado e economia vs lotes separados.",
                icone="◆",
            )
        return

    # Calcula o mix
    try:
        resultado: MixResult = calcular_mix(
            itens_validos,
            mercado="Brasil",
            skus_em_retirada=[
                int(d.get("codigo") or 0) for d, _ in itens_validos
                if sku_em_retirada(int(d.get("codigo") or 0))
            ],
        )
    except ValueError as e:
        st.error(f"Não foi possível calcular o kit: {e}")
        return

    total_un = resultado.total_unidades
    invalida_pdf = False

    # ----------- ALERTAS NO TOPO DOS PAINÉIS RESULTADO ----------- #
    with col_mid:
        st.markdown('<div class="panel-title">Resultado consolidado</div>',
                    unsafe_allow_html=True)

        if skus_em_retirada_no_kit:
            st.warning(
                "⚠ Algum SKU do kit está em **retirada de linha**: "
                + ", ".join(s[:35] for s in skus_em_retirada_no_kit)
                + ". Confirme estoque antes de fechar."
            )
        if total_un < _MIX_TOTAL_ALERTA:
            st.warning(
                f"⚠ Volume total muito baixo ({total_un}un) — abaixo do "
                f"mínimo recomendado de {_MIX_TOTAL_ALERTA}un para kit. "
                "A diluição do kit de envase fica desfavorável."
            )

        # Métricas blendadas em três cards
        cm1, cm2, cm3 = st.columns(3)
        with cm1:
            metric_card(
                "Total do kit",
                f"{total_un:,} un".replace(",", "."),
                f"{resultado.total_skus} produtos · {resultado.tier_nome}",
            )
        with cm2:
            metric_card(
                "Investimento total",
                fmt_brl(resultado.investimento_total),
                f"{fmt_brl(resultado.mix_pfc_unit)} / un (full-service)",
            )
        with cm3:
            economia_label = (
                fmt_brl(resultado.economia_total_lote)
                if resultado.economia_por_unidade > 0
                else "—"
            )
            economia_sub = (
                f"+{fmt_brl(resultado.economia_por_unidade)} / un vs lotes separados"
                if resultado.economia_por_unidade > 0
                else "Sem ganho de escala neste cenário"
            )
            metric_card("Economia do kit", economia_label, economia_sub)

        # Decomposição blendada
        st.markdown(
            '<div class="panel-title" style="margin-top:1.4rem;">'
            'Decomposição (blendado)</div>',
            unsafe_allow_html=True,
        )
        df_blend = pd.DataFrame([
            {"Métrica": "CVU MP blendado",                "Valor": fmt_brl(resultado.cvu_blendado)},
            {"Métrica": f"Kit envase (fator {resultado.fator_escala:.1f}x)",
                                                          "Valor": fmt_brl(resultado.custo_envase_unit)},
            {"Métrica": "CVU total / un",                 "Valor": fmt_brl(resultado.cvu_total_unit)},
            {"Métrica": f"Markup de volume ({resultado.tier_nome})",
                                                          "Valor": fmt_pct(resultado.markup_volume)},
            {"Métrica": "PI Laszlo / un",                 "Valor": fmt_brl(resultado.pi_laszlo_unit)},
            {"Métrica": "Fee de Ativação (lote único)",   "Valor": fmt_brl(resultado.fee_ativacao_total)},
            {"Métrica": "Fee diluído / un",               "Valor": fmt_brl(resultado.fee_unitario)},
            {"Métrica": "PFC final / un (mix)",           "Valor": fmt_brl(resultado.mix_pfc_unit)},
            {"Métrica": "Ticket Laszlo blendado",         "Valor": fmt_brl(resultado.ticket_medio_blendado)},
        ])
        st.dataframe(df_blend, hide_index=True, use_container_width=True)

        # Comparativo item-a-item
        st.markdown(
            '<div class="panel-title" style="margin-top:1.4rem;">'
            'Comparativo: kit vs lotes separados</div>',
            unsafe_allow_html=True,
        )
        rows = []
        for it in resultado.itens:
            rows.append({
                "Produto": it.sku,
                "Qtd": f"{it.quantidade:,}".replace(",", "."),
                "PFC isolado / un":  fmt_brl(it.pfc_individual),
                "Tier isolado":      it.tier_individual,
                "PFC no kit / un":   fmt_brl(resultado.mix_pfc_unit),
                "Δ por un":          fmt_brl(it.pfc_individual - resultado.mix_pfc_unit),
            })
        rows.append({
            "Produto": "MÉDIA PONDERADA",
            "Qtd":     f"{total_un:,}".replace(",", "."),
            "PFC isolado / un":  fmt_brl(resultado.avg_pfc_individual_ponderado),
            "Tier isolado":      "—",
            "PFC no kit / un":   fmt_brl(resultado.mix_pfc_unit),
            "Δ por un":          fmt_brl(resultado.economia_por_unidade),
        })
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        st.caption(
            "O ganho do kit vem do tier por TOTAL de unidades + diluição "
            "única do Fee + escala do envase aplicada ao lote inteiro."
        )

    # ---------------- PAINEL DIREITO: VIABILIDADE --------------- #
    with col_right:
        st.markdown('<div class="panel-title">Viabilidade do kit</div>',
                    unsafe_allow_html=True)

        metric_card_iv(
            "Índice de Viabilidade (blendado)",
            f"{resultado.iv:.2f}" if resultado.iv else "—",
            resultado.iv_status,
            resultado.iv_cor,
        )

        st.markdown(
            '<div class="panel-title" style="margin-top:1.2rem;">Retorno projetado</div>',
            unsafe_allow_html=True,
        )
        metric_card("ROI conservador", fmt_pct(resultado.roi_pct),
                    f"Lucro líquido: {fmt_brl(resultado.lucro_liquido_lote)}")
        be = (f"{resultado.break_even_un:,} un".replace(",", ".")
              if resultado.break_even_un else "—")
        metric_card("Margem líquida / un",
                    fmt_brl(resultado.margem_liquida_unit),
                    f"Break-even: {be}")

        # Bloco de proposta — só para perfis com permissão
        st.markdown(
            '<div class="panel-title" style="margin-top:1.2rem;">Proposta do kit</div>',
            unsafe_allow_html=True,
        )
        if not pode_gerar_pdf:
            st.caption("Geração de PDF restrita a ADMIN e clientes.")
        else:
            cliente_pdf = ss["mix_cliente"].strip() or "Cliente Premium"
            kit_nome_pdf = ss["mix_kit_nome"].strip() or "Kit Composto DOMME"
            if st.button(
                "Gerar Proposta do Kit",
                key="mix_gerar_pdf",
                type="primary",
                icon=":material/picture_as_pdf:",
                use_container_width=True,
            ):
                try:
                    pdf_bytes = gerar_proposta_kit_pdf(
                        resultado,
                        cliente_nome=cliente_pdf,
                        kit_nome=kit_nome_pdf,
                        usuario_nome=usuario.nome,
                    )
                    ss["mix_pdf_bytes"] = pdf_bytes
                    st.success("Proposta gerada — pronta para download.")
                except Exception as e:
                    st.error(f"Falha ao gerar PDF: {e}")

            if ss.get("mix_pdf_bytes"):
                ts = datetime.now().strftime("%Y%m%d-%H%M")
                fname = f"DOMME_kit_{ts}.pdf"
                st.download_button(
                    "Baixar PDF da proposta",
                    data=ss["mix_pdf_bytes"],
                    file_name=fname,
                    mime="application/pdf",
                    icon=":material/download:",
                    use_container_width=True,
                )

    # ============================================================
    # VISÃO CAIXA — só para ADMIN, abaixo dos painéis
    # ============================================================
    if usuario.perfil == "ADMIN":
        render_divider()
        st.markdown(
            '<div class="panel-title">Visão Caixa DOMME — kit consolidado</div>',
            unsafe_allow_html=True,
        )

        cv1, cv2, cv3, cv4 = st.columns(4)
        with cv1:
            metric_card("Repasse Fábrica",
                        fmt_brl(resultado.repasse_fabrica),
                        "PI × volume + selo")
        with cv2:
            metric_card("Renda bruta DOMME",
                        fmt_brl(resultado.renda_bruta_domme),
                        f"{fmt_pct(resultado.renda_pct_sobre_lote)} do lote")
        with cv3:
            metric_card("Fee único do lote",
                        fmt_brl(resultado.fee_ativacao_total),
                        f"diluído: {fmt_brl(resultado.fee_unitario)} / un")
        with cv4:
            label_pl = "✓ Acima do mínimo" if resultado.pro_labore_ok else "⚠ Abaixo do mínimo"
            metric_card("Pró-labore",
                        label_pl,
                        f"Mínimo: {fmt_brl(Parametros().pro_labore_minimo)}")

        if resultado.alertas:
            for a in resultado.alertas:
                st.warning(a)

    # Toast suave para alertas (uma vez por composição)
    fp = tuple(resultado.alertas)
    if fp and ss.get("_mix_last_toast") != fp:
        ss["_mix_last_toast"] = fp
        for a in resultado.alertas[:3]:
            st.toast(a, icon="⚠")
    elif not fp:
        ss["_mix_last_toast"] = None


# ========================================================================== #
#  TELA: SUGESTÕES DE MIX (motor de recomendações)
# ========================================================================== #
# Visível a TODOS os perfis. ADMIN/CLIENTE recebem o fluxo completo
# (wizard, kits recomendados, exploração e tendências). FABRICA recebe
# o mesmo conteúdo em modo somente-consulta — pode explorar o catálogo
# mas não pode pré-carregar um kit no Mix & Kits para gerar proposta.

# Cache em memória dos SKUs enriquecidos. Como `data_loader` usa lru_cache
# para o catálogo cru, basta cacheá-lo aqui também — fica leve (~491
# objetos) e evita reclassificar a cada rerun.
@st.cache_data(show_spinner=False)
def _carregar_skus_enriquecidos() -> list[dict]:
    """Carrega o catálogo, enriquece e devolve dicts (Streamlit cache
    serializa dicts melhor que dataclasses)."""
    nomes = listar_skus_disponiveis()
    raw = []
    for n in nomes:
        d = buscar_sku(n)
        if d:
            raw.append(d)
    enriched = enriquecer_skus(raw)
    return [s.to_dict() for s in enriched]


def _enriched_objs(dados: list[dict]) -> list[SkuEnriquecido]:
    """Reconstrói os dataclasses a partir do cache. Nem todo helper
    precisa do dataclass — vários só leem dicts — mas a função de
    recomendação espera os objetos."""
    return [
        SkuEnriquecido(
            nome=d["nome"], codigo=d["codigo"],
            cvu_mp=d["cvu_mp"], ticket_medio=d["ticket_medio"],
            vendas_2024=d["vendas_2024"], mc_real=d["mc_real"],
            status_wl=d["status_wl"],
            familia=d["familia"], familia_desc=d["familia_desc"],
            efeitos=list(d["efeitos"]), nichos=list(d["nichos"]),
            is_alimentos=d["is_alimentos"],
            bestseller_score=d["bestseller_score"],
            is_bestseller=d["is_bestseller"],
            is_novidade=d["is_novidade"],
        )
        for d in dados
    ]


def _reco_init_state():
    ss = st.session_state
    ss.setdefault("reco_canal", None)
    ss.setdefault("reco_ticket", None)
    ss.setdefault("reco_objetivo", None)
    ss.setdefault("reco_shortlist", [])         # lista de nomes de SKUs
    ss.setdefault("reco_explore_tab", "Famílias Aromáticas")


def _reco_chip(texto: str, classe: str = "") -> str:
    cls = "reco-chip" + (f" {classe}" if classe else "")
    return f'<span class="{cls}">{texto}</span>'


def _reco_estimar_kit_metrics(
    kit: KitTemplate,
    catalogo_nomes: list[str],
) -> Optional[dict]:
    """Roda calcular_mix sobre o kit expandido para devolver PFC e IV
    estimados. Devolve None se faltarem SKUs (kit incompleto)."""
    items = expandir_kit(kit, catalogo_nomes, buscar_sku)
    if len(items) < 2:
        return None
    try:
        codigos_retirada = _mix_load_check_retirada_codes()
        res = calcular_mix(
            items=items, mercado=kit.mercado,
            skus_em_retirada=codigos_retirada,
        )
        return {
            "pfc": res.mix_pfc_unit,
            "iv": res.iv,
            "iv_status": res.iv_status,
            "iv_cor": res.iv_cor,
            "investimento": res.investimento_total,
            "total_un": res.total_unidades,
            "skus_resolvidos": len(items),
            "skus_keywords": len(kit.sku_keywords),
        }
    except Exception:
        return None


def _reco_carregar_kit_no_mix(kit: KitTemplate, catalogo_nomes: list[str]):
    """Substitui `mix_slots` pelo kit expandido e navega para Mix & Kits.

    Reaproveita o mesmo modelo de estado já usado por `tela_mix`:
      • mix_slots: lista [{sku, qty}, …]
      • mix_widget_ver: bumped para forçar recriação dos widgets
      • mix_kit_nome / mix_cliente: pré-preenchidos
    """
    items = expandir_kit(kit, catalogo_nomes, buscar_sku)
    n_resolvidos = len(items)
    n_esperados = len(kit.sku_keywords)
    if n_resolvidos < 2:
        st.warning(
            f"Não foi possível resolver SKUs suficientes para "
            f"\"{kit.name}\" no catálogo atual."
        )
        return
    if n_resolvidos < n_esperados:
        # Carrega mesmo assim, mas avisa o usuário que o kit veio incompleto
        # — útil para clientes saberem que podem complementar manualmente.
        st.toast(
            f"Aviso: {n_resolvidos} de {n_esperados} SKUs do kit foram "
            f"resolvidos no catálogo atual.",
            icon="⚠",
        )
    _mix_init_state()  # garante chaves base
    st.session_state["mix_slots"] = [
        {"sku": sku["nome"], "qty": int(qty)} for sku, qty in items
    ]
    _mix_bump_widget_version()
    st.session_state["mix_kit_nome"] = kit.name
    st.session_state["mix_pdf_bytes"] = None
    st.session_state["nav_selected"] = "Mix & Kits"
    st.toast(f"Kit “{kit.name}” carregado no construtor", icon="✨")
    st.rerun()


def _reco_carregar_shortlist_no_mix(
    nomes_shortlist: list[str], qty_padrao: int = 100,
):
    """Idem ao kit pré-curado, mas usando uma shortlist do explorador."""
    nomes_validos = nomes_shortlist[:_MIX_MAX_SKUS]
    if len(nomes_validos) < _MIX_MIN_SKUS:
        st.warning(
            f"Adicione pelo menos {_MIX_MIN_SKUS} SKUs à sua "
            f"seleção antes de levar para o Mix & Kits."
        )
        return
    _mix_init_state()
    st.session_state["mix_slots"] = [
        {"sku": n, "qty": qty_padrao} for n in nomes_validos
    ]
    _mix_bump_widget_version()
    st.session_state["mix_kit_nome"] = "Kit Personalizado"
    st.session_state["mix_pdf_bytes"] = None
    st.session_state["nav_selected"] = "Mix & Kits"
    st.toast(
        f"{len(nomes_validos)} SKUs carregados no Mix & Kits",
        icon="✨",
    )
    st.rerun()


def _render_reco_kit_card(
    matched: MatchedKit,
    metrics: Optional[dict],
    catalogo_nomes: list[str],
    pode_simular: bool,
    idx: int,
):
    """Renderiza um cartão de kit recomendado com chips, métricas e CTA."""
    kit = matched.kit
    chips = []
    if kit.food_line:
        chips.append(_reco_chip(SELO_ALIMENTOS, "reco-chip-food"))
    if kit.seasonal:
        chips.append(_reco_chip(f"🗓 {kit.seasonal}", "reco-chip-season"))
    if matched.score >= 8:
        chips.append(_reco_chip("⭐ Top match", "reco-chip-best"))
    if kit.mercado == "Internacional":
        chips.append(_reco_chip("🌍 Internacional"))

    metric_html = ""
    if metrics:
        iv_pct = f"{metrics['iv']*100:.0f}%" if metrics.get("iv") is not None else "—"
        pfc_str = f"R$ {metrics['pfc']:.2f}"
        invest_str = f"R$ {metrics['investimento']:,.0f}".replace(",", ".")
        metric_html = (
            "<div class='rk-row'>"
            f"  <div class='rk-cell'><div class='rk-label'>PFC unit</div>"
            f"    <div class='rk-value'>{pfc_str}</div></div>"
            f"  <div class='rk-cell'><div class='rk-label'>IV blendado</div>"
            f"    <div class='rk-value'>{iv_pct}</div></div>"
            f"  <div class='rk-cell'><div class='rk-label'>Lote</div>"
            f"    <div class='rk-value'>{metrics['total_un']} un</div></div>"
            "</div>"
        )

    st.markdown(
        "<div class='reco-kit-card'>"
        f"  <div class='rk-niche'>{kit.niche}</div>"
        f"  <div class='rk-name'>{kit.name}</div>"
        f"  <div class='rk-tag'>“{kit.tagline}”</div>"
        f"  <div>{''.join(chips)}</div>"
        f"  {metric_html}"
        f"  <div class='rk-target'><strong>Para:</strong> {kit.target_client}</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    if pode_simular:
        if st.button(
            "Simular este kit →",
            key=f"reco_sim_{idx}",
            use_container_width=True,
            type="primary",
        ):
            _reco_carregar_kit_no_mix(kit, catalogo_nomes)
    else:
        st.caption("Apenas ADMIN/CLIENTE pode simular o kit no Mix & Kits.")


def _render_reco_sku_card(
    sku: SkuEnriquecido,
    catalogo_nomes_idx: int,
    pode_simular: bool,
):
    """Cartão compacto de SKU dentro das abas do explorador.

    Mostra família, efeitos, badges e botão "+ adicionar à seleção".
    O caller passa um índice estável para a key do botão.
    """
    chips = [_reco_chip(sku.familia)]
    for ef in sku.efeitos[:2]:
        chips.append(_reco_chip(ef))
    if sku.is_alimentos:
        chips.append(_reco_chip("🍃 Alimentos", "reco-chip-food"))
    if sku.is_bestseller:
        chips.append(_reco_chip("⭐ Mais vendido", "reco-chip-best"))
    if sku.is_novidade:
        chips.append(_reco_chip("✨ Novo", "reco-chip-novo"))

    estrelas = "★" * max(1, min(5, int(round(sku.mc_real * 5 / 0.5)) if sku.mc_real else 1))
    estrelas_html = (f"<span class='reco-stars'>{estrelas}</span>"
                     f" <span style='color:#6B6256;font-size:0.72rem;'>"
                     f"MC {sku.mc_real*100:.0f}%</span>")

    st.markdown(
        "<div class='reco-sku-card'>"
        f"  <div class='rs-name'>{sku.nome}</div>"
        f"  <div>{''.join(chips)}</div>"
        f"  <div class='rs-meta'>{estrelas_html} · "
        f"     Vendas 2024: <strong>{sku.vendas_2024}</strong></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    if pode_simular:
        ja_na_lista = sku.nome in st.session_state.get("reco_shortlist", [])
        rotulo = "✓ Na seleção" if ja_na_lista else "+ Adicionar à seleção"
        btn_type = "primary" if ja_na_lista else "secondary"
        if st.button(
            rotulo,
            key=f"reco_add_{catalogo_nomes_idx}",
            use_container_width=True,
            type=btn_type,
            disabled=ja_na_lista,
        ):
            ss = st.session_state
            if sku.nome not in ss["reco_shortlist"]:
                ss["reco_shortlist"].append(sku.nome)
                st.rerun()


def tela_sugestoes(usuario: Usuario):
    render_breadcrumb("Sugestões de Mix — Recomendações inteligentes")
    st.markdown("# Sugestões de Mix")
    st.caption(
        "Responda 3 perguntas e receba kits sob medida · Explore por família, "
        "efeito ou nicho · Insights ao vivo do catálogo"
    )

    _reco_init_state()
    ss = st.session_state

    # Permissão: ADMIN e CLIENTE podem simular kits no Mix & Kits.
    # FABRICA navega em modo consulta — vê tudo, não carrega kit.
    pode_simular = pode(usuario, "proposta") or usuario.perfil == "ADMIN"
    if usuario.perfil == "FABRICA":
        st.info(
            "Você está em modo de consulta. As recomendações ficam "
            "visíveis, mas a simulação de kits é restrita a ADMIN e clientes."
        )

    # Banner sazonal sempre no topo
    titulo_saz, desc_saz = tendencia_sazonal()
    st.markdown(
        "<div class='reco-banner'>"
        f"  <div class='rb-title'>{titulo_saz}</div>"
        f"  <div class='rb-sub'>{desc_saz}</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Carrega base enriquecida uma vez
    catalogo_nomes = listar_skus_disponiveis()
    enriched = _enriched_objs(_carregar_skus_enriquecidos())

    # ------------------------------------------------------------ #
    # SEÇÃO A — Wizard "Qual é o seu perfil?"
    # ------------------------------------------------------------ #
    st.markdown(
        '<div class="panel-title" style="margin-top:1.4rem;">'
        'A · Qual é o seu perfil?</div>',
        unsafe_allow_html=True,
    )

    col_q1, col_q2, col_q3 = st.columns(3, gap="large")

    with col_q1:
        st.markdown(
            "<div style='font-size:0.78rem; color:#6B6256; "
            "letter-spacing:1.4px; text-transform:uppercase; "
            "margin-bottom:0.5rem;'>1. Canal de Venda</div>",
            unsafe_allow_html=True,
        )
        canal_label = st.radio(
            "Canal de venda",
            options=CANAIS,
            format_func=lambda c: f"{CANAIS_ICONES.get(c,'')}  {c}",
            index=CANAIS.index(ss["reco_canal"]) if ss["reco_canal"] in CANAIS else 0,
            key="reco_canal_radio",
            label_visibility="collapsed",
        )
        if canal_label != ss["reco_canal"]:
            ss["reco_canal"] = canal_label

    with col_q2:
        st.markdown(
            "<div style='font-size:0.78rem; color:#6B6256; "
            "letter-spacing:1.4px; text-transform:uppercase; "
            "margin-bottom:0.5rem;'>2. Ticket do Cliente Final</div>",
            unsafe_allow_html=True,
        )
        ticket_label = st.select_slider(
            "Ticket do cliente",
            options=TICKETS,
            value=ss["reco_ticket"] or "intermediario",
            format_func=lambda t: TICKETS_LABEL[t],
            key="reco_ticket_slider",
            label_visibility="collapsed",
        )
        if ticket_label != ss["reco_ticket"]:
            ss["reco_ticket"] = ticket_label

    with col_q3:
        st.markdown(
            "<div style='font-size:0.78rem; color:#6B6256; "
            "letter-spacing:1.4px; text-transform:uppercase; "
            "margin-bottom:0.5rem;'>3. Objetivo Principal</div>",
            unsafe_allow_html=True,
        )
        obj_label = st.radio(
            "Objetivo",
            options=OBJETIVOS,
            format_func=lambda o: OBJETIVOS_LABEL[o],
            index=OBJETIVOS.index(ss["reco_objetivo"]) if ss["reco_objetivo"] in OBJETIVOS else 0,
            key="reco_objetivo_radio",
            label_visibility="collapsed",
        )
        if obj_label != ss["reco_objetivo"]:
            ss["reco_objetivo"] = obj_label

    # ------------------------------------------------------------ #
    # SEÇÃO B — Kits recomendados
    # ------------------------------------------------------------ #
    st.markdown(
        '<div class="panel-title" style="margin-top:1.6rem;">'
        'B · Kits recomendados para você</div>',
        unsafe_allow_html=True,
    )

    matched = recomendar_kits(
        canal=ss["reco_canal"] or CANAIS[0],
        ticket=ss["reco_ticket"] or "intermediario",
        objetivo=ss["reco_objetivo"] or OBJETIVOS[0],
        enriched_skus=enriched,
    )

    top3 = [m for m in matched if m.score > 3][:3]
    if not top3:
        st.markdown(
            "<div class='reco-empty'>Nenhuma combinação fechou um match "
            "forte. Explore o catálogo completo abaixo ou tente outras "
            "combinações no wizard.</div>",
            unsafe_allow_html=True,
        )
    else:
        cols = st.columns(len(top3), gap="medium")
        for idx, (col, m) in enumerate(zip(cols, top3)):
            with col:
                metrics = _reco_estimar_kit_metrics(m.kit, catalogo_nomes)
                _render_reco_kit_card(
                    matched=m,
                    metrics=metrics,
                    catalogo_nomes=catalogo_nomes,
                    pode_simular=pode_simular,
                    idx=idx,
                )

    # ------------------------------------------------------------ #
    # SEÇÃO C — Explore por categoria
    # ------------------------------------------------------------ #
    st.markdown(
        '<div class="panel-title" style="margin-top:1.8rem;">'
        'C · Explore por categoria</div>',
        unsafe_allow_html=True,
    )

    # Shortlist bar (sticky-ish)
    sl = ss["reco_shortlist"]
    sl_html = ", ".join(sl[:6]) + ("…" if len(sl) > 6 else "") if sl else "Nenhum SKU selecionado ainda."
    cnt_text = (f"{len(sl)} SKU{'s' if len(sl) != 1 else ''} na seleção"
                if sl else "Sua seleção está vazia")
    col_bar, col_send, col_clear = st.columns([5, 2, 1], gap="small")
    with col_bar:
        st.markdown(
            f"<div class='reco-shortlist-bar'>"
            f"<div><strong>{cnt_text}</strong> · {sl_html}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_send:
        if st.button(
            "Levar para Mix & Kits →",
            key="reco_sl_send",
            use_container_width=True,
            type="primary",
            disabled=not pode_simular or len(sl) < _MIX_MIN_SKUS,
            help=("Adicione ao menos 2 SKUs"
                  if len(sl) < _MIX_MIN_SKUS
                  else "Pré-carrega no construtor de kit"),
        ):
            _reco_carregar_shortlist_no_mix(sl)
    with col_clear:
        if st.button(
            "Limpar",
            key="reco_sl_clear",
            use_container_width=True,
            disabled=not sl,
        ):
            ss["reco_shortlist"] = []
            st.rerun()

    # Tabs do explorador
    abas = [
        "Famílias Aromáticas", "Efeitos", "Nichos",
        f"Linha Alimentos 🍃", "Mais Vendidos ⭐", "Sazonais 🗓",
    ]
    tab_familias, tab_efeitos, tab_nichos, tab_alim, tab_best, tab_saz = st.tabs(abas)

    # Cada aba reorganiza os mesmos `enriched` em filtros/agrupamentos.
    # Para keys estáveis nos botões "+ Adicionar", usamos o índice
    # do SKU no enriched (mantém-se entre reruns).
    nome_to_idx = {s.nome: i for i, s in enumerate(enriched)}

    def _grid_skus(skus: list[SkuEnriquecido], chave_grupo: str, limite: int = 18):
        if not skus:
            st.markdown("<div class='reco-empty'>Nenhum SKU neste filtro.</div>",
                        unsafe_allow_html=True)
            return
        skus = skus[:limite]
        # 3 colunas no desktop
        n_cols = 3
        cols = st.columns(n_cols, gap="small")
        for i, sku in enumerate(skus):
            with cols[i % n_cols]:
                _render_reco_sku_card(
                    sku,
                    catalogo_nomes_idx=nome_to_idx.get(sku.nome, i) * 100
                    + hash(chave_grupo) % 90,
                    pode_simular=pode_simular,
                )

    with tab_familias:
        familias_existentes = sorted({s.familia for s in enriched})
        fam_sel = st.selectbox(
            "Filtrar por família",
            options=familias_existentes,
            key="reco_filtro_familia",
        )
        skus_fam = [s for s in enriched if s.familia == fam_sel]
        skus_fam.sort(key=lambda s: s.bestseller_score, reverse=True)
        st.caption(f"{len(skus_fam)} SKUs disponíveis em **{fam_sel}**.")
        _grid_skus(skus_fam, f"fam_{fam_sel}")

    with tab_efeitos:
        efeitos_existentes = sorted({e for s in enriched for e in s.efeitos})
        if not efeitos_existentes:
            st.markdown("<div class='reco-empty'>Nenhum efeito catalogado ainda.</div>",
                        unsafe_allow_html=True)
        else:
            ef_sel = st.selectbox(
                "Filtrar por efeito",
                options=efeitos_existentes,
                key="reco_filtro_efeito",
            )
            skus_ef = [s for s in enriched if ef_sel in s.efeitos]
            skus_ef.sort(key=lambda s: s.bestseller_score, reverse=True)
            st.caption(f"{len(skus_ef)} SKUs com efeito **{ef_sel}**.")
            _grid_skus(skus_ef, f"ef_{ef_sel}")

    with tab_nichos:
        nichos_existentes = sorted({n for s in enriched for n in s.nichos})
        if not nichos_existentes:
            st.markdown("<div class='reco-empty'>Nenhum nicho disponível.</div>",
                        unsafe_allow_html=True)
        else:
            ni_sel = st.selectbox(
                "Filtrar por nicho",
                options=nichos_existentes,
                key="reco_filtro_nicho",
            )
            skus_ni = [s for s in enriched if ni_sel in s.nichos]
            skus_ni.sort(key=lambda s: s.bestseller_score, reverse=True)
            st.caption(f"{len(skus_ni)} SKUs no nicho **{ni_sel}**.")
            _grid_skus(skus_ni, f"ni_{ni_sel}")

    with tab_alim:
        skus_alim = [s for s in enriched if s.is_alimentos]
        skus_alim.sort(key=lambda s: s.bestseller_score, reverse=True)
        st.caption(
            f"{len(skus_alim)} SKUs aptos a uso alimentar — registrados como "
            "Aroma Natural. " + TOOLTIP_ALIMENTOS
        )
        _grid_skus(skus_alim, "alim")

    with tab_best:
        skus_best = [s for s in enriched if s.is_bestseller]
        skus_best.sort(key=lambda s: s.bestseller_score, reverse=True)
        st.caption(f"{len(skus_best)} SKUs no top 20% por score combinado de vendas + margem.")
        _grid_skus(skus_best, "best")

    with tab_saz:
        # Sugestão sazonal: para cada estação mostramos famílias relevantes
        m = datetime.today().month
        if 1 <= m <= 3:
            destaque = ["HERBACEA", "CITRICA"]
        elif 4 <= m <= 5:
            destaque = ["FLORAL"]
        elif 6 <= m <= 8:
            destaque = ["ORIENTAL", "ESPECIADA"]
        elif 9 <= m <= 10:
            destaque = ["FLORAL", "CITRICA"]
        else:
            destaque = ["ESPECIADA", "ORIENTAL"]
        skus_saz = [s for s in enriched if s.familia in destaque]
        skus_saz.sort(key=lambda s: s.bestseller_score, reverse=True)
        st.caption(
            f"Famílias em alta agora: **{', '.join(destaque)}** "
            f"({len(skus_saz)} SKUs)."
        )
        _grid_skus(skus_saz, "saz")

    # ------------------------------------------------------------ #
    # SEÇÃO D — Tendências do catálogo
    # ------------------------------------------------------------ #
    st.markdown(
        '<div class="panel-title" style="margin-top:1.8rem;">'
        'D · Tendências do catálogo</div>',
        unsafe_allow_html=True,
    )

    insights = gerar_insights(enriched)

    col_a, col_b, col_c, col_d = st.columns(4, gap="medium")

    with col_a:
        rows = "".join(
            f"<div class='ri-row'><span class='ri-num'>#{i+1}</span>"
            f"{s.nome[:38]}{'…' if len(s.nome) > 38 else ''} "
            f"<span style='color:#6B6256;float:right;'>{s.vendas_2024}</span></div>"
            for i, s in enumerate(insights.top5_vendas)
        )
        st.markdown(
            "<div class='reco-insight-card'>"
            "  <div class='ri-title'>Top 5 SKUs em 2024</div>"
            f"  {rows or '<div class=ri-row>—</div>'}"
            "</div>",
            unsafe_allow_html=True,
        )
    with col_b:
        rows = "".join(
            f"<div class='ri-row'>{f}<span style='color:#A88B5C;float:right;'>"
            f"{mc*100:.1f}%</span></div>"
            for f, mc, _ in insights.melhor_familia_margem
        )
        st.markdown(
            "<div class='reco-insight-card'>"
            "  <div class='ri-title'>Melhor margem por família</div>"
            f"  {rows or '<div class=ri-row>—</div>'}"
            "</div>",
            unsafe_allow_html=True,
        )
    with col_c:
        st.markdown(
            "<div class='reco-insight-card'>"
            "  <div class='ri-title'>Linha Alimentos 🍃</div>"
            f"  <div class='ri-big'>{insights.qtd_alimentos}</div>"
            "  <div style='font-size:0.8rem;color:#0E0E0E;'>"
            "  SKUs disponíveis para uso gastronômico — registrados "
            "  como Aroma Natural.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    with col_d:
        if insights.novidades:
            rows = "".join(
                f"<div class='ri-row'>{s.nome[:40]}{'…' if len(s.nome) > 40 else ''}</div>"
                for s in insights.novidades[:5]
            )
            big = ""
        else:
            rows = ("<div style='font-size:0.8rem;color:#6B6256;'>"
                    "Nenhuma novidade catalogada agora — "
                    "fique de olho nos próximos lançamentos da Laszlo.</div>")
            big = f"<div class='ri-big'>{len(insights.novidades)}</div>"
        st.markdown(
            "<div class='reco-insight-card'>"
            "  <div class='ri-title'>Novidades do catálogo</div>"
            f"  {big}{rows}"
            "</div>",
            unsafe_allow_html=True,
        )


# --------------------------- TELA: EXPORTAÇÃO ----------------------------- #
def tela_exportacao(usuario: Usuario):
    render_breadcrumb("Módulo de Exportação")
    st.markdown("# Módulo de Exportação")
    st.caption("WL Export · Markup de luxo (8x sobre CVU) · Sem IPI/ICMS internos")

    col1, col2, col3 = st.columns(3)
    with col1:
        usd = st.number_input("Cotação USD → BRL", min_value=0.01, value=5.50, step=0.10)
    with col2:
        eur = st.number_input("Cotação EUR → BRL", min_value=0.01, value=5.90, step=0.10)
    with col3:
        frete = st.number_input("Frete internacional (USD/un)", min_value=0.0, value=2.0, step=0.5)

    sku = selector_sku_busca("SKU", key="export_sku")
    volume = st.number_input("Volume", min_value=1, value=500, step=50)

    if not sku:
        render_empty_state(
            "Selecione um produto para simular a exportação",
            "Markup 8x sobre CVU em múltiplas moedas.",
            icone="✦",
        )
        return
    dados = buscar_sku(sku)
    if not dados:
        return

    p = Parametros(cotacao_usd=usd, cotacao_eur=eur, frete_internacional_usd=frete)
    r = calcular_pricing(sku, volume, dados["cvu_mp"], dados["ticket_medio"],
                          mercado="Internacional", parametros=p)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("PFC Export (R$)", fmt_brl(r.pfc_final_unit))
    with c2:
        metric_card("PFC Export (USD)", f"$ {r.pfc_final_unit/usd:,.2f}")
    with c3:
        metric_card("PFC Export (EUR)", f"€ {r.pfc_final_unit/eur:,.2f}")
    with c4:
        pfc_frete_usd = r.pfc_final_unit/usd + frete
        metric_card("PFC + Frete (USD)", f"$ {pfc_frete_usd:,.2f}")

    if pode(usuario, "visao_caixa"):
        render_divider()
        st.markdown("### Renda Garantida no Export")
        st.write(f"Repasse à Fábrica: **{fmt_brl(r.repasse_fabrica)}** "
                 f"· Renda DOMME: **{fmt_brl(r.renda_bruta_domme)}** "
                 f"({fmt_pct(r.renda_pct_sobre_lote)} do lote)")
        st.caption("Política Export: Laszlo recebe PI normal + 50% do excedente; DOMME captura o restante.")


# --------------------------- TELA: CATÁLOGO ------------------------------- #
def tela_catalogo(usuario: Usuario):
    render_breadcrumb("Catálogo Laszlo")
    st.markdown("# Catálogo Laszlo")

    with st.spinner("Carregando catálogo..."):
        df = carregar_catalogo()

    if usuario.perfil == "CLIENTE":
        df_view = df[["Nome do Produto", "Ticket Médio (R$)", "Status WL", "Volume (ml)"]]
    elif usuario.perfil == "FABRICA":
        df_view = df
    else:
        df_view = df

    st.caption(f"{len(df)} SKUs · Perfil {usuario.perfil}: visualização adaptada")
    st.dataframe(df_view, use_container_width=True, hide_index=True)


# --------------------------- TELA: BASE MP -------------------------------- #
def tela_base_mp(usuario: Usuario):
    render_breadcrumb("Base de Matérias-Primas")
    st.markdown("# Base de Matérias-Primas")
    st.caption("⚙ Acesso restrito · Apenas Fábrica e Admin")

    with st.spinner("Carregando base de MP..."):
        df = carregar_base_mp()
    st.write(f"**{len(df)}** matérias-primas cadastradas")

    if usuario.perfil == "FABRICA":
        st.info("Você pode atualizar o **Preço Custo Real** das matérias-primas. "
                "O Motor v3 puxa esse valor automaticamente para o cálculo do CVU.")

    st.dataframe(df, use_container_width=True, hide_index=True)


# --------------------------- TELA: RETIRADA ------------------------------- #
def tela_retirada(usuario: Usuario):
    render_breadcrumb("Check de Retirada de Linha")
    st.markdown("# Check de Retirada de Linha")
    st.caption("⛔ SKUs em retirada bloqueiam o Motor v3 automaticamente")

    with st.spinner("Carregando lista de retirada..."):
        df = carregar_check_retirada()
    st.dataframe(df, use_container_width=True, hide_index=True)


# --------------------------- TELA: PARÂMETROS ----------------------------- #
def tela_parametros(usuario: Usuario):
    render_breadcrumb("Parâmetros Globais")
    st.markdown("# Parâmetros Globais (Admin)")
    st.caption("Ajuste taxas, tiers e limites · Toda a aplicação herda essas mudanças")

    p = st.session_state.get("parametros_custom", Parametros())

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Margens & Taxas")
        mil = st.slider("MIL — Margem Industrial Laszlo", 0.20, 0.60, p.mil, 0.01)
        md = st.slider("MD — Margem Comercial DOMME", 0.10, 0.40, p.md, 0.01)
        selo = st.slider("Selo Laszlo (%)", 0.0, 0.10, p.selo_laszlo, 0.005)
        mc_min = st.slider("MC mínima Laszlo (trava)", 0.10, 0.30, p.mc_minima_laszlo, 0.01)

        st.markdown("### Tiers de Markup")
        t1m = st.slider("Tier 1 markup", 0.0, 0.40, p.tier1_markup, 0.01)
        t2m = st.slider("Tier 2 markup", 0.0, 0.30, p.tier2_markup, 0.01)
        t3m = st.slider("Tier 3 markup", 0.0, 0.20, p.tier3_markup, 0.01)

    with col2:
        st.markdown("### Fee de Ativação Dinâmico (Renda Garantida)")
        fee_t1 = st.number_input("Fee Tier 1 (≤500 un)", value=p.fee_t1, step=100.0)
        fee_t2 = st.number_input("Fee Tier 2 (501-2000 un)", value=p.fee_t2, step=100.0)
        fee_t3_min = st.number_input("Fee Tier 3 mínimo", value=p.fee_t3_minimo, step=500.0)
        fee_t3_pct = st.slider("Fee Tier 3 — % sobre lote", 0.01, 0.10, p.fee_t3_pct, 0.005)

        st.markdown("### Trava de Pro Labore")
        pl_min = st.number_input("Mínimo aceitável por projeto (R$)", value=p.pro_labore_minimo, step=100.0)

        st.markdown("### Viabilidade")
        iv_v = st.slider("Limite verde IV", 0.30, 0.70, p.iv_verde, 0.05)
        iv_a = st.slider("Limite amarelo IV", 0.55, 0.85, p.iv_amarelo, 0.05)

        st.markdown("### Exportação")
        markup_e = st.slider("Markup Export (multiplicador)", 3.0, 12.0, p.markup_export, 0.5)

    if st.button("💾 Salvar parâmetros nesta sessão"):
        st.session_state["parametros_custom"] = Parametros(
            mil=mil, md=md, selo_laszlo=selo, mc_minima_laszlo=mc_min,
            tier1_markup=t1m, tier2_markup=t2m, tier3_markup=t3m,
            fee_t1=fee_t1, fee_t2=fee_t2, fee_t3_minimo=fee_t3_min, fee_t3_pct=fee_t3_pct,
            pro_labore_minimo=pl_min,
            iv_verde=iv_v, iv_amarelo=iv_a, markup_export=markup_e,
        )
        st.toast("✓ Parâmetros salvos nesta sessão.", icon="✅")
        st.success("Parâmetros salvos. Em produção, persistir em banco.")


# --------------------------- TELA: REGRAS --------------------------------- #
def tela_regras(usuario: Usuario):
    render_breadcrumb("Regras de Negócio")
    st.markdown("# Regras de Negócio · Motor v3")
    st.markdown("""
### 1. Inteligência de Custos
- CVU puxado automaticamente do **Catálogo Laszlo**
- Lotes ≤100 un: insumos de envase (frasco/tampa/gotejador) **multiplicados por 2x**
- **Trava Laszlo:** mínimo 20% de MC no atacado — alerta automático se violado
- SKUs em **Check_Retirada** bloqueiam o cálculo

### 2. Estrutura v3 + Renda Garantida
- Volume = por **Lote/Pedido** (não anual)
- Full-Service obrigatório: Kit Envase + **Fee de Ativação dinâmico**
- **Fee Tier 1 (≤500 un):** R$ 1.500
- **Fee Tier 2 (501-2000 un):** R$ 2.500
- **Fee Tier 3 (>2000 un):** max(R$ 5.000; 5% do valor do lote)
- Tiers: T1≤500 (+20%) · T2≤2000 (+10%) · T3>2000 (0%)

### 3. Métricas de Sucesso
- **IV** = PFC ÷ Varejo Laszlo · Verde (<0.55) / Amarelo (0.55–0.70) / Vermelho (>0.70)
- Benchmark vs. Ticket Médio Laszlo · Alerta se preço > 120%
- Break-Even = Investimento Total ÷ Margem Líquida por unidade
- ROI Conservador: desconta 15% do preço de venda (impostos + frete)

### 4. Exportação
- **Markup 8x** sobre CVU
- Sem IPI/ICMS internos · campo de frete internacional
- Cotação USD/EUR editável
- **Política Export:** Laszlo recebe PI + 50% do excedente · DOMME captura o restante

### 5. Renda Garantida DOMME (visão interna)
- **Repasse à Fábrica** = (PI Laszlo × volume) + (Selo × PFC × volume)
- **Renda Bruta DOMME** = (PFC × volume) − Repasse à Fábrica
- **Trava de Pro Labore:** alerta se Renda Bruta < R$ 2.000

### 6. Compliance & Design
- Verso técnico/legal: **imutável** (compliance regulatório)
- Design exclusivo: serviço à parte (não incluído no fee)
- Foco regulatório: **Aromas Naturais / Alimentos**
""")


# --------------------------- TELA: VISÃO CAIXA ---------------------------- #
def tela_visao_caixa(usuario: Usuario):
    render_breadcrumb("Gestão de Caixa DOMME")
    st.markdown("# Gestão de Caixa DOMME")
    st.caption("⚡ Confidencial · Apenas Admin · Separação Repasse vs. Renda Líquida")

    st.info(
        "Esta tela simula o caixa consolidado de um portfólio de projetos. "
        "Em produção, integrar com banco para acumular projetos reais."
    )

    if "portfolio" not in st.session_state:
        st.session_state["portfolio"] = []

    with st.expander("➕ Adicionar projeto ao portfólio (simulação)"):
        sku = selector_sku_busca("SKU", key="port_sku")
        col1, col2 = st.columns(2)
        with col1:
            vol = st.number_input("Volume", 1, 50000, 500, 50, key="port_vol")
        with col2:
            cliente = st.text_input("Cliente", "Cliente X", key="port_cli")
        if st.button("Adicionar") and sku:
            d = buscar_sku(sku)
            r = calcular_pricing(sku, vol, d["cvu_mp"], d["ticket_medio"])
            st.session_state["portfolio"].append({
                "Cliente": cliente,
                "SKU": sku[:30],
                "Volume": vol,
                "Tier": r.tier_nome,
                "Repasse Fábrica (R$)": r.repasse_fabrica,
                "Renda DOMME (R$)": r.renda_bruta_domme,
                "Fee (R$)": r.fee_ativacao_total,
                "Pro Labore OK": "✓" if r.pro_labore_ok else "⚠",
            })

    if st.session_state["portfolio"]:
        df_port = pd.DataFrame(st.session_state["portfolio"])
        st.dataframe(df_port, use_container_width=True, hide_index=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("Repasse Fábrica", fmt_brl(df_port["Repasse Fábrica (R$)"].sum()),
                        f"{len(df_port)} projetos")
        with c2:
            metric_card("Renda DOMME Total", fmt_brl(df_port["Renda DOMME (R$)"].sum()),
                        "Pro labore consolidado")
        with c3:
            metric_card("Fees Capturados", fmt_brl(df_port["Fee (R$)"].sum()),
                        "Receita previsível")
        with c4:
            ratio = df_port["Renda DOMME (R$)"].sum() / df_port["Repasse Fábrica (R$)"].sum() if df_port["Repasse Fábrica (R$)"].sum() > 0 else 0
            metric_card("Ratio Renda/Repasse", f"{ratio:.2f}x",
                        "Quanto DOMME captura por R$ Laszlo")

        if st.button("🗑 Limpar portfólio"):
            st.session_state["portfolio"] = []
            st.rerun()


# --------------------------- TELA: DASHBOARD ------------------------------ #
def _calcular_score_portfolio(k: dict) -> float:
    """Score 0-100: % disponíveis - penalidade por risco/retirada."""
    total = max(int(k.get("total_skus", 0)), 1)
    disp = int(k.get("skus_disponiveis", 0))
    risco = int(k.get("skus_risco", 0))
    retirada = max(int(k.get("skus_retirada", 0)), 0)
    base = (disp / total) * 100.0
    penalty = (risco * 0.5 + retirada * 0.8) / total * 100.0
    score = base - penalty
    return max(0.0, min(100.0, score))


def _calcular_acoes(cat: pd.DataFrame, k: dict) -> list[dict]:
    """Gera até 3 recomendações baseadas nos sinais do catálogo."""
    acoes = []
    risco = int(k.get("skus_risco", 0))
    retirada = int(k.get("skus_retirada", 0))
    disp = int(k.get("skus_disponiveis", 0))
    total = int(k.get("total_skus", 0))

    if risco > 0:
        acoes.append({
            "icon": "⚠",
            "text": f"{risco} SKU(s) em risco — revisar catálogo",
            "meta": "Renegociar matéria-prima ou planejar substituição",
        })
    if retirada > 0:
        acoes.append({
            "icon": "⛔",
            "text": f"{retirada} SKU(s) em retirada de linha",
            "meta": "Comunicar clientes ativos e propor substitutos",
        })

    # MC baixa
    if "% MC Real" in cat.columns:
        try:
            mc_baixa = (
                cat["% MC Real"]
                .apply(lambda v: pd.to_numeric(v, errors="coerce"))
                .lt(0.20).sum()
            )
            if mc_baixa > 0:
                acoes.append({
                    "icon": "↓",
                    "text": f"{int(mc_baixa)} SKU(s) com MC abaixo de 20%",
                    "meta": "Reavaliar precificação ou custos de envase",
                })
        except Exception:
            pass

    if not acoes and total > 0:
        acoes.append({
            "icon": "✓",
            "text": f"Catálogo saudável: {disp} de {total} SKUs disponíveis",
            "meta": "Sem alertas críticos no momento",
        })

    return acoes[:3]


def tela_dashboard(usuario: Usuario):
    render_breadcrumb("Dashboard")
    # Cabeçalho enxuto: H1 de boas-vindas + subtítulo estruturado.
    # (Removido logo "D O M M E" e tagline duplicados — já presentes
    # na sidebar mini-logo, evitando empilhamento visual no topo.)
    st.markdown(
        f"""
        <div class="dashboard-hero">
            <h1 class="dashboard-hello">Bem-vinda, <span>{usuario.nome}</span></h1>
            <div class="dashboard-subtitle">
                <span class="ds-chip">{usuario.perfil}</span>
                <span class="ds-sep">·</span>
                <span class="ds-org">{usuario.empresa}</span>
                <span class="ds-sep">·</span>
                <span class="ds-tagline">Hub de Marcas Premium · DOMME × LASZLO</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.spinner("Carregando indicadores do portfólio..."):
        k = kpis_dashboard()
        cat = carregar_catalogo()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Total SKUs", f"{k['total_skus']:,}".replace(",", "."), "no catálogo Laszlo")
    with col2:
        metric_card("Disponíveis WL", f"{k['skus_disponiveis']:,}".replace(",", "."), "para White Label")
    with col3:
        metric_card("Em Risco", f"{k['skus_risco']:,}".replace(",", "."), "atenção de estoque")
    with col4:
        metric_card("Ticket Médio", fmt_brl(k['ticket_medio_geral']), "média do catálogo")

    render_divider()

    # ---------- Saúde do portfólio + Próximas Ações ----------
    col_g, col_a = st.columns([1, 1])
    with col_g:
        score = _calcular_score_portfolio(k)
        render_health_gauge(score, "Saúde do Portfólio")
        st.caption(
            "Score = % SKUs disponíveis − penalidade por risco/retirada. "
            "Ideal: > 80."
        )
    with col_a:
        st.markdown("### Próximas Ações")
        acoes = _calcular_acoes(cat, k)
        items_html = "".join([
            f"""
            <div class="action-item">
                <div class="action-icon">{a['icon']}</div>
                <div>
                    <div class="action-text">{a['text']}</div>
                    <div class="action-meta">{a['meta']}</div>
                </div>
            </div>
            """
            for a in acoes
        ])
        st.markdown(f"""
            <div class="actions-panel">
                <div class="ap-title">Recomendações para hoje</div>
                {items_html}
            </div>
        """, unsafe_allow_html=True)

    render_divider()

    # ---------- Donut chart: distribuição de Status WL ----------
    if "Status WL" in cat.columns:
        col_chart, col_legend = st.columns([2, 1])
        with col_chart:
            st.markdown("### Distribuição de SKUs por Status WL")
            status_counts = (
                cat["Status WL"].astype(str).fillna("Não informado")
                .value_counts().reset_index()
            )
            status_counts.columns = ["Status", "Qtd"]
            paleta_status = {
                "Disponível": "#2D6A4F",
                "Em Risco": "#C49B0B",
                "Risco": "#C49B0B",
                "Retirada": "#9E2A2B",
                "Indisponível": "#6B6B6B",
            }
            cores = [
                next((v for k_, v in paleta_status.items() if k_.lower() in s.lower()),
                     "#A88B5C")
                for s in status_counts["Status"]
            ]
            donut = (
                alt.Chart(status_counts)
                .mark_arc(innerRadius=70, outerRadius=120, stroke="#FAFAF7", strokeWidth=2)
                .encode(
                    theta=alt.Theta("Qtd:Q", stack=True),
                    color=alt.Color(
                        "Status:N",
                        scale=alt.Scale(domain=status_counts["Status"].tolist(), range=cores),
                        legend=alt.Legend(title="Status WL"),
                    ),
                    tooltip=["Status:N", alt.Tooltip("Qtd:Q", title="SKUs")],
                )
                .properties(height=300)
            )
            st.altair_chart(donut, use_container_width=True)
        with col_legend:
            st.markdown("### Resumo")
            total = int(status_counts["Qtd"].sum())
            for _, row in status_counts.iterrows():
                pct = (row["Qtd"] / total * 100) if total else 0
                st.markdown(
                    f"**{row['Status']}** · {int(row['Qtd'])} SKUs "
                    f"<span style='color:#6B6B6B;'>({pct:.1f}%)</span>",
                    unsafe_allow_html=True,
                )

    render_divider()
    if usuario.perfil == "ADMIN":
        st.markdown("""
**Atalhos rápidos:**
- **Motor v3** → simulador principal · cliente insere SKU + lote
- **Cenários** → comparativo "e se eu produzir mais?"
- **Exportação** → markup 8x · multimoeda
- **Visão Caixa DOMME** → consolidado da Renda Garantida (confidencial)
- **Parâmetros v3** → ajustar margens, fees, tiers
        """)
    elif usuario.perfil == "FABRICA":
        st.markdown("""
**Áreas que você gerencia:**
- **Catálogo Laszlo** → atualizar custos e ticket médio
- **Base cadastro MP** → manter preços de matérias-primas atualizados
- **Check_Retirada** → declarar SKUs em descontinuação (bloqueia Motor)
        """)
    else:  # CLIENTE
        st.markdown("""
**Suas ferramentas:**
- **Motor v3** → simule lotes e gere o preço final do seu projeto
- **Exportação** → para venda internacional (USD/EUR)
- **Proposta PDF** → exporte e envie ao seu time
        """)


# --------------------------- SIDEBAR / NAV -------------------------------- #
def _sidebar_nav(usuario: Usuario) -> str:
    """Renderiza navegação por botões e devolve a opção selecionada.

    Cada item é uma tupla (rótulo, ícone Material). O rótulo é a chave
    canônica usada por roteamento, NAV_QUERY_MAP e bottom-nav.
    """
    # Lógica original de visibilidade preservada
    grupos: list[tuple[str, list[tuple[str, str]]]] = []

    principais: list[tuple[str, str]] = [("Dashboard", ":material/dashboard:")]
    if pode(usuario, "motor") or usuario.perfil == "ADMIN":
        principais.append(("Motor v3", ":material/precision_manufacturing:"))
    # Sugestões de Mix — visível a TODOS os perfis (motor de
    # recomendações que precede e alimenta o Mix & Kits).
    principais.append(("Sugestões", ":material/lightbulb:"))
    # Mix & Kits — visível a TODOS os perfis (FABRICA usa em modo
    # consulta, sem PDF; ADMIN/CLIENTE simulam e geram proposta).
    principais.append(("Mix & Kits", ":material/widgets:"))
    if usuario.perfil == "ADMIN":
        principais.append(("Cenários", ":material/insights:"))
    if pode(usuario, "exportacao") or usuario.perfil == "ADMIN":
        principais.append(("Exportação", ":material/public:"))
    grupos.append(("Operação", principais))

    catalogo_grupo: list[tuple[str, str]] = []
    if usuario.perfil == "ADMIN" or usuario.perfil == "FABRICA" or pode(usuario, "motor"):
        catalogo_grupo.append(("Catálogo Laszlo", ":material/menu_book:"))
    if usuario.perfil in ("ADMIN", "FABRICA"):
        catalogo_grupo.append(("Base MP", ":material/science:"))
        catalogo_grupo.append(("Check Retirada", ":material/block:"))
    if catalogo_grupo:
        grupos.append(("Catálogo & Dados", catalogo_grupo))

    admin_grupo: list[tuple[str, str]] = []
    if usuario.perfil == "ADMIN":
        admin_grupo.append(("Visão Caixa DOMME", ":material/account_balance:"))
        admin_grupo.append(("Parâmetros", ":material/tune:"))
        admin_grupo.append(("Regras", ":material/gavel:"))
    if admin_grupo:
        grupos.append(("Administração", admin_grupo))

    todas = [opt for _, lst in grupos for opt, _ in lst]
    if "nav_selected" not in st.session_state or st.session_state["nav_selected"] not in todas:
        st.session_state["nav_selected"] = todas[0]

    # Atalhos de teclado para os destinos principais (Alt+letra).
    # Streamlit reserva C e R (copiar / recarregar do navegador), por isso
    # Cenários usa Alt+N (a inicial fonética disponível em "ceNários").
    nav_shortcuts = {
        "Dashboard":   "Alt+D",
        "Motor v3":    "Alt+M",
        "Sugestões":   "Alt+G",   # G de "suGestões" — S/H reservados pelo Streamlit
        "Mix & Kits":  "Alt+K",
        "Cenários":    "Alt+N",
        "Exportação":  "Alt+E",
    }

    for idx, (titulo_grupo, opcoes) in enumerate(grupos):
        if idx > 0:
            st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="sidebar-section-label">{titulo_grupo}</div>',
            unsafe_allow_html=True,
        )
        for opt, icon in opcoes:
            is_active = (st.session_state["nav_selected"] == opt)
            btn_type = "primary" if is_active else "secondary"
            btn_kwargs = dict(
                key=f"nav_{opt}",
                icon=icon,
                use_container_width=True,
                type=btn_type,
            )
            sc = nav_shortcuts.get(opt)
            if sc and _BUTTON_SUPPORTS_SHORTCUT:
                btn_kwargs["shortcut"] = sc
            if st.button(opt, **btn_kwargs):
                st.session_state["nav_selected"] = opt
                st.rerun()

    return st.session_state["nav_selected"]


# --------------------------------- MAIN ----------------------------------- #

# Mapeia chaves de query string (?nav=...) e accesskeys para os labels usados
# pelo sidebar nav. As chaves curtas batem com os accesskeys (Alt+M / Alt+C / etc).
NAV_QUERY_MAP = {
    "dashboard":  "Dashboard",
    "motor":      "Motor v3",
    "sugestoes":  "Sugestões",
    "mix":        "Mix & Kits",
    "cenarios":   "Cenários",
    "exportacao": "Exportação",
}


def _aplicar_query_nav():
    """Aplica deep-link `?nav=...` ao `nav_selected` e remove o param
    em seguida, para que atalhos repetidos (M, M, M) sempre disparem."""
    try:
        qp = st.query_params
        nav_val = qp.get("nav", None)
    except Exception:
        return
    if not nav_val:
        return
    if isinstance(nav_val, list):
        nav_val = nav_val[0] if nav_val else None
    if not nav_val:
        return
    nav_val = str(nav_val).lower()
    label = NAV_QUERY_MAP.get(nav_val)
    if label:
        st.session_state["nav_selected"] = label
        # Limpa o param para que o próximo atalho do mesmo destino
        # também seja processado (idempotente em uma única passada).
        try:
            del st.query_params["nav"]
        except Exception:
            pass


def _render_hidden_kbd_buttons(usuario: Usuario):
    """Renderiza 4 botões Streamlit invisíveis (`_kbd_<destino>`) que
    o handler JS aciona via .click() para trocar de tela SEM recarregar
    a página — preservando a sessão e o `st.session_state['usuario']`.

    Cada botão é envolvido por uma div com classe .st-key-_kbd_<destino>
    (gerada automaticamente pelo Streamlit a partir do `key=`), o que
    serve de selector estável tanto para o CSS de ocultação quanto para
    o JS encontrar o nó correto."""
    target_to_label = {
        "dashboard":  "Dashboard",
        "motor":      "Motor v3",
        "sugestoes":  "Sugestões",
        "mix":        "Mix & Kits",
        "cenarios":   "Cenários",
        "exportacao": "Exportação",
    }
    # Filtra apenas destinos a que o usuário tem acesso (evita
    # navegar para uma tela bloqueada via teclado). "Sugestões" e
    # "Mix & Kits" são visíveis a todos os perfis e por isso nunca
    # são removidos.
    if not (pode(usuario, "motor") or usuario.perfil == "ADMIN"):
        target_to_label.pop("motor", None)
    if usuario.perfil != "ADMIN":
        target_to_label.pop("cenarios", None)
    if not (pode(usuario, "exportacao") or usuario.perfil == "ADMIN"):
        target_to_label.pop("exportacao", None)

    with st.container(key="domme-kbd-buttons"):
        for target, label in target_to_label.items():
            if st.button(" ", key=f"_kbd_{target}", help=f"Atalho: {target}"):
                st.session_state["nav_selected"] = label
                st.rerun()


def _inject_nav_keyboard_handler():
    """Atalhos de teclado M / C / E / D para navegação rápida.

    Use letras simples (sem modificador). O handler ignora keypresses
    quando o usuário está digitando em campos input/textarea/contentEditable,
    e dispara um .click() programático no botão Streamlit oculto
    correspondente (renderizado por _render_hidden_kbd_buttons), o que
    aciona um rerun nativo SEM recarregar a página e SEM perder
    `st.session_state` (incluindo o login do usuário)."""
    components.html(
        """
<script>
(function () {
  const map = {
    "m": "motor",
    "g": "sugestoes",
    "k": "mix",
    "c": "cenarios",
    "e": "exportacao",
    "d": "dashboard"
  };
  const win = window.parent;
  if (!win || !win.document) return;
  const doc = win.document;
  if (doc.__dommeNavHandlerAttached) return;
  doc.__dommeNavHandlerAttached = true;
  function isTyping(el) {
    if (!el) return false;
    const t = (el.tagName || "").toLowerCase();
    if (t === "input" || t === "textarea" || t === "select") return true;
    if (el.isContentEditable) return true;
    return false;
  }
  doc.addEventListener("keydown", function (e) {
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    if (isTyping(doc.activeElement)) return;
    const k = (e.key || "").toLowerCase();
    const target = map[k];
    if (!target) return;
    // Localiza o botão Streamlit oculto pelo container key gerado
    // automaticamente: st.button(key="_kbd_motor") → .st-key-_kbd_motor.
    const wrap = doc.querySelector(".st-key-_kbd_" + target);
    if (!wrap) return;
    const btn = wrap.querySelector("button");
    if (!btn) return;
    e.preventDefault();
    btn.click();
  });
})();
</script>
""",
        height=0,
    )


def _render_keyboard_shortcuts_and_mobile_nav(usuario: Usuario):
    """Bottom-nav fixo (visível só em ≤768px via CSS) usando st.button
    nativos com ícones Material — sem reload de iframe, sem perda de login.

    Cada item: (key, icon Material, tag curta exibida, rótulo canônico
    usado por nav_selected/roteamento).
    """
    items: list[tuple[str, str, str, str]] = [
        ("dashboard", ":material/dashboard:", "Início", "Dashboard"),
    ]
    if pode(usuario, "motor") or usuario.perfil == "ADMIN":
        items.append(("motor", ":material/precision_manufacturing:", "Motor", "Motor v3"))
    items.append(("sugestoes", ":material/lightbulb:", "Ideias", "Sugestões"))
    items.append(("mix", ":material/widgets:", "Mix", "Mix & Kits"))
    if usuario.perfil == "ADMIN":
        items.append(("cenarios", ":material/insights:", "Cenários", "Cenários"))
    if pode(usuario, "exportacao") or usuario.perfil == "ADMIN":
        items.append(("exportacao", ":material/public:", "Export", "Exportação"))

    nav_atual = st.session_state.get("nav_selected", "")

    with st.container(key="domme-mobile-botnav"):
        cols = st.columns(len(items))
        for col, (key, icon, tag, label) in zip(cols, items):
            with col:
                ativo = nav_atual == label
                if st.button(
                    tag,
                    key=f"botnav_{key}",
                    icon=icon,
                    use_container_width=True,
                    type="primary" if ativo else "secondary",
                ):
                    if not ativo:
                        st.session_state["nav_selected"] = label
                        st.rerun()


def main():
    aplicar_estilos()

    if "usuario" not in st.session_state:
        tela_login()
        render_footer()
        return

    usuario: Usuario = st.session_state["usuario"]

    # Aplica navegação vinda de ?nav=... (atalhos de teclado e bottom-nav)
    # ANTES de renderizar a sidebar, para que o item correto fique destacado.
    _aplicar_query_nav()

    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-mini-logo">DOMME</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-mini-tag">White Label · Hub</div>', unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center; font-size:0.85rem;'>{usuario.nome}</div>",
                    unsafe_allow_html=True)
        st.markdown(
            f"<div style='text-align:center; font-size:0.7rem; letter-spacing:1.5px; "
            f"text-transform:uppercase; color:#6B6256;'>{usuario.perfil} · {usuario.empresa}</div>",
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        escolha = _sidebar_nav(usuario)

        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        if st.button("Sair", key="nav_sair", use_container_width=True):
            st.session_state.pop("usuario", None)
            st.rerun()

    # Roteamento (rótulos canônicos sem emoji — ícones vão no botão)
    if escolha == "Dashboard":
        tela_dashboard(usuario)
    elif escolha == "Motor v3":
        tela_motor(usuario)
    elif escolha == "Sugestões":
        tela_sugestoes(usuario)
    elif escolha == "Mix & Kits":
        tela_mix(usuario)
    elif escolha == "Cenários":
        tela_cenarios(usuario)
    elif escolha == "Exportação":
        tela_exportacao(usuario)
    elif escolha == "Catálogo Laszlo":
        tela_catalogo(usuario)
    elif escolha == "Base MP":
        tela_base_mp(usuario)
    elif escolha == "Check Retirada":
        tela_retirada(usuario)
    elif escolha == "Visão Caixa DOMME":
        tela_visao_caixa(usuario)
    elif escolha == "Parâmetros":
        tela_parametros(usuario)
    elif escolha == "Regras":
        tela_regras(usuario)

    # Atalhos de teclado (M / C / E / D) — botões ocultos + handler JS,
    # bottom-nav mobile e contagem progressiva no final do body.
    _render_hidden_kbd_buttons(usuario)
    _inject_nav_keyboard_handler()
    _inject_metric_countup()
    _render_keyboard_shortcuts_and_mobile_nav(usuario)
    render_footer()


if __name__ == "__main__":
    main()
