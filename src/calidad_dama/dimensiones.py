"""
Implementación de las 7 dimensiones DAMA de calidad de datos.
Cada función devuelve un score de 0 a 100.
"""

import re
import pandas as pd

# ── 1. COMPLETITUD ────────────────────────────────────────────────────────────

def completitud(df: pd.DataFrame, columnas: list[str] | None = None) -> float:
    cols = _filtrar_cols(df, columnas)
    if not cols:
        return 100.0
    scores = [(df[c].notna() & (df[c].astype(str).str.strip() != "")).sum() / len(df) * 100 for c in cols]
    return round(sum(scores) / len(scores), 2)


# ── 2. UNICIDAD ───────────────────────────────────────────────────────────────

CLAVES_UNICIDAD = {
    "liberar_formula": ["NumEntrega", "CodigoServicio"],
    "direccionamientos": ["ID_DireccionamientoMipres"],
    "consultar_cedula": ["IDDispensacion"],
    "capital_salud": ["NumeroAutorizacion", "CodigoMedicamento"],
}


def unicidad(df: pd.DataFrame, nombre_archivo: str) -> float:
    claves = [c for c in CLAVES_UNICIDAD.get(nombre_archivo, []) if c in df.columns]
    if not claves or len(df) == 0:
        return 100.0
    n_unicos = df[claves].drop_duplicates().shape[0]
    return round(n_unicos / len(df) * 100, 2)


# ── 3. VALIDEZ ────────────────────────────────────────────────────────────────

def validez(df: pd.DataFrame, reglas: dict, columnas: list[str] | None = None) -> float:
    cols_con_reglas = [c for c in (columnas or list(reglas.keys())) if c in df.columns and c in reglas]
    if not cols_con_reglas:
        return 100.0

    scores = []
    for col in cols_con_reglas:
        regla = reglas[col]
        serie = df[col]
        n_total = len(df)
        if n_total == 0:
            continue

        tipo = regla.get("tipo")

        if tipo == "regex":
            patron = regla["patron"]
            n_ok = serie.dropna().astype(str).str.match(patron).sum()

        elif tipo == "dominio":
            valores = regla["valores"]
            n_ok = serie.isin(valores).sum()

        elif tipo == "numerico":
            num = pd.to_numeric(serie, errors="coerce")
            mascara = num.notna()
            if "min" in regla:
                mascara &= num >= regla["min"]
            if "max" in regla:
                mascara &= num <= regla["max"]
            n_ok = mascara.sum()

        elif tipo == "fecha":
            parsed = pd.to_datetime(serie, errors="coerce", dayfirst=True)
            n_ok = parsed.notna().sum()

        elif tipo == "fecha_yyyymmdd":
            parsed = pd.to_datetime(serie, format="%Y%m%d", errors="coerce")
            n_ok = parsed.notna().sum()

        else:
            continue

        scores.append(n_ok / n_total * 100)

    return round(sum(scores) / len(scores), 2) if scores else 100.0


# ── 4. EXACTITUD (coherencia lógica interna) ──────────────────────────────────

