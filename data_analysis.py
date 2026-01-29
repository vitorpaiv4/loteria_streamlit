import requests
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed

# URL base da API oficial da Caixa
API_URL_BASE = "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena"

def fetch_contest(contest_number):
    """Busca o resultado de um concurso específico."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(f"{API_URL_BASE}/{contest_number}", headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None # Retorna None se houver erro para aquele concurso

@st.cache_data(ttl=3600)
def get_latest_result():
    """Busca o último resultado da Mega-Sena da API oficial."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(API_URL_BASE, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão ao buscar o último resultado: {e}")
        return None
    except requests.exceptions.JSONDecodeError:
        st.error("Erro ao decodificar a resposta da API (último resultado).")
        return None

@st.cache_data(ttl=86400)
def get_all_results():
    """
    Busca o histórico completo de resultados da Mega-Sena,
    baixando todos os concursos em paralelo.
    """
    latest_result = get_latest_result()
    if not latest_result:
        st.error("Não foi possível determinar o último concurso para buscar o histórico.")
        return []

    last_contest_num = latest_result.get("numero")
    if not last_contest_num:
        st.error("Não foi possível extrair o número do último concurso.")
        return []

    all_results = []
    
    # Usando ThreadPoolExecutor para baixar concursos em paralelo
    # Aumenta drasticamente a velocidade de download do histórico
    progress_bar = st.progress(0, text="Baixando histórico de concursos...")
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(fetch_contest, i): i for i in range(1, last_contest_num + 1)}
        
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result:
                # Extrai e formata apenas os dados essenciais
                formatted_result = {
                    "concurso": result.get("numero"),
                    "data": result.get("dataApuracao"),
                    "dezenas": sorted(result.get("listaDezenas", [])),
                }
                all_results.append(formatted_result)
            
            # Atualiza a barra de progresso
            progress_value = (i + 1) / last_contest_num
            progress_text = f"Baixando histórico... {i+1}/{last_contest_num} concursos"
            progress_bar.progress(progress_value, text=progress_text)

    progress_bar.empty() # Limpa a barra de progresso ao concluir
    
    # Ordena os resultados por número do concurso
    return sorted(all_results, key=lambda x: x["concurso"])

# --- Funções de Análise Estatística ---

def _get_frequency(all_results):
    """Calcula a frequência de cada dezena."""
    from collections import Counter
    all_numbers = [int(n) for result in all_results for n in result['dezenas']]
    return Counter(all_numbers)

def _get_hot_and_cold(frequency, count=10):
    """Retorna as dezenas mais (quentes) e menos (frias) sorteadas."""
    if not frequency:
        return [], []
    most_common = frequency.most_common(count)
    least_common = sorted(frequency.items(), key=lambda x: x[1])[:count]
    return most_common, least_common

def _get_even_odd_analysis(all_results):
    """Analisa a proporção de números pares e ímpares por sorteio."""
    analysis = []
    for result in all_results:
        numbers = [int(n) for n in result['dezenas']]
        evens = sum(1 for n in numbers if n % 2 == 0)
        odds = len(numbers) - evens
        analysis.append({
            "concurso": result["concurso"],
            "pares": evens,
            "ímpares": odds,
            "proporcao": f"{evens}P / {odds}I"
        })
    return analysis

@st.cache_data(ttl=86400)
def calculate_statistics(all_results):
    """Executa todas as análises estatísticas sobre o histórico de resultados."""
    if not all_results:
        return {}

    frequency = _get_frequency(all_results)
    most_common, least_common = _get_hot_and_cold(frequency)
    even_odd = _get_even_odd_analysis(all_results)
    
    return {
        "frequency": frequency,
        "most_common": most_common,
        "least_common": least_common,
        "even_odd_distribution": even_odd,
    }

# --- Geração de Jogos ---

import random

