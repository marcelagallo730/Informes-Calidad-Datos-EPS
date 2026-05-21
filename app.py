import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

import io
import yaml
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

try:
    import tkinter as tk
    from tkinter import filedialog as _fd
    _TKINTER_OK = True
except ImportError:
    _TKINTER_OK = False

from src.loader import cargar_datos, NOMBRES_DISPLAY
from src.calidad_dama.indicador import calcular_indicadores, DIMENSIONES
from src.calidad_dama.detalle import (
    detalle_por_columna, generar_recomendaciones,
    UMBRAL_OPTIMO, UMBRAL_ACEPTABLE,
)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# PAGE CONFIG
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.set_page_config(
    page_title="Calidad de Datos · DAMA-DMBOK2",
    page_icon="ðŸ“Š",
    layout="wide",
    initial_sidebar_state="expanded",
)

CONFIG_DIR = Path(__file__).parent / "config"
RUTA_COLS   = CONFIG_DIR / "columnas_relevantes.yaml"
RUTA_PESOS  = CONFIG_DIR / "pesos_dama.yaml"
RUTA_REGLAS = CONFIG_DIR / "reglas_validez.yaml"
RUTA_DATOS_DEFAULT = r"C:\Users\Usuario\Documents\Claude\Análisis Calidad Completo"

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# DESIGN TOKENS  (match the HTML reports exactly)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
BG       = "#0f1117"
SURFACE  = "#1a1d27"
SURFACE2 = "#22263a"
BORDER   = "#2e3250"
ACCENT   = "#5b7cfa"
ACCENT2  = "#7c5bfa"
GOOD     = "#22c55e"
WARN     = "#f59e0b"
BAD      = "#ef4444"
INFO     = "#38bdf8"
TEXT     = "#e2e8f0"
TEXT2    = "#94a3b8"
TEXT3    = "#64748b"

DIM_ICONS = {
    "Completitud": "âœ…", "Unicidad": "ðŸ”‘", "Validez": "âœ”ï¸",
    "Exactitud": "ðŸŽ¯",  "Oportunidad": "â±ï¸", "Consistencia": "ðŸ”„", "Integridad": "ðŸ”—",
}
DIM_DESCS = {
    "Completitud":  "Registros sin nulos ni vacíos",
    "Unicidad":     "Ausencia de duplicados en clave primaria",
    "Validez":      "Cumplimiento de formatos y dominios",
    "Exactitud":    "Coherencia lógica entre campos",
    "Oportunidad":  "Frescura temporal de los datos",
    "Consistencia": "Coherencia de códigos entre archivos",
    "Integridad":   "Integridad referencial entre fuentes",
}

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# GLOBAL CSS  (dark theme matching the HTML reports)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CSS_GLOBAL = f"""
<style>
/* â”€â”€ Tokens â”€â”€ */
:root {{
  --bg:{BG}; --surface:{SURFACE}; --surface2:{SURFACE2}; --border:{BORDER};
  --accent:{ACCENT}; --accent2:{ACCENT2};
  --good:{GOOD}; --warn:{WARN}; --bad:{BAD}; --info:{INFO};
  --text:{TEXT}; --text2:{TEXT2}; --text3:{TEXT3};
  --radius:12px; --radius-sm:7px;
}}

/* â”€â”€ Streamlit overrides â”€â”€ */
.stApp,[data-testid="stAppViewContainer"],.main {{
  background:{BG} !important;
}}
.main .block-container {{
  background:{BG} !important;
  max-width:1400px !important;
  padding:0 2rem 2rem !important;
}}
section[data-testid="stSidebar"] {{
  background:#12152b !important;
  border-right:1px solid {BORDER} !important;
}}
section[data-testid="stSidebar"] * {{ color:{TEXT} !important; }}
section[data-testid="stSidebar"] .stTextInput input {{
  background:{SURFACE} !important;
  border:1px solid {BORDER} !important;
  color:{TEXT} !important;
  border-radius:8px !important;
}}
section[data-testid="stSidebar"] .stButton>button {{
  background:{ACCENT} !important;
  color:#fff !important;
  border:none !important;
  border-radius:8px !important;
  width:100% !important;
  font-weight:700 !important;
}}
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] {{
  background:{SURFACE} !important;
  border:1px solid {BORDER} !important;
}}

/* â”€â”€ Tabs â”€â”€ */
.stTabs [data-baseweb="tab-list"] {{
  background:{SURFACE} !important;
  border:1px solid {BORDER} !important;
  border-radius:10px !important;
  gap:0 !important;
  padding:4px !important;
}}
.stTabs [data-baseweb="tab"] {{
  background:transparent !important;
  color:{TEXT3} !important;
  font-size:12px !important;
  font-weight:700 !important;
  text-transform:uppercase !important;
  letter-spacing:1px !important;
  border-radius:8px !important;
  padding:8px 18px !important;
}}
.stTabs [aria-selected="true"] {{
  background:rgba(91,124,250,.15) !important;
  color:{ACCENT} !important;
}}
.stTabs [data-baseweb="tab-border"] {{ display:none !important; }}
.stTabs [data-baseweb="tab-panel"] {{ padding-top:24px !important; }}

/* â”€â”€ Expanders â”€â”€ */
[data-testid="stExpander"] {{
  background:{SURFACE} !important;
  border:1px solid {BORDER} !important;
  border-radius:var(--radius) !important;
  margin-bottom:8px !important;
}}
[data-testid="stExpander"] summary {{
  color:{TEXT} !important;
  font-weight:600 !important;
  font-size:13px !important;
}}
[data-testid="stExpander"] summary:hover {{ background:rgba(91,124,250,.05) !important; }}

