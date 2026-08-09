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
A lógica de cada parte vive nos módulos dentro de orcamentos_core/.
"""

import logging

import streamlit as st

from orcamentos_core.config import configurar_logging
from orcamentos_core.data.orcamentos_repo import OrcamentosRepo
from orcamentos_core.data.supabase_client import obter_supabase
from orcamentos_core.styles import aplicar_estilo, indicador_passos, mostrar_cabecalho
from orcamentos_core.ui.login import ecra_login
from orcamentos_core.ui.passo1_foto import passo_1_foto
from orcamentos_core.ui.passo2_confirmar import passo_2_confirmar
from orcamentos_core.ui.passo3_download import passo_3_download
from orcamentos_core.ui.sidebar_historico import mostrar_historico_lateral

configurar_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    st.set_page_config(
        page_title="Meu Orçamento",
        page_icon=None,
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    aplicar_estilo()

    supabase = obter_supabase()
    repo = OrcamentosRepo(supabase)

    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        mostrar_cabecalho()
        ecra_login(supabase)
        return

    mostrar_historico_lateral(repo)

    if "passo" not in st.session_state:
        st.session_state.passo = 1

    mostrar_cabecalho()
    indicador_passos(st.session_state.passo)

    if st.session_state.passo == 1:
        passo_1_foto()
    elif st.session_state.passo == 2:
        passo_2_confirmar(repo)
    elif st.session_state.passo == 3:
        passo_3_download()


if __name__ == "__main__":
    main()
