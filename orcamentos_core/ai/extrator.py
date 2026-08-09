"""
Extração de dados a partir da foto do orçamento manuscrito.

Este módulo não depende de `st.session_state`: recebe o cliente de IA já
criado como argumento em vez de o gerir sozinho. Isso mantém a lógica de
extração testável com um cliente falso (ver tests/test_extrator.py); a
decisão de cache-por-sessão fica na camada de UI (orcamentos_core/ui/passo1_foto.py).
"""

import json
import logging

from google import genai
from PIL import Image

from orcamentos_core import config
from orcamentos_core.utils import normalizar_dados

logger = logging.getLogger(__name__)

PROMPT_EXTRACAO = """
Lê atentamente as anotações manuscritas desta imagem, referentes a um
orçamento de obra ou serviço.

Extrai o nome do cliente, a morada do cliente (se existirem), as
condições de pagamento e a lista de trabalhos/materiais.

Devolve APENAS um objeto JSON válido, sem texto adicional, sem
comentários e sem marcações ```json, com esta estrutura exata:
{
  "Titulo": "Um resumo de 3 a 5 palavras do orçamento (ex: 'Orçamento Pintura Exterior')",
  "NomeCliente": "nome do cliente ou string vazia",
  "MoradaCliente": "morada do cliente ou string vazia",
  "Pagamento": "condições de pagamento ou string vazia",
  "NomeEmpresa": "nome da empresa / pessoa ou string vazia",
  "Contato": "telefone ou telemóvel ou string vazia",
  "Email": "email ou string vazia",
  "Itens": [
    {
      "Designação": "descrição do trabalho ou material",
      "Unidade": "Vg.",
      "Quantidade": 1,
      "Preço Unitário (€)": 0.00
    }
  ]
}

Regras:
- "Quantidade" e "Preço Unitário (€)" devem ser números, não texto.
- Se não existir uma quantidade explícita, usa 1.
- "Unidade" pode ser "Vg." (verba), "un.", "m2", "m", "h" ou outra
  unidade indicada nas anotações.
"""


def preparar_imagem_para_ia(imagem: Image.Image) -> Image.Image:
    """Reduz o tamanho da fotografia antes de a enviar para a IA. As fotos
    de telemóveis atuais são muito grandes e isso torna a análise mais
    lenta sem ganho de qualidade na leitura do texto."""
    imagem = imagem.convert("RGB")
    largura_max = 1600
    if imagem.width > largura_max:
        proporcao = largura_max / imagem.width
        nova_altura = int(imagem.height * proporcao)
        imagem = imagem.resize((largura_max, nova_altura))
    return imagem


def obter_cliente_ia() -> genai.Client:
    """Cria um cliente novo do Gemini. Lança RuntimeError se a chave da
    API não estiver configurada, para dar um erro claro em vez de uma
    exceção genérica mais tarde."""
    if not config.GOOGLE_API_KEY:
        raise RuntimeError("A chave da API de IA não está configurada.")
    return genai.Client(api_key=config.GOOGLE_API_KEY)


def extrair_dados_da_imagem(imagem: Image.Image, cliente_ia: genai.Client) -> dict:
    """Envia a imagem para o Gemini e devolve os dados já normalizados."""
    imagem_preparada = preparar_imagem_para_ia(imagem)

    logger.info("A enviar imagem para o modelo de IA (%s).", config.NOME_MODELO_IA)
    resposta = cliente_ia.models.generate_content(
        model=config.NOME_MODELO_IA, contents=[PROMPT_EXTRACAO, imagem_preparada]
    )

    texto = resposta.text.strip()
    texto = texto.replace("```json", "").replace("```", "").strip()

    try:
        dados = json.loads(texto)
    except json.JSONDecodeError:
        inicio, fim = texto.find("{"), texto.rfind("}")
        if inicio == -1 or fim == -1:
            logger.error("A resposta da IA não contém nenhum JSON reconhecível.")
            raise
        dados = json.loads(texto[inicio : fim + 1])

    dados_normalizados = normalizar_dados(dados)
    logger.info("Dados extraídos com sucesso (%d itens).", len(dados_normalizados["Itens"]))
    return dados_normalizados
