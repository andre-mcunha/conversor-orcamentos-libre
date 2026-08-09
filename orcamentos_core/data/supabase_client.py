"""
Inicialização do cliente Supabase.
"""

import logging

import streamlit as st
from supabase import Client, create_client

from orcamentos_core import config

logger = logging.getLogger(__name__)


@st.cache_resource
def obter_supabase() -> Client | None:
    """Cria (uma única vez por processo, graças à cache do Streamlit) o
    cliente Supabase. Devolve None se as credenciais não estiverem
    configuradas, para que o resto da app possa lidar com esse caso de
    forma explícita em vez de rebentar mais tarde com um erro confuso."""
    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        logger.warning("Supabase não está configurado (falta SUPABASE_URL ou SUPABASE_KEY).")
        return None
    logger.info("Cliente Supabase inicializado.")
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
