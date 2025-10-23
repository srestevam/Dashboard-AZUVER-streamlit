
# streamlit_app.py — Dashboard de Relações (AZUVER) — Excel + Barras horizontais por métrica + Evolução por ator
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Relações AZUVER — Dashboard Informacional", layout="wide")

# ======= Configurações =======
BASELINE_DATE = pd.to_datetime("2025-10-16")  # Matriz Inicial fixa
DEFAULT_XLSX = "AZUVER_dashboard_data_2.xlsx"   # Planilha Excel com abas: relations_daily, actors, events, event_impacts

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

def base_colors(partido: str):
    # (base_color, base_light, highlight_orange)
    if partido == "VERMELHO":
        return "#c0392b", "#f1948a", "#ffa500"
    return "#3566cc", "#a9c1ff", "#ffa500"

def metric_column(metric: str, label: str, partido: str, day_df: pd.DataFrame, baseline_df: pd.DataFrame, date_sel):
    base, base_light, hl = base_colors(partido)

    # Baseline
    bl = baseline_df[["nome", metric]].dropna().copy()
    import streamlit as st
    bl = bl.sort_values("nome")
    bl.rename(columns={metric: "Valor"}, inplace=True)
    bl["Cor"] = base_light

    fig_top = px.bar(
        bl, y="nome", x="Valor", orientation="h",
        title=f"{label} — Baseline (16/10/2025) — {partido}",
        text_auto=True
    )
    fig_top.update_traces(marker_color=bl["Cor"])
    n = bl["nome"].nunique()
    h = max(260, 40 * n + 120)
    fig_top.update_layout(
        xaxis_title="Valor (0–100)",
        yaxis_title="Atores",
        height=h,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    fig_top.update_yaxes(categoryorder="category ascending")
    st.plotly_chart(fig_top, use_container_width=True)

    # Dia de comparação (date_sel) + destaque mudanças
    cur = day_df[["nome", metric]].dropna().copy()
    cur = cur.sort_values("nome")
    cur.rename(columns={metric: "Valor"}, inplace=True)
    # Map baseline for delta
    ref = bl.set_index("nome")["Valor"]
    cur["Δ"] = cur.apply(lambda r: (r["Valor"] - ref.get(r["nome"], r["Valor"])) if r["nome"] in ref else 0, axis=1)
    cur["Mudou"] = (cur["Δ"].fillna(0).astype(float).round(6) != 0.0)

    fig_bot = px.bar(
        cur, y="nome", x="Valor", orientation="h",
        title=f"{label} — Dia {pd.to_datetime(date_sel).strftime('%d/%m/%Y')} — {partido}",
        text_auto=True,
        color="Mudou",
        color_discrete_map={True: hl, False: base}
    )
    m = cur["nome"].nunique()
    h2 = max(260, 40 * m + 120)
    fig_bot.update_layout(
        xaxis_title="Valor (0–100)",
        yaxis_title="Atores",
        height=h2,
        margin=dict(l=10, r=10, t=50, b=10),
        legend_title_text="Mudou vs Baseline"
    )
    fig_bot.update_yaxes(categoryorder="category ascending")
    st.plotly_chart(fig_bot, use_container_width=True)

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
st.title("Dashboard Informacional da AZUVER")
st.caption("Visualização diária de R (afinidade) e C (respeito/temor) por ator e partido, com comparação à Matriz Inicial (16/10/2025).")

# ======= Nota explicativa (boas práticas de destaque) =======
st.markdown(
    """
**Escalas e Classificações — Referência Analítica**

- **Escala**: R (boas-vontades/afinidade) e C (respeito/dissuasão), ambos em **0–100**.

**Classificação subjetiva (7 níveis, por R):**  
0–19 **Hostilidade extrema** · 20–34 **Hostil** · 35–49 **Tenso/Desfavorável** · 50–59 **Neutro** · 60–69 **Cooperativo** · 70–79 **Parceiro** · 80–100 **Aliado**.

**Classificação subjetiva (5 níveis, por C):**  
0–19 **Impunidade/Desdém** · 20–39 **Respeito/Temor Baixo** · 40–59 **Respeito/Temor Moderado** · 60–79 **Respeito/Temor Elevado** · 80–100 **Dissuasão Dominante**.
""",
)
# ======= Matriz de relacionamento — Atual vs Baseline por métrica (barras horizontais) =======
st.subheader("Matriz de relacionamento Atual")
col_r, col_c = st.columns(2)
with col_r:
    metric_column("R", "R (afinidade)", partido_opt, day_df, baseline_df, date_sel)
with col_c:
    metric_column("C", "C (respeito/temor)", partido_opt, day_df, baseline_df, date_sel)

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

# ======= Variação por ator — barras verticais (Δ vs Dia anterior | seção isolada) =======
st.markdown("### Variação por ator — ΔR e ΔC vs Dia anterior")

# Paletas (tons) — NÃO ALTERAR
POS_GREENS = ["#C8E6C9", "#A5D6A7", "#81C784", "#66BB6A", "#43A047", "#2E7D32"]
NEG_ORANGES = ["#FFE0B2", "#FFCC80", "#FFB74D", "#FFA726", "#FB8C00", "#EF6C00"]

# --------- Dataframes LOCAIS (isolados) ---------
# Não reutiliza/edita day_df/baseline_df/outros; filtra tudo daqui p/ evitar efeitos colaterais
_rel_all_local = relations.copy()
_rel_all_local["data"] = pd.to_datetime(_rel_all_local["data"], errors="coerce")

# Datas locais
_dates_sorted_local = sorted(d for d in _rel_all_local["data"].dropna().unique())
try:
    _idx_local = _dates_sorted_local.index(pd.to_datetime(date_sel))
    _prev_date_local = _dates_sorted_local[_idx_local - 1] if _idx_local > 0 else None
except ValueError:
    _prev_date_local = None

if _prev_date_local is None:
    st.info("Não há data anterior para comparar.")
else:
    # Filtra por PARTIDO (local)
    _rel_party_local = _rel_all_local[_rel_all_local["partido"] == partido_opt].copy()

    # Subconjuntos locais: atual e anterior
    _today_local = _rel_party_local[_rel_party_local["data"] == pd.to_datetime(date_sel)][["actor_id","nome","R","C"]].copy()
    _prev_local  = _rel_party_local[_rel_party_local["data"] == pd.to_datetime(_prev_date_local)][["actor_id","nome","R","C"]].copy()
    if _prev_local.empty or _today_local.empty:
        st.info("Sem dados suficientes no dia anterior ou no dia atual para calcular as variações.")
    else:
        # Merge por actor_id (nome do dia atual preferencial; se faltar, usa do dia anterior)
        _cmp_local = _today_local.merge(
            _prev_local.rename(columns={"R":"R_prev","C":"C_prev","nome":"nome_prev"}),
            on="actor_id", how="left"
        )
        _cmp_local["nome"] = _cmp_local["nome"].fillna(_cmp_local["nome_prev"])
        _cmp_local.drop(columns=["nome_prev"], inplace=True)

        # Deltas locais (sem tocar outros DFs)
        _cmp_local["dR"] = pd.to_numeric(_cmp_local["R"], errors="coerce") - pd.to_numeric(_cmp_local["R_prev"], errors="coerce")
        _cmp_local["dC"] = pd.to_numeric(_cmp_local["C"], errors="coerce") - pd.to_numeric(_cmp_local["C_prev"], errors="coerce")

        # Função de tonalidade (local)
        def _shade_local(delta: float, cap: float = 30.0) -> str:
            if pd.isna(delta) or float(delta) == 0.0:
                return "#BDBDBD"  # neutro
            idx = int(round(min(abs(float(delta)), cap) / cap * (len(POS_GREENS) - 1)))
            return (POS_GREENS if delta > 0 else NEG_ORANGES)[idx]

        # DataFrames de plot locais
        _plot_R_local = _cmp_local[["nome","dR"]].dropna().copy()
        _plot_C_local = _cmp_local[["nome","dC"]].dropna().copy()

        # Ordenação por magnitude (local)
        _plot_R_local["abs"] = _plot_R_local["dR"].abs()
        _plot_C_local["abs"] = _plot_C_local["dC"].abs()
        _plot_R_local = _plot_R_local.sort_values("abs", ascending=False).drop(columns="abs")
        _plot_C_local = _plot_C_local.sort_values("abs", ascending=False).drop(columns="abs")

        # Cores por barra (local, usando as paletas acima)
        _colors_R_local = [_shade_local(v) for v in _plot_R_local["dR"]]
        _colors_C_local = [_shade_local(v) for v in _plot_C_local["dC"]]

        _colR_local, _colC_local = st.columns(2)

        with _colR_local:
            _fig_dR_local = px.bar(
                _plot_R_local,
                x="nome",
                y="dR",
                title=f"ΔR por ator — {partido_opt} (Atual − {pd.to_datetime(_prev_date_local).strftime('%d/%m/%Y')})",
                text_auto=True
            )
            _fig_dR_local.update_traces(marker_color=_colors_R_local)
            _fig_dR_local.update_layout(
                xaxis_title="Atores",
                yaxis_title="ΔR (pontos)",
                height=520,
                margin=dict(l=10, r=10, t=60, b=80)
            )
            _fig_dR_local.add_hline(y=0, line_dash="dot", line_color="#9E9E9E")
            st.plotly_chart(_fig_dR_local, use_container_width=True)

        with _colC_local:
            _fig_dC_local = px.bar(
                _plot_C_local,
                x="nome",
                y="dC",
                title=f"ΔC por ator — {partido_opt} (Atual − {pd.to_datetime(_prev_date_local).strftime('%d/%m/%Y')})",
                text_auto=True
            )
            _fig_dC_local.update_traces(marker_color=_colors_C_local)
            _fig_dC_local.update_layout(
                xaxis_title="Atores",
                yaxis_title="ΔC (pontos)",
                height=520,
                margin=dict(l=10, r=10, t=60, b=80)
            )
            _fig_dC_local.add_hline(y=0, line_dash="dot", line_color="#9E9E9E")
            st.plotly_chart(_fig_dC_local, use_container_width=True)



# ======= Evolução por ator — baseline vs atual (até 4 atores lado a lado) =======
st.markdown("### Evolução por ator — baseline vs data atual")

# Subconjuntos do dia e da baseline (já filtrados por partido_opt acima)
sub_today = relations[(relations["data"] == pd.to_datetime(date_sel)) & (relations["partido"] == partido_opt)]
sub_base  = baseline_df  # já é a baseline filtrada por partido_opt

# Opções de atores disponíveis na interseção baseline × atual
actor_options = sorted(set(sub_today["nome"].tolist()) | set(sub_base.get("nome", pd.Series(dtype=str)).tolist()))
if len(actor_options) == 0:
    st.info("Não há atores para exibir neste partido/datas.")
else:
    sel = st.multiselect(
        "Selecione até 4 atores para comparar (Baseline 16/10/2025 × Data atual)",
        options=actor_options,
        default=actor_options[:4] if len(actor_options) >= 4 else actor_options,
        max_selections=4
    )
    if not sel:
        st.info("Selecione pelo menos um ator para visualizar.")
    else:
        # Garantir no máximo 4 (só por segurança se a UI permitir mais no futuro)
        sel = sel[:4]

        # Paleta consistente com o partido
        pal = {
            "R": ("#c0392b" if partido_opt == "VERMELHO" else "#3566cc"),
            "C": ("#f1948a" if partido_opt == "VERMELHO" else "#6ea0ff")
        }

        def _get_vals(df, name):
            row = df[df["nome"] == name].head(1)
            if row.empty:
                return None, None
            return float(row["R"].iloc[0]) if pd.notna(row["R"].iloc[0]) else None, \
                   float(row["C"].iloc[0]) if pd.notna(row["C"].iloc[0]) else None

        def _render_actor_card(actor_name, col_container):
            with col_container:
                R_base, C_base = _get_vals(sub_base, actor_name)
                R_curr, C_curr = _get_vals(sub_today, actor_name)

                rows = []
                # baseline
                rows.append({"data": BASELINE_DATE, "Métrica": "R", "Valor": R_base})
                rows.append({"data": BASELINE_DATE, "Métrica": "C", "Valor": C_base})
                # atual
                rows.append({"data": pd.to_datetime(date_sel), "Métrica": "R", "Valor": R_curr})
                rows.append({"data": pd.to_datetime(date_sel), "Métrica": "C", "Valor": C_curr})

                chart_long = pd.DataFrame(rows).dropna(subset=["Valor"])

                st.markdown(f"**{actor_name}**")
                if chart_long.empty or chart_long["Métrica"].nunique() == 0:
                    st.info("Sem dados suficientes para plotar R/C.")
                    return

                fig_line = px.line(
                    chart_long,
                    x="data",
                    y="Valor",
                    color="Métrica",
                    markers=True,
                    color_discrete_map={"R": pal["R"], "C": pal["C"]},
                    title=None
                )
                fig_line.update_traces(
                    mode="lines+markers",
                    hovertemplate="<b>%{customdata[0]}</b><br>Data: %{x|%d/%m/%Y}<br>Valor: %{y:.1f}<extra></extra>",
                    customdata=np.stack([chart_long["Métrica"]], axis=-1)
                )
                fig_line.update_layout(
                    xaxis_title=None,
                    yaxis_title="Valor (0–100)",
                    height=320,
                    margin=dict(l=6, r=6, t=8, b=6),
                    showlegend=True
                )
                # Limites suaves 0–100
                fig_line.update_yaxes(range=[0, 100])

                st.plotly_chart(fig_line, use_container_width=True)

                # Métricas Δ (atual - baseline)
                c1, c2 = st.columns(2)
                with c1:
                    dR = (R_curr - R_base) if (R_curr is not None and R_base is not None) else None
                    st.metric("ΔR (atual - baseline)", f"{dR:+.1f}" if dR is not None else "—")
                with c2:
                    dC = (C_curr - C_base) if (C_curr is not None and C_base is not None) else None
                    st.metric("ΔC (atual - baseline)", f"{dC:+.1f}" if dC is not None else "—")

        # Layout em 4 colunas
        cols = st.columns(4)
        for i, actor in enumerate(sel):
            _render_actor_card(actor, cols[i])

        # Se escolher menos de 4, mantém o grid limpo (sem placeholders obrigatórios)

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

# ======= Eventos e impactos (corrigido: filtro por dia inteiro) =======
st.markdown("### Eventos e impactos")

# Garante dtype datetime, caso algo tenha vindo como string
events = events.copy()
events["data"] = pd.to_datetime(events["data"], errors="coerce")

day_start = pd.to_datetime(date_sel).normalize()              # 2025-10-22 00:00:00
day_end   = day_start + pd.Timedelta(days=1)                  # 2025-10-23 00:00:00

# Filtra todos os eventos dentro do dia selecionado (independente da hora)
ev = events[(events["data"] >= day_start) & (events["data"] < day_end)].sort_values("data")

if ev.empty:
    st.write("Sem eventos cadastrados para a data selecionada.")
else:
    def _fmt_event(eid: str) -> str:
        row = ev.loc[ev["event_id"] == eid].iloc[0]
        dt  = pd.to_datetime(row["data"]) if pd.notna(row["data"]) else None
        when = dt.strftime("%d/%m/%Y %H:%M") if dt is not None else "data inválida"
        return f"{eid} — {row.get('titulo', '')} ({when})"

    sel_event = st.selectbox(
        "Selecione um evento",
        options=ev["event_id"].tolist(),
        format_func=_fmt_event
    )

    impacts = event_impacts[event_impacts["event_id"] == sel_event]
    impacts = impacts[impacts["partido"] == partido_opt]
    impacts = impacts.merge(actors, on="actor_id", how="left")

    if impacts.empty:
        st.write("Nenhum impacto registrado para o partido/atores filtrados.")
    else:
        impacts_disp = impacts[["nome", "partido", "delta_R", "delta_C", "racional", "atraso_dias"]]
        st.dataframe(impacts_disp, use_container_width=True)

st.caption("Versão Excel • Barras horizontais por métrica (Baseline vs Dia, destaque laranja) • Linha de evolução por ator (R/C) • Matriz Inicial 16/10/2025.")

# ======= Opinião Pública — Seção (6 subseções com atores ponderados por geografia) =======
import os
import unicodedata
import plotly.graph_objects as go

st.markdown("## Opinião Pública a favor das operações do PARTIDO")

# --- Figuras explicativas lado a lado (img1, img2, img3) ---
img_cols = st.columns(3)
IMG_PATHS = [
    st.session_state.get("img1_path", "img1.png"),
    st.session_state.get("img2_path", "img2.png"),
    st.session_state.get("img3_path", "img3.png"),
]
for i, (col, pth) in enumerate(zip(img_cols, IMG_PATHS), start=1):
    with col:
        if isinstance(pth, str) and os.path.exists(pth):
            st.image(pth, caption=f"img{i}", use_container_width=True)
        else:
            st.image(f"https://placehold.co/640x360?text=img{i}", caption=f"img{i}", use_container_width=True)

# ---------- Persistência por PARTIDO (entradas independentes por partido) ----------
if "op_inputs" not in st.session_state:
    st.session_state["op_inputs"] = {
        "azul":     {"pesquisas": 50, "midia_base": 50, "fb": None, "manif": 50, "midia_val": 50},
        "vermelho": {"pesquisas": 50, "midia_base": 50, "fb": None, "manif": 50, "midia_val": 50},
    }

_party_key = partido_opt.lower()  # "azul" | "vermelho"
_party_store = st.session_state["op_inputs"].get(_party_key, {"pesquisas": 50, "midia_base": 50, "fb": None, "manif": 50, "midia_val": 50})

_key_pesq = f"pesquisas_{_party_key}"
_key_fb   = f"fb_media_{_party_key}"
_key_mid  = f"midia_sent_{_party_key}"
_key_man  = f"manif_{_party_key}"

with st.expander("Entradas do dia — compondo 60% do índice (Pesquisas 15%, Mídia/Redes 20%, Manifestações 25%)", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        pesquisas_val = st.slider(
            "Pesquisas de Opinião Direta (0–100)",
            0, 100, _party_store.get("pesquisas", 50), 1,
            key=_key_pesq,
            help="Resultado agregado de pesquisas do dia (amostra simplificada)."
        )
    with c2:
        st.caption("Feedback rápido — Mídia/Redes (polegar para sinal)")
        fb_val = st.feedback("thumbs", key=_key_fb)  # 1 (up), 0 (down) ou None
        midia_base = st.select_slider(
            "Análise de Mídia e Redes (0–100)",
            options=list(range(0, 101, 5)),
            value=_party_store.get("midia_base", 50),
            key=_key_mid,
            help="Percepção consolidada do tom/volume (sentimento e cobertura)."
        )
        is_pos = (fb_val == 1) or (fb_val == "positive")
        is_neg = (fb_val == 0) or (fb_val == "negative")
        adj = 5 if is_pos else (-5 if is_neg else 0)
        midia_val = int(np.clip(midia_base + adj, 0, 100))
    with c3:
        manif_val = st.slider(
            "Manifestações Públicas (0–100)",
            0, 100, _party_store.get("manif", 50), 1,
            key=_key_man,
            help="Sinal líquido de protestos/atos de apoio (tamanho, frequência, adesão)."
        )

# Atualiza e relê o armazenamento persistente do partido
st.session_state["op_inputs"][_party_key] = {
    "pesquisas": st.session_state.get(_key_pesq, pesquisas_val),
    "midia_base": st.session_state.get(_key_mid, midia_base),
    "fb": st.session_state.get(_key_fb, fb_val),
    "manif": st.session_state.get(_key_man, manif_val),
    "midia_val": midia_val,
}
_party_store = st.session_state["op_inputs"][_party_key]
pesquisas_val = _party_store["pesquisas"]
midia_base    = _party_store["midia_base"]
fb_val        = _party_store["fb"]
midia_val     = _party_store["midia_val"]
manif_val     = _party_store["manif"]

# ---------- Parâmetros fixos (fatores secundários por partido) ----------
ECON_SOC = {"AZUL": 62, "VERMELHO": 43}
HIST_CULT = {"AZUL": 68, "VERMELHO": 49}
econ_val = ECON_SOC.get(partido_opt, 50)
hist_val = HIST_CULT.get(partido_opt, 50)

# ---------- Especificação de atores por geografia (pesos devem somar 100) ----------
REGION_SPECS = {
    "INTERNACIONAL": [
        ("CSOI (Conselho de Segurança)", 35),
        ("AIEA (Ag. Int. de Energia Atômica)", 10),
        ("ONGs (Internacionais)", 25),
        ("GELO", 10),
        ("CINZA", 5),
        ("MARROM", 5),
        ("ESCURO", 10),
    ],
    "CONTINENTE": [
        ("CINZA", 50),
        ("MARROM", 50),
    ],
    "PAÍS VERMELHO": [
        ("SOWETO VERMELHO", 20),
        ("População (VERMELHO)", 60),
        ("APAV", 20),
    ],
    "PAÍS AZUL": [
        ("PDC (Partido Democrático Cristão)", 30),
        ("FILTO (Frente de Libertação de Topázio)", 10),
        ("População (AZUL)", 60),
    ],
    "TOPÁZIO": [
        ("FILTO (Frente de Libertação de Topázio)", 15),
        ("MPL (Movimento Popular de Libertação)", 25),
        ("Vermelhinos em TOPÁZIO", 20),
        ("População (AZUL)", 15),
        ("PDC (Partido Democrático Cristão)", 10),
        ("PCS", 10),
        ("Descendentes de Chumbo em TOPÁZIO", 5),
    ],
    "FENO": [
        ("População (VERMELHO)", 50),
        ("População (AZUL)", 50),
    ],
}

# ---------- Utilidades de cálculo ----------
def _normalize(txt: str) -> str:
    if pd.isna(txt):
        return ""
    t = unicodedata.normalize("NFD", str(txt))
    t = "".join([c for c in t if unicodedata.category(c) != "Mn"])
    return t.upper().strip()

def _actor_score_from_row(row: pd.Series) -> float:
    """
    Converte R/C (0–100) do ator em um escore único 0–100.
    Escolha conservadora: produto normalizado (R*C)/100 mantém limites 0–100.
    """
    r = pd.to_numeric(row.get("R", np.nan), errors="coerce")
    c = pd.to_numeric(row.get("C", np.nan), errors="coerce")
    if pd.isna(r) or pd.isna(c):
        return np.nan
    return float((r * c) / 100.0)

def _rc_weighted_named(df_day_party: pd.DataFrame, region_key: str) -> float:
    """
    Retorna escore 0–100 a partir de uma média ponderada (pesos em % na REGION_SPECS)
    sobre atores específicos por geografia. Renormaliza pesos se atores faltarem.
    Se nenhum ator for encontrado, faz fallback para Σ(R*C)/Σ(C).
    """
    spec = REGION_SPECS.get(region_key, [])
    if df_day_party is None or df_day_party.empty or not spec:
        return 50.0

    df = df_day_party[["actor_id", "nome", "R", "C"]].copy()
    df["nome_norm"] = df["nome"].map(_normalize)

    weighted_scores = []
    weights_found = []

    for label, w in spec:
        target = _normalize(label)
        # match por substring normalizada
        hit = df[df["nome_norm"].str.contains(target, na=False)]
        if hit.empty:
            continue
        # se houver múltiplos, usa média simples do escore desses matches
        score_i = hit.apply(_actor_score_from_row, axis=1).mean(skipna=True)
        if pd.notna(score_i):
            weighted_scores.append(score_i * w)
            weights_found.append(w)

    if weights_found:
        rcw = float(np.sum(weighted_scores) / np.sum(weights_found))
        return float(np.clip(rcw, 0, 100))

    # fallback — usa Σ(R*C)/Σ(C) com todos os atores do partido (no dia)
    R = pd.to_numeric(df["R"], errors="coerce")
    C = pd.to_numeric(df["C"], errors="coerce").clip(lower=0)
    denom = C.sum()
    if denom > 0:
        return float(((R * C).sum() / denom))
    mR = R.mean(skipna=True)
    return float(mR) if pd.notna(mR) else 50.0

def _op_score(rc: float, pesquisas: float, midia: float, manif: float, econ: float, hist: float) -> float:
    """
    OP_Final(região) =
      0.15*Pesquisas + 0.20*Mídia/Redes + 0.25*Manifestações +
      0.25*RC + 0.10*Econ/Soc + 0.05*Hist/Cult
    """
    comp = (
        0.15 * pesquisas +
        0.20 * midia +
        0.25 * manif +
        0.25 * rc +
        0.10 * econ +
        0.05 * hist
    )
    return float(np.clip(comp, 0, 100))

def _gauge(value: float, title: str, subtitle: str = "") -> go.Figure:
    """Gauge 0–100 com faixas qualitativas e threshold no valor (paleta inalterada)."""
    return go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": f"<b>{title}</b><br><span style='font-size:0.85em;color:gray;'>{subtitle}</span>"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#1f77b4"},
                "steps": [
                    {"range": [0, 20], "color": "#EF5350"},
                    {"range": [20, 40], "color": "#FB8C00"},
                    {"range": [40, 60], "color": "#FDD835"},
                    {"range": [60, 80], "color": "#9CCC65"},
                    {"range": [80, 100], "color": "#2E7D32"},
                ],
                "threshold": {"line": {"color": "#000", "width": 2}, "thickness": 0.75, "value": value},
            },
            number={"suffix": " /100"}
        )
    )

