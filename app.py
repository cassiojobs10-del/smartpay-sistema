import streamlit as st
import pandas as pd

# ==========================================
# CONFIGURAÇÃO DA PÁGINA & MEMÓRIA DE SESSÃO
# ==========================================
st.set_page_config(
    page_title="App Finanças CLT & IA",
    page_icon="💰",
    layout="centered"
)

# Inicializando variáveis na memória para integrar as telas
if "salario_liquido" not in st.session_state:
    st.session_state["salario_liquido"] = 3802.43
if "hora_liquida" not in st.session_state:
    st.session_state["hora_liquida"] = 17.28
if "salario_bruto_total" not in st.session_state:
    st.session_state["salario_bruto_total"] = 4500.00

# ==========================================
# TABELAS DE IMPOSTOS & LÓGICA CLT
# ==========================================
TABELA_INSS = [
    {"piso": 0.00, "teto": 1412.00, "aliquota": 0.075},
    {"piso": 1412.00, "teto": 2666.68, "aliquota": 0.090},
    {"piso": 2666.68, "teto": 4000.03, "aliquota": 0.120},
    {"piso": 4000.03, "teto": 7786.02, "aliquota": 0.140},
]

TABELA_IRRF = [
    {"piso": 0.00, "teto": 2259.20, "aliquota": 0.000, "deducao": 0.00},
    {"piso": 2259.20, "teto": 2826.65, "aliquota": 0.075, "deducao": 169.44},
    {"piso": 2826.65, "teto": 3751.05, "aliquota": 0.150, "deducao": 381.44},
    {"piso": 3751.05, "teto": 4664.68, "aliquota": 0.225, "deducao": 662.77},
    {"piso": 4664.68, "teto": float("inf"), "aliquota": 0.275, "deducao": 896.00},
]

DEDUCAO_POR_DEPENDENTE = 189.59

def calcular_clt(salario_base, jornada, dependentes, aplicar_irrf=True, horas_50=0.0, horas_100=0.0):
    hora_normal = salario_base / jornada if jornada > 0 else 0.0
    valor_he_50 = round(horas_50 * (hora_normal * 1.5), 2)
    valor_he_100 = round(horas_100 * (hora_normal * 2.0), 2)
    total_horas_extras = round(valor_he_50 + valor_he_100, 2)
    
    salario_bruto_total = round(salario_base + total_horas_extras, 2)

    # INSS
    inss = 0.0
    for f in TABELA_INSS:
        if salario_bruto_total > f["piso"]:
            base = min(salario_bruto_total, f["teto"]) - f["piso"]
            inss += base * f["aliquota"]
        if salario_bruto_total <= f["teto"]:
            break
    inss = round(inss, 2)

    # IRRF
    irrf = 0.0
    if aplicar_irrf:
        base_irrf = salario_bruto_total - inss - (dependentes * DEDUCAO_POR_DEPENDENTE)
        if base_irrf > 0:
            for f in TABELA_IRRF:
                if f["piso"] < base_irrf <= f["teto"]:
                    irrf = max(0.0, (base_irrf * f["aliquota"]) - f["deducao"])
                    break
        irrf = round(irrf, 2)

    # FGTS (8% pago pelo empregador - não desconta do líquido)
    fgts = round(salario_bruto_total * 0.08, 2)

    salario_liquido = round(salario_bruto_total - inss - irrf, 2)
    jornada_total_real = jornada + horas_50 + horas_100
    hora_liquida = round(salario_liquido / jornada_total_real, 2) if jornada_total_real > 0 else 0.0
    
    return {
        "salario_bruto_total": salario_bruto_total,
        "total_horas_extras": total_horas_extras,
        "inss": inss,
        "irrf": irrf,
        "fgts": fgts,
        "salario_liquido": salario_liquido,
        "hora_liquida": hora_liquida
    }

# ==========================================
# BARRA LATERAL DE NAVEGAÇÃO (MENU)
# ==========================================
st.sidebar.title("📌 Menu Financeiro")
menu_selecionado = st.sidebar.radio(
    "Navegue pelas áreas do app:",
    ["🏢 1. Trabalhista & CLT", "💵 2. Dinheiro Pessoal & Orçamento", "💳 3. Cartões de Crédito"]
)

st.sidebar.divider()
st.sidebar.caption("💡 **Dica:** Os cálculos trabalhistas atualizam automaticamente o seu orçamento e cartões nas outras abas!")

