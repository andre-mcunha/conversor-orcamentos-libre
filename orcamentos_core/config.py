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


def _obter_chave_google():
    """Procura a chave do Gemini com nomes alternativos e também dentro de
    secções do secrets.toml (ex: [google]), porque um nome ligeiramente
    diferente no painel do Streamlit Cloud faz a chave "desaparecer"."""
    nomes = ("GOOGLE_API_KEY", "GEMINI_API_KEY", "API_KEY")
    for nome in nomes:
        valor = _obter_segredo(nome, nome)
        if valor:
            return str(valor).strip()

    try:
        for seccao in st.secrets.values():
            if hasattr(seccao, "get"):
                for nome in nomes:
                    if seccao.get(nome):
                        return str(seccao.get(nome)).strip()
    except Exception:
        pass

    # Só os nomes (nunca os valores), para diagnosticar no log do deploy.
    try:
        disponiveis = list(st.secrets.keys())
    except Exception:
        disponiveis = []
    logging.getLogger(__name__).warning(
        "GOOGLE_API_KEY não encontrada. Secrets disponíveis: %s", disponiveis
    )
    return None


GOOGLE_API_KEY = _obter_chave_google()
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
