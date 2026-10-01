"""
Editor dos trabalhos/materiais do Passo 2, em formato de cartões.

Substitui o antigo `st.data_editor` (uma grelha de células minúsculas,
difícil de usar no telemóvel) por um cartão por item: a descrição tem uma
caixa de texto grande e multilinha, os números usam campos numéricos
(teclado numérico no telemóvel) e cada cartão mostra o seu subtotal.

Os itens vivem em `st.session_state.itens_editor`, cada um com um id
estável. As chaves dos widgets usam esse id (e não a posição), para que
mover, duplicar ou apagar um item nunca troque os valores entre cartões.
"""

import uuid

import pandas as pd
import streamlit as st

from orcamentos_core.config import COLUNAS_TABELA
from orcamentos_core.utils import formatar_euro, parse_numero

UNIDADES_COMUNS = ["Vg.", "un.", "m²", "m", "m³", "h", "dia", "kg", "L"]

# Campo do item -> (sufixo da chave do widget, valor por omissão)
_CAMPOS = {
    "Designação": ("desc", ""),
    "Unidade": ("unid", "Vg."),
    "Quantidade": ("qtd", 1.0),
    "Preço Unitário (€)": ("preco", 0.0),
}


def _chave(id_item: str, campo: str) -> str:
    return f"item_{id_item}_{_CAMPOS[campo][0]}"


def _novo_item(valores: dict | None = None) -> dict:
    valores = valores or {}
    item = {"id": uuid.uuid4().hex[:8]}
    for campo, (_, omissao) in _CAMPOS.items():
        valor = valores.get(campo, omissao)
        if campo in ("Quantidade", "Preço Unitário (€)"):
            valor = parse_numero(valor, default=omissao)
        else:
            valor = str(valor or omissao)
        item[campo] = valor
    return item


def _sincronizar_widgets_para_itens() -> None:
    """Copia os valores atuais dos widgets para a lista de itens. Corre no
    início de cada callback, para que nada do que foi escrito se perca
    quando a ordem dos cartões muda."""
    for item in st.session_state.itens_editor:
        for campo in _CAMPOS:
            chave = _chave(item["id"], campo)
            if chave in st.session_state:
                item[campo] = st.session_state[chave]


def _limpar_widgets(id_item: str) -> None:
    for campo in _CAMPOS:
        st.session_state.pop(_chave(id_item, campo), None)


# --- Ações dos botões (callbacks: correm antes do rerun) -------------------

def _adicionar() -> None:
    _sincronizar_widgets_para_itens()
    st.session_state.itens_editor.append(_novo_item())


def _apagar(indice: int) -> None:
    _sincronizar_widgets_para_itens()
    item = st.session_state.itens_editor.pop(indice)
    _limpar_widgets(item["id"])
    if not st.session_state.itens_editor:
        st.session_state.itens_editor.append(_novo_item())


def _duplicar(indice: int) -> None:
    _sincronizar_widgets_para_itens()
    copia = _novo_item(st.session_state.itens_editor[indice])
    st.session_state.itens_editor.insert(indice + 1, copia)


def _mover(indice: int, deslocamento: int) -> None:
    _sincronizar_widgets_para_itens()
    itens = st.session_state.itens_editor
    destino = indice + deslocamento
    if 0 <= destino < len(itens):
        itens[indice], itens[destino] = itens[destino], itens[indice]


# --- Renderização -----------------------------------------------------------

def _preparar_estado(itens_iniciais: list, origem: dict) -> None:
    """(Re)cria a lista de itens quando chegam dados novos (nova foto,
    orçamento do histórico ou "preencher manualmente"). `origem` é o dict
    de `dados_extraidos`: um objeto novo significa dados novos."""
    if st.session_state.get("itens_editor_origem") is origem:
        return
    for item in st.session_state.get("itens_editor", []):
        _limpar_widgets(item["id"])
    st.session_state.itens_editor = [_novo_item(i) for i in itens_iniciais] or [_novo_item()]
    st.session_state.itens_editor_origem = origem


