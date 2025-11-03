
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
    relations_daily = pd.read_excel(xlsx_path, sheet_name="relations_daily")

    return relations, actors, events, event_impacts, relations_daily

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

relations, actors, events, event_impacts, relations_daily = load_data(xlsx_file)
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

# ======= fim da seção de matriz de relacionamento =======
# ====== Valor atual do R — Linha (global) sobre Barras por Grupo (diário; por partido) ======
import plotly.graph_objects as go
import pandas as pd
import unicodedata, re

st.markdown("### Valor atual do R — média global diária × média diária por grupo")

try:
    _rd = relations_daily.copy()
except NameError:
    _rd = relations.copy()

try:
    _actors = actors.copy()
except NameError:
    _actors = None

_rd["data"] = pd.to_datetime(_rd["data"], errors="coerce")
_rd["partido"] = _rd["partido"].astype(str).str.upper().str.strip()

partido_sel_R = st.selectbox(          # <<< variável e KEY distintos desta seção
    "Partido",
    options=["Ambos", "AZUL", "VERMELHO"],
    index=0,
    key="w_Ratual_partido_sel"         # <<< KEY ÚNICO
)

if partido_sel_R != "Ambos":
    _rd = _rd[_rd["partido"] == partido_sel_R]

if _rd.empty:
    st.info("Não há dados de relações diárias para o filtro selecionado.")
