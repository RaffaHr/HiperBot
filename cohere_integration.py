import streamlit as st
import json
import os
import re
import time
from dotenv import load_dotenv
import requests
import cohere

# Carregar as variáveis de ambiente
load_dotenv()

# Inicializa o cliente Cohere usando a chave de API do arquivo .env
api_key = os.getenv("COHERE_API_KEY")
if api_key is None:
    st.error("API key da Cohere não encontrada. Verifique seu arquivo .env.")
else:
    co = cohere.ClientV2(api_key)

# Função para chamar a API do Cohere e verificar se a completions tem relação com a pergunta
def check_response_with_cohere(question, completion):
    prompt = f"Pergunta do usuário: {question}\nResposta sugerida: {completion}\n\nA resposta sugerida está relacionada com a pergunta? Responda apenas 'sim' ou 'não'."
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'command-xlarge-nightly',
        'prompt': prompt,
        'max_tokens': 40,  # Para evitar respostas longas
        'temperature': 0.2  # Tornar a resposta mais focada
    }
    
    response = requests.post('https://api.cohere.ai/generate', headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if 'text' in result:
            return result['text'].strip().lower() == 'sim'
        else:
            st.error("Erro ao verificar relação da resposta: 'text' não encontrado.")
            return False
    else:
        st.error(f"Erro ao verificar relação da resposta: {response.status_code} - {response.text}")
        return False

# Função para carregar os dados do arquivo JSON
@st.cache_resource
def load_json_data():
    try:
        with open('db_process.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        st.error(f"Erro ao carregar os dados do JSON: {e}")
        return None

# Carregar a base de dados JSON
data = load_json_data()
if data is None:
    st.stop()

st.markdown("<h1 style='text-align: center;'>Assistente Virtual - Hiper Bot 🤖</h1>", unsafe_allow_html=True)

def extract_keywords(user_input):
    keywords = ["prazo", "acareação", "transportadora", "protheus", "nota fiscal", "cce", "cc", "cc-e", "baixar", "emitir nf", "baixar nf", "imprimir nf", "nf", "emitir", "gerar", "jadlog", "generoso", "solistica", "correios", "favorita", "comprovante de entrega", "comprovante"]
    found_keywords = [word for word in keywords if re.search(r'\b' + re.escape(word) + r'\b', user_input.lower())]
    return found_keywords

def run_chain(user_input):
    data = load_json_data()
    keywords = extract_keywords(user_input)
    
    st.write(f"Palavras-chave encontradas: {keywords}")
    response = None

    if keywords:
        for empresa in data["transportadoras"]:
            transportadora_nome = empresa["transportadora"]["nome"].upper()
            if transportadora_nome in user_input.upper():
                for key in keywords:
                    for sub_key, content in empresa["transportadora"].items():
                        if key in sub_key.lower():
                            possible_response = content.get("completions", "")
                            if possible_response:
                                response = possible_response
                            break
                if response:
                    break

        if not response:
            st.write("Verificando sistemas...")
            for sistema in data["sistemas"]:
                protheus = sistema["sistema"].get("Protheus", {})
                for key in keywords:
                    for sub_key, content in protheus.items():
                        if key.lower() in sub_key.lower():
                            possible_response = content.get("completions", "")
                            if possible_response:
                                response = possible_response
                            break
                if response:
                    break

    return response if response else "Desculpe, não tenho informações suficientes para responder a essa pergunta no momento."

# Função para simular a digitação da resposta
def simulate_typing(text):
    # Cria um espaço vazio onde o texto será exibido
    response_placeholder = st.empty()
    
    displayed_text = ""
    for char in text:
        time.sleep(0.005)  # Ajuste a velocidade da digitação
        displayed_text += char  # Adiciona o caractere à string acumulada
        response_placeholder.markdown(displayed_text)  # Atualiza o espaço com o texto acumulado

# Inicializar sessão de conversas
if 'conversations' not in st.session_state:
    st.session_state.conversations = {}
if 'selected_chat' not in st.session_state:
    st.session_state.selected_chat = ""

# Sidebar para exibir conversas
st.sidebar.title("Conversas")
chat_names = list(st.session_state.conversations.keys())

if st.sidebar.button("Iniciar Nova Conversa"):
    st.session_state.selected_chat = ""

for chat_name in chat_names:
    if st.sidebar.button(chat_name):
        st.session_state.selected_chat = chat_name

selected_chat = st.session_state.selected_chat
if selected_chat and selected_chat in st.session_state.conversations:
    messages = st.session_state.conversations[selected_chat]
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if user_input := st.chat_input("Você:", max_chars=100):
    if selected_chat:
        st.session_state.conversations[selected_chat].append({"role": "user", "content": user_input})
    else:
        st.session_state.conversations[user_input[:50]] = []
        st.session_state.selected_chat = user_input[:50]

    with st.chat_message("user"):
        st.markdown(user_input)

    # Exibir loader enquanto a IA busca a resposta
    with st.spinner("Aguarde enquanto a IA busca a resposta..."):
        response = run_chain(user_input)
        
    # Usar um loader skeleton enquanto a IA digita a resposta
    with st.chat_message("assistant"):
        assistant_message_placeholder = st.empty()
        
        # Exibe o "skeleton loader" com animação
        assistant_message_placeholder.markdown(
            """
            <style>
                @keyframes pulse {
                    0% { background-color: #e0e0e0; }
                    50% { background-color: #c0c0c0; }
                    100% { background-color: #e0e0e0; }
                }
                .skeleton {
                    height: 20px; 
                    width: 80%; 
                    border-radius: 5px; 
                    margin: 5px 0;
                    animation: pulse 1.5s infinite;
                }
            </style>
            <div class="skeleton"></div>
            <div class="skeleton" style="width: 60%;"></div>
            <div class="skeleton" style="width: 40%;"></div>
            """,
            unsafe_allow_html=True
        )

        time.sleep(1)  # Simula o tempo de espera antes da IA começar a "digitar"

        # Limpa o placeholder e começa a digitar a resposta
        assistant_message_placeholder.empty()
        simulate_typing(response)  # Simula a digitação da resposta
        
    st.session_state.conversations[st.session_state.selected_chat].append({"role": "assistant", "content": response})
