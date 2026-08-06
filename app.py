import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from PIL import Image
import os
import json
from datetime import datetime
import subprocess
from copy import deepcopy
from docx.enum.text import WD_ALIGN_PARAGRAPH
from dotenv import load_dotenv

# Carregar variáveis de ambiente (localmente lê o .env, na Cloud lê os Streamlit Secrets)
load_dotenv()

# CONFIGURAÇÕES
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except Exception:
    API_KEY = os.getenv("API_KEY")

TEMPLATE_PATH = "template.docx"
DOCX_TEMP_PATH = "orcamento_final.docx"
PDF_FINAL_PATH = "orcamento_final.pdf"

def configurar_ia():
    """Configura a ligação à API do Google Gemini."""
    if API_KEY:
        genai.configure(api_key=API_KEY)

def extrair_dados_da_imagem(imagem):
    """Envia a imagem para o Gemini e devolve os dados estruturados."""
    model = genai.GenerativeModel('gemini-1.5-pro')
    prompt = """
    Lê as anotações desta imagem referentes a um orçamento. 
    Extrai o nome do cliente, a morada do cliente (se existirem) e a informação para preencher a tabela de trabalhos/materiais.
    Devolve APENAS um ficheiro JSON válido com a seguinte estrutura exata, sem texto adicional (nem marcações ```json):
    {
      "NomeCliente": "nome extraido ou vazio",
      "MoradaCliente": "morada extraida ou vazio",
      "Pagamento": "condições de pagamento extraídas ou vazio",
      "Itens": [
        {
          "Item": "",
          "Designação": "descrição dos trabalhos terminada com ponto e vírgula",
          "Unidade": "Vg.",
          "Quantidade": "1",
          "Preço Unitário (€)": "0.00",
          "Preço Total (€)": "0.00"
        }
      ]
    }
    """
    resposta = model.generate_content([prompt, imagem])
    
    # Limpar a resposta e converter para dicionário Python
    texto_limpo = resposta.text.replace('```json', '').replace('```', '').strip()
    return json.loads(texto_limpo)

