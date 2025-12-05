import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai # Biblioteca nova do Google (SDK v2)

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="O Construtor",
    page_icon="🏗️",
    layout="wide"
)

# Carrega as senhas do arquivo .env
load_dotenv()

# --- 2. CONFIGURAÇÃO DA IA (GOOGLE) ---
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("🚨 ERRO CRÍTICO: Chave GOOGLE_API_KEY não encontrada no arquivo .env")
    st.info("Crie um arquivo .env na raiz e cole sua chave: GOOGLE_API_KEY=AIza...")
    st.stop()

# Configura a API Key do Google
try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Erro ao configurar a API do Google: {e}")
    st.stop()

# --- 3. ESCOLHA DO MODELO ---
MODELO_ATUAL = "gemini-1.5-flash-latest" 

# --- 4. INTERFACE VISUAL ---
st.title("🏗️ O Construtor")
st.caption(f"Sistema Autônomo de Engenharia de Software | Motor: {MODELO_ATUAL}")

# Botão na barra lateral para limpar memória
if st.sidebar.button("🗑️ Limpar Conversa"):
    st.session_state.messages = []
    st.rerun()

# --- 5. GERENCIAMENTO DE ESTADO (MEMÓRIA) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostra o histórico de mensagens na tela
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. LÓGICA DO CHAT ---
if prompt := st.chat_input("Dê uma ordem para a construção..."):
    # 1. Mostra a mensagem do usuário
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Gera a resposta da IA
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⏳ *O Construtor está pensando...*")
        
        try:
            # Cria o modelo e gera o conteúdo
            model = genai.GenerativeModel(MODELO_ATUAL)
            response = model.generate_content(prompt)
            
            texto_resposta = response.text
            placeholder.markdown(texto_resposta)
            
            # 3. Salva no histórico
            st.session_state.messages.append({"role": "assistant", "content": texto_resposta})
            
        except Exception as e:
            placeholder.error(f"❌ Erro no processamento: {e}")