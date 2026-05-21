import pandas as pd


def calcular_brechas(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Compara CantidadDireccionada vs CantidadEntregada por CodigoServicio/Estado.
    Retorna DataFrame con columnas: CodigoServicio, descripcion, Estado,
    dirigido, entregado, brecha, tasa_entrega_pct.
    """
    df = dfs.get("liberar_formula")
    if df is None or df.empty:
        return pd.DataFrame()

    cols_req = {"CantidadDireccionada", "CantidadEntregada", "CodigoServicio", "Estado"}
    if not cols_req.issubset(df.columns):
        return pd.DataFrame()

    work = df[list(cols_req | ({"descripcion"} & set(df.columns)))].copy()
    work["CantidadDireccionada"] = pd.to_numeric(work["CantidadDireccionada"], errors="coerce").fillna(0)
    work["CantidadEntregada"] = pd.to_numeric(work["CantidadEntregada"], errors="coerce").fillna(0)

    grupo = (
        work.groupby(["CodigoServicio", "Estado"], dropna=False)
        .agg(
            dirigido=("CantidadDireccionada", "sum"),
            entregado=("CantidadEntregada", "sum"),
            registros=("CantidadDireccionada", "count"),
        )
        .reset_index()
    )

    grupo["brecha"] = grupo["dirigido"] - grupo["entregado"]
    entregado_f = pd.to_numeric(grupo["entregado"], errors="coerce")
    dirigido_f = pd.to_numeric(grupo["dirigido"], errors="coerce").replace(0.0, float("nan"))
    grupo["tasa_entrega_pct"] = (entregado_f / dirigido_f * 100).round(1)

    return grupo.sort_values("brecha", ascending=False)


def resumen_brecha_global(dfs: dict[str, pd.DataFrame]) -> dict:
    df = dfs.get("liberar_formula")
    if df is None or df.empty:
        return {}

    cd = pd.to_numeric(df.get("CantidadDireccionada", pd.Series(dtype=float)), errors="coerce").fillna(0)
    ce = pd.to_numeric(df.get("CantidadEntregada", pd.Series(dtype=float)), errors="coerce").fillna(0)

    total_dir = cd.sum()
    total_ent = ce.sum()
    brecha = total_dir - total_ent

    return {
        "total_dirigido": int(total_dir),
        "total_entregado": int(total_ent),
        "brecha_total": int(brecha),
        "tasa_entrega_pct": round(total_ent / total_dir * 100, 1) if total_dir else 0,
        "registros_no_entregados": int((df.get("Estado", pd.Series()) != "Entregado").sum()) if "Estado" in df.columns else 0,
    }
