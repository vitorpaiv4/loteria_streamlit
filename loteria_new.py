import streamlit as st
import random
import data_analysis as da
import pandas as pd
import altair as alt

st.set_page_config(layout="wide")
st.title("🎰 Loteria Inteligente")

# --- Abas para Organização ---
tab_gerador, tab_analise, tab_simulador = st.tabs([
    "🍀 Gerador de Jogos", 
    "📊 Análise de Resultados",
    "🎰 Simulador"
])

with tab_gerador:
    st.header("Gerador de Jogos")
    
    # Carrega os dados uma vez para usar em ambos os geradores
    historico = da.get_all_results()
    stats = da.calculate_statistics(historico) if historico else None

    # --- Gerador Inteligente ---
    st.subheader("🤖 Gerador Inteligente")
    with st.form("intelligent_generator_form"):
        st.markdown("Use as estatísticas para gerar um jogo com uma estratégia definida.")
        
        num_dezenas_inteligente = st.number_input(
            "Quantas dezenas quer no seu jogo?", 6, 15, 6, key="ig_num"
        )
        
        # Garante que numeros_fixos não exceda o total do jogo
        max_fixos = num_dezenas_inteligente -1 if num_dezenas_inteligente > 6 else 5
        numeros_fixos = st.multiselect(
            "Quer fixar alguns números? Escolha abaixo:",
            options=range(1, 61),
            max_selections=max_fixos
        )

        col1, col2 = st.columns(2)
        with col1:
            usar_quentes = st.slider(
                "Nº de dezenas 'quentes' para usar (do top 10)", 0, 5, 2,
                help="O gerador irá incluir este número de dezenas do grupo das 10 mais sorteadas."
            )
            evitar_frias = st.slider(
                "Nº de dezenas 'frias' para evitar (do top 10)", 0, 10, 5,
                help="O gerador irá excluir este número de dezenas do grupo das 10 menos sorteadas."
            )
        with col2:
            # Opções de equilíbrio mudam se o número de dezenas não for 6
            equilibrio_opts = ["Qualquer"]
            if num_dezenas_inteligente == 6:
                equilibrio_opts.extend(["3P / 3I", "4P / 2I", "2P / 4I", "5P / 1I", "1P / 5I"])

            equilibrio_par_impar = st.selectbox(
                "Equilíbrio Par/Ímpar",
                options=equilibrio_opts,
                index=0,
                help="Define a proporção de números pares e ímpares. Funcionalidade otimizada para 6 dezenas."
            )

        submitted = st.form_submit_button("✨ Gerar Jogo Inteligente!")
        if submitted:
            if not stats:
                st.error("As estatísticas não puderam ser carregadas. Não é possível gerar um jogo inteligente.")
            else:
                with st.spinner("Gerando seu jogo com base na estratégia..."):
                    jogo, msg = da.generate_smart_game(
                        stats,
                        num_dezenas_inteligente,
                        numeros_fixos,
                        usar_quentes,
                        evitar_frias,
                        equilibrio_par_impar
                    )
                
                if jogo:
                    jogo_formatado = " - ".join([str(n).zfill(2) for n in jogo])
                    st.success("✅ Jogo gerado com sucesso!")
                    st.code(jogo_formatado, language="text")
                else:
                    st.error(f"Falha ao gerar o jogo: {msg}")

    st.divider()

    # --- Gerador Rápido (Antigo) ---
    st.subheader("🍀 Gerador Aleatório Rápido")
    num_dezenas_rapido = st.number_input("Quantas dezenas?", 6, 15, 6, key="rapido_num")
    if st.button("Gerar Jogo Aleatório e Verificar Último Sorteio"):
        dezenas = sorted(random.sample(range(1, 61), num_dezenas_rapido))
        
        dezenas_formatadas = " - ".join([str(n).zfill(2) for n in dezenas])
        st.write(f"### Seus Números:")
        st.code(dezenas_formatadas, language="text")

        with st.spinner('Consultando o último resultado...'):
            resultado = da.get_latest_result()
        
        if resultado:
            lista_dezenas_str = resultado.get("listaDezenas", [])
            concurso = resultado.get("numero", "Desconhecido")
            ultimo_sorteio = sorted([int(n) for n in lista_dezenas_str])
            
            sorteio_formatado = " - ".join([str(n).zfill(2) for n in ultimo_sorteio])
            st.write(f"### 📢 Último Sorteio (Concurso {concurso}):") 
            st.code(sorteio_formatado, language="text")

            acertos = sorted(list(set(dezenas).intersection(set(ultimo_sorteio))))
            num_acertos = len(acertos)
            
            st.markdown("---") 
            if num_acertos >= 4:
                st.balloons()
                st.success(f"🏆 PARABÉNS! Teria feito {num_acertos} pontos: {acertos}")
            elif num_acertos > 0:
                st.info(f"Teria feito {num_acertos} ponto(s): {acertos}")
            else:
                st.warning("Não teria acertado nenhum número. Tente novamente!")
        else:
            st.error("Não foi possível obter o último resultado.")

