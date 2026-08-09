"""
Orçamentos - Papel para PDF
----------------------------
Aplicação Streamlit que permite tirar uma foto a um orçamento escrito à
mão e transformá-la automaticamente num PDF profissional, pronto a
enviar ao cliente.

Fluxo em 3 passos, pensado para ser usado a partir de um telemóvel por
pessoas com pouca experiência em aplicações digitais:
    1. Foto do orçamento em papel
    2. Confirmação e edição dos dados extraídos
    3. Descarregar o PDF final

Este ficheiro é só o ponto de entrada: orquestra o fluxo entre passos.
A lógica de cada parte vive nos módulos dentro de .
"""

import logging

import streamlit as st

from config import configurar_logging
from data.orcamentos_repo import OrcamentosRepo
from data.supabase_client import obter_supabase
from styles import aplicar_estilo, indicador_passos
from ui.login import ecra_login
from ui.passo1 import passo_1_foto
from ui.passo2 import passo_2_confirmar
from ui.passo3 import passo_3_download
from ui.sidebar_hist import mostrar_historico_lateral

configurar_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    st.set_page_config(
        page_title="Orçamentos",
        page_icon="🧾",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    aplicar_estilo()

    supabase = obter_supabase()
    repo = OrcamentosRepo(supabase)

    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.markdown("<h1>Orçamentos</h1>", unsafe_allow_html=True)
        ecra_login(supabase)
        return

    mostrar_historico_lateral(repo)

    if "passo" not in st.session_state:
        st.session_state.passo = 1

    st.markdown("<h1>Orçamentos</h1>", unsafe_allow_html=True)
    indicador_passos(st.session_state.passo)

    if st.session_state.passo == 1:
        passo_1_foto()
    elif st.session_state.passo == 2:
        passo_2_confirmar(repo)
    elif st.session_state.passo == 3:
        passo_3_download()


if __name__ == "__main__":
    main()