def _render_geo_panel(col_container, region_label: str):
    """
    Renderiza uma subseção para a geografia:
    - Calcula RC ponderado pelos atores definidos para a geografia.
    - Calcula OP final com as entradas do dia + fatores secundários do partido.
    - Mostra um gauge 0–100 com um resumo dos componentes.
    """
    with col_container:
        # filtra localmente por data/partido (sem tocar outros DFs)
        df_day_party_local = relations[
            (relations["data"] == pd.to_datetime(date_sel)) &
            (relations["partido"] == partido_opt)
        ].copy()

        rcw = _rc_weighted_named(df_day_party_local, region_label)
        op  = _op_score(rcw, pesquisas_val, midia_val, manif_val, econ_val, hist_val)

        subtitle = (
            f"RC (ponderado) {rcw:.1f} • Pesq {pesquisas_val:.0f} • "
            f"Mídia {midia_val:.0f} • Manif {manif_val:.0f} • Econ {econ_val:.0f} • Hist {hist_val:.0f}"
        )
        st.markdown(f"#### {region_label}")
        fig = _gauge(op, f"{region_label}", subtitle)
        fig.update_layout(height=260, margin=dict(l=8, r=8, t=40, b=8))
        st.plotly_chart(fig, use_container_width=True)

# ---------- Layout em duas colunas (6 subseções) ----------
left_col, right_col = st.columns(2)

