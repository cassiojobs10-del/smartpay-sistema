import streamlit as st

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="App Finanças CLT & IA",
    page_icon="💰",
    layout="centered"
)

# ==========================================
# LÓGICA DE CÁLCULO (TABELAS DE IMPOSTOS - CLT)
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

    # INSS Progressivo
    inss = 0.0
    for f in TABELA_INSS:
        if salario_bruto_total > f["piso"]:
            base = min(salario_bruto_total, f["teto"]) - f["piso"]
            inss += base * f["aliquota"]
        if salario_bruto_total <= f["teto"]:
            break
    inss = round(inss, 2)

    # IRRF Opcional
    irrf = 0.0
    if aplicar_irrf:
        base_irrf = salario_bruto_total - inss - (dependentes * DEDUCAO_POR_DEPENDENTE)
        if base_irrf > 0:
            for f in TABELA_IRRF:
                if f["piso"] < base_irrf <= f["teto"]:
                    irrf = max(0.0, (base_irrf * f["aliquota"]) - f["deducao"])
                    break
        irrf = round(irrf, 2)

    salario_liquido = round(salario_bruto_total - inss - irrf, 2)
    jornada_total_real = jornada + horas_50 + horas_100
    hora_liquida = round(salario_liquido / jornada_total_real, 2) if jornada_total_real > 0 else 0.0
    
    return {
        "salario_bruto_total": salario_bruto_total,
        "total_horas_extras": total_horas_extras,
        "inss": inss,
        "irrf": irrf,
        "salario_liquido": salario_liquido,
        "hora_liquida": hora_liquida
    }

# ==========================================
# INTERFACE VISUAL (TELAS DO APP)
# ==========================================
st.title("💰 Meu Controle Financeiro & CLT")
st.write("Entenda seu ganho real, controle seus gastos e descubra seu **Dinheiro Livre** no mês.")

st.divider()

# --- SEÇÃO 1: PERFIL TRABALHISTA ---
st.subheader("1. Configure sua Renda")

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
    st.write("Informe a quantidade de horas extras realizadas:")
    col_he1, col_he2 = st.columns(2)
    with col_he1:
        horas_50 = st.number_input("Horas Extras 50% (Qtd)", min_value=0.0, value=0.0, step=1.0)
    with col_he2:
        horas_100 = st.number_input("Horas Extras 100% (Qtd)", min_value=0.0, value=0.0, step=1.0)

# Cálculo CLT
folha = calcular_clt(salario_base, jornada, dependentes, aplicar_irrf, horas_50, horas_100)

st.divider()

# --- SEÇÃO 2: RAIO-X DO SALÁRIO ---
st.subheader("2. Seu Salário Real (Líquido)")

if folha["total_horas_extras"] > 0:
    st.success(f"📈 **Salário Bruto com Horas Extras:** R$ {folha['salario_bruto_total']:,.2f} *(+ R$ {folha['total_horas_extras']:,.2f} em extras)*")

card1, card2, card3 = st.columns(3)
with card1:
    st.metric(
        label="Salário Líquido",
        value=f"R$ {folha['salario_liquido']:,.2f}",
        delta=f"Hora real: R$ {folha['hora_liquida']:,.2f}"
    )
with card2:
    st.metric("Desconto INSS", f"R$ {folha['inss']:,.2f}")
with card3:
    if aplicar_irrf:
        st.metric("Desconto IRRF", f"R$ {folha['irrf']:,.2f}")
    else:
        st.metric("Desconto IRRF", "R$ 0,00", delta="Isento", delta_color="off")

st.divider()

# --- SEÇÃO 3: O DIFERENCIAL (CUSTO EM HORAS DE VIDA) ---
st.subheader("⏱️ Termômetro de Gastos: Custo em Horas de Vida")
st.write("Antes de fazer uma compra, descubra quanto tempo de trabalho líquido ela vai custar:")

col_gasto1, col_gasto2 = st.columns([1, 2])
with col_gasto1:
    valor_compra = st.number_input("Valor da despesa (R$)", min_value=1.0, value=150.0, step=10.0)