/* â”€â”€ Radio â”€â”€ */
.stRadio label {{ color:{TEXT2} !important; font-size:13px !important; }}
.stRadio [data-testid="stRadioLabel"] {{ color:{TEXT} !important; }}

/* â”€â”€ Spinner â”€â”€ */
.stSpinner > div {{ border-top-color:{ACCENT} !important; }}

/* â”€â”€ Divider â”€â”€ */
hr {{ border-color:{BORDER} !important; }}

/* â”€â”€ Scrollbar â”€â”€ */
::-webkit-scrollbar {{ width:6px; height:6px; }}
::-webkit-scrollbar-track {{ background:{BG}; }}
::-webkit-scrollbar-thumb {{ background:{BORDER}; border-radius:3px; }}
::-webkit-scrollbar-thumb:hover {{ background:{ACCENT}; }}

/* â”€â”€ Hide Streamlit chrome â”€â”€ */
#MainMenu,footer {{ display:none !important; }}
[data-testid="stHeader"] {{ visibility:hidden !important; height:0 !important; min-height:0 !important; }}

/* â”€â”€ Sidebar: always keep it in the DOM, override Streamlit's transform collapse â”€â”€ */
section[data-testid="stSidebar"] {{
  transform: none !important;
  min-width: 21rem !important;
  width: 21rem !important;
  transition: min-width .3s ease, width .3s ease !important;
  overflow: hidden !important;
}}
/* When our JS hides it, collapse the width to 0 */
section[data-testid="stSidebar"].dq-sb-hidden {{
  min-width: 0 !important;
  width: 0 !important;
  padding: 0 !important;
  border: none !important;
}}
/* Kill Streamlit's native toggle (ours replaces it) */
[data-testid="collapsedControl"] {{ display:none !important; }}

/* â”€â”€ Space so content never hides under the floating toggle â”€â”€ */
.main .block-container {{ padding-top:56px !important; }}

