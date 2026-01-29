# Loteria Inteligente

Este é um aplicativo Streamlit que oferece ferramentas para análise e geração de jogos da Mega-Sena. Ele busca os resultados oficiais diretamente da API da Caixa para fornecer estatísticas atualizadas.

## Funcionalidades

-   **Gerador de Jogos Inteligente**: Gera apostas com base em estatísticas de dezenas "quentes" e "frias", além de balanceamento de pares e ímpares.
-   **Análise de Resultados**: Exibe a frequência de cada dezena, dezenas mais e menos sorteadas, e a distribuição de pares/ímpares ao longo do histórico.
-   **Simulador de Apostas**: Permite simular um jogo contra todo o histórico de concursos da Mega-Sena, mostrando quantos acertos (Quadra, Quina, Sena) o jogo teria tido.

## Como Rodar

1.  **Clone este repositório** (ou baixe os arquivos).
2.  **Instale as dependências** do Python. Certifique-se de ter `pip` instalado:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Execute o aplicativo Streamlit**:
    ```bash
    streamlit run loteria_new.py
    ```

O aplicativo será aberto automaticamente no seu navegador padrão.
