"""Simulador de Precificacao e Vendas.

Aplicacao Streamlit em um unico arquivo para estimar preco de venda e lucro.
"""

import io

import pandas as pd
import streamlit as st


# Configuracao geral da pagina
st.set_page_config(
	page_title="Simulador de Precificacao",
	page_icon="💰",
	layout="wide",
)


def formatar_reais(valor: float) -> str:
	"""Formata um numero no padrao monetario brasileiro."""
	texto = f"R$ {valor:,.2f}"
	return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def calcular_precificacao(custo: float, margem: float, impostos: float) -> dict:
	"""Calcula preco, impostos e lucro liquido a partir dos percentuais informados.

	Margem e impostos sao considerados percentuais do preco final de venda.
	"""
	percentual_restante = 1 - margem / 100 - impostos / 100
	if percentual_restante <= 0:
		raise ValueError("A margem e os impostos juntos devem ser menores que 100%.")

	preco_venda = custo / percentual_restante
	valor_impostos = preco_venda * impostos / 100
	lucro_liquido = preco_venda - custo - valor_impostos

	return {
		"Preco de venda sugerido": preco_venda,
		"Custo de producao": custo,
		"Impostos": valor_impostos,
		"Lucro liquido": lucro_liquido,
		"Margem desejada (%)": margem,
		"Impostos (%)": impostos,
	}


def criar_tabela_historico() -> pd.DataFrame:
	"""Cria um DataFrame com os calculos salvos na sessao atual."""
	if not st.session_state.historico:
		return pd.DataFrame(
			columns=[
				"Produto",
				"Custo de producao (R$)",
				"Margem desejada (%)",
				"Impostos (%)",
				"Preco sugerido (R$)",
				"Impostos (R$)",
				"Lucro liquido (R$)",
			]
		)
	return pd.DataFrame(st.session_state.historico)


# O historico permanece disponivel enquanto o usuario usa a aplicacao.
if "historico" not in st.session_state:
	st.session_state.historico = []


st.title("💰 Simulador de Precificacao e Vendas")
st.caption("Descubra um preco de venda que cobre seus custos e preserva a margem desejada.")

aba_simulador, aba_historico = st.tabs(["🧮 Simulador", "📋 Historico de calculos"])

with aba_simulador:
	st.subheader("Dados do produto")

	with st.form("formulario_precificacao"):
		coluna_esquerda, coluna_direita = st.columns(2)
		with coluna_esquerda:
			nome_produto = st.text_input(
				"Nome do produto *",
				placeholder="Ex.: Bolo de chocolate",
			)
			custo_producao = st.number_input(
				"Custo de producao (R$) *",
				min_value=0.0,
				value=100.0,
				step=10.0,
				format="%.2f",
			)
		with coluna_direita:
			margem_lucro = st.number_input(
				"Margem de lucro desejada (%) *",
				min_value=0.0,
				max_value=99.99,
				value=30.0,
				step=1.0,
				format="%.2f",
			)
			impostos = st.number_input(
				"Impostos sobre a venda (%) *",
				min_value=0.0,
				max_value=99.99,
				value=10.0,
				step=1.0,
				format="%.2f",
			)

		calcular = st.form_submit_button("Calcular preco", type="primary", use_container_width=True)

	if calcular:
		nome_produto = nome_produto.strip()

		if not nome_produto:
			st.warning("Informe o nome do produto antes de calcular.")
		elif custo_producao <= 0:
			st.warning("O custo de producao deve ser maior que zero.")
		else:
			try:
				resultado = calcular_precificacao(custo_producao, margem_lucro, impostos)
				st.session_state.ultimo_resultado = resultado
				st.session_state.ultimo_produto = nome_produto

				st.session_state.historico.append(
					{
						"Produto": nome_produto,
						"Custo de producao (R$)": resultado["Custo de producao"],
						"Margem desejada (%)": resultado["Margem desejada (%)"],
						"Impostos (%)": resultado["Impostos (%)"],
						"Preco sugerido (R$)": resultado["Preco de venda sugerido"],
						"Impostos (R$)": resultado["Impostos"],
						"Lucro liquido (R$)": resultado["Lucro liquido"],
					}
				)
				st.success(f"Calculo concluido para **{nome_produto}**.")
			except ValueError as erro:
				st.error(str(erro))

	if "ultimo_resultado" in st.session_state:
		resultado = st.session_state.ultimo_resultado
		st.divider()
		st.subheader(f"Resultado: {st.session_state.ultimo_produto}")

		metricas = st.columns(3)
		metricas[0].metric("Preco final sugerido", formatar_reais(resultado["Preco de venda sugerido"]))
		metricas[1].metric("Lucro liquido", formatar_reais(resultado["Lucro liquido"]))
		metricas[2].metric("Impostos pagos", formatar_reais(resultado["Impostos"]))

		dados_grafico = pd.DataFrame(
			{
				"Composicao do preco": ["Custo", "Impostos", "Lucro liquido"],
				"Valor (R$)": [
					resultado["Custo de producao"],
					resultado["Impostos"],
					resultado["Lucro liquido"],
				],
			}
		).set_index("Composicao do preco")
		st.write("**Composicao do preco sugerido**")
		st.bar_chart(dados_grafico, color="#0f766e", height=300)

with aba_historico:
	st.subheader("Calculos realizados nesta sessao")
	tabela = criar_tabela_historico()

	if tabela.empty:
		st.info("Ainda nao ha calculos salvos. Use a aba Simulador para adicionar um produto.")
	else:
		st.dataframe(
			tabela.style.format(
				{
					"Custo de producao (R$)": "R$ {:,.2f}",
					"Preco sugerido (R$)": "R$ {:,.2f}",
					"Impostos (R$)": "R$ {:,.2f}",
					"Lucro liquido (R$)": "R$ {:,.2f}",
					"Margem desejada (%)": "{:.2f}%",
					"Impostos (%)": "{:.2f}%",
				}
			),
			use_container_width=True,
			hide_index=True,
		)

		csv_buffer = io.StringIO()
		tabela.to_csv(csv_buffer, index=False, sep=";", encoding="utf-8-sig")
		st.download_button(
			label="Baixar tabela em CSV",
			data=csv_buffer.getvalue(),
			file_name="historico_precificacao.csv",
			mime="text/csv",
			use_container_width=True,
		)

		if st.button("Limpar historico", type="secondary"):
			st.session_state.historico = []
			st.rerun()


st.divider()
st.caption("Os valores sao estimativas. Confirme as regras tributarias aplicaveis ao seu negocio.")
