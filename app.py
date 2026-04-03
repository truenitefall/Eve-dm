import streamlit as st
from groq import Groq

# --- EVE'S SETTINGS ---
st.set_page_config(page_title="Eve: AI DM", page_icon="🎲")
st.title("🧙‍♀️ Eve: The Cloud Dungeon Master")

# 1. Securely get the API Key
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("Missing API Key! Go to Settings -> Secrets in Streamlit.")
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
        try:
            # Change the model to the most current stable version
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=st.session_state.messages,
                temperature=0.8,
                max_tokens=1024 # Prevents the response from cutting off
            )
            answer = response.choices[0].message.content
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            st.error(f"Groq Error: {e}")
            st.info("Tip: Check if the model name is correct in the Groq Playground.")
          
