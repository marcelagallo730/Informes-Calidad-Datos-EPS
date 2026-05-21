import pandas as pd
from pathlib import Path

# ── Archivos con clave semántica conocida ────────────────────────────────────
# La clave semántica la usa el código de análisis (dimensiones DAMA, costos, etc.)
# Cualquier CSV que NO esté aquí se carga usando su nombre de archivo como clave.
ARCHIVOS: dict[str, str] = {
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

# Tabla inversa: nombre_de_archivo.lower() → clave semántica
_FILENAME_A_CLAVE: dict[str, str] = {v.lower(): k for k, v in ARCHIVOS.items()}

# Archivos que no generan error si no están presentes
ARCHIVOS_OPCIONALES: set[str] = {
    "nueva_eps", "capital_salud_aut",
    "nueva_eps_afiliado", "nueva_eps_ordenes", "nueva_eps_liberar",
}

# Limpieza numérica por clave semántica
COLS_NUM: dict[str, list[str]] = {
    "liberar_formula":    ["CantidadDireccionada", "CantidadEntregada", "Valor"],
    "direccionamientos":  ["pago_final", "porc_cobertura", "CantidadDosis", "Duracion"],
    "consultar_cedula":   ["pago_final", "porc_cobertura", "CantidadDosis", "Duracion"],
    "capital_salud":      ["CantidadMedicamento", "CuotaModeradora"],
    "capital_salud_aut":  ["cantTotAEntregar", "cantTotEntregada", "cuotaModeradora", "copagoAuto"],
    "nueva_eps":          ["edad", "semanasCotizadas", "cantidad"],
    "nueva_eps_afiliado": ["edad", "semanasCotizadas"],
    "nueva_eps_ordenes":  ["edad", "valor_orden", "cant_presentacion",
                           "cantidad_dispensada", "dias_tratamiento", "nro_dosis"],
    "nueva_eps_liberar":  ["edad", "semanasCotizadas", "cantidad"],
}

# Nombres legibles por clave semántica
NOMBRES_DISPLAY: dict[str, str] = {
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


# ── Utilidades ───────────────────────────────────────────────────────────────

def _nombre_a_clave(nombre_archivo: str) -> str:
    """
    Devuelve la clave para un archivo CSV.
    - Si el nombre exacto está registrado en ARCHIVOS → clave semántica.
    - Si no → nombre del archivo sin extensión, en minúsculas (garantiza unicidad).
    """
    return _FILENAME_A_CLAVE.get(
        nombre_archivo.lower(),
        Path(nombre_archivo).stem.lower().replace(" ", "_")[:60],
    )


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


def _cargar_archivo(ruta: Path) -> pd.DataFrame | None:
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


# ── Carga principal ──────────────────────────────────────────────────────────

def cargar_datos(ruta_datos: str) -> dict[str, pd.DataFrame]:
    """
    Carga TODOS los archivos CSV de *ruta_datos* sin excepción.

    Regla de clave (sin patrones, sin ambigüedad):
      • Nombre exacto registrado en ARCHIVOS  →  clave semántica conocida
      • Cualquier otro CSV                    →  nombre_del_archivo (sin .csv)

    Cada archivo recibe una clave única derivada de su nombre exacto,
    por lo que nunca se descartan archivos por colisión de patrones.
    """
    ruta_base = Path(ruta_datos)
    dfs: dict[str, pd.DataFrame] = {}
    errores: list[str] = []

    for csv_path in sorted(ruta_base.glob("*.[cC][sS][vV]")):
        clave = _nombre_a_clave(csv_path.name)
        df = _cargar_archivo(csv_path)
        if df is not None:
            dfs[clave] = df
        else:
            errores.append(f"No se pudo leer: {csv_path.name}")

    # Verificar que los archivos obligatorios estén presentes
    for clave_sem, archivo in ARCHIVOS.items():
        if clave_sem not in ARCHIVOS_OPCIONALES and clave_sem not in dfs:
            errores.append(f"{archivo} no encontrado en {ruta_base}")

    # Limpieza numérica para claves semánticas conocidas
    for clave, cols in COLS_NUM.items():
        if clave in dfs:
            dfs[clave] = _limpiar_numericos(dfs[clave], cols)

    if errores:
        raise RuntimeError("\n".join(errores))

    return dfs


# ── Compatibilidad con código legado ─────────────────────────────────────────
# Exportamos _clave_desde_filename por si algún módulo lo importa
def _clave_desde_filename(nombre_archivo: str) -> str:
    return Path(nombre_archivo).stem.lower().replace(" ", "_")[:60]