else:
    GRUPOS_ORD = [
        "1) Estatais – âmbito interno",
        "2) Estatais – externo/intergovernamental",
        "3) Político-sociais e comunitários",
        "4) Populações vulneráveis",
        "5) Ecossistema informacional e de mídia",
        "6) Atores armados não estatais / irregulares",
    ]

    def _normkey(s: str) -> str:
        s = str(s or "")
        s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
        return re.sub(r"\s+", " ", s).strip().lower()

    NAME_MAP_MULTI = {
        _normkey("APAV (Assoc. de Produtores de VERMELHO)"): ["3) Político-sociais e comunitários"],
        _normkey("ESCURO"): ["2) Estatais – externo/intergovernamental"],
        _normkey("CSOI"): ["2) Estatais – externo/intergovernamental", "5) Ecossistema informacional e de mídia"],
        _normkey("SOWETO VERMELHO"): ["6) Atores armados não estatais / irregulares", "3) Político-sociais e comunitários"],
        _normkey("PCS"): ["3) Político-sociais e comunitários", "5) Ecossistema informacional e de mídia"],
        _normkey("População AZULINA"): ["3) Político-sociais e comunitários", "4) Populações vulneráveis"],
        _normkey("PDC"): ["3) Político-sociais e comunitários", "5) Ecossistema informacional e de mídia"],
        _normkey("AIEA"): ["2) Estatais – externo/intergovernamental", "5) Ecossistema informacional e de mídia"],
        _normkey("CINZA"): ["2) Estatais – externo/intergovernamental"],
        _normkey("MARROM"): ["2) Estatais – externo/intergovernamental"],
        _normkey("FILTO"): ["3) Político-sociais e comunitários", "5) Ecossistema informacional e de mídia"],
        _normkey("VERMELHINOS"): ["3) Político-sociais e comunitários", "4) Populações vulneráveis"],
        _normkey("Descendentes de CHUMBO em TOPÁZIO"): ["3) Político-sociais e comunitários", "4) Populações vulneráveis"],
        _normkey("GELO"): ["2) Estatais – externo/intergovernamental"],
        _normkey("ONGs no TO"): ["3) Político-sociais e comunitários", "4) Populações vulneráveis", "5) Ecossistema informacional e de mídia"],
        _normkey("MPL"): ["6) Atores armados não estatais / irregulares", "3) Político-sociais e comunitários", "5) Ecossistema informacional e de mídia"],
    }

    id_to_name = None
    if _actors is not None and {"actor_id", "nome"}.issubset(_actors.columns):
        aux = _actors[["actor_id", "nome"]].dropna()
        aux["actor_id"] = aux["actor_id"].astype(str).str.strip()
        aux["nome"] = aux["nome"].astype(str).str.strip()
        id_to_name = dict(zip(aux["actor_id"], aux["nome"]))

    def _classify_groups_by_id(actor_id: str) -> list[str]:
        canonical_name = id_to_name.get(str(actor_id).strip()) if (id_to_name and pd.notna(actor_id)) else None
        if not canonical_name or str(canonical_name).strip() == "":
            return []
        glist = NAME_MAP_MULTI.get(_normkey(canonical_name), [])
        return [g for g in dict.fromkeys(glist) if g in GRUPOS_ORD]

    base = _rd[["data", "actor_id", "R"]].dropna(subset=["data", "actor_id", "R"]).copy()

    linha_global = (
        base.groupby("data", as_index=False)
        .agg(R_medio_global=("R", "mean"), n=("R", "size"))
        .sort_values("data")
    )

    base["grupos"] = base["actor_id"].apply(_classify_groups_by_id)
    base = base[base["grupos"].map(lambda x: isinstance(x, list) and len(x) > 0)]
    base = base.explode("grupos").rename(columns={"grupos": "grupo"})

    por_grupo = (
        base.groupby(["data", "grupo"], as_index=False)
        .agg(R_medio=("R", "mean"), n=("R", "size"))
    )

    if linha_global.empty and por_grupo.empty:
        st.info("Sem dados suficientes para o período/partido selecionado.")
    else:
        pivot_mean = por_grupo.pivot_table(index="data", columns="grupo", values="R_medio", aggfunc="mean")
        pivot_n = por_grupo.pivot_table(index="data", columns="grupo", values="n", aggfunc="sum")
        for g in GRUPOS_ORD:
            if g not in pivot_mean.columns:
                pivot_mean[g] = None
                pivot_n[g] = 0
        pivot_mean = pivot_mean[GRUPOS_ORD].sort_index()
        pivot_n = pivot_n[GRUPOS_ORD].loc[pivot_mean.index]

        x_dates = pivot_mean.index.to_pydatetime().tolist()
        group_colors = {
            "1) Estatais – âmbito interno": "#636EFA",
            "2) Estatais – externo/intergovernamental": "#EF553B",
            "3) Político-sociais e comunitários": "#00CC96",
            "4) Populações vulneráveis": "#AB63FA",
            "5) Ecossistema informacional e de mídia": "#FFA15A",
            "6) Atores armados não estatais / irregulares": "#19D3F3",
        }

        fig = go.Figure()
        for g in GRUPOS_ORD:
            y_vals = pivot_mean[g].tolist()
            n_vals = pivot_n[g].tolist()
            fig.add_trace(go.Bar(
                name=g, x=x_dates, y=y_vals,
                marker_color=group_colors.get(g, None),
                hovertemplate="<b>%{x|%d/%m/%Y}</b><br>Grupo: "+g+"<br>R médio (atual): %{y:.2f}<br>Nº de atores no grupo: %{customdata}<extra></extra>",
                customdata=n_vals
            ))

        total_series = linha_global.set_index("data").reindex(pivot_mean.index)
        legenda_partido = partido_sel_R if partido_sel_R != "Ambos" else "Ambos os partidos"
        fig.add_trace(go.Scatter(
            name=f"R médio global diário — {legenda_partido}",
            x=x_dates,
            y=total_series["R_medio_global"].tolist(),
            mode="lines+markers",
            line=dict(width=3, color="#222"),
            hovertemplate="<b>%{x|%d/%m/%Y}</b><br>R médio global: %{y:.2f}<extra></extra>"
        ))

        fig.update_layout(
            barmode="group",
            xaxis_title="Data",
            yaxis_title=f"R (valor atual) — {legenda_partido}",
            legend_title_text="Grupos",
            height=520,
            margin=dict(l=10, r=10, t=40, b=10)
        )
        fig.update_yaxes(zeroline=True, zerolinewidth=1, range=[0, 100])
        fig.update_xaxes(tickformat="%d/%m/%Y")
        # >>> SUPRIMIR DIAS SEM DADOS (sem fins de semana/feriados vazios)
        if len(pivot_mean.index) >= 2:
            full_range = pd.date_range(pivot_mean.index.min(), pivot_mean.index.max(), freq="D")
            missing_dates = full_range.difference(pivot_mean.index)
            if len(missing_dates) > 0:
                fig.update_xaxes(rangebreaks=[dict(values=missing_dates.to_pydatetime().tolist())])

        st.plotly_chart(fig, use_container_width=True)

# ======= fim da seção da linha do tempo ======

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

