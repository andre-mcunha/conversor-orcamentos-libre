"""
Passo 1 - Captura/upload da foto do orçamento em papel.
"""

import json
import logging

import streamlit as st
from PIL import Image

from orcamentos_core.ai import extrator
from orcamentos_core.utils import dados_vazios

logger = logging.getLogger(__name__)


def _obter_cliente_ia_sessao():
    """Cria o cliente de IA uma única vez por sessão (evita recriá-lo a
    cada interação) e guarda-o em st.session_state."""
    if "cliente_ia" not in st.session_state:
        st.session_state.cliente_ia = extrator.obter_cliente_ia()
    return st.session_state.cliente_ia


def passo_1_foto() -> None:
    st.markdown("## Passo 1 - Foto do Orçamento")
    st.markdown(
        '<div class="anotacao"><span class="anotacao-marca">Nota</span>'
        '<span class="anotacao-texto">Tire a foto num local bem iluminado, '
        "com o papel esticado e sem sombras por cima do texto.</span></div>",
        unsafe_allow_html=True,
    )

    aba_camera, aba_ficheiro = st.tabs(["Tirar Foto", "Escolher Ficheiro"])
    with aba_camera:
        foto_camera = st.camera_input("Tirar foto", label_visibility="collapsed")
    with aba_ficheiro:
        foto_ficheiro = st.file_uploader(
            "Escolher imagem", type=["jpg", "jpeg", "png"], label_visibility="collapsed"
        )

    arquivo_imagem = foto_ficheiro
    if foto_camera is not None:
        arquivo_imagem = foto_camera

    if arquivo_imagem is not None:
        imagem = Image.open(arquivo_imagem)
        st.image(imagem, caption="Pré-visualização", use_container_width=True)

        if st.button("Confirmar e Analisar", use_container_width=True, type="primary"):
            with st.spinner("A analisar o orçamento... alguns segundos."):
                try:
                    cliente_ia = _obter_cliente_ia_sessao()
                    dados = extrator.extrair_dados_da_imagem(imagem, cliente_ia)
                    st.session_state.dados_extraidos = dados
                    st.session_state.passo = 2
                    st.rerun()
                except json.JSONDecodeError:
                    logger.warning("Não foi possível interpretar o JSON devolvido pela IA.")
                    st.error(
                        "Não conseguimos interpretar os dados da foto. "
                        "Tente novamente com mais luz e o papel bem esticado."
                    )
                except Exception as e:
                    logger.exception("Erro ao analisar a foto.")
                    st.error("Ocorreu um erro ao analisar a foto. Tente novamente.")
                    with st.expander("Detalhes técnicos"):
                        st.code(str(e))

    st.markdown("---")
    if st.button("Prefiro preencher os dados manualmente"):
        st.session_state.dados_extraidos = dados_vazios()
        st.session_state.passo = 2
        st.rerun()
