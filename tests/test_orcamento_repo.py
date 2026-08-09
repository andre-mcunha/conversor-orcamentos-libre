"""
Testes para orcamentos_core/data/orcamentos_repo.py.

Usamos um cliente Supabase falso (unittest.mock) em vez de uma base de
dados real: o objetivo é testar a nossa lógica (o que fazemos com a
resposta, como tratamos erros), não o Supabase em si.
"""

from unittest.mock import MagicMock

import pytest

from orcamentos_core.data.orcamentos_repo import OrcamentosRepo, extrair_resumo_orcamento


class TestExtrairResumoOrcamento:
    def test_le_do_conteudo_quando_disponivel(self):
        orc = {
            "titulo": "coluna desatualizada",
            "cliente": "coluna desatualizada",
            "total": 100.0,
            "conteudo": {
                "Titulo": "Pintura Exterior",
                "NomeCliente": "João Silva",
                "Itens": [],
            },
        }
        titulo, cliente, total, conteudo = extrair_resumo_orcamento(orc)
        assert titulo == "Pintura Exterior"
        assert cliente == "João Silva"
        assert total == 100.0
        assert conteudo["Titulo"] == "Pintura Exterior"

    def test_usa_coluna_como_reserva_se_conteudo_incompleto(self):
        # Simula um registo antigo em que o 'conteudo' não tem os campos
        orc = {"titulo": "Orçamento Antigo", "cliente": "Maria", "total": 50.0, "conteudo": {}}
        titulo, cliente, total, _ = extrair_resumo_orcamento(orc)
        assert titulo == "Orçamento Antigo"
        assert cliente == "Maria"
        assert total == 50.0

    def test_conteudo_none_nao_rebenta(self):
        orc = {"titulo": "X", "cliente": "Y", "total": 0, "conteudo": None}
        titulo, cliente, total, conteudo = extrair_resumo_orcamento(orc)
        assert titulo == "X"
        assert cliente == "Y"
        assert conteudo == {}

    def test_recalcula_total_se_coluna_total_em_falta(self):
        orc = {
            "conteudo": {
                "Titulo": "T",
                "NomeCliente": "C",
                "Itens": [
                    {"Quantidade": 2, "Preço Unitário (€)": 10},
                    {"Quantidade": 1, "Preço Unitário (€)": 5},
                ],
            }
        }
        _, _, total, _ = extrair_resumo_orcamento(orc)
        assert total == pytest.approx(25.0)

    def test_sem_titulo_nem_cliente_usa_valores_por_omissao(self):
        orc = {"conteudo": {}}
        titulo, cliente, _, _ = extrair_resumo_orcamento(orc)
        assert titulo == "Orçamento"
        assert cliente == "Sem nome"


class TestOrcamentosRepo:
    def _supabase_falso_para_listar(self, dados_devolvidos):
        supabase = MagicMock()
        cadeia = supabase.table.return_value.select.return_value.eq.return_value.order.return_value
        cadeia.execute.return_value.data = dados_devolvidos
        return supabase

    def test_listar_por_utilizador_devolve_dados(self):
        supabase = self._supabase_falso_para_listar([{"id": 1}, {"id": 2}])
        repo = OrcamentosRepo(supabase)

        resultado = repo.listar_por_utilizador("user-123")

        assert resultado == [{"id": 1}, {"id": 2}]
        supabase.table.assert_called_with("orcamentos")

    def test_listar_por_utilizador_sem_dados_devolve_lista_vazia(self):
        supabase = self._supabase_falso_para_listar(None)
        repo = OrcamentosRepo(supabase)

        assert repo.listar_por_utilizador("user-123") == []

    def test_guardar_com_sucesso_devolve_true(self):
        supabase = MagicMock()
        repo = OrcamentosRepo(supabase)

        resultado = repo.guardar(
            user_id="user-123", titulo="Pintura", cliente="João", total=150.0, conteudo={"Itens": []}
        )

        assert resultado is True
        supabase.table.assert_called_with("orcamentos")
        supabase.table.return_value.insert.assert_called_once()
        dados_inseridos = supabase.table.return_value.insert.call_args[0][0]
        assert dados_inseridos["user_id"] == "user-123"
        assert dados_inseridos["titulo"] == "Pintura"
        assert dados_inseridos["total"] == 150.0

    def test_guardar_com_falha_devolve_false_sem_lancar_excecao(self):
        supabase = MagicMock()
        supabase.table.return_value.insert.return_value.execute.side_effect = Exception("falha de rede")
        repo = OrcamentosRepo(supabase)

        resultado = repo.guardar(
            user_id="user-123", titulo="Pintura", cliente="João", total=150.0, conteudo={}
        )

        assert resultado is False