def gerar_documento(nome_cliente, morada_cliente, dataframe_tabela, pagamento):
    """Recebe os dados, preenche o Word e converte para PDF usando LibreOffice."""
    doc = Document(TEMPLATE_PATH)
    data_hoje = datetime.today().strftime('%d/%m/%Y')
    
    # Substituir Etiquetas (Morada, Pagamento e Data)
    for paragrafo in doc.paragraphs:
        if "{{NOME_CLIENTE}}" in paragrafo.text:
            paragrafo.text = paragrafo.text.replace("{{NOME_CLIENTE}}", nome_cliente)
        if "{{MORADA}}" in paragrafo.text:
            paragrafo.text = paragrafo.text.replace("{{MORADA}}", morada_cliente)
        if "{{PAGAMENTO}}" in paragrafo.text:
            paragrafo.text = paragrafo.text.replace("{{PAGAMENTO}}", pagamento)
        if "{{DATA}}" in paragrafo.text:
            paragrafo.text = paragrafo.text.replace("{{DATA}}", data_hoje)
            
    # Preencher a Tabela com Estratégia de 2 Moldes
    tabela_word = doc.tables[0]
    total_orcamento = 0.0
        
    # Guardar as estruturas XML dos dois moldes (Linha 2 e Linha 3 do Word)
    molde_item = deepcopy(tabela_word.rows[2]._tr)
    molde_total = deepcopy(tabela_word.rows[3]._tr)
    
    # Apagar os moldes da tabela original para a limpar (fica só o cabeçalho)
    tabela_word._tbl.remove(tabela_word.rows[3]._tr)
    tabela_word._tbl.remove(tabela_word.rows[2]._tr)
    tabela_word._tbl.remove(tabela_word.rows[1]._tr)
    
    # Preencher os Itens (usando o molde branco)
    for index, row in dataframe_tabela.iterrows():
        nova_linha_tr = deepcopy(molde_item)
        tabela_word._tbl.append(nova_linha_tr)
        linha_nova = tabela_word.rows[-1].cells 
        
        for cell in linha_nova:
            cell.text = ""
            
        # Preencher colunas
        linha_nova[0].text = str(row.get("Item", ""))
        linha_nova[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        linha_nova[1].text = str(row.get("Designação", ""))
        linha_nova[2].text = str(row.get("Unidade", "Vg."))
        linha_nova[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        quantidade = str(row.get("Quantidade", ""))
        linha_nova[3].text = quantidade
        linha_nova[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        preco_str = str(row.get("Preço Unitário (€)", "")).replace(",", ".")
        try:
            preco_float = float(preco_str)
            preco_total_linha = preco_float * float(quantidade if quantidade else 1)
            total_orcamento += preco_total_linha
        except ValueError:
            preco_total_linha = 0.0
            
        linha_nova[4].text = preco_str
        linha_nova[4].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        linha_nova[5].text = f"{preco_total_linha:.2f}"
        linha_nova[5].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Inserir a linha final de Total (usando o molde verde)
    nova_linha_total_tr = deepcopy(molde_total)
    tabela_word._tbl.append(nova_linha_total_tr)
    linha_total = tabela_word.rows[-1].cells
    
    linha_total[4].text = "TOTAL:"
    linha_total[5].text = f"{total_orcamento:.2f} €"

    if len(linha_total[4].paragraphs[0].runs) > 0:
        linha_total[4].paragraphs[0].runs[0].bold = True
    if len(linha_total[5].paragraphs[0].runs) > 0:
        linha_total[5].paragraphs[0].runs[0].bold = True
    
    # Guardar o ficheiro Word temporário
    doc.save(DOCX_TEMP_PATH)
    
    # Converter para PDF usando o LibreOffice (compatível com Linux / Cloud)
    subprocess.run([
        "libreoffice", "--headless", "--convert-to", "pdf", 
        DOCX_TEMP_PATH, "--outdir", "."
    ], check=True)
    
    return PDF_FINAL_PATH, data_hoje

def main():
    configurar_ia()
    
    st.set_page_config(page_title="Conversor de Orçamentos", layout="centered")

    try:
        PASSWORD_SISTEMA = st.secrets["APP_PASSWORD"]
    except Exception:
        PASSWORD_SISTEMA = os.getenv("APP_PASSWORD")

    # Desenha a caixa de password
    pwd_inserida = st.text_input("Insira a password para aceder:", type="password")

    # Se a password estiver errada ou vazia, paramos a aplicação aqui!
    if pwd_inserida != PASSWORD_SISTEMA:
        st.stop()

    st.title("Orçamentos Papel para PDF")

    # Iniciar estado da memória para a tabela e inputs
    if "dados_tabela" not in st.session_state:
        st.session_state["dados_tabela"] = pd.DataFrame(
            columns=["Item", "Designação", "Unidade", "Quantidade", "Preço Unitário (€)", "Preço Total (€)"]
        )
    if "input_nome" not in st.session_state:
        st.session_state["input_nome"] = ""
    if "input_morada" not in st.session_state:
        st.session_state["input_morada"] = ""
    if "input_pagamento" not in st.session_state:
        st.session_state["input_pagamento"] = ""

    # --- UI: UPLOAD DA IMAGEM ---
    st.subheader("Faça upload da imagem do orçamento")
    foto = st.file_uploader(label="Selecione a imagem do orçamento", type=["jpg", "jpeg", "png"])

    if foto is not None:
        imagem = Image.open(foto)
        st.image(imagem, caption="Foto original", width=300)
        
        if st.button("Extrair dados da imagem"):
            with st.spinner("A processar..."):
                try:
                    dados_extraidos = extrair_dados_da_imagem(imagem)

                    st.session_state["input_nome"] = dados_extraidos.get("NomeCliente", "")
                    st.session_state["input_morada"] = dados_extraidos.get("MoradaCliente", "")
                    st.session_state["input_pagamento"] = dados_extraidos.get("Pagamento", "")
                    st.session_state["dados_tabela"] = pd.DataFrame(dados_extraidos.get("Itens", []))
                    st.success("Dados extraídos com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao ler a imagem. Detalhes: {e}")

    # --- UI: DADOS DO CLIENTE ---
    nome_cliente = st.text_input("Nome do Cliente:", key="input_nome")
    morada_cliente = st.text_area("Morada do Cliente:", key="input_morada")

    # --- UI: EDITAR DADOS ---
    st.write("Confirme e edite os preços e quantidades")
    tabela_editada = st.data_editor(st.session_state["dados_tabela"], num_rows="dynamic", use_container_width=True)

    # --- UI: CONDIÇÕES DE PAGAMENTO ---
    pagamento = st.text_input("Condições de Pagamento:", key="input_pagamento")

    # --- UI: GERAR PDF ---
    if st.button("Gerar PDF"):
        if not morada_cliente:
            st.warning("Por favor, preencha a morada.")
        else:
            with st.spinner("A gerar o documento Word e PDF..."):
                try:
                    pdf_gerado, data_doc = gerar_documento(nome_cliente, morada_cliente, tabela_editada, pagamento)
                    st.success("PDF gerado com sucesso!")
                    
                    with open(pdf_gerado, "rb") as pdf_file:
                        st.download_button(
                            label="Descarregar Orçamento em PDF",
                            data=pdf_file,
                            file_name=f"Orcamento_{data_doc.replace('/','-')}.pdf",
                            mime="application/pdf"
                        )
                except Exception as e:
                    st.error(f"Erro ao gerar o PDF: {e}")

# ARRANQUE DA APLICAÇÃO
if __name__ == "__main__":
    main()