def exactitud(df: pd.DataFrame, nombre_archivo: str, columnas: list[str] | None = None) -> float:
    checks: list[float] = []

    def _aplica(col: str) -> bool:
        return columnas is None or col in columnas

    if nombre_archivo == "liberar_formula":
        # CantidadEntregada <= CantidadDireccionada
        if "CantidadDireccionada" in df.columns and "CantidadEntregada" in df.columns:
            if _aplica("CantidadDireccionada") and _aplica("CantidadEntregada"):
                cd = pd.to_numeric(df["CantidadDireccionada"], errors="coerce")
                ce = pd.to_numeric(df["CantidadEntregada"], errors="coerce")
                mask = cd.notna() & ce.notna()
                if mask.sum() > 0:
                    checks.append((ce[mask] <= cd[mask]).sum() / mask.sum() * 100)

        # Valor >= 0
        if "Valor" in df.columns and _aplica("Valor"):
            v = pd.to_numeric(df["Valor"], errors="coerce").dropna()
            if len(v):
                checks.append((v >= 0).sum() / len(v) * 100)

    elif nombre_archivo in ("direccionamientos", "consultar_cedula"):
        # fecha_uso <= fecha_vto
        if "fecha_uso" in df.columns and "fecha_vto" in df.columns:
            if _aplica("fecha_uso") and _aplica("fecha_vto"):
                fu = pd.to_datetime(df["fecha_uso"], errors="coerce", dayfirst=True)
                fv = pd.to_datetime(df["fecha_vto"], errors="coerce", dayfirst=True)
                if hasattr(fu.dtype, "tz") and fu.dtype.tz is not None:
                    fu = fu.dt.tz_convert(None)
                if hasattr(fv.dtype, "tz") and fv.dtype.tz is not None:
                    fv = fv.dt.tz_convert(None)
                mask = fu.notna() & fv.notna()
                if mask.sum() > 0:
                    checks.append((fv[mask] >= fu[mask]).sum() / mask.sum() * 100)

        # pago_final >= 0
        if "pago_final" in df.columns and _aplica("pago_final"):
            v = pd.to_numeric(df["pago_final"], errors="coerce").dropna()
            if len(v):
                checks.append((v >= 0).sum() / len(v) * 100)

    elif nombre_archivo == "capital_salud":
        # CantidadMedicamento >= 0
        if "CantidadMedicamento" in df.columns and _aplica("CantidadMedicamento"):
            v = pd.to_numeric(df["CantidadMedicamento"], errors="coerce").dropna()
            if len(v):
                checks.append((v >= 0).sum() / len(v) * 100)

    return round(sum(checks) / len(checks), 2) if checks else 100.0


# ── 5. OPORTUNIDAD (frescura temporal) ───────────────────────────────────────

COLS_FECHA_POR_ARCHIVO = {
    "liberar_formula": [("FechaVencimiento", None)],
    "direccionamientos": [("fecha_uso", None), ("fecha_vto", None)],
    "consultar_cedula": [("fecha_uso", None), ("fecha_vto", None)],
    "capital_salud": [("FechaProgramacionCita", "%Y%m%d")],
}


def oportunidad(df: pd.DataFrame, nombre_archivo: str, fecha_ref: pd.Timestamp, columnas: list[str] | None = None) -> float:
    pares = COLS_FECHA_POR_ARCHIVO.get(nombre_archivo, [])
    if columnas is not None:
        pares = [(c, fmt) for c, fmt in pares if c in columnas]
    pares = [(c, fmt) for c, fmt in pares if c in df.columns]

    if not pares or len(df) == 0:
        return 100.0

    scores = []
    ventana = pd.Timedelta(days=180)
    limite_inf = fecha_ref - ventana

    for col, fmt in pares:
        if fmt:
            parsed = pd.to_datetime(df[col], format=fmt, errors="coerce")
        else:
            parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

        validas = parsed.dropna()
        if len(validas) == 0:
            continue

        # Normalizar timezone: si las fechas tienen tz, quitar para comparar con Timestamp naive
        if hasattr(validas.dtype, "tz") and validas.dtype.tz is not None:
            validas = validas.dt.tz_convert(None)

        recientes = ((validas >= limite_inf) & (validas <= fecha_ref + pd.Timedelta(days=365))).sum()
        scores.append(recientes / len(df) * 100)

    return round(sum(scores) / len(scores), 2) if scores else 100.0


# ── 6. CONSISTENCIA (coherencia entre archivos) ───────────────────────────────

