import streamlit as st
import pandas as pd
from backend import calcular_clt, responder_chat_ia

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Sistema Financeiro",
    layout="centered"
)

# --- CSS MINIMALISTA E SÓBRIO ---
st.markdown("""
<style>
/* Fundo escuro fosco e minimalista */
.stApp {
    background-color: #0E1117 !important;
    color: #FAFAFA !important;
}

/* Containers limpos com borda cinza discreta */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #161A24 !important;
    border: 1px solid #262D3D !important;
    border-radius: 8px !important;
    padding: 16px !important;
}

/* Cards de métricas sóbrios */
div[data-testid="stMetric"] {
    background-color: #11141C !important;
    border: 1px solid #262D3D !important;
    padding: 14px 18px !important;
    border-radius: 6px !important;
}
div[data-testid="stMetricValue"] > div {
    font-weight: 600 !important;
    color: #FFFFFF !important;
}

/* Removendo excesso de margens em cabeçalhos */
h1, h2, h3, h4 {
    font-weight: 600 !important;
    letter-spacing: -0.3px !important;
}

/* Estilo discreto da barra lateral */
section[data-testid="stSidebar"] {
    background-color: #0A0C10 !important;
    border-right: 1px solid #1C212E !important;
}
hr {
    border-color: #262D3D !important;
}
</style>
""", unsafe_allow_html=True)

# Inicializando estado financeiro global
if "salario_liquido" not in st.session_state:
    st.session_state["salario_liquido"] = 3802.43
if "hora_liquida" not in st.session_state:
    st.session_state["hora_liquida"] = 17.28
if "salario_bruto_total" not in st.session_state:
    st.session_state["salario_bruto_total"] = 4500.00
if "total_fixo" not in st.session_state:
    st.session_state["total_fixo"] = 2050.00
if "total_var" not in st.session_state:
    st.session_state["total_var"] = 950.00
if "total_faturas" not in st.session_state:
    st.session_state["total_faturas"] = 589.90

# Estrutura de conversas no formato limpo
if "conversas" not in st.session_state:
    st.session_state["conversas"] = {
        "1": {
            "titulo": "Diagnóstico Inicial",
            "mensagens": []
        }
    }
if "conversa_ativa" not in st.session_state:
    st.session_state["conversa_ativa"] = "1"
if "contador_conversas" not in st.session_state:
    st.session_state["contador_conversas"] = 1

# ==========================================
# BARRA LATERAL (MENU)
# ==========================================
st.sidebar.title("Sistema Financeiro")
st.sidebar.caption("Gestão Patrimonial e CLT")

menu_selecionado = st.sidebar.radio(
    "Navegação:",
    [
        "Trabalhista & CLT",
        "Orçamento Pessoal",
        "Cartões de Crédito",
        "Consultoria IA"
    ]
)

st.sidebar.divider()
st.sidebar.caption("Os cálculos e faturas são sincronizados automaticamente entre os módulos.")

# ==========================================
# 1. TRABALHISTA & CLT
# ==========================================
if menu_selecionado == "Trabalhista & CLT":
    st.title("Trabalhista & CLT")
    st.write("Demonstrativo de descontos oficiais e remuneração líquida real.")
    st.divider()

    with st.container(border=True):
        st.subheader("Parâmetros do Salário")
        col1, col2 = st.columns(2)
        with col1:
            salario_base = st.number_input("Salário Bruto Base (R$)", min_value=1000.0, value=4500.0, step=100.0)
        with col2:
            jornada = st.selectbox("Jornada Mensal (Horas)", options=[220, 180, 160], index=0)

        col3, col4 = st.columns(2)
        with col3:
            dependentes = st.number_input("Dependentes", min_value=0, value=0, step=1)
        with col4:
            st.write("")
            aplicar_irrf = st.toggle("Descontar IRRF na fonte", value=True)

        horas_50, horas_100 = 0.0, 0.0
        with st.expander("Adicionar Horas Extras no Mês"):
            col_he1, col_he2 = st.columns(2)
            with col_he1:
                horas_50 = st.number_input("Horas Extras 50% (Qtd)", min_value=0.0, value=0.0, step=1.0)
            with col_he2:
                horas_100 = st.number_input("Horas Extras 100% (Qtd)", min_value=0.0, value=0.0, step=1.0)

    folha = calcular_clt(salario_base, jornada, dependentes, aplicar_irrf, horas_50, horas_100)
    
    st.session_state["salario_liquido"] = folha["salario_liquido"]
    st.session_state["hora_liquida"] = folha["hora_liquida"]
    st.session_state["salario_bruto_total"] = folha["salario_bruto_total"]

    st.write("")
    with st.container(border=True):
        st.subheader("Composição da Remuneração")

        if folha["total_horas_extras"] > 0:
            st.write(f"**Salário Bruto Total:** R$ {folha['salario_bruto_total']:,.2f}")

        card1, card2, card3 = st.columns(3)
        with card1:
            st.metric("Salário Líquido", f"R$ {folha['salario_liquido']:,.2f}", delta=f"Hora real: R$ {folha['hora_liquida']:,.2f}")
        with card2:
            st.metric("Desconto INSS", f"R$ {folha['inss']:,.2f}")
        with card3:
            if aplicar_irrf:
                st.metric("Desconto IRRF", f"R$ {folha['irrf']:,.2f}")
            else:
                st.metric("Desconto IRRF", "R$ 0,00", delta="Isento", delta_color="off")

        st.write("")
        st.caption(f"FGTS Acumulado no Mês (8%): R$ {folha['fgts']:,.2f} — Valor recolhido integralmente pelo empregador.")

