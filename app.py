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

# --- INJEÇÃO DE CSS CUSTOMIZADO (DESIGN FINTECH ESCURO) ---
st.markdown("""
<style>
/* Estilização moderna para os cards de Métricas */
div[data-testid="stMetric"] {
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 16px 20px;
    border-radius: 14px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transition: all 0.2s ease-in-out;
}
div[data-testid="stMetric"]:hover {
    border-color: rgba(0, 210, 120, 0.4);
    transform: translateY(-2px);
    background-color: rgba(255, 255, 255, 0.05);
}

/* Tipografia e cabeçalhos com toque de dashboard */
h1, h2, h3 {
    font-weight: 700 !important;
    letter-spacing: -0.4px !important;
}

/* Estilo suave nas divisórias */
hr {
    border-color: rgba(255, 255, 255, 0.08) !important;
    margin: 24px 0 !important;
}

/* Abas mais limpas */
button[data-baseweb="tab"] {
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# Inicializando variáveis na memória global para integrar todas as telas
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
if "mensagens_chat" not in st.session_state:
    st.session_state["mensagens_chat"] = []

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

    # FGTS (8% pago pelo empregador)
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
# MOTOR INTELIGENTE DE RESPOSTAS (CHAT IA AVANÇADO)
# ==========================================
def responder_chat_ia(mensagem_usuario, sal_liq, fixos, var, faturas):
    msg = mensagem_usuario.lower()
    
    # Padronização matemática exata (Sem contradições)
    custos_sem_cartao = round(fixos + var, 2)
    sobra_sem_cartao = round(sal_liq - custos_sem_cartao, 2)
    total_saidas = round(custos_sem_cartao + faturas, 2)
    saldo_real_limpo = round(sal_liq - total_saidas, 2)

    # 1. Dúvidas sobre saldos, valores diferentes ou "Dinheiro Livre"
    if any(p in msg for p in ["livre", "sobra", "802", "212", "diferen", "quanto tenho", "pq", "por que"]):
        return (
            f"🔍 **Auditoria Exata do seu Dinheiro Livre:**\n\n"
            f"• **Saldo sem Cartão (Tela 2):** R$ {sobra_sem_cartao:,.2f} *(Salário Líquido - Fixos - Variáveis)*\n"
            f"• **Faturas de Cartão (Tela 3):** - R$ {faturas:,.2f}\n"
            f"• **Dinheiro Livre Real (Final do Mês): R$ {saldo_real_limpo:,.2f}**\n\n"
            f"💡 **Explicação:** Na área de 'Dinheiro Pessoal', o app mostra quanto sobra antes de pagar a fatura do cartão (**R$ {sobra_sem_cartao:,.2f}**). "
            f"Quando subtraímos os **R$ {faturas:,.2f}** que você deve no crédito, sobram limpos exatamente **R$ {saldo_real_limpo:,.2f}** na sua conta bancária!"
        )

    # 2. Dúvidas sobre conciliação de salário e cartão de crédito
    elif any(p in msg for p in ["conciliar", "fim de mês", "fim de mes", "recebo", "salário com o cartão", "nubank", "cartão", "cartao"]):
        return (
            f"📅 **Estratégia de Conciliação (Salário no Fim do Mês vs. Cartão):**\n\n"
            f"Como você recebe no fim do mês e sua fatura atual é de **R$ {faturas:,.2f}**, aplique a **Regra dos 3 Passos**:\n"
            f"1. **Carimbo de Pagamento:** No dia em que o salário cair, separe imediatamente os **R$ {faturas:,.2f}** do cartão e pague ou deixe rendendo em uma caixinha separada.\n"
            f"2. **Estanque de Virada:** Concentre compras variáveis no cartão **somente após o dia de fechamento**. Isso empurra o gasto para a fatura seguinte, dando 30 a 40 dias de fôlego.\n"
            f"3. **Teto do Crédito:** Nunca deixe sua fatura ultrapassar o seu saldo sem cartão (**R$ {sobra_sem_cartao:,.2f}**), senão seu Dinheiro Livre do mês ficará negativo."
        )

    # 3. Dúvidas sobre investimentos e reserva
    elif any(p in msg for p in ["invest", "guardar", "poupar", "reserva", "caixinha"]):
        if saldo_real_limpo > 0:
            meses_reserva = round((fixos * 6) / saldo_real_limpo, 1)
            return (
                f"📈 **Plano de Crescimento Patrimonial:**\n\n"
                f"Com o seu saldo livre real de **R$ {saldo_real_limpo:,.2f}** por mês:\n"
                f"• **Meta 1 (Reserva de Emergência):** O ideal é ter 6 meses de custos fixos (**R$ {(fixos * 6):,.2f}**). Guardando todo mês, você atinge essa meta em aproximadamente **{meses_reserva} meses**.\n"
                f"• **Onde aplicar:** Utilize CDBs com liquidez diária (100% do CDI) ou Tesouro Selic para segurança máxima."
            )
        else:
            return "🚨 **Atenção:** Seu saldo livre real após o cartão está zerado ou negativo. A prioridade matemática antes de investir é cortar gastos variáveis para fazer sobrar caixa."

    # 4. Resposta Analítica Completa (Fallback inteligente)
    else:
        pct_gasto = round((total_saidas / sal_liq) * 100, 1) if sal_liq > 0 else 100
        return (
            f"🤖 **Diagnóstico Financeiro Exato:**\n\n"
            f"• **Renda Disponível:** R$ {sal_liq:,.2f}\n"
            f"• **Total de Saídas (Fixos + Variáveis + Cartão):** R$ {total_saidas:,.2f} *(Compromete {pct_gasto}% da renda)*\n"
            f"• **Saldo Livre Real:** **R$ {saldo_real_limpo:,.2f}**\n\n"
            f"Você pode me fazer perguntas como: *'Por que meu saldo livre é R$ {saldo_real_limpo:,.2f}?'*, *'Como conciliar meu salário com o cartão?'* ou *'Como cortar gastos para sobrar mais?'*"
        )

# ==========================================
# BARRA LATERAL DE NAVEGAÇÃO (MENU)
# ==========================================
st.sidebar.title("📌 Menu Financeiro")
menu_selecionado = st.sidebar.radio(
    "Navegue pelas áreas do app:",
    [
        "🏢 1. Trabalhista & CLT",
        "💵 2. Dinheiro Pessoal & Orçamento",
        "💳 3. Cartões de Crédito",
        "🤖 4. Consultora IA Financeira"
    ]
)

st.sidebar.divider()
st.sidebar.caption("💡 **Dica de UX:** Os cálculos trabalhistas e suas faturas são sincronizados automaticamente entre os módulos!")

# ==========================================
# MÓDULO 1: ÁREA TRABALHISTA & CLT
# ==========================================
if menu_selecionado == "🏢 1. Trabalhista & CLT":
    st.title("🏢 Área Trabalhista & CLT")
    st.write("Calcule seus descontos oficiais, benefícios e descubra seu ganho líquido real.")
    st.divider()

    with st.container(border=True):
        st.subheader("⚙️ Parâmetros do seu Salário")
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

    folha = calcular_clt(salario_base, jornada, dependentes, aplicar_irrf, horas_50, horas_100)
    
    st.session_state["salario_liquido"] = folha["salario_liquido"]
    st.session_state["hora_liquida"] = folha["hora_liquida"]
    st.session_state["salario_bruto_total"] = folha["salario_bruto_total"]

    st.write("")
    with st.container(border=True):
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
        st.info(
            f"🏛️ **FGTS Acumulado no Mês (8%): R$ {folha['fgts']:,.2f}**\n\n"
            f"*Nota: O FGTS é pago integralmente pelo empregador na conta da Caixa, não sendo descontado do seu salário líquido.*"
        )

# ==========================================
# MÓDULO 2: DINHEIRO PESSOAL & ORÇAMENTO
# ==========================================
elif menu_selecionado == "💵 2. Dinheiro Pessoal & Orçamento":
    st.title("💵 Dinheiro Pessoal & Orçamento")
    st.write("Gerencie seus custos de vida e visualize suas margens de sobra.")
    st.divider()

    sal_liquido = st.session_state["salario_liquido"]
    hora_liq = st.session_state["hora_liquida"]

    st.success(f"💰 **Renda Disponível (Salário Líquido importado): R$ {sal_liquido:,.2f}**")

    with st.container(border=True):
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
    
    st.session_state["total_fixo"] = total_fixo
    st.session_state["total_var"] = total_var

    total_gastos = round(total_fixo + total_var, 2)
    sobra_antes_cartao = round(sal_liquido - total_gastos, 2)

    st.write("")
    with st.container(border=True):
        st.subheader("📋 Balanço Mensal (Débito & Contas)")
        b_card1, b_card2, b_card3 = st.columns(3)
        with b_card1:
            st.metric("Custos Fixos", f"R$ {total_fixo:,.2f}")
        with b_card2:
            st.metric("Custos Variáveis", f"R$ {total_var:,.2f}")
        with b_card3:
            if sobra_antes_cartao >= 0:
                st.metric("💵 Saldo (Antes do Cartão)", f"R$ {sobra_antes_cartao:,.2f}", delta="Sem subtrair faturas")
            else:
                st.metric("🚨 Saldo (Antes do Cartão)", f"R$ {sobra_antes_cartao:,.2f}", delta="Orçamento Estourado", delta_color="inverse")

    st.write("")
    with st.container(border=True):
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

    aba1, aba2 = st.tabs(["💳 Cartão 1 (Principal)", "💳 Cartão 2 (Secundário)"])

    with aba1:
        with st.container(border=True):
            st.subheader("Configurações do Cartão Principal")
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

    with aba2:
        with st.container(border=True):
            st.subheader("Configurações do Cartão Secundário")
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

    st.session_state["total_faturas"] = round(fatura_total_c1 + fatura_total_c2, 2)

    st.write("")
    st.info(f"📊 **Total Geral em Cartões neste mês:** R$ {st.session_state['total_faturas']:,.2f}")

# ==========================================
# MÓDULO 4: CONSULTORA IA FINANCEIRA + CHAT
# ==========================================
elif menu_selecionado == "🤖 4. Consultora IA Financeira":
    st.title("🤖 Consultora IA Financeira")
    st.write("Sua assistente inteligente analisa seus números e responde às suas dúvidas no chat abaixo.")
    st.divider()

    sal_liq = st.session_state["salario_liquido"]
    fixos = st.session_state["total_fixo"]
    variaveis = st.session_state["total_var"]
    faturas = st.session_state["total_faturas"]
    
    total_saidas = round(fixos + variaveis + faturas, 2)
    saldo_livre = round(sal_liq - total_saidas, 2)

    # 1. INDICADOR DE SAÚDE FINANCEIRA EM CARD FINTECH
    pct_comprometido = (total_saidas / sal_liq) * 100 if sal_liq > 0 else 100
    
    with st.container(border=True):
        st.subheader("📊 1. Termômetro de Saúde Financeira")
        col_saude1, col_saude2 = st.columns([1, 2])
        
        with col_saude1:
            if pct_comprometido <= 80:
                st.success("🟢 **Status: EXCELENTE**")
            elif pct_comprometido <= 95:
                st.warning("🟡 **Status: ATENÇÃO**")
            else:
                st.error("🔴 **Status: RISCO CRÍTICO**")
                
        with col_saude2:
            st.write(f"Você comprometeu **{pct_comprometido:.1f}%** do seu salário líquido deste mês.")
            st.progress(min(1.0, max(0.0, total_saidas / sal_liq if sal_liq > 0 else 1.0)))

    st.write("")

    # 2. CHAT INTERATIVO EM CONTAINER
    with st.container(border=True):
        st.subheader("💬 2. Chat Interativo: Converse com sua Consultora IA")
        st.caption("Faça perguntas sobre como organizar seu salário, investimentos, corte de gastos ou cartões:")

        # Botão para limpar histórico do chat
        col_btn_limpar, _ = st.columns([1, 3])
        with col_btn_limpar:
            if st.button("🗑️ Limpar Conversa"):
                st.session_state["mensagens_chat"] = []
                st.rerun()

        # Se o histórico estiver vazio, adiciona uma mensagem inicial explicativa
        if not st.session_state["mensagens_chat"]:
            sobra_sem_c = round(sal_liq - (fixos + variaveis), 2)
            msg_boas_vindas = (
                f"Olá! Sou sua **Consultora Financeira IA**. Já analisei seus números em detalhes:\n\n"
                f"• **Salário Líquido CLT:** R$ {sal_liq:,.2f}\n"
                f"• **Despesas Fixas + Variáveis:** R$ {(fixos + variaveis):,.2f} *(Saldo de R$ {sobra_sem_c:,.2f} na Tela 2)*\n"
                f"• **Fatura Total dos Cartões:** R$ {faturas:,.2f}\n"
                f"• **💵 Dinheiro Livre Real (Após o Cartão): R$ {saldo_livre:,.2f}**\n\n"
                "Em que posso te aconselhar hoje? Pergunte sobre as diferenças de saldo, estratégias de cartão ou como montar sua reserva!"
            )
            st.session_state["mensagens_chat"].append({"role": "assistant", "content": msg_boas_vindas})

        # Exibir todas as mensagens do histórico na tela
        for mensagem in st.session_state["mensagens_chat"]:
            with st.chat_message(mensagem["role"], avatar="🤖" if mensagem["role"] == "assistant" else "👤"):
                st.markdown(mensagem["content"])

        # Captura a pergunta digitada pelo usuário na barra inferior
        if prompt := st.chat_input("Digite sua dúvida financeira (ex: Por que meu saldo livre deu esse valor?)..."):
            # 1. Mostra a mensagem do usuário imediatamente
            st.session_state["mensagens_chat"].append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)

            # 2. Gera a resposta da IA baseada no motor analítico corrigido
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Analisando suas finanças..."):
                    resposta_gerada = responder_chat_ia(prompt, sal_liq, fixos, variaveis, faturas)
                    st.markdown(resposta_gerada)
            
            # 3. Salva a resposta no histórico da sessão
            st.session_state["mensagens_chat"].append({"role": "assistant", "content": resposta_gerada})
