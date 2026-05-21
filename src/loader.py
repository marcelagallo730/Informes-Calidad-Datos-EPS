import pandas as pd
from pathlib import Path

ARCHIVOS = {
    "liberar_formula":      "SaludTotal_LiberarFormulaV2.csv",
    "direccionamientos":    "SaludTotal_ConsultaDireccionamientosxCedula.csv",
    "consultar_cedula":     "SaludTotal_ConsultarCedula.csv",
    "capital_salud":        "CapitalSalud_ConsultaMedicamentos.csv",
    "capital_salud_aut":    "CapitalSalud_ConsultarAutorizacion.csv",
    "nueva_eps":            "NuevaEPS_ConsultaPreautorizacion.csv",
    "nueva_eps_afiliado":   "NuevaEPS_ConsultarAfiliado.csv",
    "nueva_eps_ordenes":    "NuevaEPS_ConsultarOrdenes.csv",
    "nueva_eps_liberar":    "NuevaEPS_LiberarPreautorizacion.csv",
}

# Archivos que no generan error si no están presentes en la carpeta
ARCHIVOS_OPCIONALES = {
    "nueva_eps",
    "capital_salud_aut",
    "nueva_eps_afiliado",
    "nueva_eps_ordenes",
    "nueva_eps_liberar",
}

# ── Patrones de nombre (fragmento en minúsculas → clave interna) ─────────────
# ORDEN IMPORTA: los más específicos deben ir primero.
# Regla general: patrones con prefijo "nuevaeps" van ANTES de los genéricos
# ("liberar", "consultar", etc.) para evitar colisiones.
PATRONES_NOMBRE: list[tuple[str, str]] = [

    # ── NuevaEPS — específicos (ANTES que patrones genéricos) ────────────────
    ("nuevaeps_liberarpreaut",      "nueva_eps_liberar"),
    ("nuevaeps_liberar",            "nueva_eps_liberar"),
    ("liberarpreautorizacion",      "nueva_eps_liberar"),
    ("nuevaeps_consultarafil",      "nueva_eps_afiliado"),
    ("consultarafiliado",           "nueva_eps_afiliado"),
    ("afiliado",                    "nueva_eps_afiliado"),
    ("nuevaeps_consultarord",       "nueva_eps_ordenes"),
    ("consultarordenes",            "nueva_eps_ordenes"),
    ("ordenes",                     "nueva_eps_ordenes"),
    ("nuevaeps_consultapreaut",     "nueva_eps"),
    ("nuevaeps_preaut",             "nueva_eps"),
    ("preautorizacion",             "nueva_eps"),
    ("preautor",                    "nueva_eps"),
    ("nuevaeps",                    "nueva_eps"),
    ("nueva_eps",                   "nueva_eps"),

    # ── Salud Total ──────────────────────────────────────────────────────────
    ("liberarformulav",             "liberar_formula"),
    ("liberar_formula",             "liberar_formula"),
    ("liberarformula",              "liberar_formula"),
    ("liberar",                     "liberar_formula"),   # genérico — va DESPUÉS de NuevaEPS
    ("formula",                     "liberar_formula"),
    ("direccionamientos",           "direccionamientos"),
    ("direccionamiento",            "direccionamientos"),
    ("direccion",                   "direccionamientos"),
    ("consultarcedula",             "consultar_cedula"),
    ("consultarced",                "consultar_cedula"),

    # ── Capital Salud ────────────────────────────────────────────────────────
    ("consultarautorizacion",       "capital_salud_aut"),
    ("consultaraut",                "capital_salud_aut"),
    ("autorizacion",                "capital_salud_aut"),
    ("capitalsalud_consultar",      "capital_salud_aut"),
    ("consultamedicamentos",        "capital_salud"),
    ("capitalsalud",                "capital_salud"),
    ("capital",                     "capital_salud"),
    ("medicamento",                 "capital_salud"),
]

COLS_NUM: dict[str, list[str]] = {
    "liberar_formula":    ["CantidadDireccionada", "CantidadEntregada", "Valor"],
    "direccionamientos":  ["pago_final", "porc_cobertura", "CantidadDosis", "Duracion"],
    "consultar_cedula":   ["pago_final", "porc_cobertura", "CantidadDosis", "Duracion"],
    "capital_salud":      ["CantidadMedicamento", "CuotaModeradora"],
    "capital_salud_aut":  ["cantTotAEntregar", "cantTotEntregada", "cuotaModeradora", "copagoAuto"],
    "nueva_eps":          ["edad", "semanasCotizadas", "cantidad"],
    "nueva_eps_afiliado": ["edad", "semanasCotizadas"],
    "nueva_eps_ordenes":  ["edad", "valor_orden", "cant_presentacion", "cantidad_dispensada",
                           "dias_tratamiento", "nro_dosis"],
    "nueva_eps_liberar":  ["edad", "semanasCotizadas", "cantidad"],
}

