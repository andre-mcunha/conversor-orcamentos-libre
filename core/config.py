"""
Configuração central da aplicação.

Reúne num único sítio a leitura de credenciais (a partir de st.secrets,
com fallback para variáveis de ambiente) e a configuração do logging,
para que nenhum outro módulo precise de saber de onde vêm estes valores.
"""

import logging
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _obter_segredo(chave_secrets: str, chave_env: str):
    """Lê um valor primeiro de st.secrets (deploy no Streamlit Cloud) e,
    se não existir, da variável de ambiente correspondente (.env local)."""
    try:
        return st.secrets[chave_secrets]
    except Exception:
        return os.getenv(chave_env)


GOOGLE_API_KEY = _obter_segredo("GOOGLE_API_KEY", "GOOGLE_API_KEY")
SUPABASE_URL = _obter_segredo("SUPABASE_URL", "SUPABASE_URL")
SUPABASE_KEY = _obter_segredo("SUPABASE_KEY", "SUPABASE_KEY")

# Colunas da tabela de trabalhos/materiais, usadas no Passo 2
COLUNAS_TABELA = ["Designação", "Unidade", "Quantidade", "Preço Unitário (€)"]

# Modelo de IA usado para ler o orçamento manuscrito na foto
NOME_MODELO_IA = "gemini-3.5-flash-lite"

_LOGGING_CONFIGURADO = False


def configurar_logging() -> None:
    """Configura o logging da aplicação uma única vez por processo.

    O nível é controlável através da variável de ambiente LOG_LEVEL
    (por omissão, INFO). Em desenvolvimento local, corre:
        LOG_LEVEL=DEBUG streamlit run app.py
    """
    global _LOGGING_CONFIGURADO
    if _LOGGING_CONFIGURADO:
        return

    nivel = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _LOGGING_CONFIGURADO = True