/* â”€â”€ Custom report components â”€â”€ */
.rpt-header {{
  background:linear-gradient(135deg,#1e2240 0%,#12152b 100%);
  border-bottom:1px solid {BORDER};
  padding:32px 40px 24px;
  border-radius:var(--radius) var(--radius) 0 0;
  margin-bottom:0;
}}
.badge-file {{
  display:inline-flex;align-items:center;gap:8px;
  background:rgba(91,124,250,.15);border:1px solid rgba(91,124,250,.35);
  color:{ACCENT};border-radius:20px;padding:4px 14px;font-size:12px;
  margin-bottom:12px;font-weight:600;letter-spacing:.5px;
}}
.rpt-h1 {{ font-size:24px;font-weight:700;color:#fff;line-height:1.25;margin-bottom:6px; }}
.rpt-desc {{ color:{TEXT2};font-size:13px;max-width:700px; }}
.header-meta {{ display:flex;gap:28px;flex-wrap:wrap;margin-top:18px; }}
.meta-item {{ display:flex;flex-direction:column; }}
.meta-label {{ font-size:10px;text-transform:uppercase;letter-spacing:1px;color:{TEXT3};margin-bottom:2px; }}
.meta-value {{ font-size:14px;font-weight:600;color:{TEXT}; }}

.section-title {{
  font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:1.2px;
  color:{ACCENT};margin:32px 0 14px;
  display:flex;align-items:center;gap:10px;
}}
.section-title::after {{ content:'';flex:1;height:1px;background:{BORDER}; }}

.kpi-grid {{ display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin-bottom:6px; }}
.kpi-card {{
  background:{SURFACE};border:1px solid {BORDER};border-radius:var(--radius);
  padding:18px 20px;position:relative;overflow:hidden;
}}
.kpi-card::before {{
  content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:var(--kpi-color,{ACCENT});
}}
.kpi-label {{ font-size:11px;color:{TEXT3};text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px; }}
.kpi-value {{ font-size:26px;font-weight:800;color:var(--kpi-color,{TEXT});line-height:1; }}
.kpi-sub   {{ font-size:11px;color:{TEXT3};margin-top:4px; }}

.dim-grid {{ display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:12px;margin-bottom:8px; }}
.dim-card {{
  background:{SURFACE};border:1px solid {BORDER};border-radius:var(--radius);padding:16px 18px;
}}
.dim-name {{ font-size:12px;font-weight:600;color:{TEXT};margin-bottom:10px;display:flex;align-items:center;gap:6px; }}
.dim-score {{ font-size:24px;font-weight:800;margin-bottom:6px; }}
.dim-bar-wrap {{ background:{SURFACE2};border-radius:6px;height:7px;overflow:hidden;margin-bottom:4px; }}
.dim-bar {{ height:100%;border-radius:6px; }}
.dim-bar2 {{ height:4px;border-radius:4px;opacity:.5;margin-top:2px; }}
.dim-sub {{ font-size:10.5px;color:{TEXT3};margin-top:5px; }}

.status {{
  display:inline-block;font-size:10px;font-weight:700;letter-spacing:.6px;
  padding:2px 9px;border-radius:20px;text-transform:uppercase;white-space:nowrap;
}}
.status-good {{ background:rgba(34,197,94,.15);color:{GOOD};border:1px solid rgba(34,197,94,.3); }}
.status-warn {{ background:rgba(245,158,11,.15);color:{WARN};border:1px solid rgba(245,158,11,.3); }}
.status-bad  {{ background:rgba(239,68,68,.15); color:{BAD}; border:1px solid rgba(239,68,68,.3);  }}
.status-info {{ background:rgba(56,189,248,.15);color:{INFO};border:1px solid rgba(56,189,248,.3); }}

.tbl-wrap {{ overflow-x:auto;border-radius:var(--radius);border:1px solid {BORDER}; }}
table {{ width:100%;border-collapse:collapse;font-size:12.5px; }}
thead tr {{ background:{SURFACE2}; }}
th {{
  padding:11px 14px;text-align:left;font-size:10.5px;text-transform:uppercase;
  letter-spacing:.8px;color:{TEXT3};white-space:nowrap;border-bottom:1px solid {BORDER};
  position:sticky;top:0;background:{SURFACE2};
}}
td {{ padding:10px 14px;border-bottom:1px solid rgba(46,50,80,.45);color:{TEXT};vertical-align:middle; }}
tr:last-child td {{ border-bottom:none; }}
tr:hover td {{ background:rgba(91,124,250,.04); }}
.col-name {{ font-weight:600;color:#fff;min-width:150px; }}
.col-type {{ color:{TEXT3};font-size:11px;font-family:monospace; }}
.col-rel  {{ color:{ACCENT};font-weight:800; }}

.mini-bar-wrap {{ display:flex;align-items:center;gap:8px;min-width:110px; }}
.mini-bar-bg   {{ flex:1;background:{SURFACE2};border-radius:4px;height:6px;overflow:hidden;min-width:50px; }}
.mini-bar-fill {{ height:100%;border-radius:4px; }}
.mini-pct      {{ font-size:11.5px;font-weight:700;min-width:38px;text-align:right; }}
.bg-good {{ background:{GOOD}; }}
.bg-warn {{ background:{WARN}; }}
.bg-bad  {{ background:{BAD};  }}
.bg-info {{ background:{INFO}; }}
.c-good {{ color:{GOOD}; }}
.c-warn {{ color:{WARN}; }}
.c-bad  {{ color:{BAD};  }}
.c-info {{ color:{INFO}; }}

.issues-grid {{ display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px; }}
.issue-card {{
  background:{SURFACE};border:1px solid {BORDER};border-radius:var(--radius);
  padding:16px 18px;border-left:4px solid var(--issue-color,{WARN});
}}
.issue-tag   {{ font-size:10px;text-transform:uppercase;letter-spacing:.6px;color:{TEXT3};margin-bottom:5px; }}
.issue-title {{ font-weight:700;font-size:13px;margin-bottom:5px; }}
.issue-body  {{ font-size:12px;color:{TEXT2};line-height:1.6; }}

.reco-list {{ list-style:none;display:flex;flex-direction:column;gap:9px; }}
.reco-item {{
  background:{SURFACE};border:1px solid {BORDER};border-radius:var(--radius-sm);
  padding:13px 16px;display:flex;gap:13px;align-items:flex-start;
}}
.reco-num {{
  min-width:26px;height:26px;border-radius:50%;
  background:linear-gradient(135deg,{ACCENT},{ACCENT2});
  display:flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:800;color:#fff;flex-shrink:0;
}}
.reco-text {{ font-size:12.5px;color:{TEXT2};line-height:1.6; }}
.reco-text strong {{ color:{TEXT}; }}

.rpt-footer {{
  border-top:1px solid {BORDER};padding:18px 40px;
  display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;
  font-size:11.5px;color:{TEXT3};background:{SURFACE};
  border-radius:0 0 var(--radius) var(--radius);margin-top:0;
}}
.footer-logo {{ font-weight:800;font-size:13px;color:{ACCENT}; }}
</style>
"""

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# HELPERS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _sc(s: float) -> str:
    return GOOD if s >= UMBRAL_OPTIMO else WARN if s >= UMBRAL_ACEPTABLE else BAD

def _st(s: float) -> str:
    return "Óptimo" if s >= UMBRAL_OPTIMO else "Aceptable" if s >= UMBRAL_ACEPTABLE else "Crítico"

def _st_class(s: float) -> str:
    return "status-good" if s >= UMBRAL_OPTIMO else "status-warn" if s >= UMBRAL_ACEPTABLE else "status-bad"

def _mini_bar(pct: float) -> str:
    cls = "bg-good" if pct >= UMBRAL_OPTIMO else "bg-warn" if pct >= UMBRAL_ACEPTABLE else "bg-bad"
    txt = "c-good" if pct >= UMBRAL_OPTIMO else "c-warn" if pct >= UMBRAL_ACEPTABLE else "c-bad"
    return (f'<div class="mini-bar-wrap">'
            f'<div class="mini-bar-bg"><div class="mini-bar-fill {cls}" style="width:{min(pct,100):.1f}%"></div></div>'
            f'<span class="mini-pct {txt}">{pct:.1f}%</span></div>')

def _status(label: str, tipo: str) -> str:
    return f'<span class="status status-{tipo}">{label}</span>'

def _html_section_title(icon: str, text: str) -> str:
    return f'<div class="section-title">{icon} {text}</div>'

def _html_kpi_grid(kpis: list[tuple]) -> str:
    cards = ""
    for label, value, sub, color in kpis:
        cards += f"""<div class="kpi-card" style="--kpi-color:{color}">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value" style="color:{color}">{value}</div>
          <div class="kpi-sub">{sub}</div>
        </div>"""
    return f'<div class="kpi-grid">{cards}</div>'

def _html_dim_grid(scores_g: dict, scores_f: dict) -> str:
    cards = ""
    for dim in DIMENSIONES:
        sg = scores_g.get(dim, 0)
        sf = scores_f.get(dim, 0)
        color = _sc(sg)
        estado = _st(sg)
        icon = DIM_ICONS.get(dim, "")
        desc = DIM_DESCS.get(dim, "")
        cards += f"""<div class="dim-card">
          <div class="dim-name">{icon} {dim}</div>
          <div class="dim-score" style="color:{color}">{sg:.1f}%</div>
          <div class="dim-bar-wrap"><div class="dim-bar" style="width:{sg:.1f}%;background:{color}"></div></div>
          <div class="dim-bar-wrap" style="height:4px;margin-top:3px">
            <div class="dim-bar" style="width:{sf:.1f}%;background:{color};opacity:.45"></div>
          </div>
          <div class="dim-sub">{desc}</div>
          <div style="margin-top:8px">{_status(estado, _st_class(sg))}</div>
        </div>"""
    return f'<div class="dim-grid">{cards}</div>'

def _hallazgo(col: str, comp: float, nulos: int, uniques: int, n: int,
              reglas: dict, valid_pct: float | None) -> str:
    parts = []
    if comp >= 100:
        parts.append("Sin registros nulos.")
    elif comp >= 95:
        parts.append(f"{nulos:,} nulos ({100-comp:.1f}%).")
    elif comp >= UMBRAL_OPTIMO:
        parts.append(f"{nulos:,} nulos ({100-comp:.1f}%). Revisar fuente de captura.")
    elif comp >= UMBRAL_ACEPTABLE:
        parts.append(f"ðŸŸ¡ {nulos:,} nulos ({100-comp:.1f}%). Afecta análisis.")
    else:
        parts.append(f"ðŸ”´ {100-comp:.1f}% de nulos â€” campo con cobertura insuficiente ({nulos:,} registros).")

    if uniques == 1:
        parts.append("Columna constante: un único valor en todo el dataset.")
    elif uniques <= 5:
        parts.append(f"Dominio reducido: {uniques} valores únicos.")
    elif uniques > 0 and (uniques / n) > 0.85:
        parts.append(f"Alta cardinalidad: {uniques:,} valores únicos.")
    else:
        parts.append(f"{uniques:,} valores únicos.")

    if valid_pct is not None:
        if valid_pct < UMBRAL_ACEPTABLE:
            parts.append(f"âš ï¸ Validez crítica ({valid_pct:.1f}%) â€” muchos valores fuera del dominio.")
        elif valid_pct < UMBRAL_OPTIMO:
            parts.append(f"Validez moderada ({valid_pct:.1f}%).")

    return " ".join(parts)

def _html_col_table(df: pd.DataFrame, reglas: dict, cols_rel: list[str],
                    filtro: str = "Todas") -> str:
    n = len(df)
    if n == 0:
        return "<p style='color:#64748b'>Sin datos</p>"

    rows = ""
    for i, col in enumerate(df.columns, 1):
        comp_c = (df[col].notna() & (df[col].astype(str).str.strip() != "")).sum()
        comp   = comp_c / n * 100
        nulos  = n - comp_c
        uniq   = df[col].nunique()
        dtype  = str(df[col].dtype)
        is_rel = col in cols_rel

        # Validez
        valid_pct: float | None = None
        valid_label, valid_tipo = "No Aplica", "info"
        if col in reglas:
            r = reglas[col]
            s = df[col]
            t = r.get("tipo")
            if t == "regex":
                v = s.dropna().astype(str).str.match(r["patron"]).sum() / n * 100
            elif t == "dominio":
                v = s.isin(r["valores"]).sum() / n * 100
            elif t == "numerico":
                m = pd.to_numeric(s, errors="coerce").notna()
                if "min" in r: m &= pd.to_numeric(s, errors="coerce") >= r["min"]
                v = m.sum() / n * 100
            elif t in ("fecha", "fecha_yyyymmdd"):
                fmt = "%Y%m%d" if t == "fecha_yyyymmdd" else None
                p = pd.to_datetime(s, format=fmt, errors="coerce") if fmt else pd.to_datetime(s, errors="coerce", dayfirst=True)
                v = p.notna().sum() / n * 100
            else:
                v = None
            if v is not None:
                valid_pct = v
                valid_label = "Alta" if v >= UMBRAL_OPTIMO else "Media" if v >= UMBRAL_ACEPTABLE else "Baja"
                valid_tipo  = "good" if v >= UMBRAL_OPTIMO else "warn" if v >= UMBRAL_ACEPTABLE else "bad"

        # Score y estado
        score = (comp + valid_pct) / 2 if valid_pct is not None else comp
        estado_label = _st(score)
        estado_tipo  = _st_class(score)

        # Filtro
        if filtro == "Solo relevantes" and not is_rel:
            continue
        if filtro == "Solo críticas" and estado_label != "Crítico":
            continue

        # Marcador de relevante
        rel_mark = '<span class="col-rel">â˜…</span> ' if is_rel else ""
        hallazgo = _hallazgo(col, comp, nulos, uniq, n, reglas, valid_pct)

        rows += f"""<tr>
          <td style="color:{TEXT3}">{i}</td>
          <td class="col-name">{rel_mark}{col}</td>
          <td class="col-type">{dtype}</td>
          <td>{_mini_bar(comp)}</td>
          <td style="color:{TEXT2}">{nulos:,}</td>
          <td style="color:{TEXT3};font-size:11px">{uniq:,} únicos</td>
          <td>{_status(valid_label, valid_tipo)}</td>
          <td style="font-size:11.5px;color:{TEXT2};max-width:280px">{hallazgo}</td>
          <td>{_status(estado_label, estado_tipo)}</td>
        </tr>"""

    if not rows:
        return f"<p style='color:{TEXT3};padding:16px'>Sin resultados para el filtro seleccionado.</p>"

    return f"""<div class="tbl-wrap"><table>
      <thead><tr>
        <th>#</th><th>Columna</th><th>Tipo</th><th>Completitud</th>
        <th>Nulos</th><th>Unicidad</th><th>Validez</th><th>Hallazgos clave</th><th>Estado</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table></div>"""

def _html_issues(recos: list[dict]) -> str:
    if not recos:
        return f"<p style='color:{GOOD};font-size:13px'>âœ… Sin hallazgos críticos en variables relevantes.</p>"
    cards = ""
    for r in recos:
        color = BAD if r["nivel"] == "Crítico" else WARN
        cards += f"""<div class="issue-card" style="--issue-color:{color}">
          <div class="issue-tag">{r['dimension']} · {r['nivel']}</div>
          <div class="issue-title" style="color:{color}">{r['variable']}</div>
          <div class="issue-body">Score: {r['score']:.1f}% â€” {r['acciones'][0] if r['acciones'] else ''}</div>
        </div>"""
    return f'<div class="issues-grid">{cards}</div>'

def _html_reco_list(recos: list[dict]) -> str:
    if not recos:
        return f"<p style='color:{GOOD};font-size:13px'>âœ… No se generaron recomendaciones para las variables relevantes.</p>"
    items = ""
    idx = 1
    for r in recos:
        color = BAD if r["nivel"] == "Crítico" else WARN
        acciones_html = "".join(
            f'<li style="border-left:3px solid {color};padding-left:10px;margin:6px 0;'
            f'font-size:12px;color:{TEXT2}">{a}</li>'
            for a in r["acciones"]
        )
        items += f"""<li class="reco-item">
          <div class="reco-num" style="background:linear-gradient(135deg,{color},{color}bb)">{idx}</div>
          <div class="reco-text">
            <strong>{r['variable']}</strong> ·
            <span style="color:{color};font-weight:700">{r['dimension']} ({r['nivel']} â€” {r['score']:.1f}%)</span>
            <ul style="margin:8px 0 0;padding:0;list-style:none">{acciones_html}</ul>
          </div>
        </li>"""
        idx += 1
    return f'<ul class="reco-list">{items}</ul>'

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# YAML helpers
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _load_yaml(p: Path) -> dict:
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {} if p.exists() else {}

def _save_yaml(p: Path, data: dict):
    p.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False), encoding="utf-8")

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# DATA LOADING
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@st.cache_data(show_spinner=False)
def _cargar(ruta: str) -> dict[str, pd.DataFrame]:
    return cargar_datos(ruta)

def _pick_folder() -> str:
    """Open a native Windows folder-picker dialog and return the selected path."""
    if not _TKINTER_OK:
        return ""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    folder = _fd.askdirectory(title="Seleccionar carpeta con archivos CSV")
    root.destroy()
    return folder or ""

def _cargar_desde_uploads(archivos) -> dict[str, pd.DataFrame]:
    """Load dataframes from st.file_uploader objects using flexible name matching."""
    from src.loader import _limpiar_numericos  # reuse numeric cleaner

    PATRONES = [
        ("liberar",       "liberar_formula"),
        ("formula",       "liberar_formula"),
        ("direccion",     "direccionamientos"),
        ("consultar",     "consultar_cedula"),
        ("cedula",        "consultar_cedula"),
        ("capital",       "capital_salud"),
        ("medicamento",   "capital_salud"),
    ]
    COLS_NUM = {
        "liberar_formula":  ["CantidadDireccionada", "CantidadEntregada", "Valor"],
        "direccionamientos": ["pago_final", "CantidadDosis", "Duracion"],
        "consultar_cedula":  ["pago_final", "CantidadDosis", "Duracion"],
        "capital_salud":     ["CantidadMedicamento", "CuotaModeradora"],
    }

    result: dict[str, pd.DataFrame] = {}
    for f in archivos:
        fname = f.name.lower()
        clave = next((k for p, k in PATRONES if p in fname), None)
        if clave is None:
            continue

        raw = f.read()
        contenido = None
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                contenido = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if contenido is None:
            continue

        primera = contenido.split("\n")[0]
        sep = ";" if primera.count(";") > primera.count(",") else ","
        df = pd.read_csv(io.StringIO(contenido), sep=sep, dtype=str, low_memory=False)
        df.columns = df.columns.str.strip()
        df = _limpiar_numericos(df, COLS_NUM.get(clave, []))
        result[clave] = df
        f.seek(0)  # reset pointer for potential re-reads

    return result

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# INJECT CSS (once)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# FLOATING SIDEBAR TOGGLE  (JS injected into parent document)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_TOGGLE_JS = """
<script>
(function() {
  var D = window.parent.document;
  var OPEN  = true;   // track state locally

  /* â”€â”€ Force sidebar open: override inline transforms Streamlit may have set â”€â”€ */
  function forceOpen() {
    var sb = D.querySelector('section[data-testid="stSidebar"]');
    if (!sb) return;
    sb.style.setProperty('transform',  'none',  'important');
    sb.style.setProperty('min-width',  '21rem', 'important');
    sb.style.setProperty('width',      '21rem', 'important');
    sb.style.setProperty('overflow',   'hidden','important');
    sb.classList.remove('dq-sb-hidden');
    OPEN = true;
  }

  /* â”€â”€ Toggle â”€â”€ */
  function toggleSidebar() {
    var sb = D.querySelector('section[data-testid="stSidebar"]');
    if (!sb) return;
    if (OPEN) {
      sb.style.setProperty('min-width', '0', 'important');
      sb.style.setProperty('width',     '0', 'important');
      sb.classList.add('dq-sb-hidden');
      OPEN = false;
    } else {
      forceOpen();
    }
  }

  /* â”€â”€ Floating â˜° button â”€â”€ */
  function ensureBtn() {
    if (D.getElementById('dq-menu-btn')) return;
    var b = D.createElement('button');
    b.id = 'dq-menu-btn';
    b.innerHTML = '&#9776;';
    b.title = 'Mostrar / Ocultar menú';
    b.style.cssText =
      'position:fixed;top:14px;left:14px;z-index:2147483647;' +
      'background:#1a1d27;border:1px solid #2e3250;border-radius:8px;' +
      'padding:7px 14px;cursor:pointer;color:#5b7cfa;font-size:18px;' +
      'font-weight:bold;line-height:1;' +
      'box-shadow:0 2px 12px rgba(0,0,0,.55);transition:background .2s,border-color .2s;';
    b.addEventListener('mouseover', function(){
      this.style.background = 'rgba(91,124,250,.18)';
      this.style.borderColor = '#5b7cfa';
    });
    b.addEventListener('mouseout', function(){
      this.style.background  = '#1a1d27';
      this.style.borderColor = '#2e3250';
    });
    b.addEventListener('click', toggleSidebar);
    D.body.appendChild(b);
  }

  /* Run immediately and after Streamlit re-renders */
  ensureBtn();
  forceOpen();
  setTimeout(function(){ ensureBtn(); forceOpen(); }, 500);
  setTimeout(function(){ ensureBtn(); forceOpen(); }, 1500);
})();
</script>
"""
components.html(_TOGGLE_JS, height=0)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SIDEBAR
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
with st.sidebar:
    st.markdown(
        f'<div style="font-size:18px;font-weight:800;color:{ACCENT};margin-bottom:2px">ðŸ“Š DataQuality</div>'
        f'<div style="font-size:11px;color:{TEXT3};margin-bottom:16px">DAMA-DMBOK2 · ISO/IEC 25012</div>',
        unsafe_allow_html=True,
    )

    # â”€â”€ Modo de carga â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    modo = st.radio(
        "Fuente de datos",
        ["ðŸ“  Carpeta", "ðŸ“„  Archivos CSV"],
        key="modo_carga",
        horizontal=True,
    )

    st.markdown(f'<div style="height:10px"></div>', unsafe_allow_html=True)

    # â”€â”€ Modo carpeta â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if modo == "ðŸ“  Carpeta":
        if _TKINTER_OK:
            if st.button("ðŸ“‚  Buscar carpetaâ€¦", use_container_width=True):
                carpeta = _pick_folder()
                if carpeta:
                    st.session_state.ruta_seleccionada = carpeta
                    st.session_state.pop("dfs", None)

        ruta_actual = st.session_state.get("ruta_seleccionada", RUTA_DATOS_DEFAULT)
        ruta_input = st.text_input("Ruta de la carpeta", value=ruta_actual, key="ruta_txt")
        if ruta_input != st.session_state.get("ruta_seleccionada"):
            st.session_state.ruta_seleccionada = ruta_input

        if st.button("âŸ³  Cargar / Recargar", type="primary", use_container_width=True,
                     key="btn_cargar_carpeta"):
            st.cache_data.clear()
            st.session_state.pop("dfs", None)
            # no rerun needed â€” load block below runs immediately

    # â”€â”€ Modo archivos CSV â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    else:
        uploads = st.file_uploader(
            "Seleccionar archivos CSV",
            type=["csv"],
            accept_multiple_files=True,
            key="csv_uploads",
            help="Selecciona uno o más CSV (LiberarFormula, Direccionamientos, ConsultarCedula, CapitalSalud)",
        )
        # Detect when a new set of files is uploaded â†’ force reload
        ids_nuevos = tuple(f.file_id for f in (uploads or []))
        if ids_nuevos != st.session_state.get("_upload_ids"):
            st.session_state._upload_ids = ids_nuevos
            st.session_state.pop("dfs", None)

        if uploads:
            for f in uploads:
                st.markdown(
                    f'<div style="font-size:11px;color:{TEXT2};padding:2px 0">ðŸ“„ {f.name}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No hay archivos seleccionados.")

        if st.button("âŸ³  Cargar archivos", type="primary", use_container_width=True,
                     key="btn_cargar_uploads", disabled=not uploads):
            st.session_state.pop("dfs", None)

    # â”€â”€ Carga efectiva de datos â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if "dfs" not in st.session_state:
        with st.spinner("Cargando datosâ€¦"):
            try:
                if modo == "ðŸ“  Carpeta":
                    ruta = st.session_state.get("ruta_seleccionada", RUTA_DATOS_DEFAULT)
                    st.session_state.dfs = _cargar(ruta)
                else:
                    archivos_sel = st.session_state.get("csv_uploads") or []
                    if archivos_sel:
                        st.session_state.dfs = _cargar_desde_uploads(archivos_sel)
                    else:
                        st.session_state.dfs = {}
            except Exception as exc:
                st.error(str(exc))
                st.session_state.dfs = {}

    # â”€â”€ Estado de carga â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    dfs_cargados = st.session_state.get("dfs", {})
    if dfs_cargados:
        n_total = sum(len(d) for d in dfs_cargados.values())
        st.markdown(
            f'<div style="background:{SURFACE};border:1px solid rgba(34,197,94,.3);'
            f'border-radius:8px;padding:10px 14px;margin:10px 0;font-size:12px;color:{GOOD}">'
            f'âœ“ {len(dfs_cargados)} archivo(s) · {n_total:,} registros</div>',
            unsafe_allow_html=True,
        )
    elif st.session_state.get("dfs") is not None:
        st.warning("Sin datos. Selecciona una carpeta o archivos CSV válidos.")

    # â”€â”€ Columnas relevantes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(f'<hr style="border-color:{BORDER};margin:16px 0">', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:11px;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:1px;color:{ACCENT};margin-bottom:8px">Columnas Relevantes</div>',
        unsafe_allow_html=True,
    )
    st.caption("â˜… Determinan el Indicador Relevante (Focalizado).")

    cols_guardadas = _load_yaml(RUTA_COLS)
    columnas_relevantes: dict[str, list[str]] = {}

    if dfs_cargados:
        for clave, df in dfs_cargados.items():
            nombre_display = NOMBRES_DISPLAY.get(clave, clave)
            default = [c for c in cols_guardadas.get(clave, []) if c in df.columns]
            with st.expander(nombre_display, expanded=False):
                sel = st.multiselect(
                    "", options=df.columns.tolist(), default=default,
                    key=f"cols_{clave}", label_visibility="collapsed",
                )
                columnas_relevantes[clave] = sel

        if st.button("ðŸ’¾  Guardar selección", use_container_width=True):
            _save_yaml(RUTA_COLS, columnas_relevantes)
            st.success("Guardado en columnas_relevantes.yaml")

    st.markdown(f'<hr style="border-color:{BORDER};margin:16px 0">', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:10px;color:{TEXT3};text-align:center">'
        f'ISO 25012 · DAMA-DMBOK2 · DCAM<br>Resolución 3512/2019 MSPS Colombia</div>',
        unsafe_allow_html=True,
    )

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# GUARD: need data
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
dfs = st.session_state.get("dfs", {})
if not dfs:
    st.markdown(
        f'<div style="background:{SURFACE};border:1px solid {BORDER};border-radius:var(--radius);'
        f'padding:48px;text-align:center;margin-top:40px">'
        f'<div style="font-size:40px;margin-bottom:16px">ðŸ“‚</div>'
        f'<div style="font-size:18px;font-weight:700;color:{TEXT};margin-bottom:8px">'
        f'Sin datos cargados</div>'
        f'<div style="font-size:13px;color:{TEXT2}">'
        f'Usa el menú lateral para seleccionar una <strong style="color:{ACCENT}">carpeta</strong> '
        f'o subir <strong style="color:{ACCENT}">archivos CSV</strong> directamente.</div></div>',
        unsafe_allow_html=True,
    )
    st.stop()

# dfs already set above (before the guard)
pesos_raw = _load_yaml(RUTA_PESOS)
pesos  = {d: float(pesos_raw.get(d, 1.0)) for d in DIMENSIONES}
reglas = _load_yaml(RUTA_REGLAS)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# INDICADORES DAMA
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
with st.spinner("Calculando indicadores DAMAâ€¦"):
    resultado = calcular_indicadores(dfs, columnas_relevantes, reglas, pesos)

total_g = resultado["global"].get("__total__", {})
total_f = resultado["focalizado"].get("__total__", {})
sg_total = total_g.get("score_total", 0)
sf_total = total_f.get("score_total", 0)
n_regs_total  = sum(len(d) for d in dfs.values())
n_cols_total  = sum(len(d.columns) for d in dfs.values())
n_rel_total   = sum(len(v) for v in columnas_relevantes.values() if v)

# â”€â”€ Encabezado ejecutivo â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.markdown(f"""
<div class="rpt-header">
  <div class="badge-file">ðŸ“Š Informe de Calidad · {len(dfs)} archivos analizados</div>
  <div class="rpt-h1">Informe de Calidad de Datos â€” Audifarma / EPS</div>
  <div class="rpt-desc">Análisis exhaustivo por columna aplicando las dimensiones de calidad
    de la ISO/IEC 25012, DAMA-DMBOK2 y prácticas vigentes de Gobernanza de Datos.</div>
  <div class="header-meta">
    <div class="meta-item">
      <span class="meta-label">Total de registros</span>
      <span class="meta-value">{n_regs_total:,}</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Columnas analizadas</span>
      <span class="meta-value">{n_cols_total}</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Columnas relevantes</span>
      <span class="meta-value">{n_rel_total}</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Fecha de análisis</span>
      <span class="meta-value">{datetime.now().strftime('%d / %m / %Y')}</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Marco de referencia</span>
      <span class="meta-value">ISO 25012 · DAMA-DMBOK2 · DCAM</span>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

# â”€â”€ KPIs globales â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.markdown(_html_section_title("ðŸ“Š", "Indicadores Generales del Dataset"), unsafe_allow_html=True)
st.markdown(_html_kpi_grid([
    ("Indicador General",   f"{sg_total:.1f}%",   "Promedio ponderado DAMA",          _sc(sg_total)),
    ("Indicador Relevante", f"{sf_total:.1f}%",   "Columnas marcadas como relevantes", _sc(sf_total)),
    ("Total Registros",     f"{n_regs_total:,}",  f"{len(dfs)} archivos fuente",       INFO),
    ("Columnas Totales",    str(n_cols_total),     "Todas las variables",               INFO),
    ("Columnas Relevantes", str(n_rel_total),      "Seleccionadas para análisis",       ACCENT),
]), unsafe_allow_html=True)

# â”€â”€ Dimensiones consolidadas â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.markdown(_html_section_title("ðŸ”", "Resumen de Dimensiones DAMA â€” Consolidado"), unsafe_allow_html=True)
st.markdown(_html_dim_grid(total_g, total_f), unsafe_allow_html=True)
st.markdown(f'<div style="font-size:11px;color:{TEXT3};margin-bottom:8px">'
            f'Barra superior = Indicador General · Barra tenue inferior = Indicador Relevante</div>',
            unsafe_allow_html=True)

st.markdown(f'<hr style="border-color:{BORDER};margin:32px 0 0">', unsafe_allow_html=True)

# â”€â”€ Sección por archivo â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
archivos_claves = [k for k in resultado["global"] if not k.startswith("__")]

for idx_a, clave in enumerate(archivos_claves, 1):
    df_arch      = dfs[clave]
    nombre_disp  = NOMBRES_DISPLAY.get(clave, clave)
    cols_sel     = columnas_relevantes.get(clave) or []
    reglas_arch  = reglas.get(clave, {})
    sg_a         = resultado["global"][clave].get("score_total", 0)
    sf_a         = resultado["focalizado"][clave].get("score_total", 0)
    scores_dim_g = resultado["global"][clave]
    scores_dim_f = resultado["focalizado"][clave]
    n_criticas   = sum(1 for c in df_arch.columns
                      if ((df_arch[c].notna() & (df_arch[c].astype(str).str.strip()!="")).sum()
                          / len(df_arch) * 100) < UMBRAL_ACEPTABLE)

    # â”€â”€ Encabezado del archivo â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(f"""
    <div class="rpt-header" style="margin-top:28px;border-radius:var(--radius) var(--radius) 0 0">
      <div class="badge-file">ðŸ“„ Archivo {idx_a} de {len(archivos_claves)}</div>
      <div class="rpt-h1">{nombre_disp}</div>
      <div class="rpt-desc">Análisis de calidad aplicando ISO/IEC 25012 y DAMA-DMBOK2 â€”
        {len(df_arch.columns)} columnas · {len(df_arch):,} registros</div>
      <div class="header-meta">
        <div class="meta-item">
          <span class="meta-label">Indicador General</span>
          <span class="meta-value" style="color:{_sc(sg_a)}">{sg_a:.1f}%</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Indicador Relevante</span>
          <span class="meta-value" style="color:{_sc(sf_a)}">{sf_a:.1f}%</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Total registros</span>
          <span class="meta-value">{len(df_arch):,}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Columnas</span>
          <span class="meta-value">{len(df_arch.columns)}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Columnas relevantes</span>
          <span class="meta-value" style="color:{ACCENT}">{len(cols_sel)}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Columnas críticas</span>
          <span class="meta-value" style="color:{BAD}">{n_criticas}</span>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    # â”€â”€ KPIs del archivo â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(_html_section_title("ðŸ“Š", "Indicadores Generales del Archivo"), unsafe_allow_html=True)
    st.markdown(_html_kpi_grid([
        ("Indicador General",    f"{sg_a:.1f}%",             "Promedio ponderado DAMA",    _sc(sg_a)),
        ("Indicador Relevante",  f"{sf_a:.1f}%",             "Variables relevantes",       _sc(sf_a)),
        ("Total Registros",      f"{len(df_arch):,}",        "Filas en el archivo",        INFO),
        ("Columnas Totales",     str(len(df_arch.columns)),  "Variables analizadas",        INFO),
        ("Columnas Relevantes",  str(len(cols_sel)),         "Marcadas para análisis",     ACCENT),
        ("Columnas Críticas",    str(n_criticas),            "Completitud < 70%",          BAD),
    ]), unsafe_allow_html=True)

    # â”€â”€ Dimensiones del archivo â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(_html_section_title("ðŸ”", "Resumen de Dimensiones DAMA"), unsafe_allow_html=True)
    st.markdown(_html_dim_grid(scores_dim_g, scores_dim_f), unsafe_allow_html=True)

    # â”€â”€ Tabla de columnas â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(_html_section_title("ðŸ“‹", "Análisis Detallado por Columna (ISO 25012 / DAMA-DMBOK2)"),
                unsafe_allow_html=True)

    with st.expander(f"Ver tabla de {len(df_arch.columns)} columnas â€” {nombre_disp}", expanded=True):
        filtro = st.radio(
            "Mostrar",
            ["Todas", "Solo relevantes", "Solo críticas"],
            horizontal=True, key=f"filtro_{clave}",
        )
        with st.spinner("Generando tablaâ€¦"):
            tabla_html = _html_col_table(df_arch, reglas_arch, cols_sel, filtro)
        st.markdown(tabla_html, unsafe_allow_html=True)

    # â”€â”€ Hallazgos â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(_html_section_title("âš ï¸", "Hallazgos de Calidad â€” Variables Relevantes"),
                unsafe_allow_html=True)

    with st.expander(f"Ver hallazgos â€” {nombre_disp}", expanded=False):
        with st.spinner("Calculando hallazgosâ€¦"):
            df_det = detalle_por_columna(df_arch, reglas_arch, cols_sel)
            recos  = generar_recomendaciones(df_det, scores_dim_g)
        st.markdown(_html_issues(recos), unsafe_allow_html=True)

    # â”€â”€ Recomendaciones â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(_html_section_title("ðŸ’¡", "Recomendaciones DAMA â€” ISO/IEC 25012"),
                unsafe_allow_html=True)

    with st.expander(f"Ver recomendaciones ({len(recos) if 'recos' in dir() else 0}) â€” {nombre_disp}",
                     expanded=False):
        if "recos" not in dir() or not recos:
            with st.spinner("Generando recomendacionesâ€¦"):
                df_det = detalle_por_columna(df_arch, reglas_arch, cols_sel)
                recos  = generar_recomendaciones(df_det, scores_dim_g)
        st.markdown(_html_reco_list(recos), unsafe_allow_html=True)

    # â”€â”€ Footer del archivo â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(f"""
    <div class="rpt-footer">
      <div>
        <div class="footer-logo">DataQuality Report</div>
        <div>Marco: ISO/IEC 25012 · DAMA-DMBOK2 · DCAM · Resolución 3512/2019 (MSPS Colombia)</div>
      </div>
      <div>Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} ·
           Archivo {idx_a} de {len(archivos_claves)} · {nombre_disp}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

# â”€â”€ Footer global â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.markdown(f"""
<div class="rpt-footer" style="margin-top:40px;border-radius:var(--radius)">
  <div>
    <div class="footer-logo">DataQuality Report · Audifarma</div>
    <div>Marco: ISO/IEC 25012 · DAMA-DMBOK2 · DCAM · Resolución 3512/2019 (MSPS Colombia)</div>
  </div>
  <div>Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
</div>""", unsafe_allow_html=True)
