import streamlit as st
from textwrap import dedent

st.set_page_config(page_title="AZUVER Dashboard - Matrizes de Relacionamento", layout="wide")

HTML = dedent("""\
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AZUVER Dashboard - Matrizes de Relacionamento</title>
    <style>
        :root {
            --bg-primary: #0a0a0a;
            --bg-secondary: #1a1a1a;
            --bg-tertiary: #2a2a2a;
            --text-primary: #e0e0e0;
            --text-secondary: #a0a0a0;
            --border: #333333;
            --shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            --shadow-highlight: 0 12px 40px rgba(0, 0, 0, 0.4);
            --transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            --blue-dark: #0a2540;
            --blue-light: #1e40af;
            --blue-accent: #3b82f6;
            --red-dark: #451a03;
            --red-light: #b91c1c;
            --red-accent: #f87171;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 {
            font-size: 2rem;
            margin: 0;
            background: linear-gradient(135deg, var(--blue-accent), var(--red-accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .controls {
            display: flex; justify-content: center; align-items: center; gap: 10px;
            margin-bottom: 20px; flex-wrap: wrap;
        }
        .edit-btn, .view-toggle {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border);
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            transition: var(--transition);
            box-shadow: var(--shadow);
        }
        .edit-btn:hover, .view-toggle.active {
            background: var(--bg-secondary);
            box-shadow: var(--shadow-highlight);
            transform: translateY(-1px);
        }
        .view-toggle { background: none; color: var(--text-secondary); }
        .view-toggle:hover { color: var(--text-primary); }
        .legend { font-size: 0.8rem; color: var(--text-secondary); margin-top: 10px; text-align: center; }
        .dashboard { display: flex; gap: 20px; justify-content: space-between; width: 100%; max-width: 1400px; margin: 0 auto; }
        .matrix-panel {
            flex: 1; background: var(--bg-secondary); border-radius: 12px; padding: 20px;
            box-shadow: var(--shadow); transition: var(--transition); border: 1px solid var(--border); position: relative;
        }
        .matrix-panel.hidden { display: none; }
        .matrix-panel.highlight { flex: 2; box-shadow: var(--shadow-highlight); border-color: var(--blue-accent); }
        .panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
        .panel-title { font-size: 1.5rem; font-weight: 700; margin: 0; }
        .red .panel-title {
            color: var(--red-accent);
            background: linear-gradient(135deg, var(--red-light), var(--red-accent));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
        }
        .blue .panel-title {
            color: var(--blue-accent);
            background: linear-gradient(135deg, var(--blue-light), var(--blue-accent));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
        }
        .prioritize-btn {
            background: none; border: none; color: var(--text-secondary);
            cursor: pointer; font-size: 0.9rem; padding: 4px 8px; border-radius: 4px; transition: var(--transition);
        }
        .prioritize-btn:hover { color: var(--text-primary); background: var(--bg-tertiary); }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid var(--border); }
        th {
            background: var(--bg-tertiary); font-weight: 600; text-transform: uppercase;
            font-size: 0.85rem; letter-spacing: 0.5px; color: var(--text-secondary);
        }
        .actor { font-weight: 500; color: var(--text-primary); }
        .classification {
            font-weight: 600; padding: 6px 12px; border-radius: 6px; text-align: center; display: inline-block; min-width: 120px;
        }
        /* R */
        .hostilidade-extrema { background: rgba(185, 28, 28, 0.2); color: #f87171; border: 1px solid rgba(185, 28, 28, 0.3); }
        .hostil { background: rgba(220, 38, 38, 0.2); color: #fca5a5; border: 1px solid rgba(220, 38, 38, 0.3); }
        .tenso { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
        .neutro { background: rgba(107, 114, 128, 0.2); color: var(--text-primary); border: 1px solid rgba(107, 114, 128, 0.3); }
        .cooperativo { background: rgba(34, 197, 94, 0.2); color: #86efac; border: 1px solid rgba(34, 197, 94, 0.3); }
        .parceiro { background: rgba(22, 163, 74, 0.2); color: #4ade80; border: 1px solid rgba(22, 163, 74, 0.3); }
        .aliado { background: rgba(5, 150, 105, 0.2); color: #2dd4bf; border: 1px solid rgba(5, 150, 105, 0.3); }
        /* C */
        .impunidade { background: rgba(185, 28, 28, 0.2); color: #f87171; border: 1px solid rgba(185, 28, 28, 0.3); }
        .baixo { background: rgba(220, 38, 38, 0.2); color: #fca5a5; border: 1px solid rgba(220, 38, 38, 0.3); }
        .moderado { background: rgba(107, 114, 128, 0.2); color: var(--text-primary); border: 1px solid rgba(107, 114, 128, 0.3); }
        .elevado { background: rgba(34, 197, 94, 0.2); color: #86efac; border: 1px solid rgba(34, 197, 94, 0.3); }
        .dominante { background: rgba(5, 150, 105, 0.2); color: #2dd4bf; border: 1px solid rgba(5, 150, 105, 0.3); }
        /* Edição */
        .edit-controls { display: none; }
        .edit-mode .view-only { display: none; }
        .edit-mode .edit-controls { display: flex; align-items: center; gap: 8px; }
        .edit-controls input[type="range"] {
            flex: 1; height: 4px; border-radius: 2px; background: var(--border); outline: none;
        }
        .edit-controls input[type="range"]::-webkit-slider-thumb {
            appearance: none; width: 14px; height: 14px; border-radius: 50%; background: var(--blue-accent); cursor: pointer;
        }
        .value-display { min-width: 40px; text-align: center; font-weight: 600; font-size: 0.9rem; color: var(--text-primary); }
        .red .edit-controls input[type="range"]::-webkit-slider-thumb { background: var(--red-accent); }
        @media (max-width: 900px) {
            .dashboard { flex-direction: column; gap: 20px; }
            .matrix-panel.highlight { flex: 1; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>AZUVER 2025 - Dashboard de Matrizes de Relacionamento</h1>
        <p style="color: var(--text-secondary);">Comparação Espelhada: Partido Vermelho vs. Partido Azul</p>
    </div>
    <div class="controls">
        <button class="edit-btn" id="toggleEdit" onclick="toggleEditMode()">Direx: Ativar Edição</button>
        <button class="view-toggle active" onclick="setView('both', this)">Ambos</button>
        <button class="view-toggle" onclick="setView('azul', this)">Azul</button>
        <button class="view-toggle" onclick="setView('vermelho', this)">Vermelho</button>
        <div class="legend">Afinidade | Respeito/Temor (ou Dissuasão)</div>
    </div>

    <div class="dashboard">
        <div class="matrix-panel red" id="redPanel">
            <div class="panel-header">
                <h2 class="panel-title">Partido Vermelho</h2>
                <button class="prioritize-btn" onclick="prioritize('vermelho')">Priorizar</button>
            </div>
            <table>
                <thead>
                    <tr><th>Ator</th><th>Afinidade</th><th>Respeito/Temor</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="actor">APAV (Associação de Produtores de VERMELHO)</td>
                        <td><span class="classification cooperativo view-only">Cooperativo</span><div class="edit-controls"><input type="range" min="0" max="100" value="66" data-type="R" onchange="updateClassification(this)"><span class="value-display">66</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="55" data-type="C" onchange="updateClassification(this)"><span class="value-display">55</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">ESCURO (país extra-regional)</td>
                        <td><span class="classification cooperativo view-only">Cooperativo</span><div class="edit-controls"><input type="range" min="0" max="100" value="60" data-type="R" onchange="updateClassification(this)"><span class="value-display">60</span></div></td>
                        <td><span class="classification elevado view-only">Respeito/Temor Elevado</span><div class="edit-controls"><input type="range" min="0" max="100" value="62" data-type="C" onchange="updateClassification(this)"><span class="value-display">62</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">CSOI (organismo internacional)</td>
                        <td><span class="classification neutro view-only">Neutro</span><div class="edit-controls"><input type="range" min="0" max="100" value="57" data-type="R" onchange="updateClassification(this)"><span class="value-display">57</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="52" data-type="C" onchange="updateClassification(this)"><span class="value-display">52</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">SOWETO VERMELHO (movimento social em VERMELHO)</td>
                        <td><span class="classification hostilidade-extrema view-only">Hostilidade extrema</span><div class="edit-controls"><input type="range" min="0" max="100" value="12" data-type="R" onchange="updateClassification(this)"><span class="value-display">12</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="48" data-type="C" onchange="updateClassification(this)"><span class="value-display">48</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">PCS (crime organizado)</td>
                        <td><span class="classification hostil view-only">Hostil</span><div class="edit-controls"><input type="range" min="0" max="100" value="33" data-type="R" onchange="updateClassification(this)"><span class="value-display">33</span></div></td>
                        <td><span class="classification elevado view-only">Respeito/Temor Elevado</span><div class="edit-controls"><input type="range" min="0" max="100" value="64" data-type="C" onchange="updateClassification(this)"><span class="value-display">64</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">População AZULINA (geral)</td>
                        <td><span class="classification tenso view-only">Tenso/Desfavorável</span><div class="edit-controls"><input type="range" min="0" max="100" value="44" data-type="R" onchange="updateClassification(this)"><span class="value-display">44</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="50" data-type="C" onchange="updateClassification(this)"><span class="value-display">50</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">PDC (oposição em AZUL)</td>
                        <td><span class="classification tenso view-only">Tenso/Desfavorável</span><div class="edit-controls"><input type="range" min="0" max="100" value="38" data-type="R" onchange="updateClassification(this)"><span class="value-display">38</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="56" data-type="C" onchange="updateClassification(this)"><span class="value-display">56</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">AIEA</td>
                        <td><span class="classification neutro view-only">Neutro</span><div class="edit-controls"><input type="range" min="0" max="100" value="50" data-type="R" onchange="updateClassification(this)"><span class="value-display">50</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="50" data-type="C" onchange="updateClassification(this)"><span class="value-display">50</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">CINZA (país vizinho)</td>
                        <td><span class="classification neutro view-only">Neutro</span><div class="edit-controls"><input type="range" min="0" max="100" value="55" data-type="R" onchange="updateClassification(this)"><span class="value-display">55</span></div></td>
                        <td><span class="classification elevado view-only">Respeito/Temor Elevado</span><div class="edit-controls"><input type="range" min="0" max="100" value="60" data-type="C" onchange="updateClassification(this)"><span class="value-display">60</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">MARROM (país vizinho)</td>
                        <td><span class="classification neutro view-only">Neutro</span><div class="edit-controls"><input type="range" min="0" max="100" value="56" data-type="R" onchange="updateClassification(this)"><span class="value-display">56</span></div></td>
                        <td><span class="classification elevado view-only">Respeito/Temor Elevado</span><div class="edit-controls"><input type="range" min="0" max="100" value="60" data-type="C" onchange="updateClassification(this)"><span class="value-display">60</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">FILTO (ator econômico de AZUL)</td>
                        <td><span class="classification neutro view-only">Neutro</span><div class="edit-controls"><input type="range" min="0" max="100" value="52" data-type="R" onchange="updateClassification(this)"><span class="value-display">52</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="48" data-type="C" onchange="updateClassification(this)"><span class="value-display">48</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">“VERMELHINOS” (descendentes de VERMELHO em TOPÁZIO)</td>
                        <td><span class="classification cooperativo view-only">Cooperativo</span><div class="edit-controls"><input type="range" min="0" max="100" value="68" data-type="R" onchange="updateClassification(this)"><span class="value-display">68</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="45" data-type="C" onchange="updateClassification(this)"><span class="value-display">45</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">Descendentes de CHUMBO em TOPÁZIO</td>
                        <td><span class="classification tenso view-only">Tenso/Desfavorável</span><div class="edit-controls"><input type="range" min="0" max="100" value="46" data-type="R" onchange="updateClassification(this)"><span class="value-display">46</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="48" data-type="C" onchange="updateClassification(this)"><span class="value-display">48</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">GELO (país extra-regional)</td>
                        <td><span class="classification neutro view-only">Neutro</span><div class="edit-controls"><input type="range" min="0" max="100" value="58" data-type="R" onchange="updateClassification(this)"><span class="value-display">58</span></div></td>
                        <td><span class="classification elevado view-only">Respeito/Temor Elevado</span><div class="edit-controls"><input type="range" min="0" max="100" value="63" data-type="C" onchange="updateClassification(this)"><span class="value-display">63</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">ONGs no TO (ICRC/MSF/HRW — meta-ator)</td>
                        <td><span class="classification neutro view-only">Neutro</span><div class="edit-controls"><input type="range" min="0" max="100" value="59" data-type="R" onchange="updateClassification(this)"><span class="value-display">59</span></div></td>
                        <td><span class="classification elevado view-only">Respeito/Temor Elevado</span><div class="edit-controls"><input type="range" min="0" max="100" value="70" data-type="C" onchange="updateClassification(this)"><span class="value-display">70</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">MPL</td>
                        <td><span class="classification neutro view-only">Neutro</span><div class="edit-controls"><input type="range" min="0" max="100" value="50" data-type="R" onchange="updateClassification(this)"><span class="value-display">50</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="50" data-type="C" onchange="updateClassification(this)"><span class="value-display">50</span></div></td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="matrix-panel blue" id="bluePanel">
            <div class="panel-header">
                <h2 class="panel-title">Partido Azul</h2>
                <button class="prioritize-btn" onclick="prioritize('azul')">Priorizar</button>
            </div>
            <table>
                <thead>
                    <tr><th>Ator</th><th>Afinidade</th><th>Respeito/Dissuasão</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="actor">APAV (Assoc. de Produtores de VERMELHO)</td>
                        <td><span class="classification tenso view-only">Tenso/Desfavorável</span><div class="edit-controls"><input type="range" min="0" max="100" value="42" data-type="R" onchange="updateClassification(this)"><span class="value-display">42</span></div></td>
                        <td><span class="classification elevado view-only">Respeito/Temor Elevado</span><div class="edit-controls"><input type="range" min="0" max="100" value="60" data-type="C" onchange="updateClassification(this)"><span class="value-display">60</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">ESCURO (país extra-regional)</td>
                        <td><span class="classification neutro view-only">Neutro</span><div class="edit-controls"><input type="range" min="0" max="100" value="55" data-type="R" onchange="updateClassification(this)"><span class="value-display">55</span></div></td>
                        <td><span class="classification elevado view-only">Respeito/Temor Elevado</span><div class="edit-controls"><input type="range" min="0" max="100" value="65" data-type="C" onchange="updateClassification(this)"><span class="value-display">65</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">CSOI (organismo internacional)</td>
                        <td><span class="classification neutro view-only">Neutro</span><div class="edit-controls"><input type="range" min="0" max="100" value="58" data-type="R" onchange="updateClassification(this)"><span class="value-display">58</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="50" data-type="C" onchange="updateClassification(this)"><span class="value-display">50</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">SOWETO VERMELHO (movimento em VERMELHO)</td>
                        <td><span class="classification neutro view-only">Neutro</span><div class="edit-controls"><input type="range" min="0" max="100" value="50" data-type="R" onchange="updateClassification(this)"><span class="value-display">50</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="50" data-type="C" onchange="updateClassification(this)"><span class="value-display">50</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">PCS (crime organizado)</td>
                        <td><span class="classification hostilidade-extrema view-only">Hostilidade extrema</span><div class="edit-controls"><input type="range" min="0" max="100" value="10" data-type="R" onchange="updateClassification(this)"><span class="value-display">10</span></div></td>
                        <td><span class="classification elevado view-only">Respeito/Temor Elevado</span><div class="edit-controls"><input type="range" min="0" max="100" value="60" data-type="C" onchange="updateClassification(this)"><span class="value-display">60</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">População AZULINA (geral)</td>
                        <td><span class="classification cooperativo view-only">Cooperativo</span><div class="edit-controls"><input type="range" min="0" max="100" value="60" data-type="R" onchange="updateClassification(this)"><span class="value-display">60</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="55" data-type="C" onchange="updateClassification(this)"><span class="value-display">55</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">PDC (oposição em AZUL)</td>
                        <td><span class="classification tenso view-only">Tenso/Desfavorável</span><div class="edit-controls"><input type="range" min="0" max="100" value="40" data-type="R" onchange="updateClassification(this)"><span class="value-display">40</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="58" data-type="C" onchange="updateClassification(this)"><span class="value-display">58</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">AIEA</td>
                        <td><span class="classification tenso view-only">Tenso/Desfavorável</span><div class="edit-controls"><input type="range" min="0" max="100" value="48" data-type="R" onchange="updateClassification(this)"><span class="value-display">48</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="50" data-type="C" onchange="updateClassification(this)"><span class="value-display">50</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">CINZA (país vizinho)</td>
                        <td><span class="classification neutro view-only">Neutro</span><div class="edit-controls"><input type="range" min="0" max="100" value="55" data-type="R" onchange="updateClassification(this)"><span class="value-display">55</span></div></td>
                        <td><span class="classification elevado view-only">Respeito/Temor Elevado</span><div class="edit-controls"><input type="range" min="0" max="100" value="60" data-type="C" onchange="updateClassification(this)"><span class="value-display">60</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">MARROM (país vizinho)</td>
                        <td><span class="classification neutro view-only">Neutro</span><div class="edit-controls"><input type="range" min="0" max="100" value="55" data-type="R" onchange="updateClassification(this)"><span class="value-display">55</span></div></td>
                        <td><span class="classification elevado view-only">Respeito/Temor Elevado</span><div class="edit-controls"><input type="range" min="0" max="100" value="60" data-type="C" onchange="updateClassification(this)"><span class="value-display">60</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">FILTO (ator econômico de AZUL)</td>
                        <td><span class="classification tenso view-only">Tenso/Desfavorável</span><div class="edit-controls"><input type="range" min="0" max="100" value="40" data-type="R" onchange="updateClassification(this)"><span class="value-display">40</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="50" data-type="C" onchange="updateClassification(this)"><span class="value-display">50</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">“VERMELHINOS” (descendentes de VERMELHO em TOPÁZIO)</td>
                        <td><span class="classification tenso view-only">Tenso/Desfavorável</span><div class="edit-controls"><input type="range" min="0" max="100" value="35" data-type="R" onchange="updateClassification(this)"><span class="value-display">35</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="45" data-type="C" onchange="updateClassification(this)"><span class="value-display">45</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">Descendentes de CHUMBO em TOPÁZIO</td>
                        <td><span class="classification tenso view-only">Tenso/Desfavorável</span><div class="edit-controls"><input type="range" min="0" max="100" value="45" data-type="R" onchange="updateClassification(this)"><span class="value-display">45</span></div></td>
                        <td><span class="classification moderado view-only">Respeito/Temor Moderado</span><div class="edit-controls"><input type="range" min="0" max="100" value="45" data-type="C" onchange="updateClassification(this)"><span class="value-display">45</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">GELO (país extra-regional)</td>
                        <td><span class="classification cooperativo view-only">Cooperativo</span><div class="edit-controls"><input type="range" min="0" max="100" value="60" data-type="R" onchange="updateClassification(this)"><span class="value-display">60</span></div></td>
                        <td><span class="classification elevado view-only">Respeito/Temor Elevado</span><div class="edit-controls"><input type="range" min="0" max="100" value="65" data-type="C" onchange="updateClassification(this)"><span class="value-display">65</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">ONGs no TO (ICRC/MSF/HRW – meta-ator)</td>
                        <td><span class="classification neutro view-only">Neutro</span><div class="edit-controls"><input type="range" min="0" max="100" value="58" data-type="R" onchange="updateClassification(this)"><span class="value-display">58</span></div></td>
                        <td><span class="classification elevado view-only">Respeito/Temor Elevado</span><div class="edit-controls"><input type="range" min="0" max="100" value="68" data-type="C" onchange="updateClassification(this)"><span class="value-display">68</span></div></td>
                    </tr>
                    <tr>
                        <td class="actor">MPL</td>
                        <td><span class="classification hostilidade-extrema view-only">Hostilidade extrema</span><div class="edit-controls"><input type="range" min="0" max="100" value="12" data-type="R" onchange="updateClassification(this)"><span class="value-display">12</span></div></td>
                        <td><span class="classification baixo view-only">Respeito/Temor Baixo</span><div class="edit-controls"><input type="range" min="0" max="100" value="33" data-type="C" onchange="updateClassification(this)"><span class="value-display">33</span></div></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        let editMode = false;
        let currentView = 'both'; // 'both', 'azul', 'vermelho'

        function toggleEditMode() {
            editMode = !editMode;
            document.body.classList.toggle('edit-mode', editMode);
            const btn = document.getElementById('toggleEdit');
            btn.textContent = editMode ? 'Direx: Desativar Edição' : 'Direx: Ativar Edição';
            if (!editMode) {
                document.querySelectorAll('.edit-controls').forEach(el => {
                    const range = el.querySelector('input[type="range"]');
                    const value = range.value;
                    const type = range.dataset.type;
                    const cell = el.parentElement;
                    const classSpan = cell.querySelector('.classification');
                    classSpan.textContent = getClassification(value, type);
                    classSpan.className = `classification ${getClassName(value, type)} view-only`;
                });
            }
        }

        function updateClassification(range) {
            const value = range.value;
            const type = range.dataset.type;
            const cell = range.closest('td');
            const valueDisplay = cell.querySelector('.value-display');
            const classSpan = cell.querySelector('.classification');
            valueDisplay.textContent = value;
            classSpan.textContent = getClassification(value, type);
            classSpan.className = `classification ${getClassName(value, type)}`;
        }

        function getClassification(value, type) {
            const num = parseInt(value);
            if (type === 'R') {
                if (num <= 19) return 'Hostilidade extrema';
                if (num <= 34) return 'Hostil';
                if (num <= 49) return 'Tenso/Desfavorável';
                if (num <= 59) return 'Neutro';
                if (num <= 69) return 'Cooperativo';
                if (num <= 79) return 'Parceiro';
                return 'Aliado';
            } else { // C
                if (num <= 19) return 'Impunidade/Desdém';
                if (num <= 39) return 'Respeito/Temor Baixo';
                if (num <= 59) return 'Respeito/Temor Moderado';
                if (num <= 79) return 'Respeito/Temor Elevado';
                return 'Dissuasão Dominante';
            }
        }

        function getClassName(value, type) {
            const num = parseInt(value);
            if (type === 'R') {
                if (num <= 19) return 'hostilidade-extrema';
                if (num <= 34) return 'hostil';
                if (num <= 49) return 'tenso';
                if (num <= 59) return 'neutro';
                if (num <= 69) return 'cooperativo';
                if (num <= 79) return 'parceiro';
                return 'aliado';
            } else { // C
                if (num <= 19) return 'impunidade';
                if (num <= 39) return 'baixo';
                if (num <= 59) return 'moderado';
                if (num <= 79) return 'elevado';
                return 'dominante';
            }
        }

        function setView(view, btnEl) {
            currentView = view;
            document.querySelectorAll('.view-toggle').forEach(btn => btn.classList.remove('active'));
            if (btnEl) btnEl.classList.add('active');

            const redPanel = document.getElementById('redPanel');
            const bluePanel = document.getElementById('bluePanel');

            redPanel.classList.remove('hidden', 'highlight');
            bluePanel.classList.remove('hidden', 'highlight');

            if (view === 'azul') {
                redPanel.classList.add('hidden');
                bluePanel.classList.add('highlight');
            } else if (view === 'vermelho') {
                bluePanel.classList.add('hidden');
                redPanel.classList.add('highlight');
            } else {
                redPanel.style.flex = '1';
                bluePanel.style.flex = '1';
            }
        }

        function prioritize(color) {
            if (color === 'azul') setView('azul', document.querySelectorAll('.view-toggle')[2]);
            else setView('vermelho', document.querySelectorAll('.view-toggle')[3]);
        }

        document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('input[type="range"]').forEach(range => {
                updateClassification(range);
            });
            // Define a visualização padrão como 'both' e mantém o primeiro botão ativo
            setView('both', document.querySelectorAll('.view-toggle')[0]);
        });
    </script>
</body>
</html>
""")

st.markdown("### AZUVER 2025 – Matrizes de Relacionamento")
st.caption("Renderizado dentro do Streamlit via componente HTML. Use o botão abaixo para baixar o arquivo HTML completo.")

# Botão de download do HTML
st.download_button(
    label="Baixar HTML completo",
    data=HTML.encode("utf-8"),
    file_name="azuver_dashboard_matrizes.html",
    mime="text/html"
)

st.components.v1.html(HTML, height=1800, scrolling=True)
