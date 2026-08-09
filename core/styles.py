"""
Estilo visual da aplicação: CSS global e o indicador "1 → 2 → 3" que
mostra em que passo do fluxo a pessoa está.
"""

import streamlit as st


def aplicar_estilo() -> None:
    """Aplica o CSS que dá à app um aspeto profissional e adaptado a ecrãs
    de telemóvel e a utilizadores com menos à-vontade digital: texto maior,
    botões grandes e fáceis de tocar, e um indicador de passos claro."""
    st.markdown(
        """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        .stApp {
            max-width: 640px;
            margin: 0 auto;
        }

        html, body, [class*="css"] {
            font-size: 17px;
        }

        h1 {
            font-size: 1.8rem !important;
            text-align: center;
            color: #1B4965;
            margin-bottom: 0 !important;
        }
        h2 {
            font-size: 1.4rem !important;
            color: #1B4965;
            margin-bottom: 0.3rem !important;
        }
        h4 {
            color: #1B4965;
        }

        p, label, li, .stMarkdown, .stCaption {
            font-size: 1rem;
        }

        .stButton > button, .stDownloadButton > button {
            font-size: 1.05rem;
            font-weight: 600;
            padding: 0.7rem 1rem;
            border-radius: 12px;
            min-height: 3.1rem;
            border: none;
        }

        .stTextInput input, .stTextArea textarea {
            font-size: 1.05rem;
            border-radius: 10px;
        }

        div[data-testid="stMetric"] {
            background: #EEF2F5;
            padding: 1rem;
            border-radius: 14px;
        }

        /* Indicador de passos */
        .passos-container {
            display: flex;
            align-items: flex-start;
            justify-content: center;
            margin: 0.5rem 0 1.8rem 0;
        }
        .passo {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 76px;
        }
        .passo-numero {
            width: 34px;
            height: 34px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.95rem;
            background: #E3E8EC;
            color: #6B7785;
        }
        .passo.ativo .passo-numero {
            background: #D9A441;
            color: #24313D;
        }
        .passo.concluido .passo-numero {
            background: #1B4965;
            color: #FFFFFF;
        }
        .passo-nome {
            font-size: 0.78rem;
            margin-top: 5px;
            color: #6B7785;
            text-align: center;
        }
        .passo.ativo .passo-nome {
            color: #1B4965;
            font-weight: 700;
        }
        .passo-linha {
            height: 3px;
            width: 34px;
            background: #E3E8EC;
            margin-top: 17px;
        }
        .passo-linha.concluido {
            background: #1B4965;
        }

        /* Cartão de acesso */
        .login-card {
            max-width: 380px;
            margin: 3rem auto 0 auto;
            padding: 2rem 1.5rem;
            border-radius: 16px;
            background: #EEF2F5;
            text-align: center;
        }

        .dica-caixa {
            background: #FBF3E2;
            border-left: 4px solid #D9A441;
            padding: 0.7rem 1rem;
            border-radius: 8px;
            font-size: 0.95rem;
            margin-bottom: 1rem;
        }

        /* Lista de orçamentos na barra lateral (itens clicáveis) */
        [data-testid="stSidebar"] .stButton > button {
            background: #FFFFFF;
            border: 1px solid #E3E8EC;
            color: #24313D;
            text-align: left;
            font-weight: 400;
            font-size: 0.88rem;
            line-height: 1.4;
            padding: 0.55rem 0.75rem;
            border-radius: 10px;
            min-height: auto;
            white-space: normal;
            margin-bottom: 0.4rem;
            box-shadow: none;
        }
        [data-testid="stSidebar"] .stButton > button p {
            text-align: left;
            margin: 0;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            border-color: #1B4965;
            background: #EEF2F5;
            color: #1B4965;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def indicador_passos(passo_atual: int) -> None:
    """Mostra 1 → 2 → 3 no topo da página, para a pessoa saber sempre em
    que ponto do processo está."""
    nomes = ["Foto", "Confirmar", "Descarregar"]
    partes = ['<div class="passos-container">']
    for i, nome in enumerate(nomes, start=1):
        if i < passo_atual:
            estado, rotulo = "concluido", "✓"
        elif i == passo_atual:
            estado, rotulo = "ativo", str(i)
        else:
            estado, rotulo = "pendente", str(i)

        partes.append(
            f'<div class="passo {estado}">'
            f'<div class="passo-numero">{rotulo}</div>'
            f'<div class="passo-nome">{nome}</div>'
            f"</div>"
        )
        if i < len(nomes):
            linha_estado = "concluido" if i < passo_atual else ""
            partes.append(f'<div class="passo-linha {linha_estado}"></div>')
    partes.append("</div>")
    st.markdown("".join(partes), unsafe_allow_html=True)