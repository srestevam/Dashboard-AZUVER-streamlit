
# streamlit_app.py — Dashboard de Relações (AZUVER) — Versão Excel + Barras (corrigido)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Relações AZUVER — Dashboard Informacional", layout="wide")

# ======= Configurações =======
BASELINE_DATE = pd.to_datetime("2025-10-16")  # Matriz Inicial fixa
DEFAULT_XLSX = "AZUVER_dashboard_data.xlsx"   # Planilha Excel com abas: relations_daily, actors, events, event_impacts

# ======= Leitura de dados (Excel) =======
@st.cache_data
def load_data(xlsx_path: str):
    relations = pd.read_excel(xlsx_path, sheet_name="relations_daily", parse_dates=["data"])
    actors = pd.read_excel(xlsx_path, sheet_name="actors")
    events = pd.read_excel(xlsx_path, sheet_name="events", parse_dates=["data"])
    event_impacts = pd.read_excel(xlsx_path, sheet_name="event_impacts")
    return relations, actors, events, event_impacts

def ensure_merge(relations, actors):
    df = relations.merge(actors, on="actor_id", how="left")
    for col in ["R","C"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def grouped_bars(df, title: str):
    if df.empty:
        st.info("Sem dados para exibir.")
        return
    plot_df = df[["nome","R","C"]].copy().sort_values("nome")
    plot_df = plot_df.melt(id_vars="nome", value_vars=["R","C"], var_name="Métrica", value_name="Valor")
    fig = px.bar(plot_df, x="nome", y="Valor", color="Métrica", barmode="group",
                 title=title, text_auto=True)
    fig.update_layout(xaxis_title="Atores", yaxis_title="Valor (0–100)", height=520, margin=dict(l=10,r=10,t=60,b=10))
    st.plotly_chart(fig, use_container_width=True)

# ======= UI Lateral =======
st.sidebar.header("Dados de Entrada")
xlsx_file = st.sidebar.text_input("Caminho da planilha Excel (.xlsx)", value=DEFAULT_XLSX)
uploaded = st.sidebar.file_uploader("...ou envie a planilha Excel", type=["xlsx"])
if uploaded is not None:
    xlsx_file = "uploaded_data.xlsx"
    with open(xlsx_file, "wb") as f:
        f.write(uploaded.getbuffer())
st.session_state["xlsx_file"] = xlsx_file

relations, actors, events, event_impacts = load_data(xlsx_file)
relations = ensure_merge(relations, actors)

# ======= Filtros =======
st.sidebar.header("Filtros")
partido_opt = st.sidebar.selectbox("Partido", ["AZUL","VERMELHO"], index=0)  # seleção única para manter 2 barras por ator
all_dates = sorted(relations["data"].dropna().unique())
if not all_dates:
    st.stop()
date_sel = st.sidebar.selectbox("Data/Jornada", options=all_dates, index=len(all_dates)-1, format_func=lambda d: pd.to_datetime(d).strftime("%Y-%m-%d"))

compare_mode = st.sidebar.checkbox("Comparar com data anterior", value=True)
if compare_mode and len(all_dates) >= 2:
    prev_idx = max(0, list(all_dates).index(date_sel)-1)
    date_cmp = st.sidebar.selectbox("Data de comparação", options=all_dates, index=prev_idx, format_func=lambda d: pd.to_datetime(d).strftime("%Y-%m-%d"))
else:
    date_cmp = None

# ======= Dados filtrados =======
day_df = relations[(relations["data"] == pd.to_datetime(date_sel)) & (relations["partido"] == partido_opt)]
baseline_df = relations[(relations["data"] == BASELINE_DATE) & (relations["partido"] == partido_opt)]

# ======= Título =======
st.title("Dashboard Informacional da AZUVER — Relações de Atores")
st.caption("Visualização diária de R (afinidade) e C (respeito/temor) por ator e partido, com comparação à Matriz Inicial (16/10/2025).")

# ======= Matriz de relacionamento — Atual vs Inicial (barras) =======
st.subheader("Matriz de relacionamento Atual")
col_atual, col_inicial = st.columns(2)

with col_atual:
    grouped_bars(day_df, f"Atual — {pd.to_datetime(date_sel).strftime('%d/%m/%Y')} — {partido_opt}")

with col_inicial:
    grouped_bars(baseline_df, "Inicial — 16/10/2025 — " + partido_opt)

# ======= KPIs (médias simples) =======
st.markdown("### Indicadores do Dia")
k = day_df
if not k.empty:
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric(f"R médio ({partido_opt})", f"{k['R'].mean():.1f}")
    with c2: st.metric(f"C médio ({partido_opt})", f"{k['C'].mean():.1f}")
    if not baseline_df.empty:
        k_bl = baseline_df[["actor_id","R","C"]].rename(columns={"R":"R0","C":"C0"})
        merged_cmp = k.merge(k_bl, on="actor_id", how="left")
        dR = (merged_cmp["R"] - merged_cmp["R0"]).mean(skipna=True)
        dC = (merged_cmp["C"] - merged_cmp["C0"]).mean(skipna=True)
        with c3: st.metric("ΔR médio vs Inicial", f"{dR:+.1f}")
        with c4: st.metric("ΔC médio vs Inicial", f"{dC:+.1f}")
else:
    st.info("Sem dados para os filtros atuais.")

# ======= Top mudanças (depende da data de comparação) =======
st.markdown("### Top mudanças na jornada")
if date_cmp is not None and pd.to_datetime(date_cmp) != pd.to_datetime(date_sel):
    prev_df = relations[(relations["data"] == pd.to_datetime(date_cmp)) & (relations["partido"] == partido_opt)][["actor_id","R","C"]]
    merged = day_df.merge(prev_df, on="actor_id", how="left", suffixes=("","_prev"))
    if not merged.empty and merged["R_prev"].notna().any():
        merged["dR"] = merged["R"] - merged["R_prev"]
        merged["dC"] = merged["C"] - merged["C_prev"]
        def top_table(col, asc, k=5):
            t = merged[merged[col].notna()].sort_values(col, ascending=asc).head(k)[
                ["nome","R","C","dR","dC","obs"]
            ]
            return t
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("**↑ Afinidade (dR)**")
            st.dataframe(top_table("dR", asc=False))
        with c2:
            st.markdown("**↓ Afinidade (dR)**")
            st.dataframe(top_table("dR", asc=True))
        with c3:
            st.markdown("**↑ Respeito/temor (dC)**")
            st.dataframe(top_table("dC", asc=False))
        with c4:
            st.markdown("**↓ Respeito/temor (dC)**")
            st.dataframe(top_table("dC", asc=True))
    else:
        st.info("Sem base comparativa suficiente para calcular dR/dC.")
else:
    st.info("Ative a comparação na barra lateral para ver as mudanças do dia.")

# ======= Eventos e impactos =======
st.markdown("### Eventos e impactos")
ev = events[events["data"] == pd.to_datetime(date_sel)].sort_values("data")
if ev.empty:
    st.write("Sem eventos cadastrados para a data selecionada.")
else:
    # Use f-string normal sem escapes
    def _fmt_event(eid: str) -> str:
        row = ev.loc[ev["event_id"] == eid].iloc[0]
        return f"{eid} — {row['titulo']} ({pd.to_datetime(row['data']).strftime('%d/%m/%Y')})"

    sel_event = st.selectbox("Selecione um evento", options=ev["event_id"], format_func=_fmt_event)

    impacts = event_impacts[event_impacts["event_id"] == sel_event]
    impacts = impacts[impacts["partido"] == partido_opt]
    impacts = impacts.merge(actors, on="actor_id", how="left")
    if impacts.empty:
        st.write("Nenhum impacto registrado para o partido/atores filtrados.")
    else:
        impacts_disp = impacts[["nome","partido","delta_R","delta_C","racional","atraso_dias"]]
        st.dataframe(impacts_disp, use_container_width=True)

st.caption("Versão Excel • Barras agrupadas por ator (R e C) • Matriz Inicial fixada em 16/10/2025 • Seção de Dispersão removida.")
