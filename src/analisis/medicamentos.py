import pandas as pd


def tasas_por_medicamento(dfs: dict[str, pd.DataFrame], top_n: int = 30) -> pd.DataFrame:
    """
    Tasa de entrega por medicamento (CUM / CodigoServicio).
    Retorna: medicamento, total_dirigido, total_entregado, brecha, tasa_pct.
    """
    df = dfs.get("liberar_formula")
    if df is None or df.empty:
        return pd.DataFrame()

    col_med = next((c for c in ["descripcion", "CodigoServicio", "CUM"] if c in df.columns), None)
    if col_med is None or "CantidadDireccionada" not in df.columns:
        return pd.DataFrame()

    work = df[[col_med, "CantidadDireccionada", "CantidadEntregada"]].copy()
    work["CantidadDireccionada"] = pd.to_numeric(work["CantidadDireccionada"], errors="coerce").fillna(0)
    work["CantidadEntregada"] = pd.to_numeric(work["CantidadEntregada"], errors="coerce").fillna(0)

    resumen = (
        work.groupby(col_med, dropna=False)
        .agg(
            total_dirigido=("CantidadDireccionada", "sum"),
            total_entregado=("CantidadEntregada", "sum"),
        )
        .reset_index()
    )
    resumen.rename(columns={col_med: "medicamento"}, inplace=True)
    resumen["brecha"] = resumen["total_dirigido"] - resumen["total_entregado"]
    entregado_f = pd.to_numeric(resumen["total_entregado"], errors="coerce")
    dirigido_f = pd.to_numeric(resumen["total_dirigido"], errors="coerce").replace(0.0, float("nan"))
    resumen["tasa_pct"] = (entregado_f / dirigido_f * 100).round(1)

    return resumen.sort_values("brecha", ascending=False).head(top_n)


def medicamentos_capital_salud(dfs: dict[str, pd.DataFrame], top_n: int = 20) -> pd.DataFrame:
    df = dfs.get("capital_salud")
    if df is None or df.empty:
        return pd.DataFrame()

    col_med = next((c for c in ["Medicamento", "CodigoMedicamento"] if c in df.columns), None)
    if col_med is None:
        return pd.DataFrame()

    work = df[[col_med]].copy()
    if "CantidadMedicamento" in df.columns:
        work["CantidadMedicamento"] = pd.to_numeric(df["CantidadMedicamento"], errors="coerce").fillna(0)
        resumen = work.groupby(col_med).agg(
            registros=(col_med, "count"),
            cantidad_total=("CantidadMedicamento", "sum"),
        ).reset_index()
    else:
        resumen = work.groupby(col_med).size().reset_index(name="registros")

    resumen.rename(columns={col_med: "medicamento"}, inplace=True)
    return resumen.sort_values("registros", ascending=False).head(top_n)