# ==========================================
# 2. ORÇAMENTO PESSOAL
# ==========================================
elif menu_selecionado == "Orçamento Pessoal":
    st.title("Orçamento Pessoal")
    st.write("Gestão de despesas essenciais e saldo líquido disponível.")
    st.divider()

    sal_liquido = st.session_state["salario_liquido"]
    hora_liq = st.session_state["hora_liquida"]

    st.write(f"**Renda Disponível (Salário Líquido):** R$ {sal_liquido:,.2f}")

    with st.container(border=True):
        col_fixo, col_var = st.columns(2)
        with col_fixo:
            st.markdown("#### Despesas Fixas")
            moradia = st.number_input("Aluguel / Condomínio", min_value=0.0, value=1200.0, step=50.0)
            contas = st.number_input("Contas Básicas (Luz, Água, Internet)", min_value=0.0, value=300.0, step=20.0)
            transporte = st.number_input("Transporte / Combustível", min_value=0.0, value=350.0, step=20.0)
            outros_fixos = st.number_input("Outras Despesas Fixas", min_value=0.0, value=200.0, step=20.0)

        with col_var:
            st.markdown("#### Despesas Variáveis")
            alimentacao = st.number_input("Alimentação / Delivery", min_value=0.0, value=400.0, step=20.0)
            lazer = st.number_input("Lazer e Assinaturas", min_value=0.0, value=250.0, step=20.0)
            compras = st.number_input("Imprevistos e Outros", min_value=0.0, value=300.0, step=20.0)

    total_fixo = round(moradia + contas + transporte + outros_fixos, 2)
    total_var = round(alimentacao + lazer + compras, 2)
    
    st.session_state["total_fixo"] = total_fixo
    st.session_state["total_var"] = total_var

    total_gastos = round(total_fixo + total_var, 2)
    sobra_antes_cartao = round(sal_liquido - total_gastos, 2)

    st.write("")
    with st.container(border=True):
        st.subheader("Resumo de Despesas")
        b_card1, b_card2, b_card3 = st.columns(3)
        with b_card1:
            st.metric("Despesas Fixas", f"R$ {total_fixo:,.2f}")
        with b_card2:
            st.metric("Despesas Variáveis", f"R$ {total_var:,.2f}")
        with b_card3:
            st.metric("Saldo Pré-Cartão", f"R$ {sobra_antes_cartao:,.2f}", delta="Antes de faturas")

    st.write("")
    with st.container(border=True):
        st.subheader("Custo em Horas de Trabalho")
        col_gasto1, col_gasto2 = st.columns([1, 2])
        with col_gasto1:
            valor_compra = st.number_input("Valor para simular (R$)", min_value=1.0, value=150.0, step=10.0)
        with col_gasto2:
            if hora_liq > 0:
                total_minutos = round((valor_compra / hora_liq) * 60)
                horas = total_minutos // 60
                minutos = total_minutos % 60
                st.write(f"Para adquirir um item de **R$ {valor_compra:,.2f}**, o tempo de trabalho líquido correspondente é de **{horas} horas e {minutos} minutos**.")

