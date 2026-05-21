import pandas as pd
from pathlib import Path

ARCHIVOS = {
    "liberar_formula": "SaludTotal_LiberarFormulaV2.csv",
    "direccionamientos": "SaludTotal_ConsultaDireccionamientosxCedula.csv",
    "consultar_cedula": "SaludTotal_ConsultarCedula.csv",
    "capital_salud": "CapitalSalud_ConsultaMedicamentos.csv",
    "nueva_eps": "NuevaEPS_ConsultaPreautorizacion.csv",
}

# Archivos que no generan error si no están presentes en la carpeta
ARCHIVOS_OPCIONALES = {"nueva_eps"}

# Patrones de nombre (fragmento en minúsculas → clave interna).
# Se aplican tanto al escaneo de carpeta como al modo upload.
PATRONES_NOMBRE: list[tuple[str, str]] = [
    ("liberarformula",      "liberar_formula"),
    ("liberar_formula",     "liberar_formula"),
    ("liberar",             "liberar_formula"),
    ("formula",             "liberar_formula"),
    ("direccionamientos",   "direccionamientos"),
    ("direccion",           "direccionamientos"),
    ("consultarced",        "consultar_cedula"),
    ("consultar",           "consultar_cedula"),
    ("cedula",              "consultar_cedula"),
    ("capitalsalud",        "capital_salud"),
    ("capital",             "capital_salud"),
    ("medicamento",         "capital_salud"),
    ("nuevaeps",            "nueva_eps"),
    ("nueva_eps",           "nueva_eps"),
    ("preautorizacion",     "nueva_eps"),
    ("preautor",            "nueva_eps"),
]

COLS_NUM: dict[str, list[str]] = {
    "liberar_formula":   ["CantidadDireccionada", "CantidadEntregada", "Valor"],
    "direccionamientos": ["pago_final", "porc_cobertura", "CantidadDosis", "Duracion"],
    "consultar_cedula":  ["pago_final", "porc_cobertura", "CantidadDosis", "Duracion"],
    "capital_salud":     ["CantidadMedicamento", "CuotaModeradora"],
    "nueva_eps":         ["edad", "semanasCotizadas", "cantidad"],
}

NOMBRES_DISPLAY = {
    "liberar_formula":   "LiberarFormula (ST)",
    "direccionamientos": "Direccionamientos (ST)",
    "consultar_cedula":  "ConsultarCedula (ST)",
    "capital_salud":     "Medicamentos (CS)",
    "nueva_eps":         "Preautorizaciones (NE)",
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


def _cargar_archivo(ruta: Path) -> pd.DataFrame | None:
    """Intenta cargar un CSV probando encodings y detectando separador."""
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            sep = _detectar_separador(ruta, enc)
            df = pd.read_csv(ruta, encoding=enc, sep=sep,
                             low_memory=False, dtype=str)
            df.columns = df.columns.str.strip()
            return df
        except UnicodeDecodeError:
            continue
        except Exception:
            break
    return None


def cargar_datos(ruta_datos: str) -> dict[str, pd.DataFrame]:
    """
    Carga todos los CSV de *ruta_datos* que coincidan con los patrones conocidos.

    Estrategia de detección (en orden):
    1. Nombres exactos definidos en ARCHIVOS (compatibilidad original).
    2. Escaneo de todos los *.csv de la carpeta con PATRONES_NOMBRE.
       Esto permite detectar archivos nuevos aunque el nombre cambie ligeramente.
    """
    ruta_base = Path(ruta_datos)
    dfs: dict[str, pd.DataFrame] = {}
    errores: list[str] = []

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

    # ── Paso 2: escaneo flexible de la carpeta ────────────────────────────────
    # Detecta archivos nuevos o con nombres ligeramente distintos
    csvs_en_carpeta = sorted(ruta_base.glob("*.csv")) + sorted(ruta_base.glob("*.CSV"))
    nombres_ya_cargados = {Path(v).name.lower() for v in ARCHIVOS.values()}

    for csv_path in csvs_en_carpeta:
        if csv_path.name.lower() in nombres_ya_cargados:
            continue  # ya fue procesado en el paso 1
        clave = _clave_por_nombre(csv_path.name)
        if clave is None or clave in dfs:
            continue  # sin patrón coincidente o ya cargado
        df = _cargar_archivo(csv_path)
        if df is not None:
            dfs[clave] = df

    # ── Limpieza de columnas numéricas ────────────────────────────────────────
    for clave, cols in COLS_NUM.items():
        if clave in dfs:
            dfs[clave] = _limpiar_numericos(dfs[clave], cols)

    if errores:
        raise RuntimeError("\n".join(errores))

    return dfs
