import pandas as pd


def desempeno_por_sede(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Tasa de entrega por sede dispensadora (SedeProveedor en direccionamientos
    o DP en liberar_formula).
    """
    df_dir = dfs.get("direccionamientos")
    df_lib = dfs.get("liberar_formula")

    resultados = []

    # Desde LiberarFormula por DP
    if df_lib is not None and "DP" in df_lib.columns and "CantidadDireccionada" in df_lib.columns:
        work = df_lib[["DP", "CantidadDireccionada", "CantidadEntregada"]].copy()
        work["CantidadDireccionada"] = pd.to_numeric(work["CantidadDireccionada"], errors="coerce").fillna(0)
        work["CantidadEntregada"] = pd.to_numeric(work["CantidadEntregada"], errors="coerce").fillna(0)
        g = work.groupby("DP", dropna=False).agg(
            dirigido=("CantidadDireccionada", "sum"),
            entregado=("CantidadEntregada", "sum"),
            registros=("CantidadDireccionada", "count"),
        ).reset_index().rename(columns={"DP": "sede"})
        g["fuente"] = "LiberarFormula"
        resultados.append(g)

    # Desde Direccionamientos por SedeProveedor
    if df_dir is not None and "SedeProveedor" in df_dir.columns:
        work = df_dir.copy()
        col_est = "EstadoDireccionamientoMipres" if "EstadoDireccionamientoMipres" in work.columns else None
        g = work.groupby("SedeProveedor", dropna=False).agg(
            registros=("SedeProveedor", "count"),
        ).reset_index().rename(columns={"SedeProveedor": "sede"})
        g["fuente"] = "Direccionamientos"
        g["dirigido"] = g["registros"]
        g["entregado"] = pd.NA
        resultados.append(g)

    if not resultados:
        return pd.DataFrame()

    combinado = pd.concat(resultados, ignore_index=True)
    combinado["brecha"] = combinado["dirigido"] - combinado["entregado"].fillna(combinado["dirigido"])
    entregado_f = pd.to_numeric(combinado["entregado"], errors="coerce")
    dirigido_f = pd.to_numeric(combinado["dirigido"], errors="coerce").replace(0.0, float("nan"))
    combinado["tasa_pct"] = (entregado_f / dirigido_f * 100).round(1)
    return combinado.sort_values("registros", ascending=False)


def distribucion_tipo_usuario(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = dfs.get("direccionamientos")
    if df is None or "TipoUsuario" not in df.columns:
        return pd.DataFrame()

    return (
        df.groupby("TipoUsuario", dropna=False)
        .size()
        .reset_index(name="cantidad")
        .sort_values("cantidad", ascending=False)
    )


def distribucion_contratacion(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = dfs.get("direccionamientos")
    if df is None or "ModContratacionPago" not in df.columns:
        return pd.DataFrame()

    return (
        df.groupby("ModContratacionPago", dropna=False)
        .size()
        .reset_index(name="cantidad")
        .sort_values("cantidad", ascending=False)
    )