# ===================== MORAL DAS TROPAS (usa ÚLTIMA JORNADA) =====================
import numpy as np
import pandas as pd
import plotly.graph_objects as go

st.markdown("## MORAL DAS TROPAS")

st.markdown(
"""
**Métrica (IMOR-S 0–100)** — por partido (AZUL/VERMELHO), a partir de:  
**Respeito (C)** + **Apoio civil (R)** − **Estressores** + **PRC** (informado).

**Fórmula**  
IMOR_P = clamp_0_100( 50 + 35Respeito_P + 35ApoioCivil_P + 20PRC_P − 20Estressores_P )

**Faixas**: 0–37 = **BAIXA** · 37–66 = **NORMAL** · 67–100 = **ALTA**.
"""
)

# ---------- Conjuntos de atores ----------
RESPEITO_SET  = ["ESCURO","CSOI","CINZA","MARROM","FILTO","GELO","MPL","PCS"]
APOIO_SET     = ["APAV (Assoc. de Produtores de VERMELHO)","SOWETO VERMELHO","População AZULINA",
                 "VERMELHINOS","Descendentes de CHUMBO em TOPÁZIO","ONGs no TO","AIEA","PDC"]
ESTRESSOR_SET = ["ESCURO","CSOI","CINZA","MARROM","FILTO","GELO","MPL"]

# ---------- Helpers (sem mutar DFs globais) ----------
def _norm_pm1(x):      # 0–100 -> –1…+1
    return float(np.clip((float(x) - 50.0)/50.0, -1.0, 1.0)) if pd.notna(x) else 0.0

def _hostilidade(arr_like):  # 0–100 -> 0…1 (quanto abaixo de 50)
    R = np.asarray(pd.to_numeric(arr_like, errors="coerce"), dtype=float)
    return np.clip((50.0 - R)/50.0, 0.0, 1.0)

def _prc_to_pm1(prc):
    prc = max(0.0001, float(prc))  # evita div/0
    return float(np.clip((prc - 1.0)/(prc + 1.0), -1.0, 1.0))

def _class_moral(v):
    if v >= 67: return "ALTA"
    if v >= 37: return "NORMAL"
    return "BAIXA"

def _detect_time_col(df: pd.DataFrame) -> str | None:
    for c in ["jornada", "data", "timestamp", "date"]:
        if c in df.columns:
            return c
    return None