def consistencia(dfs: dict[str, pd.DataFrame], columnas_sel: dict[str, list[str]] | None = None) -> dict[str, float]:
    resultado = {k: 100.0 for k in dfs}

    df_lib = dfs.get("liberar_formula")
    df_dir = dfs.get("direccionamientos")
    df_con = dfs.get("consultar_cedula")

    def _cols_activas(clave: str, col: str) -> bool:
        if columnas_sel is None:
            return True
        return col in columnas_sel.get(clave, [col])

    # codigoIT (dir) ↔ CodigoServicio (lib)
    if df_dir is not None and df_lib is not None:
        if (_cols_activas("direccionamientos", "codigoIT") and
                _cols_activas("liberar_formula", "CodigoServicio") and
                "codigoIT" in df_dir.columns and "CodigoServicio" in df_lib.columns):

            ref = set(df_lib["CodigoServicio"].dropna().astype(str).str.strip())
            orig = df_dir["codigoIT"].dropna().astype(str).str.strip()
            if len(orig):
                score = orig.isin(ref).sum() / len(orig) * 100
                resultado["direccionamientos"] = round(score, 2)
                resultado["liberar_formula"] = round(score, 2)

    # NumEntregaMed (consultar_cedula) → NumEntrega (lib)
    if df_con is not None and df_lib is not None:
        if (_cols_activas("consultar_cedula", "NumEntregaMed") and
                _cols_activas("liberar_formula", "NumEntrega") and
                "NumEntregaMed" in df_con.columns and "NumEntrega" in df_lib.columns):

            ref = set(df_lib["NumEntrega"].dropna().astype(str).str.strip())
            orig = df_con["NumEntregaMed"].dropna().astype(str).str.strip()
            if len(orig):
                score = orig.isin(ref).sum() / len(orig) * 100
                resultado["consultar_cedula"] = round(min(resultado["consultar_cedula"], score), 2)

    return resultado


# ── 7. INTEGRIDAD REFERENCIAL ─────────────────────────────────────────────────

def integridad(dfs: dict[str, pd.DataFrame], columnas_sel: dict[str, list[str]] | None = None) -> dict[str, float]:
    resultado = {k: 100.0 for k in dfs}

    df_lib = dfs.get("liberar_formula")
    df_dir = dfs.get("direccionamientos")
    df_con = dfs.get("consultar_cedula")

    def _cols_activas(clave: str, col: str) -> bool:
        if columnas_sel is None:
            return True
        return col in columnas_sel.get(clave, [col])

    # NumEntregaMed (dir) → NumEntrega (lib)
    if df_dir is not None and df_lib is not None:
        if (_cols_activas("direccionamientos", "NumEntregaMed") and
                _cols_activas("liberar_formula", "NumEntrega") and
                "NumEntregaMed" in df_dir.columns and "NumEntrega" in df_lib.columns):

            ref = set(df_lib["NumEntrega"].dropna().astype(str).str.strip())
            orig = df_dir["NumEntregaMed"].dropna().astype(str).str.strip()
            if len(orig):
                score = orig.isin(ref).sum() / len(orig) * 100
                resultado["direccionamientos"] = round(min(resultado["direccionamientos"], score), 2)

    # NumEntregaMed (consultar_cedula) → NumEntrega (lib)
    if df_con is not None and df_lib is not None:
        if (_cols_activas("consultar_cedula", "NumEntregaMed") and
                _cols_activas("liberar_formula", "NumEntrega") and
                "NumEntregaMed" in df_con.columns and "NumEntrega" in df_lib.columns):

            ref = set(df_lib["NumEntrega"].dropna().astype(str).str.strip())
            orig = df_con["NumEntregaMed"].dropna().astype(str).str.strip()
            if len(orig):
                score = orig.isin(ref).sum() / len(orig) * 100
                resultado["consultar_cedula"] = round(min(resultado["consultar_cedula"], score), 2)

    return resultado


# ── Utilidades ────────────────────────────────────────────────────────────────

def _filtrar_cols(df: pd.DataFrame, columnas: list[str] | None) -> list[str]:
    if columnas is None:
        return df.columns.tolist()
    return [c for c in columnas if c in df.columns]
