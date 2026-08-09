"""
Ecrã de autenticação.
"""

import logging

import streamlit as st

logger = logging.getLogger(__name__)


def ecra_login(supabase) -> None:
    st.markdown("### Bem-vindo(a) ao Orçamentos")
    st.markdown("Introduza os seus dados para entrar.")

    email = st.text_input("Email", placeholder="O seu email", key="login_email")
    senha = st.text_input("Password", type="password", placeholder="A sua password", key="login_senha")

    entrar = st.button("Entrar", width='stretch', type="primary")

    if entrar:
        if not supabase:
            logger.error("Tentativa de login sem o Supabase configurado.")
            st.error("Erro de configuração: As chaves do Supabase não estão definidas.")
        elif not email or not senha:
            st.warning("Por favor, preencha o email e a password.")
        else:
            try:
                # Validação real via Supabase Auth
                resposta = supabase.auth.sign_in_with_password({"email": email, "password": senha})

                # Se passou sem lançar exceção, o login foi bem sucedido
                st.session_state.autenticado = True
                st.session_state.user_id = resposta.user.id
                st.session_state.user_email = resposta.user.email
                logger.info("Login bem sucedido (user_id=%s).", resposta.user.id)
                st.rerun()
            except Exception as e:
                logger.warning("Falha de login para %r: %s", email, e)
                st.error("Email ou password incorretos.")
                with st.expander("Detalhes"):
                    st.code(str(e))

    st.markdown("</div>", unsafe_allow_html=True)