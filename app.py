import streamlit as st
import pandas as pd
from backend import calcular_clt

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

# ==========================================
# INICIALIZAÇÃO DA MEMÓRIA GLOBAL (SESSION STATE)
# ==========================================
valores_padrao = {
    # CLT
    "salario_base": 3000.00, "beneficios": 0.00, "jornada": 220, 
    "dependentes": 0, "aplicar_irrf": True, "horas_50": 0.0, "horas_100": 0.0,
    # Orçamento Pessoal
    "moradia": 1200.0, "contas": 300.0, "transporte": 350.0, "outros_fixos": 200.0,
    "alimentacao": 400.0, "lazer": 250.0, "compras": 300.0, "valor_simulacao": 150.0,
    # Cartões de Crédito
    "nome_c1": "Nubank", "limite_c1": 5000.0, "base_c1": 300.0, "fech_c1": 25, "venc_c1": 5,
    "nome_c2": "XP / Itaú", "limite_c2": 3000.0, "base_c2": 0.0, "fech_c2": 10, "venc_c2": 20,
    # Consolidados do Motor
    "salario_liquido": 0.0, "hora_liquida": 0.0, "salario_bruto_total": 0.0,
    "total_fixo": 0.0, "total_var": 0.0, "total_faturas": 0.0
}

# Salva os valores padrões na memória se for a primeira vez
for chave, valor in valores_padrao.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor

# Tabelas e Chat requerem estruturas específicas na memória
if "df_c1_data" not in st.session_state:
    st.session_state["df_c1_data"] = pd.DataFrame([{"Descrição": "Supermercado", "Valor (R$)": 250.00}, {"Descrição": "Assinatura de Softwares", "Valor (R$)": 39.90}])
if "df_c2_data" not in st.session_state:
    st.session_state["df_c2_data"] = pd.DataFrame([{"Descrição": "Combustível", "Valor (R$)": 150.00}])
if "conversas" not in st.session_state:
    st.session_state["conversas"] = {"1": {"mensagens": []}}


# ==========================================
# BARRA LATERAL (MENU)
# ==========================================
st.sidebar.title("Sistema Financeiro")
st.sidebar.caption("Gestão Patrimonial e CLT")

