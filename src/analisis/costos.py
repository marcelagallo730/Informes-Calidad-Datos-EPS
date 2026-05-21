import pandas as pd


def impacto_financiero(dfs: dict[str, pd.DataFrame]) -> dict:
    """
    Calcula el costo de la brecha: Valor × (CantidadDireccionada - CantidadEntregada).
    Retorna resumen global y top medicamentos por impacto financiero.
    """
    df = dfs.get("liberar_formula")
    if df is None or df.empty:
        return {"global": {}, "por_medicamento": pd.DataFrame()}

    cols_req = {"Valor", "CantidadDireccionada", "CantidadEntregada"}
    if not cols_req.issubset(df.columns):
        return {"global": {}, "por_medicamento": pd.DataFrame()}

    work = df.copy()
    for col in ["Valor", "CantidadDireccionada", "CantidadEntregada"]:
        work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0)

    work["brecha_unidades"] = (work["CantidadDireccionada"] - work["CantidadEntregada"]).clip(lower=0)
    work["costo_brecha"] = work["Valor"] * work["brecha_unidades"]
    work["costo_total_dirigido"] = work["Valor"] * work["CantidadDireccionada"]

    global_res = {
        "costo_brecha_total": round(work["costo_brecha"].sum(), 0),
        "costo_total_dirigido": round(work["costo_total_dirigido"].sum(), 0),
        "porcentaje_perdida": round(
            work["costo_brecha"].sum() / work["costo_total_dirigido"].sum() * 100, 1
        ) if work["costo_total_dirigido"].sum() > 0 else 0,
    }

    col_med = next((c for c in ["descripcion", "CodigoServicio", "CUM"] if c in work.columns), None)

    if col_med:
        por_med = (
            work.groupby(col_med, dropna=False)
            .agg(
                costo_brecha=("costo_brecha", "sum"),
                costo_dirigido=("costo_total_dirigido", "sum"),
                unidades_brecha=("brecha_unidades", "sum"),
            )
            .reset_index()
            .rename(columns={col_med: "medicamento"})
            .sort_values("costo_brecha", ascending=False)
            .head(20)
        )
        brecha_f = pd.to_numeric(por_med["costo_brecha"], errors="coerce")
        dirigido_f = pd.to_numeric(por_med["costo_dirigido"], errors="coerce").replace(0.0, float("nan"))
        por_med["porcentaje_perdida"] = (
            brecha_f / dirigido_f * 100
        ).round(1)
    else:
        por_med = pd.DataFrame()

    return {"global": global_res, "por_medicamento": por_med}
