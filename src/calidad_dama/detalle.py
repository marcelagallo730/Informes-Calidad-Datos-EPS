"""
Análisis de calidad a nivel de columna individual y generación de
recomendaciones DAMA para hallazgos críticos.
"""

import pandas as pd

UMBRAL_OPTIMO = 85.0
UMBRAL_ACEPTABLE = 70.0

RECOMENDACIONES_DAMA: dict[str, dict[str, list[str]]] = {
    "Completitud": {
        "Crítico": [
            "Implementar restricciones NOT NULL en el sistema fuente para evitar nuevos registros vacíos.",
            "Revisar el formulario y proceso ETL de captura que origina este campo.",
            "Establecer un SLA de completitud mínimo del 95 % con el área de tecnología responsable.",
            "Ejecutar proceso de recuperación retroactiva consultando fuentes alternativas (MIPRES, historiales).",
            "Catalogar este campo como crítico en el inventario de activos de datos (DAMA DMBoK §6.4).",
        ],
        "Aceptable": [
            "Configurar alertas automáticas cuando la tasa de nulos supere el 5 %.",
            "Documentar en el catálogo de datos los casos que justifican valores nulos.",
            "Incluir este campo en el panel de monitoreo mensual de calidad.",
        ],
    },
    "Validez": {
        "Crítico": [
            "Implementar controles de formato y dominio en el punto de captura del sistema fuente.",
            "Actualizar y publicar las tablas de referencia y catálogos asociados al campo.",
            "Ejecutar un proceso de estandarización y limpieza retroactiva con criterios definidos.",
            "Revisar si la regla de validación refleja la realidad operativa actual del negocio.",
            "Aplicar transformaciones de estandarización en el proceso ETL (DAMA DMBoK §11.3).",
        ],
        "Aceptable": [
            "Revisar y actualizar las reglas de validación si los valores válidos han evolucionado.",
            "Implementar reportes de seguimiento periódico de la validez de este campo.",
        ],
    },
    "Unicidad": {
        "Crítico": [
            "Implementar restricciones de clave primaria o única en la base de datos fuente.",
            "Auditar el proceso de integración que puede estar generando registros duplicados.",
            "Definir y ejecutar estrategia de deduplicación con criterio de registro maestro.",
            "Revisar los procesos de carga incremental que pueden insertar duplicados (DAMA DMBoK §10.2).",
        ],
        "Aceptable": [
            "Monitorear periódicamente la tasa de duplicados para detectar tendencias crecientes.",
            "Implementar controles de deduplicación en el proceso de carga.",
        ],
    },
    "Consistencia": {
        "Crítico": [
            "Sincronizar los catálogos y tablas de referencia entre los sistemas fuente.",
            "Implementar validaciones de consistencia en el proceso de integración de datos.",
            "Establecer proceso de reconciliación periódica entre fuentes (Salud Total / Capital Salud).",
            "Garantizar homogeneidad de códigos de medicamento (CUM / codigoIT) entre archivos.",
            "Crear un Master Data Management (MDM) para las entidades clave (medicamentos, pacientes).",
        ],
        "Aceptable": [
            "Documentar las discrepancias conocidas y sus causas raíz en el catálogo de datos.",
            "Implementar un dashboard de monitoreo de consistencia entre fuentes.",
        ],
    },
    "Integridad": {
        "Crítico": [
            "Implementar restricciones de integridad referencial entre los archivos fuente.",
            "Revisar el proceso de direccionamiento para garantizar que cada prescripción tenga su entrega.",
            "Ejecutar reconciliación de claves huérfanas (NumEntregaMed sin NumEntrega) y definir su disposición.",
            "Establecer controles de validación referencial en el proceso ETL de integración.",
            "Reportar las rupturas de integridad al sistema fuente (MIPRES) para corrección en origen.",
        ],
        "Aceptable": [
            "Documentar las excepciones conocidas de integridad referencial.",
            "Configurar alertas automáticas para detectar nuevas rupturas de integridad.",
        ],
    },
    "Exactitud": {
        "Crítico": [
            "Revisar las reglas de negocio que definen relaciones lógicas entre campos relacionados.",
            "Implementar controles de coherencia en el sistema fuente (ej. cantidad entregada ≤ dirigida).",
            "Ejecutar auditoría de registros inconsistentes para determinar causa raíz.",
            "Establecer proceso de validación cruzada periódica entre campos relacionados.",
        ],
        "Aceptable": [
            "Reforzar las validaciones de coherencia lógica en el proceso ETL.",
            "Documentar las excepciones permitidas a las reglas de negocio.",
        ],
    },
    "Oportunidad": {
        "Crítico": [
            "Revisar la frecuencia de actualización de los datos en el sistema fuente.",
            "Implementar proceso de carga más frecuente para reducir la latencia de datos.",
            "Establecer SLAs de oportunidad con las EPS para la entrega periódica de información.",
            "Evaluar si datos históricos están afectando el indicador y si deben excluirse del cálculo.",
        ],
        "Aceptable": [
            "Documentar el ciclo de actualización esperado para cada fuente de datos.",
            "Monitorear la frescura de los datos en el dashboard de calidad.",
        ],
    },
}


