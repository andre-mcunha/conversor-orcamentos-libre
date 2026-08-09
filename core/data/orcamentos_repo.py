"""
Repositório de orçamentos.

Todas as operações sobre a tabela 'orcamentos' do Supabase vivem aqui.
Isto isola o resto da aplicação dos detalhes do Supabase (nomes de
tabelas/colunas, forma de consultar, etc.) e é o que torna possível
testar a lógica de negócio com um cliente falso, sem precisar de uma
base de dados real (ver tests/test_orcamentos_repo.py).
"""

import logging

from core.utils import parse_numero

logger = logging.getLogger(__name__)


class OrcamentosRepo:
    """Acesso à tabela 'orcamentos'.

    Recebe o cliente Supabase já inicializado (injeção de dependência
    simples) em vez de o ir buscar sozinho - isso permite substituí-lo
    por um cliente falso/mock nos testes, sem tocar em rede nenhuma."""

    def __init__(self, supabase_client):
        self._supabase = supabase_client

    def listar_por_utilizador(self, user_id: str) -> list[dict]:
        """Devolve os orçamentos de um utilizador, do mais recente para
        o mais antigo. Propaga qualquer exceção - quem chama decide como
        mostrar isso à pessoa (ver ui/sidebar_historico.py)."""
        resposta = (
            self._supabase.table("orcamentos")
            .select("*")
            .eq("user_id", user_id)
            .order("data_criacao", desc=True)
            .execute()
        )
        return resposta.data or []

    def guardar(self, user_id: str, titulo: str, cliente: str, total: float, conteudo: dict) -> bool:
        """Guarda um novo orçamento.

        Devolve True/False em vez de lançar exceção: uma falha ao guardar
        no histórico não deve impedir a pessoa de descarregar o PDF que
        já foi gerado com sucesso - só significa que esse orçamento não
        ficará disponível para reutilização mais tarde."""
        try:
            self._supabase.table("orcamentos").insert(
                {
                    "user_id": user_id,
                    "titulo": titulo,
                    "cliente": cliente,
                    "total": float(total),
                    "conteudo": conteudo,
                }
            ).execute()
        except Exception:
            logger.exception("Falha ao guardar orçamento na base de dados (user_id=%s).", user_id)
            return False

        logger.info("Orçamento guardado (user_id=%s, titulo=%r, total=%.2f).", user_id, titulo, total)
        return True


def extrair_resumo_orcamento(orc: dict):
    """Deriva o título, o cliente e o total a mostrar/reutilizar sempre a
    partir da MESMA fonte: o campo 'conteudo' (o JSON completo). As
    colunas 'titulo', 'cliente' e 'total' da tabela existem só para
    permitir pesquisar/ordenar na base de dados - nunca são a fonte de
    verdade para o que aparece no ecrã, para evitar que a barra lateral e
    o Passo 2 mostrem dados diferentes para o mesmo orçamento caso as
    colunas e o JSON alguma vez fiquem dessincronizados (ex.: uma futura
    função de editar/renomear que só atualize um dos dois locais).

    As colunas da tabela só são usadas como reserva, para registos
    antigos ou incompletos em que o 'conteudo' não tenha o campo."""
    conteudo = orc.get("conteudo") or {}

    titulo = str(conteudo.get("Titulo") or orc.get("titulo") or "Orçamento").strip()
    cliente = str(conteudo.get("NomeCliente") or orc.get("cliente") or "Sem nome").strip()

    total = orc.get("total")
    if total is None:
        # Reserva: recalcula a partir dos itens se a coluna 'total' faltar
        total = sum(
            parse_numero(item.get("Quantidade", 0)) * parse_numero(item.get("Preço Unitário (€)", 0))
            for item in (conteudo.get("Itens", []) or [])
        )

    return titulo, cliente, float(total or 0), conteudo