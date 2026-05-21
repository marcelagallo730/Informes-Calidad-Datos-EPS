"""
CLI: genera un reporte Excel completo con los indicadores DAMA y los análisis.
Uso: python main.py [--ruta-datos <ruta>] [--salida <archivo.xlsx>]
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).parent))

from src.loader import cargar_datos, NOMBRES_DISPLAY
from src.calidad_dama.indicador import calcular_indicadores, DIMENSIONES
from src.analisis import brechas, fallas, medicamentos, proveedores, costos

RUTA_DATOS_DEFAULT = r"C:\Users\Usuario\Documents\Claude\Análisis Calidad Completo"
CONFIG_DIR = Path(__file__).parent / "config"


def _cargar_yaml(ruta: Path) -> dict:
    if ruta.exists():
        with open(ruta, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _semaforo_excel(score: float) -> str:
    if score >= 85:
        return "00B050"  # verde
    elif score >= 70:
        return "FFC000"  # amarillo
    return "FF0000"      # rojo


def generar_reporte(ruta_datos: str, ruta_salida: Path) -> None:
    print(f"Cargando datos desde: {ruta_datos}")
    dfs = cargar_datos(ruta_datos)
    print(f"  {len(dfs)} archivos cargados: {', '.join(dfs.keys())}")

    columnas_relevantes = _cargar_yaml(CONFIG_DIR / "columnas_relevantes.yaml")
    reglas = _cargar_yaml(CONFIG_DIR / "reglas_validez.yaml")
    pesos_raw = _cargar_yaml(CONFIG_DIR / "pesos_dama.yaml")
    pesos = {d: float(pesos_raw.get(d, 1.0)) for d in DIMENSIONES}

    print("Calculando indicadores DAMA...")
    resultado = calcular_indicadores(dfs, columnas_relevantes, reglas, pesos)

    print(f"Generando reporte Excel: {ruta_salida}")
    with pd.ExcelWriter(ruta_salida, engine="xlsxwriter") as writer:
        wb = writer.book

        # ── Formatos ──────────────────────────────────────────────────────────
        fmt_titulo = wb.add_format({"bold": True, "font_size": 14, "bg_color": "#2C3E50", "font_color": "white", "align": "center"})
        fmt_header = wb.add_format({"bold": True, "bg_color": "#3498DB", "font_color": "white", "border": 1, "align": "center"})
        fmt_num = wb.add_format({"num_format": "#,##0.0", "border": 1, "align": "center"})
        fmt_pct = wb.add_format({"num_format": "#,##0.0", "border": 1, "align": "center"})
        fmt_moneda = wb.add_format({"num_format": "$#,##0", "border": 1})
        fmt_normal = wb.add_format({"border": 1})

        # ── Hoja 1: Resumen DAMA ──────────────────────────────────────────────
        ws = wb.add_worksheet("Indicadores DAMA")
        writer.sheets["Indicadores DAMA"] = ws
        ws.set_column("A:A", 28)
        ws.set_column("B:I", 16)

        ws.merge_range("A1:I1", "INDICADORES DE CALIDAD DAMA — ANÁLISIS FARMACÉUTICO", fmt_titulo)
        ws.write("A2", f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", wb.add_format({"italic": True}))

        headers = ["Dimensión"] + [NOMBRES_DISPLAY.get(k, k) for k in dfs.keys()] + ["TOTAL"]

        # Global
        ws.write(3, 0, "INDICADOR GLOBAL (todas las variables)", wb.add_format({"bold": True, "font_size": 12}))
        for col, h in enumerate(headers):
            ws.write(4, col, h, fmt_header)

        archivos = [k for k in resultado["global"] if not k.startswith("__")]
        for row, dim in enumerate(DIMENSIONES + ["score_total"], start=5):
            etiqueta = "SCORE TOTAL" if dim == "score_total" else dim
            ws.write(row, 0, etiqueta, wb.add_format({"bold": dim == "score_total", "border": 1}))
            for col, archivo in enumerate(archivos, start=1):
                val = resultado["global"][archivo].get(dim, 0)
                color = _semaforo_excel(val)
                fmt_c = wb.add_format({"num_format": "#,##0.0", "border": 1, "align": "center",
                                        "bg_color": color, "font_color": "white", "bold": dim == "score_total"})
                ws.write(row, col, val, fmt_c)
            total = resultado["global"].get("__total__", {}).get(dim, 0)
            color_t = _semaforo_excel(total)
            fmt_t = wb.add_format({"num_format": "#,##0.0", "border": 1, "align": "center",
                                    "bg_color": color_t, "font_color": "white", "bold": True})
            ws.write(row, len(archivos) + 1, total, fmt_t)

        # Focalizado
        fila_base = 5 + len(DIMENSIONES) + 3
        ws.write(fila_base, 0, "INDICADOR FOCALIZADO (columnas seleccionadas)",
                 wb.add_format({"bold": True, "font_size": 12}))
        for col, h in enumerate(headers):
            ws.write(fila_base + 1, col, h, fmt_header)

        for row, dim in enumerate(DIMENSIONES + ["score_total"], start=fila_base + 2):
            etiqueta = "SCORE TOTAL" if dim == "score_total" else dim
            ws.write(row, 0, etiqueta, wb.add_format({"bold": dim == "score_total", "border": 1}))
            for col, archivo in enumerate(archivos, start=1):
                val = resultado["focalizado"][archivo].get(dim, 0)
                color = _semaforo_excel(val)
                fmt_c = wb.add_format({"num_format": "#,##0.0", "border": 1, "align": "center",
                                        "bg_color": color, "font_color": "white", "bold": dim == "score_total"})
                ws.write(row, col, val, fmt_c)
            total = resultado["focalizado"].get("__total__", {}).get(dim, 0)
            color_t = _semaforo_excel(total)
            fmt_t = wb.add_format({"num_format": "#,##0.0", "border": 1, "align": "center",
                                    "bg_color": color_t, "font_color": "white", "bold": True})
            ws.write(row, len(archivos) + 1, total, fmt_t)

        # ── Hoja 2: Brechas ───────────────────────────────────────────────────
        df_brechas = brechas.calcular_brechas(dfs)
        if not df_brechas.empty:
            df_brechas.to_excel(writer, sheet_name="Brechas Dispensación", index=False)

        # ── Hoja 3: Motivos no entrega ────────────────────────────────────────
        df_fallas = fallas.analizar_fallas(dfs)
        if not df_fallas.empty:
            df_fallas.to_excel(writer, sheet_name="Motivos No Entrega", index=False)

        # ── Hoja 4: Medicamentos ──────────────────────────────────────────────
        df_meds = medicamentos.tasas_por_medicamento(dfs)
        if not df_meds.empty:
            df_meds.to_excel(writer, sheet_name="Medicamentos ST", index=False)

        df_cs = medicamentos.medicamentos_capital_salud(dfs)
        if not df_cs.empty:
            df_cs.to_excel(writer, sheet_name="Medicamentos CS", index=False)

        # ── Hoja 5: Proveedores ───────────────────────────────────────────────
        df_prov = proveedores.desempeno_por_sede(dfs)
        if not df_prov.empty:
            df_prov.to_excel(writer, sheet_name="Proveedores", index=False)

        # ── Hoja 6: Costos ────────────────────────────────────────────────────
        res_costos = costos.impacto_financiero(dfs)
        df_costos_med = res_costos.get("por_medicamento", pd.DataFrame())
        if not df_costos_med.empty:
            df_costos_med.to_excel(writer, sheet_name="Impacto Financiero", index=False)

    print(f"Reporte generado exitosamente: {ruta_salida}")


def main():
    parser = argparse.ArgumentParser(description="Generador de reporte de calidad DAMA")
    parser.add_argument("--ruta-datos", default=RUTA_DATOS_DEFAULT, help="Ruta a los archivos CSV")
    parser.add_argument(
        "--salida",
        default=str(Path(__file__).parent / f"reporte_calidad_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"),
        help="Ruta del archivo Excel de salida",
    )
    args = parser.parse_args()

    generar_reporte(args.ruta_datos, Path(args.salida))


if __name__ == "__main__":
    main()
