"""
Passo 3 - Descarregar o PDF gerado.
"""

import logging
import re

import streamlit as st

logger = logging.getLogger(__name__)


def passo_3_download() -> None:
    if "pdf_path" not in st.session_state:
        st.session_state.passo = 1
        st.rerun()

    st.markdown("## Orçamento Pronto")
    st.success("O PDF foi gerado com sucesso.")

    nome_base = (st.session_state.get("nome_cliente_final") or "cliente").strip()
    nome_base = re.sub(r"\s+", "_", nome_base) or "cliente"
    nome_ficheiro = f"Orcamento_{nome_base}_{st.session_state.data_doc.replace('/', '-')}.pdf"

    with open(st.session_state.pdf_path, "rb") as ficheiro_pdf:
        st.download_button(
            label="Descarregar PDF",
            data=ficheiro_pdf,
            file_name=nome_ficheiro,
            mime="application/pdf",
            width='stretch',
            type="primary",
        )

    st.markdown("---")
    if st.button("Criar Novo Orçamento", width='stretch'):
        reiniciar_sessao()
        st.rerun()


def reiniciar_sessao() -> None:
    for chave in ["dados_extraidos", "pdf_path", "data_doc", "nome_cliente_final"]:
        st.session_state.pop(chave, None)
    st.session_state.passo = 1