"""
Passo 2 - Confirmação/edição dos dados extraídos e geração do PDF.
"""

import logging

import pandas as pd
import streamlit as st

from core.config import COLUNAS_TABELA
from core.data.orcamentos_repo import OrcamentosRepo
from core.pdf.gerador import gerar_documento, nova_pasta_trabalho
from core.utils import formatar_euro, parse_numero

logger = logging.getLogger(__name__)


def _obter_pasta_trabalho_sessao() -> str:
    """Reutiliza a mesma pasta temporária durante toda a sessão, em vez
    de criar uma nova a cada rerun."""
    if "pasta_trabalho" not in st.session_state:
        st.session_state.pasta_trabalho = nova_pasta_trabalho()
    return st.session_state.pasta_trabalho


def passo_2_confirmar(repo: OrcamentosRepo) -> None:
    if "dados_extraidos" not in st.session_state:
        st.session_state.passo = 1
        st.rerun()

    st.markdown("## Passo 2 - Confirme os Dados")
    dados = st.session_state.dados_extraidos

    st.markdown("#### Resumo")
    titulo_orcamento = st.text_input("Título / Assunto do Orçamento", value=dados.get("Titulo", ""))

    st.markdown("#### Os seus dados")
    nome_empresa = st.text_input("Nome da Empresa / Pessoa", value=dados.get("NomeEmpresa", ""))
    contato = st.text_input("Contato", value=dados.get("Contato", ""))
    email = st.text_input("Email", value=dados.get("Email", ""))

    st.markdown("#### Dados do Cliente")
    nome_cliente = st.text_input("Nome do Cliente", value=dados.get("NomeCliente", ""))
    morada_cliente = st.text_area("Morada do Cliente", value=dados.get("MoradaCliente", ""))

    st.markdown("#### Trabalhos e Materiais")
    st.caption("Reveja as descrições, quantidades e preços. Pode adicionar ou apagar linhas.")

    df = pd.DataFrame(dados.get("Itens", []))
    for coluna in COLUNAS_TABELA:
        if coluna not in df.columns:
            df[coluna] = "" if coluna in ("Designação", "Unidade") else 0.0
    df = df[COLUNAS_TABELA]

    tabela_editada = st.data_editor(
        df,
        num_rows="dynamic",
        width='stretch',
        hide_index=True,
        key="editor_tabela",
        column_config={
            "Designação": st.column_config.TextColumn("Descrição", width="large"),
            "Unidade": st.column_config.TextColumn("Unid.", width="small"),
            "Quantidade": st.column_config.NumberColumn("Qtd.", min_value=0.0, step=0.5, format="%.2f"),
            "Preço Unitário (€)": st.column_config.NumberColumn(
                "Preço Unit. (€)", min_value=0.0, step=0.5, format="%.2f"
            ),
        },
    )

    quantidades = tabela_editada["Quantidade"].apply(parse_numero)
    precos = tabela_editada["Preço Unitário (€)"].apply(parse_numero)
    total = (quantidades * precos).sum()
    st.metric("Total do Orçamento", formatar_euro(total))

    pagamento = st.text_input("Condições de Pagamento", value=dados.get("Pagamento", ""))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Voltar", width='stretch'):
            st.session_state.passo = 1
            st.rerun()
    with col2:
        gerar = st.button("Gerar PDF", width='stretch', type="primary")

    if gerar:
        if not morada_cliente.strip():
            st.warning("Por favor, preencha a morada do cliente.")
        elif tabela_editada["Designação"].apply(lambda x: str(x or "").strip()).eq("").all():
            st.warning("Adicione pelo menos um trabalho ou material ao orçamento.")
        else:
            with st.spinner("A gerar o PDF..."):
                try:
                    pasta_trabalho = _obter_pasta_trabalho_sessao()
                    pdf_path, data_doc = gerar_documento(
                        pasta_trabalho,
                        nome_cliente,
                        morada_cliente,
                        tabela_editada,
                        pagamento,
                        nome_empresa,
                        contato,
                        email,
                    )

                    conteudo = {
                        "Titulo": titulo_orcamento,
                        "NomeCliente": nome_cliente,
                        "MoradaCliente": morada_cliente,
                        "Pagamento": pagamento,
                        "Itens": tabela_editada.to_dict(orient="records"),
                    }
                    guardado = repo.guardar(
                        user_id=st.session_state.user_id,
                        titulo=titulo_orcamento,
                        cliente=nome_cliente,
                        total=total,
                        conteudo=conteudo,
                    )
                    if not guardado:
                        # O PDF já foi gerado com sucesso; só o registo no
                        # histórico é que falhou - avisa sem bloquear o fluxo.
                        st.toast(
                            "O PDF foi gerado, mas não foi possível guardá-lo no histórico.",
                            icon="⚠️",
                        )

                    st.session_state.pdf_path = pdf_path
                    st.session_state.data_doc = data_doc
                    st.session_state.nome_cliente_final = nome_cliente
                    st.session_state.passo = 3
                    st.rerun()
                except Exception as e:
                    logger.exception("Erro ao gerar o documento PDF.")
                    st.error("Ocorreu um erro ao gerar o documento PDF.")
                    with st.expander("Detalhes técnicos"):
                        st.code(str(e))