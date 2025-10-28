# utils/update_relations.py
"""
Atualiza as relações (R/C) aplicando os deltas dos eventos de uma data-alvo
sobre o ÚLTIMO snapshot ANTERIOR (data < alvo) da aba relations_daily,
gerando uma planilha simples com as 32 linhas esperadas (ou a quantidade encontrada)
com R, C, class_R e class_C atualizadas.

Uso direto:
    python utils/update_relations.py

Integração:
    from utils.update_relations import update_relations_for_date
    out_path = update_relations_for_date("AZUVER_dashboard_data_2.xlsx", "28/10/2025  00:00:00")
"""

from __future__ import annotations
from pathlib import Path
from typing import Tuple, Optional
import warnings
import pandas as pd

# Silencia o aviso do openpyxl sobre validação de dados
warnings.filterwarnings(
    "ignore",
    message="Data Validation extension is not supported and will be removed",
    category=UserWarning,
    module="openpyxl",
)

# =============================
# Classificações R e C (faixas)
# =============================
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
    if v <= 19:  return "Impunidade/Desdém (0–19)"
    if v <= 39:  return "Respeito/Temor Baixo (20–39)"
    if v <= 59:  return "Respeito/Temor Moderado (40–59)"
    if v <= 79:  return "Respeito/Temor Elevado (60–79)"
    return "Dissuasão Dominante (80–100)"

def _clamp01(v: float, lo: int = 0, hi: int = 100) -> int:
    return int(max(lo, min(hi, round(v))))

def _parse_ptbr_datetime(s: str) -> pd.Timestamp:
    # tolera espaços duplos
    clean = " ".join(str(s).split())
    ts = pd.to_datetime(clean, dayfirst=True, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"Data/hora inválida: {s!r}")
    return ts

def _pick_excel_engine() -> str:
    try:
        import xlsxwriter  # noqa: F401
        return "xlsxwriter"
    except Exception:
        return "openpyxl"