def estado_columna(score: float) -> str:
    if score >= UMBRAL_OPTIMO:
        return "Óptimo"
    elif score >= UMBRAL_ACEPTABLE:
        return "Aceptable"
    return "Crítico"


def detalle_por_columna(
    df: pd.DataFrame,
    reglas: dict,
    cols_relevantes: list[str],
) -> pd.DataFrame:
    """Calidad a nivel de columna: Completitud, Validez, Score, Estado."""
    rows = []
    n = len(df)
    if n == 0:
        return pd.DataFrame()

    for col in df.columns:
        comp = (
            df[col].notna() & (df[col].astype(str).str.strip() != "")
        ).sum() / n * 100

        valid: float | None = None
        if col in reglas:
            regla = reglas[col]
            tipo = regla.get("tipo")
            serie = df[col]

            if tipo == "regex":
                valid = serie.dropna().astype(str).str.match(regla["patron"]).sum() / n * 100
            elif tipo == "dominio":
                valid = serie.isin(regla["valores"]).sum() / n * 100
            elif tipo == "numerico":
                num = pd.to_numeric(serie, errors="coerce")
                mascara = num.notna()
                if "min" in regla:
                    mascara &= num >= regla["min"]
                valid = mascara.sum() / n * 100
            elif tipo == "fecha":
                parsed = pd.to_datetime(serie, errors="coerce", dayfirst=True)
                valid = parsed.notna().sum() / n * 100
            elif tipo == "fecha_yyyymmdd":
                parsed = pd.to_datetime(serie, format="%Y%m%d", errors="coerce")
                valid = parsed.notna().sum() / n * 100

        metricas = [comp] + ([valid] if valid is not None else [])
        score = round(sum(metricas) / len(metricas), 1)

        rows.append({
            "Relevante": col in cols_relevantes,
            "Variable": col,
            "Completitud (%)": round(comp, 1),
            "Validez (%)": round(valid, 1) if valid is not None else None,
            "Score": score,
            "Estado": estado_columna(score),
        })

    df_out = pd.DataFrame(rows)
    return df_out.sort_values(["Relevante", "Score"], ascending=[False, True]).reset_index(drop=True)


def generar_recomendaciones(
    detalle_df: pd.DataFrame,
    scores_dimensiones: dict[str, float],
) -> list[dict]:
    """Recomendaciones DAMA ordenadas por criticidad para variables relevantes."""
    if detalle_df.empty:
        return []

    recomendaciones: list[dict] = []
    relevantes = detalle_df[detalle_df["Relevante"] == True]

    for _, row in relevantes.iterrows():
        var = row["Variable"]

        # Completitud
        comp = row["Completitud (%)"]
        if comp < UMBRAL_ACEPTABLE:
            nivel = "Crítico"
        elif comp < UMBRAL_OPTIMO:
            nivel = "Aceptable"
        else:
            nivel = None
        if nivel:
            recomendaciones.append({
                "variable": var,
                "dimension": "Completitud",
                "nivel": nivel,
                "score": comp,
                "acciones": RECOMENDACIONES_DAMA["Completitud"][nivel],
            })

        # Validez
        valid = row.get("Validez (%)")
        if valid is not None and not pd.isna(valid):
            if valid < UMBRAL_ACEPTABLE:
                nivel_v = "Crítico"
            elif valid < UMBRAL_OPTIMO:
                nivel_v = "Aceptable"
            else:
                nivel_v = None
            if nivel_v:
                recomendaciones.append({
                    "variable": var,
                    "dimension": "Validez",
                    "nivel": nivel_v,
                    "score": valid,
                    "acciones": RECOMENDACIONES_DAMA["Validez"][nivel_v],
                })

    # Dimensiones de archivo
    for dim in ["Unicidad", "Consistencia", "Integridad", "Exactitud", "Oportunidad"]:
        score = scores_dimensiones.get(dim, 100.0)
        if score < UMBRAL_ACEPTABLE:
            nivel = "Crítico"
        elif score < UMBRAL_OPTIMO:
            nivel = "Aceptable"
        else:
            continue
        recomendaciones.append({
            "variable": f"Archivo — {dim}",
            "dimension": dim,
            "nivel": nivel,
            "score": score,
            "acciones": RECOMENDACIONES_DAMA.get(dim, {}).get(nivel, []),
        })

    orden = {"Crítico": 0, "Aceptable": 1}
    return sorted(recomendaciones, key=lambda x: orden.get(x["nivel"], 2))