# ==========================================
# 3. CARTÕES DE CRÉDITO
# ==========================================
elif menu_selecionado == "Cartões de Crédito":
    st.title("Cartões de Crédito")
    st.write("Acompanhamento de faturas, parcelas e limites disponíveis.")
    st.divider()

    aba1, aba2 = st.tabs(["Cartão Principal", "Cartão Secundário"])

    with aba1:
        with st.container(border=True):
            st.subheader("Cartão Principal")
            nome_c1 = st.text_input("Identificação", value="Nubank", key="nome_c1")
            col_c1_a, col_c1_b = st.columns(2)
            with col_c1_a:
                limite_c1 = st.number_input("Limite Total (R$)", min_value=0.0, value=5000.0, step=100.0, key="lim_c1")
                fatura_base_c1 = st.number_input("Parcelas em Andamento (R$)", min_value=0.0, value=300.0, step=50.0, key="base_c1")
            with col_c1_b:
                fechamento_c1 = st.number_input("Dia do Fechamento", min_value=1, max_value=31, value=25, key="fech_c1")
                vencimento_c1 = st.number_input("Dia do Vencimento", min_value=1, max_value=31, value=5, key="venc_c1")

            st.markdown(f"**Registros do Mês — {nome_c1}**")
            df_c1 = st.data_editor(
                pd.DataFrame([
                    {"Descrição": "Supermercado", "Valor (R$)": 250.00},
                    {"Descrição": "Assinatura de Softwares", "Valor (R$)": 39.90}
                ]),
                num_rows="dynamic",
                use_container_width=True,
                key="tabela_c1"
            )
            
            fatura_total_c1 = round(fatura_base_c1 + df_c1["Valor (R$)"].sum(), 2)
            limite_disp_c1 = max(0.0, limite_c1 - fatura_total_c1)
            melhor_dia_c1 = (fechamento_c1 % 31) + 1

            res1, res2, res3 = st.columns(3)
            with res1:
                st.metric(f"Fatura Total — {nome_c1}", f"R$ {fatura_total_c1:,.2f}")
            with res2:
                st.metric("Limite Disponível", f"R$ {limite_disp_c1:,.2f}")
            with res3:
                st.metric("Melhor Dia de Compra", f"Dia {melhor_dia_c1}")

    with aba2:
        with st.container(border=True):
            st.subheader("Cartão Secundário")
            nome_c2 = st.text_input("Identificação", value="XP / Itaú", key="nome_c2")
            col_c2_a, col_c2_b = st.columns(2)
            with col_c2_a:
                limite_c2 = st.number_input("Limite Total (R$)", min_value=0.0, value=3000.0, step=100.0, key="lim_c2")
                fatura_base_c2 = st.number_input("Parcelas em Andamento (R$)", min_value=0.0, value=0.0, step=50.0, key="base_c2")
            with col_c2_b:
                fechamento_c2 = st.number_input("Dia do Fechamento", min_value=1, max_value=31, value=10, key="fech_c2")
                vencimento_c2 = st.number_input("Dia do Vencimento", min_value=1, max_value=31, value=20, key="venc_c2")

            st.markdown(f"**Registros do Mês — {nome_c2}**")
            df_c2 = st.data_editor(
                pd.DataFrame([{"Descrição": "Combustível", "Valor (R$)": 150.00}]),
                num_rows="dynamic",
                use_container_width=True,
                key="tabela_c2"
            )
            
            fatura_total_c2 = round(fatura_base_c2 + df_c2["Valor (R$)"].sum(), 2)
            limite_disp_c2 = max(0.0, limite_c2 - fatura_total_c2)
            melhor_dia_c2 = (fechamento_c2 % 31) + 1

            res_b1, res_b2, res_b3 = st.columns(3)
            with res_b1:
                st.metric(f"Fatura Total — {nome_c2}", f"R$ {fatura_total_c2:,.2f}")
            with res_b2:
                st.metric("Limite Disponível", f"R$ {limite_disp_c2:,.2f}")
            with res_b3:
                st.metric("Melhor Dia de Compra", f"Dia {melhor_dia_c2}")

    st.session_state["total_faturas"] = round(fatura_total_c1 + fatura_total_c2, 2)

    st.write("")
    st.write(f"**Total Agregado de Faturas:** R$ {st.session_state['total_faturas']:,.2f}")

