import streamlit as st
from groq import Groq
import json

# --- CONFIG ---
st.set_page_config(page_title="Eve: Modern DM", layout="wide")

# --- INITIALIZE SESSION STATE ---
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "party" not in st.session_state:
    st.session_state.party = {}

# --- SECURE GROQ CLIENT ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏙️ New Cyre Ops")
    with st.expander("Register Agents", expanded=True):
        p_name = st.text_input("Name")
        p_concept = st.text_area("Concept")
        if st.button("Add to Game"):
            if p_name:
                st.session_state.party[p_name] = p_concept
                st.success(f"{p_name} added!")

    st.write("---")
    if st.session_state.party:
        st.write("**Current Party:**")
        for p in st.session_state.party:
            st.write(f"• {p}")

    if st.button("🗑️ Reset All"):
        st.session_state.clear()
        st.rerun()

# --- MAIN LOGIC ---
if not st.session_state.game_started:
    st.header("✨ Project: New Cyre")
    st.info("Step 1: Register players in the sidebar. \nStep 2: Hit the button below.")
    
    if st.button("🚀 INITIATE SESSION 0"):
        if not st.session_state.party:
            st.error("Wait! You haven't added any players in the sidebar yet.")
        else:
            with st.spinner("Eve is constructing the world..."):
                party_list = "\n".join([f"{p}: {c}" for p, c in st.session_state.party.items()])
                sys_prompt = f"System: You are Eve, the DM. Setting: New Cyre (Modern Corporate Fantasy). Party: {party_list}. Narrate a 3-paragraph history, describe a starting mana-bar, and ask one player a specific character-building question."
                
                # We send the FIRST message immediately to 'kickstart' the chat
                try:
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": sys_prompt}],
                        temperature=0.8
                    )
                    first_msg = response.choices[0].message.content
                    st.session_state.messages.append({"role": "system", "content": sys_prompt})
                    st.session_state.messages.append({"role": "assistant", "content": first_msg})
                    st.session_state.game_started = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Brain Glitch: {e}")

else:
    # --- CHAT MODE ---
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    st.divider()
    user_input = st.chat_input("Speak or Type your action...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages,
                temperature=0.8
            )
            answer = response.choices[0].message.content
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()
          
