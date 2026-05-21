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

NOMBRES_DISPLAY = {
    "liberar_formula": "LiberarFormula (ST)",
    "direccionamientos": "Direccionamientos (ST)",
    "consultar_cedula": "ConsultarCedula (ST)",
    "capital_salud": "Medicamentos (CS)",
    "nueva_eps": "Preautorizaciones (NE)",
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


def cargar_datos(ruta_datos: str) -> dict[str, pd.DataFrame]:
    ruta_base = Path(ruta_datos)
    dfs: dict[str, pd.DataFrame] = {}
    errores: list[str] = []

    for clave, archivo in ARCHIVOS.items():
        ruta = ruta_base / archivo
        if not ruta.exists():
            if clave not in ARCHIVOS_OPCIONALES:
                errores.append(f"{archivo} no encontrado en {ruta_base}")
            continue

        cargado = False
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                sep = _detectar_separador(ruta, enc)
                df = pd.read_csv(
                    ruta,
                    encoding=enc,
                    sep=sep,
                    low_memory=False,
                    dtype=str,
                )
                df.columns = df.columns.str.strip()
                dfs[clave] = df
                cargado = True
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                errores.append(f"{archivo}: {e}")
                break

        if not cargado and clave not in dfs and clave not in ARCHIVOS_OPCIONALES:
            errores.append(f"No se pudo cargar {archivo}")

    # Convertir columnas numéricas conocidas
    cols_num_liberar = ["CantidadDireccionada", "CantidadEntregada", "Valor"]
    cols_num_dir = ["pago_final", "porc_cobertura", "CantidadDosis", "Duracion"]
    cols_num_cs = ["CantidadMedicamento", "CuotaModeradora"]
    cols_num_ne = ["edad", "semanasCotizadas", "cantidad"]

    if "liberar_formula" in dfs:
        dfs["liberar_formula"] = _limpiar_numericos(dfs["liberar_formula"], cols_num_liberar)
    if "direccionamientos" in dfs:
        dfs["direccionamientos"] = _limpiar_numericos(dfs["direccionamientos"], cols_num_dir)
    if "consultar_cedula" in dfs:
        dfs["consultar_cedula"] = _limpiar_numericos(dfs["consultar_cedula"], cols_num_dir)
    if "capital_salud" in dfs:
        dfs["capital_salud"] = _limpiar_numericos(dfs["capital_salud"], cols_num_cs)
    if "nueva_eps" in dfs:
        dfs["nueva_eps"] = _limpiar_numericos(dfs["nueva_eps"], cols_num_ne)

    if errores:
        raise RuntimeError("\n".join(errores))

    return dfs
