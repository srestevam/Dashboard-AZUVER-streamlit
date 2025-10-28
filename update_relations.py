# utils/update_relations.py
from __future__ import annotations
from pathlib import Path
import pandas as pd
from typing import Tuple, Optional

# -----------------------------
# Classificações R e C (faixas)
# -----------------------------
def classify_r(value: float) -> str:
    v = int(round(value))
    if v <= 19:  return "Hostilidade extrema (0–19)"
    if v <= 34:  return "Hostil (20–34)"
    if v <= 49:  return "Tenso/Desfavorável (35–49)"
    if v <= 59:  return "Neutro (50–59)"
    if v <= 69:  return "Cooperativo (60–69)"
    if v <= 79:  return "Parceiro (70–79)"
    return "Aliado (80–100)"

def classify_c(value: float) -> str:
    v = int(round(value))
    if v <= 19:  return "Impunidade/Desdêm (0–19)"
    if v <= 39:  return "Respeito/Temor Baixo (20–39)"
    if v <= 59:  return "Respeito/Temor Moderado (40–59)"
    if v <= 79:  return "Respeito/Temor Elevado (60–79)"
    return "Dissuasão Dominante (80–100)"

def _clamp01(v: float, lo: int = 0, hi: int = 100) -> int:
    return int(max(lo, min(hi, round(v))))

def _parse_ptbr_datetime(s: str) -> pd.Timestamp:
    # tolera “espaços duplos” entre data e hora
    clean = " ".join(str(s).split())
    ts = pd.to_datetime(clean, dayfirst=True, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"Data/hora inválida: {s!r}")
    return ts

# -------------------------------------------------------------
# Função principal: aplica deltas e gera nova planilha (XLSX)
# -------------------------------------------------------------
def update_relations_for_date(
    xlsx_path: str | Path,
    date_str: str,
    out_path: Optional[str | Path] = None,
    sheet_relations: str = "relations",
    sheet_events: str = "events",
    sheet_impacts: str = "event_impacts",
    partidos_validos: Tuple[str, str] = ("AZUL", "VERMELHO"),
) -> Path:
    """
    Aplica, para uma data alvo (ex.: '28/10/2025  00:00:00'), a soma de delta_R/delta_C
    dos event_impacts (apenas dos event_id que ocorrem nessa data) sobre as 32 linhas
    da aba 'relations' que representam o estado ANTERIOR das relações nessa mesma data
    (partidos AZUL e VERMELHO). Recalcula class_R e class_C e exporta um novo XLSX
    com exatamente essas mesmas linhas (R, C, class_R, class_C atualizadas).

    Retorna o caminho do arquivo gerado.
    """
    xlsx_path = Path(xlsx_path)
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {xlsx_path}")

    # Data alvo
    target_dt = _parse_ptbr_datetime(date_str)

    # Carrega abas relevantes
    xls = pd.ExcelFile(xlsx_path)
    relations = pd.read_excel(xls, sheet_relations)
    events = pd.read_excel(xls, sheet_events)
    impacts = pd.read_excel(xls, sheet_impacts)

    # Normaliza colunas de data
    for df, col in ((relations, "data"), (events, "data")):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
        else:
            raise KeyError(f"Coluna '{col}' ausente na aba usada.")

    # 1) event_id da data solicitada
    events_dt = events.loc[events["data"] == target_dt]
    event_ids = events_dt["event_id"].dropna().unique().tolist()

    # 2) deltas por (actor_id, partido) apenas desses event_id
    impacts_sel = impacts.loc[impacts["event_id"].isin(event_ids)].copy()
    if not {"actor_id", "partido", "delta_R", "delta_C"}.issubset(impacts_sel.columns):
        raise KeyError("Aba 'event_impacts' precisa conter: actor_id, partido, delta_R, delta_C.")
    grp = (
        impacts_sel.groupby(["actor_id", "partido"], dropna=False)[["delta_R", "delta_C"]]
        .sum()
        .reset_index()
    )

    # 3) conjunto das 32 linhas do estado anterior (mesma data; AZUL/VERMELHO)
    if not {"actor_id", "partido", "R", "C"}.issubset(relations.columns):
        raise KeyError("Aba 'relations' precisa conter: actor_id, partido, R, C, data.")
    base_32 = relations.loc[
        (relations["data"] == target_dt) & (relations["partido"].isin(partidos_validos))
    ].copy()

    # 4) aplica deltas nas correspondências por (actor_id, partido)
    updated = base_32.merge(grp, on=["actor_id", "partido"], how="left", validate="m:1")
    updated["delta_R"] = updated["delta_R"].fillna(0)
    updated["delta_C"] = updated["delta_C"].fillna(0)

    updated["R"] = (updated["R"].astype(float) + updated["delta_R"].astype(float)).map(_clamp01)
    updated["C"] = (updated["C"].astype(float) + updated["delta_C"].astype(float)).map(_clamp01)

    # 5) reclassifica
    updated["class_R"] = updated["R"].map(classify_r)
    updated["class_C"] = updated["C"].map(classify_c)

    # 6) remove colunas auxiliares de delta do output “simples”
    updated_out = updated.drop(columns=["delta_R", "delta_C"])

    # 7) grava nova planilha simples
    if out_path is None:
        stamp = target_dt.strftime("%Y%m%d_%H%M%S")
        out_path = xlsx_path.with_name(f"relations_updated_{stamp}.xlsx")
    out_path = Path(out_path)

    with pd.ExcelWriter(out_path, engine="xlsxwriter") as writer:
        # Grava só o conjunto de 32 linhas com as colunas atualizadas
        updated_out.to_excel(writer, sheet_name="relations_updated", index=False)

    return out_path

# -----------------------------
# Exemplo de uso (fora Streamlit)
# -----------------------------
if __name__ == "__main__":
    infile = "AZUVER_dashboard_data_2.xlsx"  # ajuste o caminho se necessário
    data_alvo = "28/10/2025  00:00:00"
    outfile = update_relations_for_date(infile, data_alvo)
    print(f"Planilha gerada: {outfile}")
