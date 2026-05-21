import pandas as pd


def analizar_fallas(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Agrupa por MotivoNoEntrega y CodigoError los registros no entregados.
    Retorna DataFrame con columna motivo, codigo_error, cantidad, porcentaje.
    """
    df = dfs.get("liberar_formula")
    if df is None or df.empty:
        return pd.DataFrame()

    if "Estado" not in df.columns:
        return pd.DataFrame()

    no_entregados = df[df["Estado"].astype(str).str.strip() != "Entregado"].copy()
    if no_entregados.empty:
        return pd.DataFrame()

    col_motivo = "MotivoNoEntrega" if "MotivoNoEntrega" in df.columns else None
    col_error = "CodigoError" if "CodigoError" in df.columns else None

    group_cols = [c for c in [col_motivo, col_error] if c]
    if not group_cols:
        return pd.DataFrame()

    resumen = (
        no_entregados.groupby(group_cols, dropna=False)
        .size()
        .reset_index(name="cantidad")
        .sort_values("cantidad", ascending=False)
    )

    total = resumen["cantidad"].sum()
    resumen["porcentaje"] = (resumen["cantidad"] / total * 100).round(1)
    resumen["porcentaje_acum"] = resumen["porcentaje"].cumsum().round(1)

    return resumen


def fallas_por_medicamento(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = dfs.get("liberar_formula")
    if df is None or "Estado" not in df.columns:
        return pd.DataFrame()

    no_ent = df[df["Estado"].astype(str).str.strip() != "Entregado"]
    col_med = next((c for c in ["descripcion", "CodigoServicio", "CUM"] if c in df.columns), None)
    if col_med is None:
        return pd.DataFrame()

    return (
        no_ent.groupby(col_med, dropna=False)
        .size()
        .reset_index(name="no_entregas")
        .sort_values("no_entregas", ascending=False)
        .head(30)
    )