# ==========================================
# MÓDULO 1: ÁREA TRABALHISTA & CLT
# ==========================================
if menu_selecionado == "🏢 1. Trabalhista & CLT":
    st.title("🏢 Área Trabalhista & CLT")
    st.write("Calcule seus descontos oficiais, benefícios e descubra seu salário líquido real.")
    st.divider()

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
        aplicar_irrf = st.toggle("Descontar IRRF na fonte?", value=True)

    horas_50, horas_100 = 0.0, 0.0
    with st.expander("➕ Adicionar Horas Extras no Mês (Opcional)"):
        col_he1, col_he2 = st.columns(2)
        with col_he1:
            horas_50 = st.number_input("Horas Extras 50% (Qtd)", min_value=0.0, value=0.0, step=1.0)
        with col_he2:
            horas_100 = st.number_input("Horas Extras 100% (Qtd)", min_value=0.0, value=0.0, step=1.0)

    # Executando cálculo
    folha = calcular_clt(salario_base, jornada, dependentes, aplicar_irrf, horas_50, horas_100)
    
    # Atualizando a memória global da sessão
    st.session_state["salario_liquido"] = folha["salario_liquido"]
    st.session_state["hora_liquida"] = folha["hora_liquida"]
    st.session_state["salario_bruto_total"] = folha["salario_bruto_total"]

    st.divider()
    st.subheader("📊 Raio-X da sua Folha de Pagamento")

    if folha["total_horas_extras"] > 0:
        st.success(f"📈 **Salário Bruto com Horas Extras:** R$ {folha['salario_bruto_total']:,.2f}")

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
    # Destaque para o FGTS (Patrimônio do Trabalhador)
    st.info(
        f"🏛️ **FGTS Acumulado no Mês (8%): R$ {folha['fgts']:,.2f}**\n\n"
        f"*Nota: O FGTS é um benefício pago integralmente pela empresa na sua conta da Caixa, não sendo descontado do seu salário líquido.*"
    )

# ==========================================
# MÓDULO 2: DINHEIRO PESSOAL & ORÇAMENTO
# ==========================================
elif menu_selecionado == "💵 2. Dinheiro Pessoal & Orçamento":
    st.title("💵 Dinheiro Pessoal & Orçamento")
    st.write("Gerencie seus custos de vida e veja quanto sobra limpo na sua conta.")
    st.divider()

    # Puxando dados da Área Trabalhista da sessão
    sal_liquido = st.session_state["salario_liquido"]
    hora_liq = st.session_state["hora_liquida"]

    st.success(f"💰 **Renda Disponível (Salário Líquido importado): R$ {sal_liquido:,.2f}**")

    col_fixo, col_var = st.columns(2)
    with col_fixo:
        st.markdown("#### 🔒 Gastos Fixos")
        moradia = st.number_input("Aluguel / Condomínio", min_value=0.0, value=1200.0, step=50.0)
        contas = st.number_input("Contas Básicas (Luz, Água, Internet)", min_value=0.0, value=300.0, step=20.0)
        transporte = st.number_input("Transporte / Combustível", min_value=0.0, value=350.0, step=20.0)
        outros_fixos = st.number_input("Outros Fixos (Saúde, Educação)", min_value=0.0, value=200.0, step=20.0)

    with col_var:
        st.markdown("#### 🛍️ Gastos Variáveis (Débito/PIX/Dinheiro)")
        alimentacao = st.number_input("Alimentação Fora / Delivery", min_value=0.0, value=400.0, step=20.0)
        lazer = st.number_input("Lazer e Assinaturas", min_value=0.0, value=250.0, step=20.0)
        compras = st.number_input("Compras / Imprevistos", min_value=0.0, value=300.0, step=20.0)

    total_fixo = round(moradia + contas + transporte + outros_fixos, 2)
    total_var = round(alimentacao + lazer + compras, 2)
    total_gastos = round(total_fixo + total_var, 2)
    dinheiro_livre = round(sal_liquido - total_gastos, 2)

    st.divider()
    
    # Cards de Balanço
    b_card1, b_card2, b_card3 = st.columns(3)
    with b_card1:
        st.metric("Custos Fixos", f"R$ {total_fixo:,.2f}")
    with b_card2:
        st.metric("Custos Variáveis", f"R$ {total_var:,.2f}")
    with b_card3:
        if dinheiro_livre >= 0:
            st.metric("💵 Dinheiro Livre (Sobra)", f"R$ {dinheiro_livre:,.2f}", delta="Saldo Positivo")
        else:
            st.metric("🚨 Dinheiro Livre (Sobra)", f"R$ {dinheiro_livre:,.2f}", delta="Orçamento Estourado", delta_color="inverse")

    st.divider()
    # Termômetro em Horas de Vida integrado aqui
    st.subheader("⏱️ Termômetro de Gastos: Custo em Horas de Vida")
    col_gasto1, col_gasto2 = st.columns([1, 2])
    with col_gasto1:
        valor_compra = st.number_input("Simular despesa (R$)", min_value=1.0, value=150.0, step=10.0)
    with col_gasto2:
        if hora_liq > 0:
            total_minutos = round((valor_compra / hora_liq) * 60)
            horas = total_minutos // 60
            minutos = total_minutos % 60
            st.info(f"💡 Para comprar algo de **R$ {valor_compra:,.2f}**, você trabalhará exatamente:\n\n### ⏳ **{horas} horas e {minutos} minutos**")

