import streamlit as st
from groq import Groq

# --- EVE'S SETTINGS ---
st.set_page_config(page_title="Eve: AI DM", page_icon="🎲")
st.title("🧙‍♀️ Eve: The Cloud Dungeon Master")

# 1. Securely get the API Key from Streamlit's "Secrets"
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("Missing API Key! Add it to Streamlit Secrets.")
    st.stop()

# 2. Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are Eve, a witty and immersive D&D 5e Dungeon Master. Narrate vividly and manage 2014 rules fairly."}
    ]

# 3. Display Chat
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 4. Handle Input
if prompt := st.chat_input("What do you do?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Eve thinks using the Groq Cloud Brain
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile", # The big, smart brain
            messages=st.session_state.messages,
            temperature=0.8,
        )
        answer = response.choices[0].message.content
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