# --- Aba 2: Análise de Resultados (Nova Funcionalidade) ---
with tab_analise:
    st.header("Análise sobre o Histórico de Sorteios")

    historico_analise = da.get_all_results()

    if historico_analise:
        stats_analise = da.calculate_statistics(historico_analise)
        
        # --- 1. Frequência das Dezenas ---
        st.subheader("Frequência de cada Dezena")
        
        freq_df = pd.DataFrame(list(stats_analise['frequency'].items()), columns=['Dezena', 'Frequência'])
        
        chart = alt.Chart(freq_df).mark_bar().encode(
            x=alt.X('Dezena:O', axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('Frequência:Q'),
            tooltip=['Dezena', 'Frequência']
        ).properties(
            title='Frequência de Sorteio de Cada Dezena (1 a 60)'
        )
        st.altair_chart(chart, use_container_width=True)

        # --- 2. Dezenas Quentes e Frias ---
        st.subheader("Dezenas Quentes e Frias")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("🔥 **Mais Sorteadas (Quentes)**")
            hot_df = pd.DataFrame(stats_analise['most_common'], columns=['Dezena', 'Vezes'])
            st.dataframe(hot_df, use_container_width=True)

        with col2:
            st.markdown("🧊 **Menos Sorteadas (Frias)**")
            cold_df = pd.DataFrame(stats_analise['least_common'], columns=['Dezena', 'Vezes'])
            st.dataframe(cold_df, use_container_width=True)
            
        # --- 3. Análise de Pares e Ímpares ---
        with st.expander("Ver Análise de Pares e Ímpares por Concurso"):
            st.subheader("Distribuição de Pares e Ímpares")
            even_odd_df = pd.DataFrame(stats_analise['even_odd_distribution'])
            st.dataframe(even_odd_df, use_container_width=True)

    else:
        st.error("Não foi possível carregar o histórico para análise.")

# --- Aba 3: Simulador de Apostas ---
with tab_simulador:
    st.header("Simulador de Apostas")
    st.markdown("Veja como seu jogo teria se saído em todos os concursos da história!")

    historico_sim = da.get_all_results()

    with st.form("simulator_form"):
        numeros_simulacao = st.multiselect(
            "Escolha de 6 a 15 dezenas para simular:",
            options=range(1, 61),
            max_selections=15,
            default=list(range(1, 7)) # Jogo padrão para exemplo
        )
        
        simular_btn = st.form_submit_button("Executar Simulação")

        if simular_btn and historico_sim:
            if len(numeros_simulacao) < 6:
                st.warning("Por favor, escolha pelo menos 6 dezenas.")
            else:
                with st.spinner("Simulando seu jogo contra todo o histórico..."):
                    resultados = da.run_simulation(historico_sim, numeros_simulacao)
                
                st.subheader("Resultados da Simulação")

                if not resultados:
                    st.success("🎉 Seu jogo nunca teria sido premiado. O que pode ser uma ótima notícia, talvez ele seja o próximo!")
                else:
                    total_concursos = len(historico_sim)
                    total_premios = len(resultados)
                    
                    sena = sum(1 for r in resultados if r['acertos'] == 6)
                    quina = sum(1 for r in resultados if r['acertos'] == 5)
                    quadra = sum(1 for r in resultados if r['acertos'] == 4)

                    st.markdown(f"Seu jogo de `{len(numeros_simulacao)}` dezenas foi verificado contra `{total_concursos}` concursos.")

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("🏆 SENA (6 acertos)", f"{sena}x")
                    col2.metric("🥇 QUINA (5 acertos)", f"{quina}x")
                    col3.metric("🥈 QUADRA (4 acertos)", f"{quadra}x")
                    col4.metric("📊 % de Prêmios", f"{((total_premios/total_concursos)*100):.4f}%")
                    
                    if sena > 0:
                        st.balloons()

                    st.markdown("---")
                    st.subheader("Detalhes dos Prêmios")
                    
                    resultados_df = pd.DataFrame(resultados)
                    st.dataframe(resultados_df, use_container_width=True)
        elif not historico_sim:
            st.error("Não foi possível carregar o histórico para a simulação.")