# ==========================================
# 4. CONSULTORIA IA
# ==========================================
elif menu_selecionado == "Consultoria IA":
    st.title("Consultoria Financeira IA")
    st.write("Diagnóstico analítico patrimonial e histórico de atendimentos.")
    st.divider()

    sal_liq = st.session_state["salario_liquido"]
    fixos = st.session_state["total_fixo"]
    variaveis = st.session_state["total_var"]
    faturas = st.session_state["total_faturas"]
    
    total_saidas = round(fixos + variaveis + faturas, 2)
    saldo_livre = round(sal_liq - total_saidas, 2)

    pct_comprometido = (total_saidas / sal_liq) * 100 if sal_liq > 0 else 100
    
    with st.container(border=True):
        st.subheader("Comprometimento Orçamentário")
        col_saude1, col_saude2 = st.columns([1, 2])
        
        with col_saude1:
            if pct_comprometido <= 80:
                st.write("**Status: Saudável**")
            elif pct_comprometido <= 95:
                st.write("**Status: Atenção**")
            else:
                st.write("**Status: Crítico**")
                
        with col_saude2:
            st.write(f"As despesas representam **{pct_comprometido:.1f}%** da sua remuneração líquida.")
            st.progress(min(1.0, max(0.0, total_saidas / sal_liq if sal_liq > 0 else 1.0)))

    st.write("")

    with st.container(border=True):
        col_hist, col_chat = st.columns([1.2, 2.8])

        with col_hist:
            st.markdown("### Consultas")
            
            if st.button("Nova Consulta", use_container_width=True, type="primary"):
                st.session_state["contador_conversas"] += 1
                novo_id = str(st.session_state["contador_conversas"])
                st.session_state["conversas"][novo_id] = {
                    "titulo": f"Consulta #{novo_id}",
                    "mensagens": []
                }
                st.session_state["conversa_ativa"] = novo_id
                st.rerun()

            st.write("")
            termo_pesquisa = st.text_input("Pesquisar...", placeholder="Filtro de busca").lower()

            st.markdown("#### Histórico")
            
            conversas_filtradas = {
                id_conv: dados for id_conv, dados in st.session_state["conversas"].items()
                if termo_pesquisa in dados["titulo"].lower() or any(
                    termo_pesquisa in m["content"].lower() for m in dados["mensagens"]
                )
            }

            if not conversas_filtradas:
                st.caption("Nenhuma consulta encontrada.")
            else:
                for id_conv, dados in reversed(list(conversas_filtradas.items())):
                    col_btn_select, col_btn_del = st.columns([3.5, 1])
                    
                    with col_btn_select:
                        eh_ativa = (id_conv == st.session_state["conversa_ativa"])
                        estilo_titulo = f"[{dados['titulo']}]" if eh_ativa else dados["titulo"]
                        
                        if st.button(f"{estilo_titulo}", key=f"sel_{id_conv}", use_container_width=True):
                            st.session_state["conversa_ativa"] = id_conv
                            st.rerun()
                    
                    with col_btn_del:
                        if st.button("X", key=f"del_{id_conv}", help="Excluir consulta"):
                            del st.session_state["conversas"][id_conv]
                            if id_conv == st.session_state["conversa_ativa"]:
                                if st.session_state["conversas"]:
                                    st.session_state["conversa_ativa"] = list(st.session_state["conversas"].keys())[0]
                                else:
                                    st.session_state["conversas"] = {"1": {"titulo": "Diagnóstico Inicial", "mensagens": []}}
                                    st.session_state["conversa_ativa"] = "1"
                            st.rerun()

        with col_chat:
            id_ativo = st.session_state["conversa_ativa"]
            dados_ativos = st.session_state["conversas"][id_ativo]

            st.subheader(f"{dados_ativos['titulo']}")
            st.caption("Atendimento analítico contábil:")
            st.divider()

            if not dados_ativos["mensagens"]:
                sobra_sem_c = round(sal_liq - (fixos + variaveis), 2)
                msg_boas_vindas = (
                    f"Resumo Financeiro Consolidado:\n\n"
                    f"• Salário Líquido CLT: R$ {sal_liq:,.2f}\n"
                    f"• Despesas Fixas + Variáveis: R$ {(fixos + variaveis):,.2f} (Saldo pré-cartão: R$ {sobra_sem_c:,.2f})\n"
                    f"• Faturas de Crédito: R$ {faturas:,.2f}\n"
                    f"• Dinheiro Livre Real (Saldo Final): R$ {saldo_livre:,.2f}\n\n"
                    "Digite abaixo o ponto financeiro ou contábil que deseja analisar."
                )
                dados_ativos["mensagens"].append({"role": "assistant", "content": msg_boas_vindas})

            for mensagem in dados_ativos["mensagens"]:
                with st.chat_message(mensagem["role"]):
                    st.markdown(mensagem["content"])

            if prompt := st.chat_input("Digite sua dúvida financeira..."):
                if len(dados_ativos["mensagens"]) <= 1 and dados_ativos["titulo"].startswith("Consulta #"):
                    titulo_curto = (prompt[:22] + "...") if len(prompt) > 22 else prompt
                    dados_ativos["titulo"] = titulo_curto

                dados_ativos["mensagens"].append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Processando..."):
                        resposta_gerada = responder_chat_ia(prompt, sal_liq, fixos, variaveis, faturas)
                        st.markdown(resposta_gerada)
                
                dados_ativos["mensagens"].append({"role": "assistant", "content": resposta_gerada})
                st.rerun()
