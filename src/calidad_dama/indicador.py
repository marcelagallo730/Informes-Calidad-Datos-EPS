"""
Agrega las 7 dimensiones DAMA en un score global y uno focalizado por archivo.
"""

import pandas as pd
from . import dimensiones as dim

DIMENSIONES = ["Completitud", "Unicidad", "Validez", "Exactitud", "Oportunidad", "Consistencia", "Integridad"]

PESOS_DEFAULT = {d: 1.0 for d in DIMENSIONES}


def _score_archivo(
    nombre: str,
    df: pd.DataFrame,
    dfs: dict[str, pd.DataFrame],
    reglas_archivo: dict,
    pesos: dict[str, float],
    columnas: list[str] | None,
    columnas_sel_global: dict[str, list[str]] | None,
    fecha_ref: pd.Timestamp,
) -> dict[str, float]:
    cons = dim.consistencia(dfs, columnas_sel_global)
    integ = dim.integridad(dfs, columnas_sel_global)

    valores = {
        "Completitud": dim.completitud(df, columnas),
        "Unicidad": dim.unicidad(df, nombre),
        "Validez": dim.validez(df, reglas_archivo, columnas),
        "Exactitud": dim.exactitud(df, nombre, columnas),
        "Oportunidad": dim.oportunidad(df, nombre, fecha_ref, columnas),
        "Consistencia": cons.get(nombre, 100.0),
        "Integridad": integ.get(nombre, 100.0),
    }

    suma_pesos = sum(pesos.get(d, 1.0) for d in DIMENSIONES)
    score = sum(valores[d] * pesos.get(d, 1.0) for d in DIMENSIONES) / suma_pesos

    return {**valores, "score_total": round(score, 2)}


def calcular_indicadores(
    dfs: dict[str, pd.DataFrame],
    columnas_relevantes: dict[str, list[str]],
    reglas: dict[str, dict],
    pesos: dict[str, float] | None = None,
    fecha_ref: pd.Timestamp | None = None,
) -> dict:
    """
    Retorna:
      {
        "global":    { nombre_archivo: {dim: score, score_total: X}, "__total__": {...} },
        "focalizado":{ nombre_archivo: {dim: score, score_total: X}, "__total__": {...} },
      }
    """
    if pesos is None:
        pesos = PESOS_DEFAULT
    if fecha_ref is None:
        fecha_ref = pd.Timestamp.today()

    resultado: dict = {"global": {}, "focalizado": {}}

    for nombre, df in dfs.items():
        cols_sel = columnas_relevantes.get(nombre) or []
        reglas_arch = reglas.get(nombre, {})

        resultado["global"][nombre] = _score_archivo(
            nombre, df, dfs, reglas_arch, pesos,
            columnas=None,
            columnas_sel_global=None,
            fecha_ref=fecha_ref,
        )

        resultado["focalizado"][nombre] = _score_archivo(
            nombre, df, dfs, reglas_arch, pesos,
            columnas=cols_sel if cols_sel else None,
            columnas_sel_global=columnas_relevantes if cols_sel else None,
            fecha_ref=fecha_ref,
        )

    for tipo in ("global", "focalizado"):
        archivos = {k: v for k, v in resultado[tipo].items() if not k.startswith("__")}
        if archivos:
            resultado[tipo]["__total__"] = {
                d: round(sum(archivos[a][d] for a in archivos) / len(archivos), 2)
                for d in DIMENSIONES + ["score_total"]
            }

    return resultado