def generate_smart_game(stats, num_dezenas, fixed_numbers, use_hot, avoid_cold, even_odd_balance):
    """
    Gera um jogo de loteria com base em uma estratégia definida.
    """
    if not stats:
        return None, "Estatísticas não disponíveis para gerar o jogo."

    # 1. Definir o universo de dezenas para o sorteio
    all_possible_numbers = set(range(1, 61))
    
    # Remove dezenas "frias" que devem ser evitadas
    cold_numbers_to_avoid = {num for num, freq in stats['least_common'][:avoid_cold]}
    eligible_numbers = all_possible_numbers - cold_numbers_to_avoid
    
    # 2. Garantir a inclusão dos números fixos
    game = set(fixed_numbers)
    
    # 3. Selecionar dezenas "quentes"
    hot_numbers_to_use = {num for num, freq in stats['most_common']} - game
    
    # Adiciona o número de dezenas quentes solicitadas, se possível
    num_hot_to_add = min(use_hot, len(hot_numbers_to_use), num_dezenas - len(game))
    if num_hot_to_add > 0:
        game.update(random.sample(list(hot_numbers_to_use), num_hot_to_add))

    # 4. Tentar gerar o restante do jogo satisfazendo o equilíbrio par/ímpar
    remaining_needed = num_dezenas - len(game)
    if remaining_needed < 0:
        return None, "Conflito: Mais números fixos e quentes do que o tamanho do jogo."

    # Define o número de pares e ímpares necessários
    target_evens, target_odds = None, None
    if num_dezenas == 6 and even_odd_balance != "Qualquer":
        parts = even_odd_balance.replace("P", "").replace("I", "").split(" / ")
        target_evens = int(parts[0])
        target_odds = int(parts[1])

    # Loop para tentar encontrar um jogo válido (evita loops infinitos)
    max_tries = 1000 
    for _ in range(max_tries):
        current_game = game.copy()
        
        # Pool de números para completar o jogo
        completion_pool = list(eligible_numbers - current_game)
        random.shuffle(completion_pool)
        
        if len(completion_pool) < remaining_needed:
            return None, "Não há números elegíveis suficientes para completar o jogo com as regras definidas."

        # Se não há equilíbrio, apenas completa aleatoriamente
        if target_evens is None:
            current_game.update(completion_pool[:remaining_needed])
            return sorted(list(current_game)), "Jogo gerado com sucesso."

        # Lógica para equilíbrio par/ímpar
        current_evens = sum(1 for n in current_game if n % 2 == 0)
        current_odds = len(current_game) - current_evens
        
        needed_evens = target_evens - current_evens
        needed_odds = target_odds - current_odds

        if needed_evens < 0 or needed_odds < 0 or (needed_evens + needed_odds) != remaining_needed:
             return None, f"Conflito nas regras de Pares/Ímpares. Necessário: {target_evens}P/{target_odds}I, mas os números fixos/quentes já definiram {current_evens}P/{current_odds}I."

        # Seleciona os números pares e ímpares necessários do pool
        evens_from_pool = [n for n in completion_pool if n % 2 == 0]
        odds_from_pool = [n for n in completion_pool if n % 2 != 0]

        if len(evens_from_pool) >= needed_evens and len(odds_from_pool) >= needed_odds:
            current_game.update(random.sample(evens_from_pool, needed_evens))
            current_game.update(random.sample(odds_from_pool, needed_odds))
            
            if len(current_game) == num_dezenas:
                 return sorted(list(current_game)), "Jogo gerado com sucesso."

    return None, "Não foi possível gerar um jogo com as regras especificadas após várias tentativas. Tente regras menos restritivas."

# --- Simulação de Jogos ---

@st.cache_data(ttl=86400)
def run_simulation(all_results, user_numbers):
    """
    Verifica um jogo do usuário contra todo o histórico de resultados.
    """
    if not all_results:
        return []

    user_numbers_set = set(user_numbers)
    winning_results = []

    for result in all_results:
        drawn_numbers = set(int(n) for n in result['dezenas'])
        hits = user_numbers_set.intersection(drawn_numbers)
        num_hits = len(hits)

        if num_hits >= 4:
            prize = ""
            if num_hits == 4: prize = "Quadra"
            elif num_hits == 5: prize = "Quina"
            elif num_hits == 6: prize = "Sena (Prêmio Máximo!)"
            
            winning_results.append({
                "concurso": result["concurso"],
                "data": result["data"],
                "acertos": num_hits,
                "numeros_acertados": sorted(list(hits)),
                "premio": prize
            })
            
    return sorted(winning_results, key=lambda x: x['concurso'], reverse=True)
