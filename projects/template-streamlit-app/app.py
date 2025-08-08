
import streamlit as st
import time

st.set_page_config(page_title="AI PM Demo Template", page_icon="🧪", layout="centered")

st.title("🧪 AI PM Demo Template")
st.write("A minimal Streamlit app you can deploy on Hugging Face Spaces.")

with st.form("demo"):
    user_input = st.text_input("Prompt or input")
    submitted = st.form_submit_button("Run")
    if submitted:
        with st.spinner("Running..."):
            time.sleep(1.2)
        st.success("Done!")
        st.write("**Echo:**", user_input or "Nothing entered yet.")

st.markdown("---")
st.caption("Edit `projects/template-streamlit-app/app.py` to build your own demo. Hook this Space to your Git repo and set app_file to this path.")
