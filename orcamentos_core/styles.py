"""
Identidade visual da aplicação: tokens de cor/tipografia, CSS global,
o indicador de passos ("régua") e o selo de conclusão do Passo 3.

Direção de design: o produto transforma um orçamento manuscrito em papel
num documento oficial - por isso a linguagem visual vem do mundo do
desenho técnico e da medição (régua, papel, carimbo), em vez de um
template genérico de SaaS. Ver conversa de design para o racional
completo.
"""

import streamlit as st

# Tokens de cor - usados também fora do CSS (ex.: nomes por extenso nos
# comentários), para que uma mudança de paleta só precise de acontecer aqui.
CORES = {
    "papel": "#FAFAF9",
    "papel_card": "#FFFFFF",
    "tinta": "#24262B",
    "tinta_suave": "#6B6D72",
    "risco": "#3D5A73",
    "risco_escuro": "#2C4356",
    "selo": "#2C4356",
    "linha": "#E3E3DF",
    "sucesso": "#3F6B4A",
}


def aplicar_estilo() -> None:
    """Aplica o CSS global: tipografia (Space Grotesk / Work Sans / IBM
    Plex Mono), paleta "papel + risco técnico", e todos os componentes
    reutilizáveis (régua de passos, anotações, cartões do histórico,
    selo de conclusão)."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600&family=Work+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap');

        :root {
            --papel: #FAFAF9;
            --papel-card: #FFFFFF;
            --tinta: #24262B;
            --tinta-suave: #6B6D72;
            --risco: #3D5A73;
            --risco-escuro: #2C4356;
            --selo: #2C4356;
            --linha: #E3E3DF;
            --sucesso: #3F6B4A;
            --raio: 4px;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        .stApp {
            max-width: 640px;
            margin: 0 auto;
            background: var(--papel);
        }

        html, body, [class*="css"] {
            font-family: 'Work Sans', sans-serif;
            font-size: 17px;
            color: var(--tinta);
        }

        /* Cabeçalho / wordmark */
        .cabecalho {
            text-align: center;
            margin: 0.3rem 0 0.1rem;
        }
        .wordmark {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 600;
            font-size: 1.55rem;
            letter-spacing: -0.01em;
            margin: 0;
            color: var(--tinta);
        }
        .wordmark span { color: var(--risco); }

        h2 {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 600;
            font-size: 1.25rem !important;
            color: var(--tinta);
            letter-spacing: -0.01em;
            margin-bottom: 0.6rem !important;
        }

        /* Rótulos de secção (substituem os antigos h4 coloridos) */
        h4 {
            font-family: 'IBM Plex Mono', monospace;
            font-weight: 500;
            font-size: 0.72rem !important;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--tinta-suave) !important;
            border-top: 1px solid var(--linha);
            padding-top: 1rem;
            margin-top: 1.3rem !important;
        }

        p, label, li, .stMarkdown, .stCaption {
            font-size: 1rem;
            color: var(--tinta);
        }
        .stCaption, [data-testid="stCaptionContainer"] {
            color: var(--tinta-suave) !important;
        }

        /* Botões */
        .stButton > button, .stDownloadButton > button {
            font-family: 'Work Sans', sans-serif;
            font-size: 1.02rem;
            font-weight: 600;
            padding: 0.7rem 1rem;
            border-radius: var(--raio);
            min-height: 3.1rem;
            box-shadow: none;
        }
        .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
            background: var(--risco);
            color: var(--papel);
            border: 1px solid var(--risco);
        }
        .stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
            background: var(--risco-escuro);
            border-color: var(--risco-escuro);
        }
        .stButton > button[kind="secondary"], .stDownloadButton > button[kind="secondary"] {
            background: transparent;
            color: var(--tinta);
            border: 1px solid var(--linha);
        }
        .stButton > button[kind="secondary"]:hover, .stDownloadButton > button[kind="secondary"]:hover {
            border-color: var(--risco);
            color: var(--risco);
        }

        /* Campos de texto */
        .stTextInput input, .stTextArea textarea {
            font-family: 'Work Sans', sans-serif;
            font-size: 1.02rem;
            background: var(--papel-card);
            border: 1px solid var(--linha) !important;
            border-radius: var(--raio);
            color: var(--tinta);
        }
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: var(--risco) !important;
            box-shadow: 0 0 0 1px var(--risco) !important;
        }

        /* Total do orçamento (st.metric) - figuras em monoespaçado */
        div[data-testid="stMetric"] {
            background: var(--papel-card);
            border: 1px solid var(--linha);
            padding: 0.9rem 1rem;
            border-radius: var(--raio);
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
            color: var(--tinta-suave) !important;
        }
        div[data-testid="stMetricValue"] {
            font-family: 'IBM Plex Mono', monospace !important;
            font-weight: 500 !important;
            color: var(--tinta) !important;
        }

        /* Indicador de passos - "régua" */
        .regua-wrap {
            padding: 6px 6px 20px;
        }
        .regua {
            position: relative;
            height: 2px;
            background: var(--linha);
            margin: 0 6px 10px;
        }
        .regua-preenchida {
            position: absolute;
            top: 0;
            left: 0;
            height: 2px;
            background: var(--risco);
            transition: width 0.2s ease;
        }
        .regua-marcas {
            display: flex;
            justify-content: space-between;
            margin: 0 -2px;
        }
        .marca {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            flex: 1;
        }
        .marca-tick {
            width: 2px;
            height: 9px;
            background: var(--linha);
            margin-top: -12px;
        }
        .marca.feito .marca-tick, .marca.ativo .marca-tick {
            background: var(--risco);
        }
        .marca-nome {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 10.5px;
            color: var(--tinta-suave);
        }
        .marca.ativo .marca-nome { color: var(--risco); font-weight: 500; }
        .marca.feito .marca-nome { color: var(--tinta); }

        /* Anotação (substitui a antiga caixa de dica amarela) */
        .anotacao {
            border: 1px solid var(--linha);
            border-radius: var(--raio);
            padding: 0.7rem 0.9rem;
            display: flex;
            gap: 10px;
            align-items: baseline;
            margin-bottom: 1rem;
        }
        .anotacao-marca {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 10.5px;
            color: var(--risco);
            white-space: nowrap;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        .anotacao-texto {
            font-size: 0.9rem;
            color: var(--tinta-suave);
            line-height: 1.5;
        }

        /* Selo de conclusão (Passo 3) */
        .carimbo-wrap {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 1.2rem 0.5rem 0.6rem;
            text-align: center;
        }
        .carimbo {
            width: 84px;
            height: 84px;
            border: 2px dashed var(--selo);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transform: rotate(-8deg);
            margin-bottom: 1rem;
        }
        .carimbo-texto {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 600;
            font-size: 10.5px;
            letter-spacing: 0.06em;
            color: var(--selo);
            text-transform: uppercase;
            line-height: 1.3;
        }
        .carimbo-titulo {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 600;
            font-size: 1.05rem;
            margin: 0 0 0.3rem;
            color: var(--tinta);
        }
        .carimbo-sub {
            font-size: 0.85rem;
            color: var(--tinta-suave);
            margin: 0;
        }

        /* Lista de orçamentos na barra lateral (itens clicáveis) */
        [data-testid="stSidebar"] {
            background: var(--papel);
        }
        [data-testid="stSidebar"] .stButton > button {
            background: var(--papel-card);
            border: 1px solid var(--linha);
            color: var(--tinta);
            text-align: left;
            font-weight: 400;
            font-size: 0.86rem;
            line-height: 1.5;
            padding: 0.6rem 0.8rem;
            border-radius: var(--raio);
            min-height: auto;
            white-space: normal;
            margin-bottom: 0.5rem;
        }
        [data-testid="stSidebar"] .stButton > button p {
            text-align: left;
            margin: 0;
        }
        [data-testid="stSidebar"] .stButton > button strong {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 500;
            color: var(--tinta);
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            border-color: var(--risco);
            background: var(--papel);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mostrar_cabecalho() -> None:
    """Mostra o wordmark da aplicação. Substitui o antigo `<h1>` simples
    por um tratamento tipográfico consistente com a identidade visual."""
    st.markdown(
        '<div class="cabecalho"><p class="wordmark">Meu<span>Orçamento</span></p></div>',
        unsafe_allow_html=True,
    )


def indicador_passos(passo_atual: int) -> None:
    """Mostra o progresso do fluxo (Foto → Confirmar → Descarregar) como
    uma "régua": uma linha com marcas, em vez de círculos numerados -
    o mesmo vocabulário visual de medição usado no resto da app."""
    nomes = ["Foto", "Confirmar", "Descarregar"]
    total_passos = len(nomes)
    percentagem = ((passo_atual - 1) / (total_passos - 1)) * 100 if total_passos > 1 else 0

    marcas_html = ""
    for i, nome in enumerate(nomes, start=1):
        if i < passo_atual:
            estado = "feito"
        elif i == passo_atual:
            estado = "ativo"
        else:
            estado = ""
        marcas_html += (
            f'<div class="marca {estado}">'
            f'<div class="marca-tick"></div>'
            f'<div class="marca-nome">{nome}</div>'
            f"</div>"
        )

    st.markdown(
        f"""
        <div class="regua-wrap">
            <div class="regua"><div class="regua-preenchida" style="width:{percentagem}%;"></div></div>
            <div class="regua-marcas">{marcas_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_carimbo_conclusao(
    titulo: str = "Orçamento gerado",
    subtitulo: str = "O PDF está pronto para descarregar.",
) -> None:
    """Mostra o "selo" de conclusão no Passo 3 - o único momento
    deliberadamente decorativo da app, reservado para a confirmação de
    que o orçamento está pronto a enviar ao cliente."""
    st.markdown(
        f"""
        <div class="carimbo-wrap">
            <div class="carimbo"><span class="carimbo-texto">Pronto<br>a enviar</span></div>
            <p class="carimbo-titulo">{titulo}</p>
            <p class="carimbo-sub">{subtitulo}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