# ==========================================
# MÓDULO 3: CARTÕES DE CRÉDITO (MULTI-CARTÃO)
# ==========================================
elif menu_selecionado == "💳 3. Cartões de Crédito":
    st.title("💳 Meus Cartões de Crédito")
    st.write("Gerencie cartões separadamente com limites, datas e faturas individuais.")
    st.divider()

    # Criando abas interativas para até 2 cartões (expansível facilmente)
    aba1, aba2 = st.tabs(["💳 Cartão 1 (Principal)", "💳 Cartão 2 (Secundário)"])

    # --- ABA: CARTÃO 1 ---
    with aba1:
        st.subheader("Cartão Principal")
        nome_c1 = st.text_input("Nome do Cartão", value="Nubank", key="nome_c1")
        col_c1_a, col_c1_b = st.columns(2)
        with col_c1_a:
            limite_c1 = st.number_input("Limite Total (R$)", min_value=0.0, value=5000.0, step=100.0, key="lim_c1")
            fatura_base_c1 = st.number_input("Parcelas Antigas (R$)", min_value=0.0, value=300.0, step=50.0, key="base_c1")
        with col_c1_b:
            fechamento_c1 = st.number_input("Dia de Fechamento", min_value=1, max_value=31, value=25, key="fech_c1")
            vencimento_c1 = st.number_input("Dia de Vencimento", min_value=1, max_value=31, value=5, key="venc_c1")

        st.markdown(f"**🛒 Compras do Mês ({nome_c1})**")
        df_c1 = st.data_editor(
            pd.DataFrame([
                {"Descrição": "Supermercado", "Valor (R$)": 250.00},
                {"Descrição": "Assinatura Streaming", "Valor (R$)": 39.90}
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
            st.metric(f"Fatura {nome_c1}", f"R$ {fatura_total_c1:,.2f}")
        with res2:
            st.metric("Limite Disponível", f"R$ {limite_disp_c1:,.2f}")
        with res3:
            st.metric("Melhor Dia Compra", f"Dia {melhor_dia_c1}", delta="Até 40 dias sem juros")

    # --- ABA: CARTÃO 2 ---
    with aba2:
        st.subheader("Cartão Secundário")
        nome_c2 = st.text_input("Nome do Cartão", value="XP / Itaú", key="nome_c2")
        col_c2_a, col_c2_b = st.columns(2)
        with col_c2_a:
            limite_c2 = st.number_input("Limite Total (R$)", min_value=0.0, value=3000.0, step=100.0, key="lim_c2")
            fatura_base_c2 = st.number_input("Parcelas Antigas (R$)", min_value=0.0, value=0.0, step=50.0, key="base_c2")
        with col_c2_b:
            fechamento_c2 = st.number_input("Dia de Fechamento", min_value=1, max_value=31, value=10, key="fech_c2")
            vencimento_c2 = st.number_input("Dia de Vencimento", min_value=1, max_value=31, value=20, key="venc_c2")

        st.markdown(f"**🛒 Compras do Mês ({nome_c2})**")
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
            st.metric(f"Fatura {nome_c2}", f"R$ {fatura_total_c2:,.2f}")
        with res_b2:
            st.metric("Limite Disponível", f"R$ {limite_disp_c2:,.2f}")
        with res_b3:
            st.metric("Melhor Dia Compra", f"Dia {melhor_dia_c2}", delta="Até 40 dias sem juros")

    st.divider()
    st.info(f"📊 **Total Geral em Cartões neste mês:** R$ {(fatura_total_c1 + fatura_total_c2):,.2f}")
