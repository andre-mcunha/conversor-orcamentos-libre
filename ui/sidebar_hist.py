"""
Barra lateral com o histórico de orçamentos.

Cada orçamento é clicável: ao tocar, os seus dados são carregados no
Passo 2, para facilitar a criação de um novo orçamento com trabalhos
idênticos aos desse orçamento.
"""

import logging

import streamlit as st

from data.orcamentos_repo import OrcamentosRepo, extrair_resumo_orcamento
from utils import normalizar_dados

logger = logging.getLogger(__name__)


def _carregar_orcamento_selecionado(orc: dict) -> None:
    """Coloca os dados de um orçamento já guardado no Passo 2, prontos a
    rever e editar. Serve para reaproveitar rapidamente trabalhos e
    materiais idênticos num novo orçamento (ex.: o mesmo tipo de obra
    para um cliente diferente), sem ter de voltar a fotografar ou a
    escrever tudo de novo."""
    _, _, _, conteudo = extrair_resumo_orcamento(orc)
    st.session_state.dados_extraidos = normalizar_dados(conteudo)

    # Limpar resíduos de um PDF gerado anteriormente nesta sessão, para
    # não mostrar por engano o ficheiro de um orçamento antigo.
    for chave in ["pdf_path", "data_doc", "nome_cliente_final"]:
        st.session_state.pop(chave, None)

    st.session_state.passo = 2
    logger.info("Orçamento reutilizado como modelo (id=%s).", orc.get("id"))
    st.rerun()


def mostrar_historico_lateral(repo: OrcamentosRepo) -> None:
    """Mostra a lista de orçamentos guardados numa barra lateral (Sidebar)."""
    with st.sidebar:
        st.markdown("## Os Meus Orçamentos")
        st.caption("Toque num orçamento para reutilizar os seus dados.")

        try:
            orcamentos = repo.listar_por_utilizador(st.session_state.user_id)

            if not orcamentos:
                st.info("Ainda não tem orçamentos guardados.")
            else:
                for indice, orc in enumerate(orcamentos):
                    # Formatar a data (ex: 2026-08-07T12:00:00 -> 07/08/2026)
                    data_str = orc["data_criacao"].split("T")[0]
                    ano, mes, dia = data_str.split("-")

                    titulo, cliente, total, _ = extrair_resumo_orcamento(orc)

                    # Item clicável (aspeto de cartão minimalista)
                    rotulo = f"**{titulo}** · {total:.2f} €\n\n{cliente} · {dia}/{mes}/{ano}"
                    if st.button(
                        rotulo,
                        key=f"orc_item_{orc.get('id', indice)}",
                        width='stretch',
                    ):
                        _carregar_orcamento_selecionado(orc)

        except Exception:
            logger.exception("Não foi possível carregar o histórico de orçamentos.")
            st.error("Não foi possível carregar o histórico.")