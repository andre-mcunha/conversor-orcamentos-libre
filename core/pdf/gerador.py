"""
Geração do PDF final do orçamento.

Recebe a pasta de trabalho como argumento em vez de a gerir sozinho via
`st.session_state`, o que mantém este módulo testável (ver
tests/test_gerador.py) e independente do Streamlit: pode gerar um PDF
para dentro de qualquer pasta temporária. A camada de UI é que decide
reutilizar sempre a mesma pasta por sessão (/ui/passo2_confirmar.py).
"""

import logging
import os
import tempfile
from datetime import datetime

import pandas as pd
from xhtml2pdf import pisa

from core.utils import formatar_numero, parse_numero

logger = logging.getLogger(__name__)


def nova_pasta_trabalho() -> str:
    """Cria uma pasta temporária isolada para os ficheiros gerados numa
    sessão, para que dois orçamentos gerados ao mesmo tempo por pessoas
    diferentes nunca se misturem."""
    return tempfile.mkdtemp(prefix="orc_")


def gerar_documento(
    pasta_trabalho: str,
    nome_cliente: str,
    morada_cliente: str,
    dataframe_tabela: pd.DataFrame,
    pagamento: str,
    nome_empresa: str,
    contato: str,
    email: str,
):
    """Gera o PDF do orçamento e devolve (caminho_do_pdf, data_formatada)."""
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
        pisa_status = pisa.CreatePDF(html_content, dest=result_file)

    if pisa_status.err:
        logger.error("xhtml2pdf devolveu %d erro(s) ao gerar o PDF.", pisa_status.err)
    else:
        logger.info("PDF gerado em %s (total=%.2f).", pdf_path, total_orcamento)

    return pdf_path, data_hoje