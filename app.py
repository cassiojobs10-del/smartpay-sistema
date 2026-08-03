# ==========================================
# 4. CONSULTORIA IA
# ==========================================
elif menu_selecionado == "Consultoria IA":
    st.title("Consultoria Financeira IA")
    st.write("Converse de forma natural sobre o seu cenário financeiro.")
    st.divider()

    sal_liq = st.session_state["salario_liquido"]
    fixos = st.session_state["total_fixo"]
    variaveis = st.session_state["total_var"]
    faturas = st.session_state["total_faturas"]
    
    total_saidas = round(fixos + variaveis + faturas, 2)
    saldo_livre = round(sal_liq - total_saidas, 2)

    # Cabeçalho limpo com botão de reiniciar chat
    col_titulo, col_btn = st.columns([4, 1])
    with col_titulo:
        st.subheader("Assistente Virtual")
    with col_btn:
        if st.button("Nova Conversa 🔄", use_container_width=True):
            st.session_state["conversas"]["1"]["mensagens"] = []
            st.rerun()

    # Container principal do chat ocupando 100% da largura
    with st.container(border=True):
        dados_ativos = st.session_state["conversas"]["1"]

        # 1. Mensagem inicial natural e amigável (estilo Gemini)
        if not dados_ativos["mensagens"]:
            msg_boas_vindas = (
                f"Olá! Analisei os dados que você preencheu nas outras abas. "
                f"Vi que sua renda líquida é de **R$ {sal_liq:,.2f}** e, após todas as suas despesas e faturas, "
                f"seu saldo livre atual projetado é de **R$ {saldo_livre:,.2f}**.\n\n"
                "Como posso te ajudar a organizar suas finanças hoje? Você pode me pedir dicas de onde cortar gastos, "
                "como investir esse saldo livre ou simular cenários!"
            )
            dados_ativos["mensagens"].append({"role": "assistant", "content": msg_boas_vindas})

        # 2. Renderiza as mensagens anteriores do chat
        for mensagem in dados_ativos["mensagens"]:
            with st.chat_message(mensagem["role"]):
                st.markdown(mensagem["content"])

        # 3. Caixa de entrada de texto (sempre no final)
        if prompt := st.chat_input("Pergunte sobre seus gastos, peça dicas de planejamento..."):
            
            # Exibe a pergunta do usuário
            dados_ativos["mensagens"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Processa e exibe a resposta da IA
            with st.chat_message("assistant"):
                with st.spinner("Pensando..."):
                    # Chama a função do seu backend enviando os dados atuais
                    resposta_gerada = responder_chat_ia(prompt, sal_liq, fixos, variaveis, faturas)
                    st.markdown(resposta_gerada)
            
            # Salva a resposta no histórico
            dados_ativos["mensagens"].append({"role": "assistant", "content": resposta_gerada})
