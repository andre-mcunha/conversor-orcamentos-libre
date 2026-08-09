"""
Testes para orcamentos_core/ai/extrator.py.

Usamos um cliente de IA falso para não depender de chamadas reais à API
do Gemini (nem de rede, nem de créditos gastos a correr os testes).
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PIL import Image

from orcamentos_core import config
from orcamentos_core.ai import extrator


def _cliente_ia_falso(texto_resposta: str):
    cliente = MagicMock()
    cliente.models.generate_content.return_value = SimpleNamespace(text=texto_resposta)
    return cliente


def _imagem_minima() -> Image.Image:
    return Image.new("RGB", (10, 10), color="white")


class TestExtrairDadosDaImagem:
    def test_json_limpo(self):
        cliente = _cliente_ia_falso('{"Titulo": "Pintura", "Itens": []}')
        dados = extrator.extrair_dados_da_imagem(_imagem_minima(), cliente)
        assert dados["Titulo"] == "Pintura"

    def test_json_com_marcacoes_markdown(self):
        cliente = _cliente_ia_falso('```json\n{"Titulo": "Pintura", "Itens": []}\n```')
        dados = extrator.extrair_dados_da_imagem(_imagem_minima(), cliente)
        assert dados["Titulo"] == "Pintura"

    def test_json_com_texto_a_volta(self):
        cliente = _cliente_ia_falso('Aqui está: {"Titulo": "Pintura", "Itens": []} obrigado')
        dados = extrator.extrair_dados_da_imagem(_imagem_minima(), cliente)
        assert dados["Titulo"] == "Pintura"

    def test_resposta_sem_json_valido_lanca_erro(self):
        cliente = _cliente_ia_falso("isto não contém nenhum json")
        with pytest.raises(Exception):
            extrator.extrair_dados_da_imagem(_imagem_minima(), cliente)

    def test_dados_devolvidos_ja_vem_normalizados(self):
        # Sem "Itens", a normalização deve garantir pelo menos uma linha em branco
        cliente = _cliente_ia_falso('{"Titulo": "Pintura"}')
        dados = extrator.extrair_dados_da_imagem(_imagem_minima(), cliente)
        assert len(dados["Itens"]) == 1


class TestPrepararImagemParaIA:
    def test_reduz_imagens_muito_largas(self):
        imagem = Image.new("RGB", (3000, 1500), color="white")
        reduzida = extrator.preparar_imagem_para_ia(imagem)
        assert reduzida.width == 1600
        assert reduzida.height == 800

    def test_nao_altera_imagens_ja_dentro_do_limite(self):
        imagem = Image.new("RGB", (400, 300), color="white")
        reduzida = extrator.preparar_imagem_para_ia(imagem)
        assert reduzida.size == (400, 300)


class TestObterClienteIA:
    def test_sem_api_key_lanca_erro_claro(self, monkeypatch):
        monkeypatch.setattr(config, "GOOGLE_API_KEY", None)
        with pytest.raises(RuntimeError):
            extrator.obter_cliente_ia()