# =========================================================
# Função principal: aplica deltas e gera nova planilha XLSX
# =========================================================
def update_relations_for_date(
    xlsx_path: str | Path,
    date_str: str,
    out_path: Optional[str | Path] = None,
    sheet_relations: str = "relations_daily",
    sheet_events: str = "events",
    sheet_impacts: str = "event_impacts",
    partidos_validos: Tuple[str, str] = ("AZUL", "VERMELHO"),
    enforce_count: Optional[int] = 32,       # None para não checar quantidade
    allow_same_day_reapply: bool = False,    # False = guarda contra reaplicação
    verbose: bool = True,
) -> Path:
    """
    Para a data alvo (ex.: '28/10/2025  00:00:00'):
      1) identifica event_id na aba de eventos dessa data (igualdade exata de timestamp);
      2) soma delta_R/delta_C em event_impacts por (actor_id, partido);
      3) aplica sobre o ÚLTIMO snapshot ANTERIOR em relations_daily (data < alvo) dos partidos válidos;
      4) recalcula class_R e class_C; seta 'data' como a data-alvo;
      5) salva um XLSX simples contendo essas linhas, com R/C e classes atualizadas.

    Parâmetros:
      - enforce_count: se 32, avisa se o número de linhas divergir; None desativa a checagem.
      - allow_same_day_reapply: se True, permite usar base_date == target_dt (reaplicando no mesmo dia).
    """
    xlsx_path = Path(xlsx_path)
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {xlsx_path}")

    target_dt = _parse_ptbr_datetime(date_str)
    partidos_norm = [str(p).upper().strip() for p in partidos_validos]

    # Carrega abas
    xls = pd.ExcelFile(xlsx_path)
    try:
        relations = pd.read_excel(xls, sheet_name=sheet_relations)
    except ValueError as e:
        raise ValueError(f"Aba '{sheet_relations}' não encontrada. Abas: {xls.sheet_names}") from e
    try:
        events = pd.read_excel(xls, sheet_name=sheet_events)
    except ValueError as e:
        raise ValueError(f"Aba '{sheet_events}' não encontrada. Abas: {xls.sheet_names}") from e
    try:
        impacts = pd.read_excel(xls, sheet_name=sheet_impacts)
    except ValueError as e:
        raise ValueError(f"Aba '{sheet_impacts}' não encontrada. Abas: {xls.sheet_names}") from e

    # Conferência de colunas mínimas
    req_rel = {"actor_id", "partido", "data", "R", "C"}
    req_evt = {"event_id", "data"}
    req_imp = {"event_id", "actor_id", "partido", "delta_R", "delta_C"}
    if not req_rel.issubset(relations.columns):
        raise KeyError(f"Aba '{sheet_relations}' precisa conter: {sorted(req_rel)}.")
    if not req_evt.issubset(events.columns):
        raise KeyError(f"Aba '{sheet_events}' precisa conter: {sorted(req_evt)}.")
    if not req_imp.issubset(impacts.columns):
        raise KeyError(f"Aba '{sheet_impacts}' precisa conter: {sorted(req_imp)}.")

    # Normaliza datas
    relations["data"] = pd.to_datetime(relations["data"], dayfirst=True, errors="coerce")
    events["data"] = pd.to_datetime(events["data"], dayfirst=True, errors="coerce")

    # 1) eventos exatamente no target_dt
    events_dt = events.loc[events["data"] == target_dt]
    event_ids = events_dt["event_id"].dropna().astype(str).unique().tolist()
    if not event_ids:
        # Ajuda de diagnóstico
        same_day = events.loc[events["data"].dt.date == target_dt.date(), ["event_id", "data"]]
        raise ValueError(
            f"Nenhum evento encontrado exatamente em {target_dt}.\n"
            f"Eventos no mesmo dia (ignorando horário):\n{same_day.to_string(index=False)}"
        )

    # 2) soma de deltas do dia por (actor_id, partido)
    impacts_sel = impacts.loc[impacts["event_id"].astype(str).isin(event_ids)].copy()
    impacts_sel["actor_id"] = impacts_sel["actor_id"].astype(str)
    impacts_sel["partido_norm"] = impacts_sel["partido"].astype(str).str.upper().str.strip()
    grp = (
        impacts_sel.groupby(["actor_id", "partido_norm"], dropna=False)[["delta_R", "delta_C"]]
        .sum()
        .reset_index()
    )

    # 3) escolher baseline: ÚLTIMA data ANTERIOR (data < alvo), por partidos válidos
    relations["partido_norm"] = relations["partido"].astype(str).str.upper().str.strip()
    valid_mask = relations["partido_norm"].isin(partidos_norm)
    prev_mask = valid_mask & (relations["data"] < target_dt)
    base_date = relations.loc[prev_mask, "data"].max()

    if pd.isna(base_date):
        # sem baseline anterior — só permitimos reaplicação se explicitamente autorizado
        same_day_mask = valid_mask & (relations["data"] == target_dt)
        if same_day_mask.any() and not allow_same_day_reapply:
            raise RuntimeError(
                "Não há snapshot anterior (data < alvo). Existe snapshot no próprio dia.\n"
                "Para evitar reaplicar deltas, ajuste a data base ou chame com "
                "allow_same_day_reapply=True se tiver certeza do que está fazendo."
            )
        elif same_day_mask.any():
            base_date = target_dt
        else:
            raise ValueError(
                "Não há snapshot anterior nem no próprio dia para os partidos válidos. "
                "Crie ao menos um snapshot base antes da data-alvo."
            )

    base_32 = relations.loc[
        (relations["data"] == base_date) & (relations["partido_norm"].isin(partidos_norm))
    ].copy()

    if enforce_count is not None and len(base_32) != enforce_count:
        # Apenas alerta; não interrompe
        print(
            f"[AVISO] Quantidade de linhas na base ({len(base_32)}) difere do esperado ({enforce_count})."
        )

    # Normaliza chaves para merge
    base_32["actor_id"] = base_32["actor_id"].astype(str)
    base_32["partido_norm"] = base_32["partido_norm"].astype(str)

    # 4) aplica deltas por (actor_id, partido_norm)
    updated = base_32.merge(
        grp, on=["actor_id", "partido_norm"], how="left", validate="m:1"
    )
    updated["delta_R"] = updated["delta_R"].fillna(0.0)
    updated["delta_C"] = updated["delta_C"].fillna(0.0)

    # garante numericidade
    updated["R"] = pd.to_numeric(updated["R"], errors="coerce").fillna(0.0)
    updated["C"] = pd.to_numeric(updated["C"], errors="coerce").fillna(0.0)

    updated["R"] = (updated["R"] + updated["delta_R"]).map(_clamp01)
    updated["C"] = (updated["C"] + updated["delta_C"]).map(_clamp01)

    # 5) classes + data do novo snapshot
    updated["class_R"] = updated["R"].map(classify_r)
    updated["class_C"] = updated["C"].map(classify_c)
    updated["data"] = target_dt  # o snapshot gerado é do dia-alvo

    # remove auxiliares e coluna partido_norm (mantém 'partido' original)
    updated_out = updated.drop(columns=["delta_R", "delta_C", "partido_norm"], errors="ignore")

    # 6) grava
    if out_path is None:
        stamp = target_dt.strftime("%Y%m%d_%H%M%S")
        out_path = xlsx_path.with_name(f"relations_updated_{stamp}.xlsx")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    engine = _pick_excel_engine()
    with pd.ExcelWriter(out_path, engine=engine) as writer:
        updated_out.to_excel(writer, sheet_name="relations_updated", index=False)

    if verbose:
        print(f"- Abas detectadas: {xls.sheet_names}")
        print(f"- Data alvo: {target_dt} | Base date usada: {base_date}")
        print(f"- Eventos na data: {event_ids}")
        print(f"- Linhas base (encontradas): {len(base_32)}")
        print(f"- Salvo em: {out_path}")

    return out_path


# ===================
# Execução de teste
# ===================
if __name__ == "__main__":
    infile = "AZUVER_dashboard_data_2.xlsx"   # ajuste conforme necessário
    data_alvo = "28/10/2025  00:00:00"
    outfile = update_relations_for_date(
        infile,
        data_alvo,
        sheet_relations="relations_daily",
        sheet_events="events",
        sheet_impacts="event_impacts",
        partidos_validos=("AZUL", "VERMELHO"),
        enforce_count=32,
        allow_same_day_reapply=False,
        verbose=True,
    )
    print(f"Planilha gerada: {outfile}")
