"""
Funções de apoio: conversão/formatação de números e normalização da
estrutura de dados de um orçamento.

Este módulo não depende do Streamlit nem de nenhum serviço externo -
são todas funções puras (a mesma entrada dá sempre a mesma saída), o
que as torna fáceis de testar.
"""

import re

import pandas as pd


def parse_numero(valor, default: float = 0.0) -> float:
    """Converte um valor (número, texto com vírgula ou ponto, ou vazio)
    num número, de forma tolerante a diferentes formatos."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return default
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip()
    if not texto:
        return default
    texto = re.sub(r"[€\s]", "", texto).replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return default


def formatar_numero(valor) -> str:
    return f"{valor:.2f}"


def formatar_euro(valor) -> str:
    return f"{valor:.2f} €"


def dados_vazios() -> dict:
    """Estrutura de dados em branco, usada quando a pessoa prefere
    preencher tudo manualmente em vez de tirar uma foto."""
    return {
        "Titulo": "",
        "NomeCliente": "",
        "MoradaCliente": "",
        "Pagamento": "",
        "Itens": [
            {"Designação": "", "Unidade": "Vg.", "Quantidade": 1.0, "Preço Unitário (€)": 0.0}
        ],
    }


def normalizar_dados(dados) -> dict:
    """Garante que os dados (vindos da IA ou de um orçamento guardado)
    têm sempre a estrutura e os tipos esperados, mesmo que a origem se
    engane ou omita campos."""
    if not isinstance(dados, dict):
        dados = {}

    itens_normalizados = []
    for item in dados.get("Itens", []) or []:
        if not isinstance(item, dict):
            continue
        designacao = str(item.get("Designação") or "").strip()
        unidade = str(item.get("Unidade") or "Vg.").strip() or "Vg."
        itens_normalizados.append(
            {
                "Designação": designacao,
                "Unidade": unidade,
                "Quantidade": parse_numero(item.get("Quantidade", 1), default=1.0),
                "Preço Unitário (€)": parse_numero(item.get("Preço Unitário (€)", 0)),
            }
        )

    if not itens_normalizados:
        itens_normalizados = [
            {"Designação": "", "Unidade": "Vg.", "Quantidade": 1.0, "Preço Unitário (€)": 0.0}
        ]

    return {
        "Titulo": str(dados.get("Titulo") or "Orçamento Geral").strip(),
        "NomeCliente": str(dados.get("NomeCliente") or "").strip(),
        "MoradaCliente": str(dados.get("MoradaCliente") or "").strip(),
        "Pagamento": str(dados.get("Pagamento") or "").strip(),
        "Itens": itens_normalizados,
    }