with left_col:
    _render_geo_panel(left_col, "INTERNACIONAL")
    st.divider()
    _render_geo_panel(left_col, "CONTINENTE")
    st.divider()
    _render_geo_panel(left_col, "PAÍS VERMELHO")

with right_col:
    _render_geo_panel(right_col, "TOPÁZIO")
    st.divider()
    _render_geo_panel(right_col, "FENO")
    st.divider()
    _render_geo_panel(right_col, "PAÍS AZUL")

# --- Nota de referência analítica (escalas) ---
st.info(
    "**Escala:** R (boas-vontades/afinidade) e C (respeito/dissuasão), ambos em 0–100.\n\n"
    "**Classificação subjetiva (7 níveis, por R):** "
    "0–19 **Hostilidade extrema** · 20–34 **Hostil** · 35–49 **Tenso/Desfavorável** · "
    "50–59 **Neutro** · 60–69 **Cooperativo** · 70–79 **Parceiro** · 80–100 **Aliado**.\n\n"
    "**Classificação subjetiva (5 níveis, por C):** "
    "0–19 **Impunidade/Desdém** · 20–39 **Respeito/Temor Baixo** · 40–59 **Respeito/Temor Moderado** · "
    "60–79 **Respeito/Temor Elevado** · 80–100 **Dissuasão Dominante**."
)
