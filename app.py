"""
Orçamentos - Papel para PDF
----------------------------
Aplicação Streamlit que permite tirar uma foto a um orçamento escrito à mão
e transformá-la automaticamente num PDF profissional, pronto a enviar ao
cliente.

Fluxo em 3 passos, pensado para ser usado a partir de um telemóvel por
pessoas com pouca experiência em aplicações digitais:
    1. Foto do orçamento em papel
    2. Confirmação e edição dos dados extraídos
    3. Descarregar o PDF final
"""

import json
import os
import re
import tempfile
from copy import deepcopy
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai
from PIL import Image
from xhtml2pdf import pisa
from supabase import create_client, Client

load_dotenv()

# =========================================================================
# CONFIGURAÇÃO
# =========================================================================

try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except Exception:
    API_KEY = os.getenv("API_KEY")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
except Exception:
    SUPABASE_URL = os.getenv("SUPABASE_URL")

try:
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Inicializar o cliente Supabase de forma segura
@st.cache_resource
def init_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()


COLUNAS_TABELA = ["Designação", "Unidade", "Quantidade", "Preço Unitário (€)"]

NOME_MODELO_IA = "gemini-3.5-flash-lite"


# ESTILO

def aplicar_estilo():
    """Aplica o CSS que dá à app um aspeto profissional e adaptado a ecrãs
    de telemóvel e a utilizadores com menos à-vontade digital: texto maior,
    botões grandes e fáceis de tocar, e um indicador de passos claro."""
    st.markdown(
        """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        .stApp {
            max-width: 640px;
            margin: 0 auto;
        }

        html, body, [class*="css"] {
            font-size: 17px;
        }

        h1 {
            font-size: 1.8rem !important;
            text-align: center;
            color: #1B4965;
            margin-bottom: 0 !important;
        }
        h2 {
            font-size: 1.4rem !important;
            color: #1B4965;
            margin-bottom: 0.3rem !important;
        }
        h4 {
            color: #1B4965;
        }

        p, label, li, .stMarkdown, .stCaption {
            font-size: 1rem;
        }

        .stButton > button, .stDownloadButton > button {
            font-size: 1.05rem;
            font-weight: 600;
            padding: 0.7rem 1rem;
            border-radius: 12px;
            min-height: 3.1rem;
            border: none;
        }

        .stTextInput input, .stTextArea textarea {
            font-size: 1.05rem;
            border-radius: 10px;
        }

        div[data-testid="stMetric"] {
            background: #EEF2F5;
            padding: 1rem;
            border-radius: 14px;
        }

        /* Indicador de passos */
        .passos-container {
            display: flex;
            align-items: flex-start;
            justify-content: center;
            margin: 0.5rem 0 1.8rem 0;
        }
        .passo {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 76px;
        }
        .passo-numero {
            width: 34px;
            height: 34px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.95rem;
            background: #E3E8EC;
            color: #6B7785;
        }
        .passo.ativo .passo-numero {
            background: #D9A441;
            color: #24313D;
        }
        .passo.concluido .passo-numero {
            background: #1B4965;
            color: #FFFFFF;
        }
        .passo-nome {
            font-size: 0.78rem;
            margin-top: 5px;
            color: #6B7785;
            text-align: center;
        }
        .passo.ativo .passo-nome {
            color: #1B4965;
            font-weight: 700;
        }
        .passo-linha {
            height: 3px;
            width: 34px;
            background: #E3E8EC;
            margin-top: 17px;
        }
        .passo-linha.concluido {
            background: #1B4965;
        }

        /* Cartão de acesso */
        .login-card {
            max-width: 380px;
            margin: 3rem auto 0 auto;
            padding: 2rem 1.5rem;
            border-radius: 16px;
            background: #EEF2F5;
            text-align: center;
        }

        .dica-caixa {
            background: #FBF3E2;
            border-left: 4px solid #D9A441;
            padding: 0.7rem 1rem;
            border-radius: 8px;
            font-size: 0.95rem;
            margin-bottom: 1rem;
        }

        /* Lista de orçamentos na barra lateral (itens clicáveis) */
        [data-testid="stSidebar"] .stButton > button {
            background: #FFFFFF;
            border: 1px solid #E3E8EC;
            color: #24313D;
            text-align: left;
            font-weight: 400;
            font-size: 0.88rem;
            line-height: 1.4;
            padding: 0.55rem 0.75rem;
            border-radius: 10px;
            min-height: auto;
            white-space: normal;
            margin-bottom: 0.4rem;
            box-shadow: none;
        }
        [data-testid="stSidebar"] .stButton > button p {
            text-align: left;
            margin: 0;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            border-color: #1B4965;
            background: #EEF2F5;
            color: #1B4965;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def indicador_passos(passo_atual):
    """Mostra 1 → 2 → 3 no topo da página, para a pessoa saber sempre em
    que ponto do processo está."""
    nomes = ["Foto", "Confirmar", "Descarregar"]
    partes = ['<div class="passos-container">']
    for i, nome in enumerate(nomes, start=1):
        if i < passo_atual:
            estado, rotulo = "concluido", "✓"
        elif i == passo_atual:
            estado, rotulo = "ativo", str(i)
        else:
            estado, rotulo = "pendente", str(i)

        partes.append(
            f'<div class="passo {estado}">'
            f'<div class="passo-numero">{rotulo}</div>'
            f'<div class="passo-nome">{nome}</div>'
            f"</div>"
        )
        if i < len(nomes):
            linha_estado = "concluido" if i < passo_atual else ""
            partes.append(f'<div class="passo-linha {linha_estado}"></div>')
    partes.append("</div>")
    st.markdown("".join(partes), unsafe_allow_html=True)

# FUNÇÕES DE APOIO (dados e formatação)

def parse_numero(valor, default=0.0):
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


def formatar_numero(valor):
    return f"{valor:.2f}"


def formatar_euro(valor):
    return f"{valor:.2f} €"


def dados_vazios():
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


def normalizar_dados(dados):
    """Garante que os dados devolvidos pela IA têm sempre a estrutura e os
    tipos esperados, mesmo que a IA se engane ou omita campos."""
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


def preparar_imagem_para_ia(imagem):
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


# INTELIGÊNCIA ARTIFICIAL

def obter_cliente_ia():
    """Cria (uma única vez por sessão) o cliente do Gemini."""
    if "cliente_ia" not in st.session_state:
        if not API_KEY:
            raise RuntimeError("A chave da API de IA não está configurada.")
        st.session_state.cliente_ia = genai.Client(api_key=API_KEY)
    return st.session_state.cliente_ia


def extrair_dados_da_imagem(imagem):
    """Envia a imagem para o Gemini e devolve os dados já normalizados."""
    imagem_preparada = preparar_imagem_para_ia(imagem)
    cliente = obter_cliente_ia()
    prompt = """
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
    resposta = cliente.models.generate_content(
        model=NOME_MODELO_IA, contents=[prompt, imagem_preparada]
    )

    texto = resposta.text.strip()
    texto = texto.replace("```json", "").replace("```", "").strip()

    try:
        dados = json.loads(texto)
    except json.JSONDecodeError:
        inicio, fim = texto.find("{"), texto.rfind("}")
        if inicio == -1 or fim == -1:
            raise
        dados = json.loads(texto[inicio : fim + 1])

    return normalizar_dados(dados)


def obter_pasta_trabalho():
    """Cada sessão (cada pessoa a usar a app) tem a sua própria pasta
    temporária, para que dois orçamentos gerados ao mesmo tempo por
    pessoas diferentes nunca se misturem."""
    if "pasta_trabalho" not in st.session_state:
        st.session_state.pasta_trabalho = tempfile.mkdtemp(prefix="orc_")
    return st.session_state.pasta_trabalho


def gerar_documento(nome_cliente, morada_cliente, dataframe_tabela, pagamento, nome_empresa, contato, email):
    pasta_trabalho = obter_pasta_trabalho()
    data_hoje = datetime.today().strftime("%d/%m/%Y")
    pdf_path = os.path.join(pasta_trabalho, "orcamento.pdf")

    linhas_html = ""
    total_orcamento = 0.0
    
    for idx, row in dataframe_tabela.iterrows():
        designacao = str(row.get("Designação", "")).strip()
        if not designacao:
            continue
            
        qtd = parse_numero(row.get("Quantidade", 0))
        preco = parse_numero(row.get("Preço Unitário (€)", 0))
        total_linha = qtd * preco
        total_orcamento += total_linha
        unidade = str(row.get("Unidade", "Vg."))
        
        linhas_html += f"""
        <tr>
            <td width="8%" style="border: 1px solid black; text-align: center; padding: 6px;">{idx + 1}</td>
            <td width="50%" style="border: 1px solid black; padding: 6px;">{designacao}</td>
            <td width="8%" style="border: 1px solid black; text-align: center; padding: 6px;">{unidade}</td>
            <td width="8%" style="border: 1px solid black; text-align: center; padding: 6px;">{formatar_numero(qtd)}</td>
            <td width="13%" style="border: 1px solid black; text-align: right; padding: 6px;">{formatar_numero(preco)}</td>
            <td width="13%" style="border: 1px solid black; text-align: right; padding: 6px;">{formatar_numero(total_linha)}</td>
        </tr>
        """

    assinatura = nome_empresa if nome_empresa else "Alfredo Cunha"

    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4;
                margin: 1.5cm; /* Margem reduzida para aproveitar melhor a folha */
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
                font-size: 11pt;
                color: #000000;
                line-height: 1.3;
            }}
            
            .header-cell {{
                border: 1px solid black;
                background-color: #A9D18E; 
                text-align: center;
                font-weight: bold;
                padding: 8px;
            }}
            
            .total-cell {{
                border: 1px solid black;
                background-color: #A9D18E; 
                font-weight: bold;
                padding: 8px;
            }}
        </style>
    </head>
    <body>
        
        <!-- CABEÇALHO COMPACTO: 2 Colunas lado a lado -->
        <table width="100%" cellpadding="0" cellspacing="0" style="font-family: Helvetica, sans-serif; font-size: 11pt; margin-bottom: 20px;">
            <tr>
                <td width="50%" style="vertical-align: top;">
                    <strong>{nome_empresa if nome_empresa else " "}</strong><br><br>
                    Telemóvel: {contato if contato else " "}<br>
                    Email: {email if email else " "}
                </td>
                <td width="50%" style="text-align: right; vertical-align: top;">
                    {data_hoje}<br><br>
                    Cliente: {nome_cliente if nome_cliente else " "}<br>
                    Local: {morada_cliente.replace(chr(10), ', ') if morada_cliente else " "}
                </td>
            </tr>
        </table>

        <!-- TABELA PRINCIPAL -->
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse;">
            <thead>
                <tr>
                    <th width="8%" class="header-cell">Art.</th>
                    <th width="50%" class="header-cell">Designação</th>
                    <th width="8%" class="header-cell">Unid.</th>
                    <th width="8%" class="header-cell">Qt.</th>
                    <th width="13%" class="header-cell">Preço Un.</th>
                    <th width="13%" class="header-cell">Total</th>
                </tr>
            </thead>
            <tbody>
                {linhas_html}
                <tr>
                    <td width="8%" class="total-cell"></td>
                    <td width="50%" class="total-cell"></td>
                    <td width="8%" class="total-cell"></td>
                    <td width="8%" class="total-cell"></td>
                    <td width="13%" class="total-cell" style="text-align: center;">TOTAL</td>
                    <td width="13%" class="total-cell" style="text-align: right;">{formatar_numero(total_orcamento)}</td>
                </tr>
            </tbody>
        </table>
        
        <br>

        <div style="font-family: Helvetica, sans-serif; font-size: 10pt;">
            <p><strong>Materiais e mão de obra incluída, assim como todas as ferramentas necessárias para a boa execução dos trabalhos.</strong></p>
            
            <p style="margin-top: 10px;"><strong>Condições gerais:</strong></p>
            <div style="margin-left: 20px; line-height: 1.4;">
                Aos preços apresentados acresce o IVA à taxa legal em vigor, caso seja necessária a emissão de fatura com número de contribuinte;<br>
                Garantias: Estão salvaguardadas todas as garantias ao abrigo das leis vigentes;<br>
                Condições de pagamento: {pagamento if pagamento else "A combinar"};<br>
                Este orçamento tem a validade de 30 dias.
            </div>
            
            <p style="margin-top: 30px;">
                <strong>Com os melhores cumprimentos,</strong><br><br>
                <strong><u>{assinatura}</u></strong>
            </p>
        </div>
        
    </body>
    </html>
    """

    with open(pdf_path, "w+b") as result_file:
        pisa.CreatePDF(html_content, dest=result_file)

    return pdf_path, data_hoje


# =========================================================================
# ECRÃS
# =========================================================================

def ecra_login():
    st.markdown("### Bem-vindo(a) ao Orçamentos")
    st.markdown("Introduza os seus dados para entrar.")
    
    email = st.text_input("Email", placeholder="O seu email", key="login_email")
    senha = st.text_input("Password", type="password", placeholder="A sua password", key="login_senha")
    
    entrar = st.button("Entrar", use_container_width=True, type="primary")
    
    if entrar:
        if not supabase:
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
                st.rerun()
            except Exception as e:
                st.error("Email ou password incorretos.")
                with st.expander("Detalhes"):
                    st.code(str(e))
                    
    st.markdown("</div>", unsafe_allow_html=True)


def passo_1_foto():
    st.markdown("## Passo 1 - Foto do Orçamento")
    st.markdown(
        '<div class="dica-caixa">Tire a foto num local bem iluminado, '
        "com o papel esticado e sem sombras por cima do texto.</div>",
        unsafe_allow_html=True,
    )

    aba_camera, aba_ficheiro = st.tabs(["Tirar Foto", "Escolher Ficheiro"])
    with aba_camera:
        foto_camera = st.camera_input("Tirar foto", label_visibility="collapsed")
    with aba_ficheiro:
        foto_ficheiro = st.file_uploader(
            "Escolher imagem", type=["jpg", "jpeg", "png"], label_visibility="collapsed"
        )

    arquivo_imagem = foto_ficheiro
    if foto_camera is not None:
        arquivo_imagem = foto_camera

    if arquivo_imagem is not None:
        imagem = Image.open(arquivo_imagem)
        st.image(imagem, caption="Pré-visualização", use_container_width=True)

        if st.button("Confirmar e Analisar", use_container_width=True, type="primary"):
            with st.spinner("A analisar o orçamento... alguns segundos."):
                try:
                    dados = extrair_dados_da_imagem(imagem)
                    st.session_state.dados_extraidos = dados
                    st.session_state.passo = 2
                    st.rerun()
                except json.JSONDecodeError:
                    st.error(
                        "Não conseguimos interpretar os dados da foto. "
                        "Tente novamente com mais luz e o papel bem esticado."
                    )
                except Exception as e:
                    st.error("Ocorreu um erro ao analisar a foto. Tente novamente.")
                    with st.expander("Detalhes técnicos"):
                        st.code(str(e))

    st.markdown("---")
    if st.button("Prefiro preencher os dados manualmente"):
        st.session_state.dados_extraidos = dados_vazios()
        st.session_state.passo = 2
        st.rerun()


def passo_2_confirmar():
    if "dados_extraidos" not in st.session_state:
        st.session_state.passo = 1
        st.rerun()

    st.markdown("## Passo 2 - Confirme os Dados")
    dados = st.session_state.dados_extraidos

    st.markdown("#### Resumo")
    titulo_orcamento = st.text_input("Título / Assunto do Orçamento", value=dados.get("Titulo", ""))

    st.markdown("#### Os seus dados")
    nome_empresa = st.text_input("Nome da Empresa / Pessoa", value=dados.get("NomeEmpresa", ""))
    contato = st.text_input("Contato", value=dados.get("Contato", ""))
    email = st.text_input("Email", value=dados.get("Email", ""))

    st.markdown("#### Dados do Cliente")
    nome_cliente = st.text_input("Nome do Cliente", value=dados.get("NomeCliente", ""))
    morada_cliente = st.text_area("Morada do Cliente", value=dados.get("MoradaCliente", ""))

    st.markdown("#### Trabalhos e Materiais")
    st.caption("Reveja as descrições, quantidades e preços. Pode adicionar ou apagar linhas.")

    df = pd.DataFrame(dados.get("Itens", []))
    for coluna in COLUNAS_TABELA:
        if coluna not in df.columns:
            df[coluna] = "" if coluna in ("Designação", "Unidade") else 0.0
    df = df[COLUNAS_TABELA]

    tabela_editada = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="editor_tabela",
        column_config={
            "Designação": st.column_config.TextColumn("Descrição", width="large"),
            "Unidade": st.column_config.TextColumn("Unid.", width="small"),
            "Quantidade": st.column_config.NumberColumn("Qtd.", min_value=0.0, step=0.5, format="%.2f"),
            "Preço Unitário (€)": st.column_config.NumberColumn(
                "Preço Unit. (€)", min_value=0.0, step=0.5, format="%.2f"
            ),
        },
    )

    quantidades = tabela_editada["Quantidade"].apply(parse_numero)
    precos = tabela_editada["Preço Unitário (€)"].apply(parse_numero)
    total = (quantidades * precos).sum()
    st.metric("Total do Orçamento", formatar_euro(total))

    pagamento = st.text_input("Condições de Pagamento", value=dados.get("Pagamento", ""))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Voltar", use_container_width=True):
            st.session_state.passo = 1
            st.rerun()
    with col2:
        gerar = st.button("Gerar PDF", use_container_width=True, type="primary")

    if gerar:
        if not morada_cliente.strip():
            st.warning("Por favor, preencha a morada do cliente.")
        elif tabela_editada["Designação"].apply(lambda x: str(x or "").strip()).eq("").all():
            st.warning("Adicione pelo menos um trabalho ou material ao orçamento.")
        else:
            with st.spinner("A gerar o PDF..."):
                try:
                    pdf_path, data_doc = gerar_documento(
                        nome_cliente, morada_cliente, tabela_editada, pagamento, nome_empresa, contato, email
                    )

                    try:
                        supabase.table("orcamentos").insert({
                            "user_id": st.session_state.user_id,
                            "titulo": titulo_orcamento,
                            "cliente": nome_cliente,
                            "total": float(total),
                            "conteudo": {
                                "Titulo": titulo_orcamento,
                                "NomeCliente": nome_cliente,
                                "MoradaCliente": morada_cliente,
                                "Pagamento": pagamento,
                                "Itens": tabela_editada.to_dict(orient="records")
                            }
                        }).execute()
                    except Exception as e:
                        print(f"Erro ao guardar na BD: {e}")

                    st.session_state.pdf_path = pdf_path
                    st.session_state.data_doc = data_doc
                    st.session_state.nome_cliente_final = nome_cliente
                    st.session_state.passo = 3
                    st.rerun()
                except Exception as e:
                    st.error("Ocorreu um erro ao gerar o documento PDF.")
                    with st.expander("Detalhes técnicos"):
                        st.code(str(e))


def passo_3_download():
    if "pdf_path" not in st.session_state:
        st.session_state.passo = 1
        st.rerun()

    st.markdown("## Orçamento Pronto")
    st.success("O PDF foi gerado com sucesso.")

    nome_base = (st.session_state.get("nome_cliente_final") or "cliente").strip()
    nome_base = re.sub(r"\s+", "_", nome_base) or "cliente"
    nome_ficheiro = f"Orcamento_{nome_base}_{st.session_state.data_doc.replace('/', '-')}.pdf"

    with open(st.session_state.pdf_path, "rb") as ficheiro_pdf:
        st.download_button(
            label="Descarregar PDF",
            data=ficheiro_pdf,
            file_name=nome_ficheiro,
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )

    st.markdown("---")
    if st.button("Criar Novo Orçamento", use_container_width=True):
        reiniciar_sessao()
        st.rerun()


def reiniciar_sessao():
    for chave in ["dados_extraidos", "pdf_path", "data_doc", "nome_cliente_final"]:
        st.session_state.pop(chave, None)
    st.session_state.passo = 1


def extrair_resumo_orcamento(orc):
    """Deriva o título, o cliente e o total a mostrar/reutilizar sempre a
    partir da MESMA fonte: o campo 'conteudo' (o JSON completo). As colunas
    'titulo', 'cliente' e 'total' da tabela existem só para permitir
    pesquisar/ordenar na base de dados - nunca são a fonte de verdade para
    o que aparece no ecrã, para evitar que a sidebar e o Passo 2 mostrem
    dados diferentes para o mesmo orçamento caso as colunas e o JSON alguma
    vez fiquem dessincronizados (ex.: uma futura função de editar/renomear
    que só atualize um dos dois locais).

    As colunas da tabela só são usadas como reserva, para registos antigos
    ou incompletos em que o 'conteudo' não tenha o campo."""
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


def carregar_orcamento_selecionado(orc):
    """Coloca os dados de um orçamento já guardado no Passo 2, prontos a
    rever e editar. Serve para reaproveitar rapidamente trabalhos e
    materiais idênticos num novo orçamento (ex.: o mesmo tipo de obra
    para um cliente diferente), sem ter de voltar a fotografar ou a
    escrever tudo de novo."""
    _, _, _, conteudo = extrair_resumo_orcamento(orc)
    st.session_state.dados_extraidos = normalizar_dados(conteudo)

    # Limpar resíduos de um PDF gerado anteriormente nesta sessão, para
    # não mostrar por engano o ficheiro de um orçamento antigo.
    for chave in ["pdf_path", "data_doc", "nome_cliente_final"]:
        st.session_state.pop(chave, None)

    st.session_state.passo = 2
    st.rerun()


def mostrar_historico_lateral():
    """Mostra a lista de orçamentos guardados numa barra lateral (Sidebar).
    Cada orçamento é clicável: ao tocar, os seus dados são carregados no
    Passo 2, para facilitar a criação de um novo orçamento com trabalhos
    idênticos aos desse orçamento."""
    with st.sidebar:
        st.markdown("## Os Meus Orçamentos")
        st.caption("Toque num orçamento para reutilizar os seus dados.")

        try:
            # Ir buscar os orçamentos do utilizador ordenados do mais recente para o mais antigo
            resposta = supabase.table("orcamentos").select("*").eq("user_id", st.session_state.user_id).order("data_criacao", desc=True).execute()
            orcamentos = resposta.data
            
            if not orcamentos:
                st.info("Ainda não tem orçamentos guardados.")
            else:
                for indice, orc in enumerate(orcamentos):
                    # Formatar a data (ex: 2026-08-07T12:00:00 -> 07/08/2026)
                    data_str = orc['data_criacao'].split('T')[0]
                    ano, mes, dia = data_str.split('-')

                    titulo, cliente, total, _ = extrair_resumo_orcamento(orc)

                    # Item clicável (aspeto de cartão minimalista, igual ao anterior)
                    rotulo = f"**{titulo}** · {total:.2f} €\n\n{cliente} · {dia}/{mes}/{ano}"
                    if st.button(
                        rotulo,
                        key=f"orc_item_{orc.get('id', indice)}",
                        use_container_width=True,
                    ):
                        carregar_orcamento_selecionado(orc)
                    
        except Exception as e:
            st.error("Não foi possível carregar o histórico.")

# ARRANQUE DA APLICAÇÃO

def main():
    st.set_page_config(page_title="Orçamentos", page_icon="🧾", layout="centered", initial_sidebar_state="collapsed")
    aplicar_estilo()

    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.markdown("<h1>Orçamentos</h1>", unsafe_allow_html=True)
        ecra_login()
        return

    mostrar_historico_lateral()

    if "passo" not in st.session_state:
        st.session_state.passo = 1

    st.markdown("<h1>Orçamentos</h1>", unsafe_allow_html=True)
    indicador_passos(st.session_state.passo)

    if st.session_state.passo == 1:
        passo_1_foto()
    elif st.session_state.passo == 2:
        passo_2_confirmar()
    elif st.session_state.passo == 3:
        passo_3_download()


if __name__ == "__main__":
    main()