def _cartao_item(indice: int, item: dict, total_itens: int) -> float:
    id_item = item["id"]

    # Repor o valor guardado se o Streamlit tiver descartado o estado do
    # widget (acontece quando se sai do Passo 2 e se volta).
    for campo in _CAMPOS:
        chave = _chave(id_item, campo)
        if chave not in st.session_state:
            st.session_state[chave] = item[campo]

    with st.container(border=True):
        # Contentor horizontal (e não st.columns), para que o cabeçalho
        # fique numa só linha mesmo no telemóvel, onde as colunas empilham.
        with st.container(horizontal=True, vertical_alignment="center", gap="small"):
            st.markdown(
                f'<span class="item-numero">Item {indice + 1}</span>',
                unsafe_allow_html=True,
                width="stretch",
            )
            st.button(
                "", icon=":material/arrow_upward:", key=f"cima_{id_item}",
                help="Mover para cima", type="tertiary",
                disabled=indice == 0, on_click=_mover, args=(indice, -1),
            )
            st.button(
                "", icon=":material/arrow_downward:", key=f"baixo_{id_item}",
                help="Mover para baixo", type="tertiary",
                disabled=indice == total_itens - 1, on_click=_mover, args=(indice, 1),
            )
            st.button(
                "", icon=":material/content_copy:", key=f"dup_{id_item}",
                help="Duplicar item", type="tertiary",
                on_click=_duplicar, args=(indice,),
            )
            st.button(
                "", icon=":material/delete:", key=f"apagar_{id_item}",
                help="Apagar item", type="tertiary",
                on_click=_apagar, args=(indice,),
            )

        st.text_area(
            "Descrição",
            key=_chave(id_item, "Designação"),
            placeholder="Ex.: Pintura de paredes interiores, 2 demãos",
            height=110,
        )

        unidade_atual = st.session_state[_chave(id_item, "Unidade")]
        opcoes = UNIDADES_COMUNS if unidade_atual in UNIDADES_COMUNS else [unidade_atual] + UNIDADES_COMUNS

        c_unid, c_qtd, c_preco = st.columns([1, 1, 1.3])
        with c_unid:
            st.selectbox(
                "Unidade",
                opcoes,
                key=_chave(id_item, "Unidade"),
                accept_new_options=True,
            )
        with c_qtd:
            st.number_input(
                "Quantidade",
                key=_chave(id_item, "Quantidade"),
                min_value=0.0,
                step=1.0,
                format="%.2f",
            )
        with c_preco:
            st.number_input(
                "Preço unit. (€)",
                key=_chave(id_item, "Preço Unitário (€)"),
                min_value=0.0,
                step=1.0,
                format="%.2f",
            )

        subtotal = (
            parse_numero(st.session_state[_chave(id_item, "Quantidade")])
            * parse_numero(st.session_state[_chave(id_item, "Preço Unitário (€)")])
        )
        st.markdown(
            f'<div class="item-subtotal">Subtotal <strong>{formatar_euro(subtotal)}</strong></div>',
            unsafe_allow_html=True,
        )
    return subtotal


def editor_itens(itens_iniciais: list, origem: dict) -> tuple[pd.DataFrame, float]:
    """Mostra os cartões de itens e devolve (DataFrame com COLUNAS_TABELA,
    total). O DataFrame tem o mesmo formato que o antigo data_editor
    devolvia, para o resto do fluxo (PDF, histórico) não mudar."""
    _preparar_estado(itens_iniciais, origem)

    itens = st.session_state.itens_editor
    total = 0.0
    for indice, item in enumerate(itens):
        total += _cartao_item(indice, item, len(itens))

    st.button(
        "Adicionar trabalho / material",
        icon=":material/add:",
        width="stretch",
        on_click=_adicionar,
        key="adicionar_item",
    )

    _sincronizar_widgets_para_itens()
    df = pd.DataFrame([{c: item[c] for c in COLUNAS_TABELA} for item in itens], columns=COLUNAS_TABELA)
    return df, total