NOMBRES_DISPLAY = {
    "liberar_formula":    "LiberarFormula (ST)",
    "direccionamientos":  "Direccionamientos (ST)",
    "consultar_cedula":   "ConsultarCedula (ST)",
    "capital_salud":      "Medicamentos (CS)",
    "capital_salud_aut":  "Autorizaciones (CS)",
    "nueva_eps":          "Preautorizaciones (NE)",
    "nueva_eps_afiliado": "Afiliados (NE)",
    "nueva_eps_ordenes":  "Ordenes (NE)",
    "nueva_eps_liberar":  "LiberarPreaut (NE)",
}


def _detectar_separador(ruta: Path, encoding: str) -> str:
    with open(ruta, encoding=encoding, errors="replace") as f:
        primera = f.readline()
    return ";" if primera.count(";") > primera.count(",") else ","


def _limpiar_numericos(df: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    for col in columnas:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"\.", "", regex=True)
                .str.replace(",", ".", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _clave_por_nombre(nombre_archivo: str) -> str | None:
    """Devuelve la clave interna para un nombre de archivo aplicando PATRONES_NOMBRE."""
    fname = nombre_archivo.lower().replace(" ", "_")
    for patron, clave in PATRONES_NOMBRE:
        if patron in fname:
            return clave
    return None


def _clave_desde_filename(nombre_archivo: str) -> str:
    """
    Genera una clave única a partir del nombre de archivo para CSVs
    que no coinciden con ningún patrón conocido.
    Ej: 'NuevaEPS_ConsultarXYZ.csv' → 'nuevaeps_consultarxyz'
    """
    stem = Path(nombre_archivo).stem          # sin extensión
    clave = stem.lower()
    for ch in (" ", "-", ".", "(", ")"):
        clave = clave.replace(ch, "_")
    return clave[:60]                          # máx 60 caracteres


def _cargar_archivo(ruta: Path) -> pd.DataFrame | None:
    """Intenta cargar un CSV probando encodings y detectando separador."""
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            sep = _detectar_separador(ruta, enc)
            df = pd.read_csv(ruta, encoding=enc, sep=sep,
                             low_memory=False, dtype=str)
            df.columns = df.columns.str.strip().str.lstrip("﻿").str.strip('"')
            return df
        except UnicodeDecodeError:
            continue
        except Exception:
            break
    return None


def cargar_datos(ruta_datos: str) -> dict[str, pd.DataFrame]:
    """
    Carga TODOS los CSV de *ruta_datos*.

    Estrategia (en orden de prioridad):
    1. Nombres exactos registrados en ARCHIVOS → clave semántica conocida.
    2. Patrón de nombre coincidente (PATRONES_NOMBRE) → clave semántica conocida.
    3. Cualquier CSV restante → clave derivada del nombre del archivo.
       Esto garantiza que NINGÚN archivo sea ignorado.
    """
    ruta_base = Path(ruta_datos)
    dfs: dict[str, pd.DataFrame] = {}
    errores: list[str] = []

    nombres_exactos_lower = {v.lower() for v in ARCHIVOS.values()}

    # ── Paso 1: nombres exactos registrados ──────────────────────────────────
    for clave, archivo in ARCHIVOS.items():
        ruta = ruta_base / archivo
        if not ruta.exists():
            if clave not in ARCHIVOS_OPCIONALES:
                errores.append(f"{archivo} no encontrado en {ruta_base}")
            continue
        df = _cargar_archivo(ruta)
        if df is not None:
            dfs[clave] = df
        elif clave not in ARCHIVOS_OPCIONALES:
            errores.append(f"No se pudo cargar {archivo}")

    # ── Pasos 2 y 3: escaneo completo de la carpeta ──────────────────────────
    # Paso 2 → patrón conocido; Paso 3 → nombre de archivo como clave.
    # Ningún CSV queda sin cargar.
    for csv_path in sorted(ruta_base.glob("*.[cC][sS][vV]")):
        if csv_path.name.lower() in nombres_exactos_lower:
            continue  # ya procesado en paso 1

        # Intentar patrón conocido primero
        clave = _clave_por_nombre(csv_path.name)

        # Si no hay patrón → derivar clave desde el nombre del archivo
        if clave is None:
            clave = _clave_desde_filename(csv_path.name)

        if clave in dfs:
            continue  # ya cargado (mismo patrón desde otro archivo)

        df = _cargar_archivo(csv_path)
        if df is not None:
            dfs[clave] = df

    # ── Limpieza de columnas numéricas (solo para claves conocidas) ───────────
    for clave, cols in COLS_NUM.items():
        if clave in dfs:
            dfs[clave] = _limpiar_numericos(dfs[clave], cols)

    if errores:
        raise RuntimeError("\n".join(errores))

    return dfs