def _to_datetime_safe(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce", utc=True).dt.tz_convert(None)

def _prepare_rel_local(relations_df: pd.DataFrame, actors_df: pd.DataFrame | None) -> pd.DataFrame:
    """
    Cria cópia local mínima, garantindo 'actor_name' se possível.
    """
    _rel = relations_df.copy(deep=True)
    cols = [c for c in ["partido","actor_id","actor_name","R","C","jornada","data","timestamp","date"] if c in _rel.columns]
    _rel = _rel[cols].copy(deep=True)

    if "actor_name" not in _rel.columns and "actor_id" in _rel.columns and actors_df is not None:
        _act = actors_df.copy(deep=True)
        if {"actor_id","actor_name"}.issubset(_act.columns):
            _map = (_act.drop_duplicates("actor_id").set_index("actor_id")["actor_name"].to_dict())
            _rel["actor_name"] = _rel["actor_id"].map(_map)

    return _rel

def _latest_snapshot(rel_local: pd.DataFrame) -> tuple[pd.DataFrame, str, str]:
    """
    Seleciona a **última jornada disponível** globalmente (mesmo dia para todos).
    Se houver 'jornada' (numérica ou ordinal), usa o max; senão tenta data/timestamp.
    Retorna (df_filtrado, nome_col_tempo, valor_ultimo).
    """
    time_col = _detect_time_col(rel_local)
    if not time_col:
        # Sem coluna temporal: devolve como está (deve ser um snapshot único)
        return rel_local, "(sem coluna temporal)", "(snapshot único)"

    # normaliza só para escolha, sem modificar o original
    _tmp = rel_local[[time_col]].copy()
    if time_col == "jornada":
        # Mantém como está; tenta converter a numérico para garantir max correto
        _last_val = pd.to_numeric(_tmp[time_col], errors="coerce").max()
        df_last = rel_local[pd.to_numeric(rel_local[time_col], errors="coerce") == _last_val].copy(deep=True)
        return df_last, "jornada", str(_last_val)
    else:
        # data/timestamp/date
        _last_dt = _to_datetime_safe(_tmp[time_col]).max()
        df_last = rel_local[_to_datetime_safe(rel_local[time_col]) == _last_dt].copy(deep=True)
        return df_last, time_col, (_last_dt.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(_last_dt) else "inválido")

def calc_imor_s(rel_df_local: pd.DataFrame, partido: str, prc_value: float) -> tuple[float, dict]:
    base = rel_df_local.loc[rel_df_local["partido"] == partido].copy(deep=True)

    c_slice = base.loc[base.get("actor_name").isin(RESPEITO_SET) if "actor_name" in base.columns else [], "C"].dropna()
    respeito = _norm_pm1(c_slice.mean()) if not c_slice.empty else 0.0

    r_slice = base.loc[base.get("actor_name").isin(APOIO_SET) if "actor_name" in base.columns else [], "R"].dropna()
    apoio = _norm_pm1(r_slice.mean()) if not r_slice.empty else 0.0

    e_slice = base.loc[base.get("actor_name").isin(ESTRESSOR_SET) if "actor_name" in base.columns else [], "R"].dropna()
    estressores = float(_hostilidade(e_slice).mean()) if not e_slice.empty else 0.0  # 0..1

    prc = _prc_to_pm1(prc_value)

    imor = float(np.clip(50 + 35*respeito + 35*apoio + 20*prc - 20*estressores, 0, 100))
    comps = {
        "Respeito": respeito,
        "Apoio civil": apoio,
        "PRC (–1..+1)": prc,
        "Estressores (0..1)": estressores
    }
    return imor, comps

# ---------- PRC em sessão (independente de filtros) ----------
if "prc_AZUL" not in st.session_state: st.session_state["prc_AZUL"] = 1.0
if "prc_VERMELHO" not in st.session_state: st.session_state["prc_VERMELHO"] = 1.0

c1, c2 = st.columns(2)
with c1:
    st.number_input("PRC — AZUL (poder AZUL / poder VERMELHO)", min_value=0.05, max_value=20.0, step=0.05, key="prc_AZUL")
with c2:
    st.number_input("PRC — VERMELHO (poder VERMELHO / poder AZUL)", min_value=0.05, max_value=20.0, step=0.05, key="prc_VERMELHO")

# ---------- Preparação LOCAL + última jornada (NÃO altera DFs globais) ----------
_relations_src = relations.copy(deep=True)
_actors_src = actors.copy(deep=True) if "actors" in globals() else None
_rel_local = _prepare_rel_local(_relations_src, _actors_src)
_rel_latest, _time_col, _last_val = _latest_snapshot(_rel_local)

st.caption(f"Snapshot usado na moral: **última {_time_col} = {_last_val}**.")

# ---------- Cálculo ----------
imor_azul, comps_azul = calc_imor_s(_rel_latest, "AZUL",     st.session_state["prc_AZUL"])
imor_verm, comps_verm = calc_imor_s(_rel_latest, "VERMELHO", st.session_state["prc_VERMELHO"])

# ---------- Gráfico ----------
fig = go.Figure()
fig.add_shape(type="rect", x0=0,  x1=37, y0=-0.5, y1=1.5, fillcolor="#ef4444", opacity=0.15, layer="below", line_width=0)
fig.add_shape(type="rect", x0=37, x1=66, y0=-0.5, y1=1.5, fillcolor="#f59e0b", opacity=0.15, layer="below", line_width=0)
fig.add_shape(type="rect", x0=67, x1=100,y0=-0.5, y1=1.5, fillcolor="#10b981", opacity=0.15, layer="below", line_width=0)

fig.add_trace(go.Bar(
    y=["AZUL", "VERMELHO"],
    x=[imor_azul, imor_verm],
    orientation="h",
    text=[f"{imor_azul:.1f} ({_class_moral(imor_azul)})", f"{imor_verm:.1f} ({_class_moral(imor_verm)})"],
    textposition="outside",
    hovertemplate="<b>%{y}</b><br>IMOR: %{x:.1f}<extra></extra>"
))
fig.add_vline(x=37, line_dash="dot", line_color="#666", opacity=0.8)
fig.add_vline(x=66, line_dash="dot", line_color="#666", opacity=0.8)
fig.update_layout(
    height=320, margin=dict(l=80, r=20, t=10, b=30),
    xaxis=dict(range=[0,100], title="Índice de Moral (0–100)"),
    yaxis=dict(autorange="reversed"), showlegend=False
)
st.plotly_chart(fig, use_container_width=True)

# ---------- Componentes ----------
with st.expander("Ver componentes e notas metodológicas"):
    colA, colB = st.columns(2)
    with colA:
        st.write("**AZUL — componentes (–1…+1 | estressores 0…1)**")
        st.json(comps_azul)
    with colB:
        st.write("**VERMELHO — componentes (–1…+1 | estressores 0…1)**")
        st.json(comps_verm)
    st.markdown(
        """
        **Atores usados**  
        • Respeito: ESCURO, CSOI, CINZA, MARROM, FILTO, GELO, MPL, PCS  
        • Apoio civil: APAV, SOWETO VERMELHO, População AZULINA, VERMELHINOS, Descendentes de CHUMBO em TOPÁZIO, ONGs no TO, AIEA, PDC  
        • Estressores: ESCURO, CSOI, CINZA, MARROM, FILTO, GELO, MPL

        *Observação*: PRCs vivem em `st.session_state` e **não** sofrem com filtros do dashboard.
        """
    )
# =================== FIM / MORAL DAS TROPAS ===================
# ======= Evolução diária do R — Ator × Média do Partido =======
import plotly.graph_objects as go

st.markdown("### Evolução diária do R — Ator × Média do Partido")

# Trabalhar em cópia local para não alterar DFs usados em outras seções
_rel_local = relations.copy()
_rel_local["data"] = pd.to_datetime(_rel_local["data"], errors="coerce")

# Lista de atores do partido atual
_opts_df = _rel_local[_rel_local["partido"] == partido_opt].dropna(subset=["nome"])
actor_options = sorted(_opts_df["nome"].unique().tolist())

if not actor_options:
    st.info("Não há atores disponíveis para este partido.")
else:
    actor_sel = st.selectbox(
        "Selecione o ator",
        options=actor_options,
        index=0
    )

    # Série diária do R do ator selecionado (agregação por segurança: média se houver duplicidade)
    actor_daily = (
        _opts_df[_opts_df["nome"] == actor_sel]
        .groupby("data", as_index=False)
        .agg(R_ator=("R", "mean"))
        .sort_values("data")
    )

    # Série diária da média de R do partido
    party_daily = (
        _opts_df.groupby("data", as_index=False)
        .agg(R_medio_partido=("R", "mean"))
        .sort_values("data")
    )

    # Garante o mesmo eixo X (união de datas)
    all_days = pd.DataFrame({"data": sorted(set(actor_daily["data"]).union(set(party_daily["data"])))})
    plot_df = (
        all_days
        .merge(actor_daily, on="data", how="left")
        .merge(party_daily, on="data", how="left")
        .sort_values("data")
    )

    if plot_df.empty or plot_df["data"].isna().all():
        st.info("Sem dados suficientes para plotar a evolução diária.")
    else:
        base, base_light, hl = base_colors(partido_opt)

        fig = go.Figure()

        # Barras: R diário do ator
        fig.add_bar(
            x=plot_df["data"],
            y=plot_df["R_ator"],
            name=f"R do ator — {actor_sel}",
            marker_color=base_light
        )

        # Linha: média diária de R do partido
        fig.add_trace(
            go.Scatter(
                x=plot_df["data"],
                y=plot_df["R_medio_partido"],
                name=f"Média de R — {partido_opt}",
                mode="lines+markers",
                line=dict(width=3, color=base)
            )
        )

        fig.update_layout(
            xaxis_title="Data",
            yaxis_title="R (0–100)",
            height=460,
            margin=dict(l=10, r=10, t=40, b=10),
            legend_title_text="Séries"
        )
        # Escala fixa 0–100 para facilitar leitura
        fig.update_yaxes(range=[0, 100])
        # Formatação amigável da data no hover
        fig.update_xaxes(tickformat="%d/%m/%Y")
        # >>> SUPRIMIR DIAS SEM DADOS (sem fins de semana/feriados vazios)
        if len(pivot_mean.index) >= 2:
            full_range = pd.date_range(pivot_mean.index.min(), pivot_mean.index.max(), freq="D")
            missing_dates = full_range.difference(pivot_mean.index)
            if len(missing_dates) > 0:
                fig.update_xaxes(rangebreaks=[dict(values=missing_dates.to_pydatetime().tolist())])

        st.plotly_chart(fig, use_container_width=True)

# ========== ΔR médio diário — Linha (total) sobre Barras lado a lado por Grupo (filtro por CRI; grupos não exclusivos; com partido) ==========
import plotly.graph_objects as go
import pandas as pd
import unicodedata, re

st.markdown("### ΔR médio diário — filtro por CRI e Partido (linha total sobre barras por grupo; grupos não exclusivos)")

# --- Pré-requisitos: DFs 'events', 'event_impacts' (e opcionalmente 'actors') já carregados no app ---
_ev = events.copy()
_imp = event_impacts.copy()
try:
    _actors = actors.copy()
except NameError:
    _actors = None

# Normalizações defensivas
for col in ["event_id", "data", "CRI_lista"]:
    if col not in _ev.columns:
        _ev[col] = ""
_ev["CRI_lista"] = _ev["CRI_lista"].fillna("")
_ev["data"] = pd.to_datetime(_ev["data"], errors="coerce")

# ======= UI: filtros =======
CRI_OPCOES = [
    "Operações Psicológicas (Op Psc)",
    "Guerra Eletrônica (GE)",
    "Defesa Cibernética",
    "Comunicação Social (Com Soc)",
    "Assuntos Civis (Ass Civ)",
]
colf1, colf2 = st.columns([3, 1])
with colf1:
    cri_sel_delta = st.multiselect(
        "Selecione uma ou mais CRI",
        options=CRI_OPCOES,
        default=[],
        key="w_deltaR_cri_ms"  # <<< KEY ÚNICO
    )
with colf2:
    partido_sel_delta = st.selectbox(
        "Partido",
        options=["Ambos", "AZUL", "VERMELHO"],
        index=0,
        key="w_deltaR_partido_sel"  # <<< KEY ÚNICO
    )

if not cri_sel_delta:
    st.info("Selecione pelo menos uma CRI para aplicar o filtro.")
else:
    # Explode CRI por evento (CRI separadas por ';')
    _ev_cri = (
        _ev[["event_id", "data", "CRI_lista"]]
        .assign(CRI=_ev["CRI_lista"].astype(str).str.split(";"))
        .explode("CRI")
    )
    _ev_cri["CRI"] = _ev_cri["CRI"].fillna("").str.strip()
    cri_sel_set = {c.strip().lower() for c in cri_sel_delta}

    # Eventos que possuem ao menos UMA CRI selecionada
    ev_ok = (
        _ev_cri[_ev_cri["CRI"].str.lower().isin(cri_sel_set)]
        [["event_id", "data"]]
        .drop_duplicates()
    )

    if ev_ok.empty:
        st.warning("Nenhum evento encontrado com as CRI selecionadas.")
    else:
        GRUPOS_ORD = [
            "1) Estatais – âmbito interno",
            "2) Estatais – externo/intergovernamental",
            "3) Político-sociais e comunitários",
            "4) Populações vulneráveis",
            "5) Ecossistema informacional e de mídia",
            "6) Atores armados não estatais / irregulares",
        ]

        def _normkey(s: str) -> str:
            s = str(s or "")
            s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
            return re.sub(r"\s+", " ", s).strip().lower()

        NAME_MAP_MULTI = {
            _normkey("APAV (Assoc. de Produtores de VERMELHO)"): ["3) Político-sociais e comunitários"],
            _normkey("ESCURO"): ["2) Estatais – externo/intergovernamental"],
            _normkey("CSOI"): ["2) Estatais – externo/intergovernamental", "5) Ecossistema informacional e de mídia"],
            _normkey("SOWETO VERMELHO"): ["6) Atores armados não estatais / irregulares", "3) Político-sociais e comunitários"],
            _normkey("PCS"): ["3) Político-sociais e comunitários", "5) Ecossistema informacional e de mídia"],
            _normkey("População AZULINA"): ["3) Político-sociais e comunitários", "4) Populações vulneráveis"],
            _normkey("PDC"): ["3) Político-sociais e comunitários", "5) Ecossistema informacional e de mídia"],
            _normkey("AIEA"): ["2) Estatais – externo/intergovernamental", "5) Ecossistema informacional e de mídia"],
            _normkey("CINZA"): ["2) Estatais – externo/intergovernamental"],
            _normkey("MARROM"): ["2) Estatais – externo/intergovernamental"],
            _normkey("FILTO"): ["3) Político-sociais e comunitários", "5) Ecossistema informacional e de mídia"],
            _normkey("VERMELHINOS"): ["3) Político-sociais e comunitários", "4) Populações vulneráveis"],
            _normkey("Descendentes de CHUMBO em TOPÁZIO"): ["3) Político-sociais e comunitários", "4) Populações vulneráveis"],
            _normkey("GELO"): ["2) Estatais – externo/intergovernamental"],
            _normkey("ONGs no TO"): ["3) Político-sociais e comunitários", "4) Populações vulneráveis", "5) Ecossistema informacional e de mídia"],
            _normkey("MPL"): ["6) Atores armados não estatais / irregulares", "3) Político-sociais e comunitários", "5) Ecossistema informacional e de mídia"],
        }

        id_to_name = None
        try:
            if _actors is not None and {"actor_id","nome"}.issubset(_actors.columns):
                aux = _actors[["actor_id","nome"]].dropna()
                aux["actor_id"] = aux["actor_id"].astype(str).str.strip()
                aux["nome"] = aux["nome"].astype(str).str.strip()
                id_to_name = dict(zip(aux["actor_id"], aux["nome"]))
        except Exception:
            id_to_name = None

        KW_RULES_MULTI = [
            (r'(paramilitar|mil[ií]cia|grupo armado|irregular|guerrilha|bra[cç]o militar|mpl)\b',
             ["6) Atores armados não estatais / irregulares"]),
            (r'\b(conselho|organismo|organiza[cç][aã]o|ag[eê]ncia)\s+(internacional|intergovernamental)\b',
             ["2) Estatais – externo/intergovernamental"]),
            (r'\b(pa[ií]s|estado)\b', ["2) Estatais – externo/intergovernamental"]),
            (r'\b(partido|federa[cç][aã]o|associa[cç][aã]o|sindicato|ong)\b',
             ["3) Político-sociais e comunitários"]),
            (r'(refugiad|deslocad|ferid|idos|crian[cç]a|gestant|vulner[aá]v|desabrig|fam[ií]lia)\b',
             ["4) Populações vulneráveis"]),
            (r'\bpopula[cç][aã]o\b', ["3) Político-sociais e comunitários"]),
        ]

        def _classify_groups(actor_id: str, actor_name: str) -> list[str]:
            canonical_name = None
            if id_to_name and pd.notna(actor_id):
                canonical_name = id_to_name.get(str(actor_id).strip())
            if not canonical_name or str(canonical_name).strip() == "":
                canonical_name = str(actor_name or "").strip()
            nk = _normkey(canonical_name)
            groups = NAME_MAP_MULTI.get(nk, []).copy()
            if not groups:
                for pat, glist in KW_RULES_MULTI:
                    if re.search(pat, nk):
                        groups.extend(glist)
            return [g for g in dict.fromkeys(groups) if g in GRUPOS_ORD]

        # ======= Filtra impacts pelos eventos qualificados E PELO PARTIDO =======
        _imp["partido"] = _imp["partido"].astype(str).str.upper().str.strip()
        imp_ok = _imp[_imp["event_id"].isin(ev_ok["event_id"])].copy()
        if partido_sel_delta != "Ambos":
            imp_ok = imp_ok[imp_ok["partido"] == partido_sel_delta]

        if imp_ok.empty:
            st.warning("Não há impactos correspondentes aos filtros aplicados.")
        else:
            imp_ok = imp_ok.merge(ev_ok, on="event_id", how="left", validate="many_to_one")
            imp_ok["data_dia"] = pd.to_datetime(imp_ok["data"], errors="coerce").dt.floor("D")
            imp_ok["grupos"] = imp_ok.apply(lambda r: _classify_groups(r.get("actor_id"), r.get("actor_name")), axis=1)

            total_diario = (
                imp_ok.groupby("data_dia", as_index=False)
                .agg(delta_R_medio_total=("delta_R", "mean"),
                     n_total=("delta_R", "size"))
                .sort_values("data_dia")
            )

            imp_exploded = imp_ok.explode("grupos")
            imp_exploded = imp_exploded[imp_exploded["grupos"].notna()].copy()
            imp_exploded.rename(columns={"grupos": "grupo"}, inplace=True)

            por_grupo = (
                imp_exploded
                .groupby(["data_dia", "grupo"], as_index=False)
                .agg(delta_R_medio=("delta_R", "mean"),
                     n=("delta_R", "size"))
            )

            all_days = pd.DataFrame({"data_dia": sorted(imp_ok["data_dia"].dropna().unique())})
            grupos_df = pd.DataFrame({"grupo": GRUPOS_ORD})
            grade = all_days.assign(key=1).merge(grupos_df.assign(key=1), on="key", how="left").drop(columns="key")
            barras_full = grade.merge(por_grupo, on=["data_dia", "grupo"], how="left")
            barras_full["delta_R_medio"] = barras_full["delta_R_medio"].fillna(0.0)
            barras_full["n"] = barras_full["n"].fillna(0).astype(int)

            pivot_mean = barras_full.pivot_table(index="data_dia", columns="grupo", values="delta_R_medio", aggfunc="mean")
            pivot_n = barras_full.pivot_table(index="data_dia", columns="grupo", values="n", aggfunc="sum")
            for g in GRUPOS_ORD:
                if g not in pivot_mean.columns:
                    pivot_mean[g] = 0.0
                    pivot_n[g] = 0
            pivot_mean = pivot_mean[GRUPOS_ORD].sort_index()
            pivot_n = pivot_n[GRUPOS_ORD].loc[pivot_mean.index]

            x_dates = pivot_mean.index.to_pydatetime().tolist()
            group_colors = {
                "1) Estatais – âmbito interno": "#636EFA",
                "2) Estatais – externo/intergovernamental": "#EF553B",
                "3) Político-sociais e comunitários": "#00CC96",
                "4) Populações vulneráveis": "#AB63FA",
                "5) Ecossistema informacional e de mídia": "#FFA15A",
                "6) Atores armados não estatais / irregulares": "#19D3F3",
            }

            fig = go.Figure()
            for g in GRUPOS_ORD:
                y_vals = pivot_mean[g].tolist()
                n_vals = pivot_n[g].tolist()
                fig.add_trace(go.Bar(
                    name=g, x=x_dates, y=y_vals,
                    marker_color=group_colors.get(g, None),
                    hovertemplate="<b>%{x|%d/%m/%Y}</b><br>Grupo: "+g+"<br>ΔR médio: %{y:.2f}<br>Nº de variações: %{customdata}<extra></extra>",
                    customdata=n_vals
                ))

            total_series = total_diario.set_index("data_dia").reindex(pivot_mean.index)
            legenda_partido = partido_sel_delta if partido_sel_delta != "Ambos" else "Ambos os partidos"
            fig.add_trace(go.Scatter(
                name=f"ΔR médio diário (total filtrado — {legenda_partido})",
                x=x_dates,
                y=total_series["delta_R_medio_total"].tolist(),
                mode="lines+markers",
                line=dict(width=3, color="#222"),
                hovertemplate="<b>%{x|%d/%m/%Y}</b><br>ΔR médio (total): %{y:.2f}<extra></extra>"
            ))

            fig.update_layout(
                barmode="group",
                xaxis_title="Data",
                yaxis_title=f"ΔR médio (filtrado por CRI; partido: {legenda_partido})",
                legend_title_text="Grupos",
                height=520,
                margin=dict(l=10, r=10, t=40, b=10)
            )
            fig.update_yaxes(zeroline=True, zerolinewidth=1)
            fig.update_xaxes(tickformat="%d/%m/%Y")
            # >>> SUPRIMIR DIAS SEM DADOS (sem fins de semana/feriados vazios)
            if len(pivot_mean.index) >= 2:
                full_range = pd.date_range(pivot_mean.index.min(), pivot_mean.index.max(), freq="D")
                missing_dates = full_range.difference(pivot_mean.index)
                if len(missing_dates) > 0:
                    fig.update_xaxes(rangebreaks=[dict(values=missing_dates.to_pydatetime().tolist())])

            st.plotly_chart(fig, use_container_width=True)
