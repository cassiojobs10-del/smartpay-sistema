# ==========================================
# MOTOR CONTÁBIL & LÓGICA DE NEGÓCIO (BACKEND)
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

    inss = 0.0
    for f in TABELA_INSS:
        if salario_bruto_total > f["piso"]:
            base = min(salario_bruto_total, f["teto"]) - f["piso"]
            inss += base * f["aliquota"]
        if salario_bruto_total <= f["teto"]:
            break
    inss = round(inss, 2)

    irrf = 0.0
    if aplicar_irrf:
        base_irrf = salario_bruto_total - inss - (dependentes * DEDUCAO_POR_DEPENDENTE)
        if base_irrf > 0:
            for f in TABELA_IRRF:
                if f["piso"] < base_irrf <= f["teto"]:
                    irrf = max(0.0, (base_irrf * f["aliquota"]) - f["deducao"])
                    break
        irrf = round(irrf, 2)

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


def responder_chat_ia(mensagem_usuario, sal_liq, fixos, var, faturas):
    msg = mensagem_usuario.lower()
    
    custos_sem_cartao = round(fixos + var, 2)
    sobra_sem_cartao = round(sal_liq - custos_sem_cartao, 2)
    total_saidas = round(custos_sem_cartao + faturas, 2)
    saldo_real_limpo = round(sal_liq - total_saidas, 2)

    if any(p in msg for p in ["livre", "sobra", "802", "212", "diferen", "quanto tenho", "pq", "por que"]):
        return (
            f"Auditoria Exata do seu Dinheiro Livre:\n\n"
            f"• Saldo sem Cartão (Tela 2): R$ {sobra_sem_cartao:,.2f} (Salário Líquido - Fixos - Variáveis)\n"
            f"• Faturas de Cartão (Tela 3): - R$ {faturas:,.2f}\n"
            f"• Dinheiro Livre Real (Final do Mês): R$ {saldo_real_limpo:,.2f}\n\n"
            f"Nota: Na área de Dinheiro Pessoal, o sistema mostra quanto sobra antes de pagar a fatura do cartão (R$ {sobra_sem_cartao:,.2f}). "
            f"Ao subtrair os R$ {faturas:,.2f} das faturas de crédito, o saldo real na sua conta é de R$ {saldo_real_limpo:,.2f}."
        )

    elif any(p in msg for p in ["conciliar", "fim de mês", "fim de mes", "recebo", "salário com o cartão", "nubank", "cartão", "cartao"]):
        return (
            f"Estratégia de Conciliação:\n\n"
            f"Como o recebimento ocorre no fim do mês e sua fatura atual é de R$ {faturas:,.2f}, aplique o método abaixo:\n"
            f"1. Separação Imediata: No dia do pagamento, separe os R$ {faturas:,.2f} do cartão em uma conta com liquidez diária.\n"
            f"2. Virada da Fatura: Concentre compras variáveis somente após o fechamento para alongar o prazo de pagamento.\n"
            f"3. Limite de Gastos: Não permita que as faturas superem o saldo disponível (R$ {sobra_sem_cartao:,.2f})."
        )

    elif any(p in msg for p in ["invest", "guardar", "poupar", "reserva", "caixinha"]):
        if saldo_real_limpo > 0:
            meses_reserva = round((fixos * 6) / saldo_real_limpo, 1)
            return (
                f"Planejamento de Reserva de Emergência:\n\n"
                f"Com um saldo livre mensal de R$ {saldo_real_limpo:,.2f}:\n"
                f"• Meta de Segurança: 6 meses dos seus custos fixos (R$ {(fixos * 6):,.2f}). Mantendo os aportes, a meta será atingida em aproximadamente {meses_reserva} meses.\n"
                f"• Alocação recomendada: Títulos de renda fixa com baixa volatilidade e liquidez diária."
            )
        else:
            return "Atenção: Seu saldo livre real está zerado ou negativo. A prioridade matemática é a redução das despesas variáveis antes de iniciar novos investimentos."

    else:
        pct_gasto = round((total_saidas / sal_liq) * 100, 1) if sal_liq > 0 else 100
        return (
            f"Resumo Operacional:\n\n"
            f"• Renda Disponível: R$ {sal_liq:,.2f}\n"
            f"• Total de Despesas: R$ {total_saidas:,.2f} (Compromete {pct_gasto}% da renda)\n"
            f"• Saldo Livre Real: R$ {saldo_real_limpo:,.2f}\n\n"
            f"Faça perguntas específicas sobre conciliação de faturas, redução de custos ou tempo estimado para formação de reserva."
        )