with col_gasto2:
    if folha["hora_liquida"] > 0:
        total_minutos = round((valor_compra / folha["hora_liquida"]) * 60)
        horas = total_minutos // 60
        minutos = total_minutos % 60
        
        st.info(f"💡 Para comprar algo de **R$ {valor_compra:,.2f}**, você precisará trabalhar exatamente:")
        st.header(f"⏳ **{horas} horas e {minutos} minutos**")

st.divider()

# --- SEÇÃO 4: GESTÃO DE GASTOS & DINHEIRO LIVRE ---
st.subheader("4. Controle de Gastos e 'Dinheiro Livre'")
st.write("Registre suas despesas (não inclua compras feitas no cartão que ainda vão vencer):")

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

st.divider()

# --- SEÇÃO 5: CARTÃO DE CRÉDITO & ESTRATÉGIA DE FLUXO ---
st.subheader("5. 💳 Cartão de Crédito: Estratégia de Vencimento")
st.write("Use as datas do seu cartão para não ficar zerado antes do próximo salário:")

col_cartao1, col_cartao2 = st.columns(2)

with col_cartao1:
    limite_cartao = st.number_input("Limite Total do Cartão (R$)", min_value=0.0, value=5000.0, step=100.0)
    fatura_atual = st.number_input("Fatura a Pagar Este Mês (R$)", min_value=0.0, value=800.0, step=50.0)

with col_cartao2:
    dia_fechamento = st.number_input("Dia de Fechamento da Fatura", min_value=1, max_value=31, value=25)
    dia_vencimento = st.number_input("Dia de Vencimento da Fatura", min_value=1, max_value=31, value=5)
    dia_salario = st.number_input("Dia em que Você Recebe o Salário", min_value=1, max_value=31, value=5)

# Cálculos do Cartão
limite_disponivel = max(0.0, limite_cartao - fatura_atual)
melhor_dia_compra = (dia_fechamento % 31) + 1

# Totalização com Fatura
total_gastos = round(total_fixo + total_var + fatura_atual, 2)
dinheiro_livre = round(folha["salario_liquido"] - total_gastos, 2)

# Cards do Cartão
c_card1, c_card2, c_card3 = st.columns(3)
with c_card1:
    st.metric("Limite Disponível", f"R$ {limite_disponivel:,.2f}")
with c_card2:
    st.metric("Melhor Dia de Compra", f"Dia {melhor_dia_compra}", delta="Até 40 dias para pagar")
with c_card3:
    if dinheiro_livre >= 0:
        st.metric("💵 Dinheiro Livre (Sobra)", f"R$ {dinheiro_livre:,.2f}", delta="Saldo Positivo")
    else:
        st.metric("🚨 Dinheiro Livre (Sobra)", f"R$ {dinheiro_livre:,.2f}", delta="Orçamento Estourado", delta_color="inverse")

# --- CONSELHEIRO DE LIQUIDEZ E ESTRATÉGIA ---
st.markdown("### 🧠 Conselheiro de Liquidez (Para Não Zerar a Conta)")

if dia_fechamento < dia_salario:
    st.info(
        f"💡 **Estratégia de Oxigênio:** Seu cartão fecha no **dia {dia_fechamento}** e você recebe no **dia {dia_salario}**. "
        f"Se o dinheiro em conta estiver curto, **concentre compras variáveis a partir do dia {melhor_dia_compra}**. "
        f"Essas compras só serão pagas na fatura do mês seguinte, preservando seu saldo atual!"
    )
else:
    st.info(
        f"💡 **Estratégia de Organização:** Você recebe no **dia {dia_salario}** e a fatura vence no **dia {dia_vencimento}**. "
        f"Separe o valor da fatura (**R$ {fatura_atual:,.2f}**) logo no dia do pagamento para não comprometer o **Dinheiro Livre** que sobra para o mês."
    )

# Barra de Alerta de Consumo da Renda
if folha["salario_liquido"] > 0:
    percentual_gasto = min(1.0, total_gastos / folha["salario_liquido"])
    percentual_exibicao = round((total_gastos / folha["salario_liquido"]) * 100, 1)
    
    st.write(f"**Comprometimento da Renda:** Você já comprometeu **{percentual_exibicao}%** do seu salário líquido deste mês (Fixos + Variáveis + Fatura).")
    st.progress(percentual_gasto)