menu_selecionado = st.sidebar.radio(
    "Navegação:",
    ["Trabalhista & CLT", "Orçamento Pessoal", "Cartões de Crédito", "Consultoria IA"]
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
            salario_base = st.number_input("Salário Bruto Base (R$)", min_value=1000.0, value=float(st.session_state["salario_base"]), step=100.0)
            st.session_state["salario_base"] = salario_base
        with col2:
            beneficios = st.number_input("Benefícios Isentos (R$)", min_value=0.0, value=float(st.session_state["beneficios"]), step=50.0, help="Soma de Auxílio Alimentação, Refeição, Creche, etc.")
            st.session_state["beneficios"] = beneficios

        col3, col4, col5 = st.columns(3)
        with col3:
            opcoes_jornada = [220, 200, 180, 150]
            jornada = st.selectbox("Jornada Mensal (Horas)", options=opcoes_jornada, index=opcoes_jornada.index(st.session_state["jornada"]))
            st.session_state["jornada"] = jornada
        with col4:
            dependentes = st.number_input("Dependentes", min_value=0, value=int(st.session_state["dependentes"]), step=1)
            st.session_state["dependentes"] = dependentes
        with col5:
            st.write("")
            aplicar_irrf = st.toggle("Descontar IRRF", value=bool(st.session_state["aplicar_irrf"]))
            st.session_state["aplicar_irrf"] = aplicar_irrf

        with st.expander("Adicionar Horas Extras no Mês"):
            col_he1, col_he2 = st.columns(2)
            with col_he1:
                horas_50 = st.number_input("Horas Extras 50% (Qtd)", min_value=0.0, value=float(st.session_state["horas_50"]), step=1.0)
                st.session_state["horas_50"] = horas_50
            with col_he2:
                horas_100 = st.number_input("Horas Extras 100% (Qtd)", min_value=0.0, value=float(st.session_state["horas_100"]), step=1.0)
                st.session_state["horas_100"] = horas_100

    folha = calcular_clt(salario_base, jornada, dependentes, aplicar_irrf, horas_50, horas_100)
    
    salario_liquido_real = folha["salario_liquido"] + beneficios
    salario_bruto_real = folha["salario_bruto_total"] + beneficios
    
    st.session_state["salario_liquido"] = salario_liquido_real
    st.session_state["hora_liquida"] = folha["hora_liquida"]
    st.session_state["salario_bruto_total"] = salario_bruto_real

    st.write("")
    with st.container(border=True):
        st.subheader("Composição da Remuneração Mensal")

        if folha["total_horas_extras"] > 0 or beneficios > 0:
            st.write(f"**Salário Bruto Total:** R$ {salario_bruto_real:,.2f}")

        card1, card2, card3 = st.columns(3)
        with card1:
            st.metric("Salário Líquido", f"R$ {salario_liquido_real:,.2f}", delta=f"Hora real: R$ {folha['hora_liquida']:,.2f}")
        with card2:
            st.metric("Desconto INSS", f"R$ {folha['inss']:,.2f}")
        with card3:
            if aplicar_irrf and folha['irrf'] > 0:
                st.metric("Desconto IRRF", f"R$ {folha['irrf']:,.2f}")
            else:
                st.metric("Desconto IRRF", "R$ 0,00", delta="Isento", delta_color="off")
                
        st.write("")
        st.caption(f"FGTS Acumulado no Mês (8%): R$ {folha['fgts']:,.2f} — Valor recolhido integralmente pelo empregador.")

    st.write("")
    with st.expander("Simular Recebimento de Férias"):
        st.write("Demonstrativo do cálculo de Férias Integrais (30 dias) com terço constitucional.")
        ferias_bruto = salario_base + (salario_base / 3)
        desc_ferias = calcular_clt(ferias_bruto, 220, dependentes, aplicar_irrf, 0, 0)
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            st.metric("Férias Brutas", f"R$ {ferias_bruto:,.2f}")
        with col_f2:
            st.metric("Adicional 1/3", f"R$ {(salario_base / 3):,.2f}")
        with col_f3:
            st.metric("Líquido a Receber", f"R$ {desc_ferias['salario_liquido']:,.2f}", delta="Com descontos aplicados", delta_color="normal")


# ==========================================
# 2. ORÇAMENTO PESSOAL
# ==========================================
elif menu_selecionado == "Orçamento Pessoal":
    st.title("Orçamento Pessoal")
    st.write("Gestão de despesas essenciais, distribuição de renda e dinheiro livre.")
    st.divider()

    sal_liquido = st.session_state["salario_liquido"]
    hora_liq = st.session_state["hora_liquida"]
    faturas_cartao = st.session_state["total_faturas"]

    with st.container(border=True):
        st.subheader("Caixa Disponível do Mês")
        
        despesas_atuais = st.session_state["total_fixo"] + st.session_state["total_var"] + faturas_cartao
        dinheiro_livre = max(0.0, sal_liquido - despesas_atuais)
        
        delta_cor = "normal" if dinheiro_livre > (sal_liquido * 0.1) else "off"
        if dinheiro_livre <= 0: delta_cor = "inverse"
        
        col_d1, col_d2 = st.columns([1, 1.5])
        with col_d1:
            st.metric("Free Money (Livre)", f"R$ {dinheiro_livre:,.2f}", delta=f"Renda Base: R$ {sal_liquido:,.2f}", delta_color=delta_cor)
        with col_d2:
            st.write("Distribuição Orçamentária:")
            if sal_liquido > 0:
                pct_fixo = (st.session_state['total_fixo'] / sal_liquido) * 100
                pct_var = (st.session_state['total_var'] / sal_liquido) * 100
                pct_cartao = (faturas_cartao / sal_liquido) * 100
                pct_livre = (dinheiro_livre / sal_liquido) * 100
                st.caption(f"Fixas: {pct_fixo:.1f}% | Variáveis: {pct_var:.1f}% | Cartões: {pct_cartao:.1f}% | **Livre: {pct_livre:.1f}%**")
                st.progress(min(1.0, (despesas_atuais/sal_liquido)))
            else:
                st.caption("Aguardando entrada de receita.")

    st.write("")

    with st.container(border=True):
        col_fixo, col_var = st.columns(2)
        with col_fixo:
            st.markdown("#### Despesas Fixas")
            moradia = st.number_input("Aluguel / Condomínio", min_value=0.0, value=float(st.session_state["moradia"]), step=50.0)
            contas = st.number_input("Contas Básicas", min_value=0.0, value=float(st.session_state["contas"]), step=20.0)
            transporte = st.number_input("Transporte", min_value=0.0, value=float(st.session_state["transporte"]), step=20.0)
            outros_fixos = st.number_input("Outras Fixas", min_value=0.0, value=float(st.session_state["outros_fixos"]), step=20.0)
            
            st.session_state.update({"moradia": moradia, "contas": contas, "transporte": transporte, "outros_fixos": outros_fixos})

        with col_var:
            st.markdown("#### Despesas Variáveis")
            alimentacao = st.number_input("Alimentação / Delivery", min_value=0.0, value=float(st.session_state["alimentacao"]), step=20.0)
            lazer = st.number_input("Lazer", min_value=0.0, value=float(st.session_state["lazer"]), step=20.0)
            compras = st.number_input("Imprevistos", min_value=0.0, value=float(st.session_state["compras"]), step=20.0)
            
            st.session_state.update({"alimentacao": alimentacao, "lazer": lazer, "compras": compras})

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
            valor_compra = st.number_input("Valor para simular (R$)", min_value=1.0, value=float(st.session_state["valor_simulacao"]), step=10.0)
            st.session_state["valor_simulacao"] = valor_compra
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
            nome_c1 = st.text_input("Identificação", value=st.session_state["nome_c1"], key="in_nome_c1")
            
            col_c1_a, col_c1_b = st.columns(2)
            with col_c1_a:
                limite_c1 = st.number_input("Limite Total (R$)", min_value=0.0, value=float(st.session_state["limite_c1"]), step=100.0)
                fatura_base_c1 = st.number_input("Parcelas em Andamento (R$)", min_value=0.0, value=float(st.session_state["base_c1"]), step=50.0)
            with col_c1_b:
                fechamento_c1 = st.number_input("Dia do Fechamento", min_value=1, max_value=31, value=int(st.session_state["fech_c1"]))
                vencimento_c1 = st.number_input("Dia do Vencimento", min_value=1, max_value=31, value=int(st.session_state["venc_c1"]))

            st.session_state.update({"nome_c1": nome_c1, "limite_c1": limite_c1, "base_c1": fatura_base_c1, "fech_c1": fechamento_c1, "venc_c1": vencimento_c1})

            st.markdown(f"**Registros do Mês — {nome_c1}**")
            df_c1 = st.data_editor(st.session_state["df_c1_data"], num_rows="dynamic", use_container_width=True)
            st.session_state["df_c1_data"] = df_c1
            
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
            nome_c2 = st.text_input("Identificação", value=st.session_state["nome_c2"], key="in_nome_c2")
            
            col_c2_a, col_c2_b = st.columns(2)
            with col_c2_a:
                limite_c2 = st.number_input("Limite Total (R$)", min_value=0.0, value=float(st.session_state["limite_c2"]), step=100.0, key="in_lim_c2")
                fatura_base_c2 = st.number_input("Parcelas em Andamento (R$)", min_value=0.0, value=float(st.session_state["base_c2"]), step=50.0, key="in_base_c2")
            with col_c2_b:
                fechamento_c2 = st.number_input("Dia do Fechamento", min_value=1, max_value=31, value=int(st.session_state["fech_c2"]), key="in_fech_c2")
                vencimento_c2 = st.number_input("Dia do Vencimento", min_value=1, max_value=31, value=int(st.session_state["venc_c2"]), key="in_venc_c2")

            st.session_state.update({"nome_c2": nome_c2, "limite_c2": limite_c2, "base_c2": fatura_base_c2, "fech_c2": fechamento_c2, "venc_c2": vencimento_c2})

            st.markdown(f"**Registros do Mês — {nome_c2}**")
            df_c2 = st.data_editor(st.session_state["df_c2_data"], num_rows="dynamic", use_container_width=True)
            st.session_state["df_c2_data"] = df_c2
            
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
    st.write("Converse de forma natural sobre o seu cenário financeiro.")
    st.divider()

    contexto = {
        "sal_liq": st.session_state["salario_liquido"],
        "salario_base": st.session_state["salario_base"],
        "beneficios": st.session_state["beneficios"],
        "fixos": st.session_state["total_fixo"],
        "variaveis": st.session_state["total_var"],
        "faturas": st.session_state["total_faturas"]
    }
    
    total_saidas = round(contexto["fixos"] + contexto["variaveis"] + contexto["faturas"], 2)
    contexto["saldo_livre"] = round(contexto["sal_liq"] - total_saidas, 2)

    col_titulo, col_btn = st.columns([4, 1])
    with col_titulo:
        st.subheader("Assistente Virtual")
    with col_btn:
        if st.button("Nova Conversa 🔄", use_container_width=True):
            st.session_state["conversas"]["1"]["mensagens"] = []
            st.rerun()

    def motor_ia_interno(pergunta, dados):
        p = pergunta.lower()
        if "benefício" in p or "beneficio" in p or "auxílio" in p or "auxilio" in p:
            if dados['beneficios'] == 0:
                return "Analisando seus dados, notei que **você não possui nenhum benefício ou auxílio isento cadastrado** no momento (o valor está R$ 0,00). Você pode ajustar isso na aba 'Trabalhista & CLT'."
            else:
                return f"Você tem cadastrado o valor de **R$ {dados['beneficios']:,.2f}** em benefícios isentos mensais na sua folha."
        elif "salário" in p or "salario" in p or "ganho" in p:
            return f"Seu salário bruto base está configurado em R$ {dados['salario_base']:,.2f}. Após a aplicação dos descontos oficiais e somando os seus benefícios, a sua remuneração líquida real disponível é de **R$ {dados['sal_liq']:,.2f}**."
        elif "despesa" in p or "gasto" in p or "fixo" in p or "variável" in p or "variavel" in p:
            total_despesas = dados['fixos'] + dados['variaveis']
            return f"No seu orçamento pessoal, as despesas somam **R$ {total_despesas:,.2f}**, sendo divididas em R$ {dados['fixos']:,.2f} para custos fixos e R$ {dados['variaveis']:,.2f} para variáveis."
        elif "fatura" in p or "cartão" in p or "cartao" in p or "crédito" in p:
            return f"De acordo com a aba de Cartões de Crédito, a projeção atual das suas faturas totaliza **R$ {dados['faturas']:,.2f}** neste mês."
        elif "livre" in p or "sobra" in p or "investir" in p or "saldo" in p or "resumo" in p:
            if dados['saldo_livre'] <= 0:
                return f"Atenção: A projeção do seu saldo livre está negativa em **R$ {dados['saldo_livre']:,.2f}**. É recomendável entrar nas abas de Orçamento e Cartões para revisar os gastos variáveis e evitar o uso de limite."
            else:
                return f"Boas notícias! Seu dinheiro livre projetado após pagar todas as obrigações é de **R$ {dados['saldo_livre']:,.2f}**. Esse montante está livre para direcionamento em investimentos ou lazer."
        else:
            return "Com base nos dados que você inseriu, estou monitorando seu fluxo de caixa. Como o nosso papo é focado em finanças, por favor me faça perguntas mais diretas sobre seus números, como:\n- *'Quanto eu recebo de benefício?'*\n- *'Qual meu saldo livre?'*\n- *'Como estão as minhas despesas?'*"

    with st.container(border=True):
        dados_ativos = st.session_state["conversas"]["1"]

        if not dados_ativos["mensagens"]:
            msg_boas_vindas = (
                f"Olá! Eu sou o assistente do seu Sistema Financeiro.\n\n"
                f"Analisei os dados das outras abas e vi que sua renda líquida é de **R$ {contexto['sal_liq']:,.2f}** e, após todas as obrigações, "
                f"seu saldo livre atual projetado é de **R$ {contexto['saldo_livre']:,.2f}**.\n\n"
                "Você pode me perguntar detalhes do seu orçamento. Tente algo como: *'Quanto eu recebo de benefício?'*"
            )
            dados_ativos["mensagens"].append({"role": "assistant", "content": msg_boas_vindas})

        for mensagem in dados_ativos["mensagens"]:
            with st.chat_message(mensagem["role"]):
                st.markdown(mensagem["content"])

        if prompt := st.chat_input("Pergunte sobre seus benefícios, salário, faturas..."):
            dados_ativos["mensagens"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Processando seus dados..."):
                    resposta_gerada = motor_ia_interno(prompt, contexto)
                    st.markdown(resposta_gerada)
            
            dados_ativos["mensagens"].append({"role": "assistant", "content": resposta_gerada})
            st.rerun()
