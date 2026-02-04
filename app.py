import streamlit as st
import pandas as pd
import time
import os

from dotenv import load_dotenv
load_dotenv()

try:
    from auth import login
    from utils.router import choose_models
    from utils.parallel import run_parallel
    from utils.rate_limiter import check_limit
    from utils.report import generate_report
except Exception as e:
    st.error(e)
    st.stop()

st.set_page_config(
    page_title="LLM Nexus | Enterprise Comparison",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background-color: #000000;
    color: #f8fafc;
}

section[data-testid="stSidebar"] {
    background-color: #000000;
    border-right: 1px solid #111827;
}

h1, h2, h3 {
    color: #f8fafc !important;
    font-weight: 700;
}

.main-header {
    font-size: 2.5rem;
    background: -webkit-linear-gradient(#38bdf8, #0ea5e9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}

.sub-header {
    font-size: 1.1rem;
    color: #94a3b8;
    margin-bottom: 2rem;
}

.stTextArea textarea {
    background-color: #0b0f1a;
    border: 1px solid #334155;
    color: #e2e8f0;
    border-radius: 8px;
}

.stTextArea textarea:focus {
    border-color: #38bdf8;
    box-shadow: 0 0 0 1px #38bdf8;
}

div[data-baseweb="select"] > div {
    background-color: #0b0f1a;
    border: 1px solid #334155;
    border-radius: 8px;
    color: white;
}

div.stButton > button {
    background: #38bdf8;
    color: #000000;
    border: none;
    padding: 0.75rem 2rem;
    font-weight: 600;
    border-radius: 8px;
    width: 100%;
    transition: all 0.2s;
}

div.stButton > button:hover {
    background: #0ea5e9;
    box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
}

.model-card {
    background-color: #0b0f1a;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px;
    height: 100%;
}

.model-name {
    font-weight: 700;
    color: #38bdf8;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 0.9rem;
    margin-bottom: 10px;
    border-bottom: 1px solid #334155;
    padding-bottom: 8px;
}

div[data-testid="metric-container"] {
    background-color: #0b0f1a;
    border: 1px solid #334155;
    padding: 10px 20px;
    border-radius: 8px;
}

hr {
    border-color: #111827;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ Controls")

    if "user" in st.session_state:
        st.info(f"👤 Logged in as: **{st.session_state.user}**")

    st.markdown("---")
    st.subheader("Configuration")

    model_temp = st.slider("Temperature (Creativity)", 0.0, 1.0, 0.7)
    max_tokens = st.number_input("Max Tokens", value=1024, step=256)

    st.markdown("---")
    st.caption("v2.1.0 | Enterprise Edition")


def main():
    login()
    if "user" not in st.session_state:
        st.stop()

    st.markdown('<div class="main-header">LLM Nexus</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Intelligent routing & cost-analysis engine for Generative AI.</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1, 3])

    with col1:
        task = st.selectbox(
            "Target Objective",
            ["General", "Coding", "Fast Response", "Cost Saving"]
        )
        st.metric("Active Models", "3 Online", "All Systems Go")

    with col2:
        prompt = st.text_area(
            "Input Prompt",
            height=140,
            placeholder="E.g., Write a secure Python function to connect to AWS S3..."
        )

    col_submit, _ = st.columns([1, 4])
    with col_submit:
        run_btn = st.button("⚡ Execute Query")

    if run_btn:
        if not check_limit(st.session_state.user):
            st.error("🚫 Rate limit reached")
            st.stop()

        if not prompt.strip():
            st.warning("⚠️ Please provide a prompt")
            st.stop()

        with st.status("🔄 Orchestrating Model Requests...", expanded=True):
            models = choose_models(task)
            start_time = time.time()
            responses = run_parallel(prompt, models)
            elapsed = round(time.time() - start_time, 2)

        st.markdown("### 📊 Analysis Results")

        tab1, tab2, tab3, tab4 = st.tabs([
            "👁️ Visual Comparison",
            "📝 Raw Data",
            "📉 Cost Report",
            "📊 Performance Dashboard"
        ])

        with tab1:
            cols = st.columns(len(responses))
            for i, (name, text) in enumerate(responses.items()):
                with cols[i]:
                    st.markdown(
                        f"<div class='model-card'><div class='model-name'>{name}</div></div>",
                        unsafe_allow_html=True
                    )
                    st.markdown(text)

        with tab2:
            st.json(responses)

        with tab3:
            generate_report(prompt, responses)
            st.success("Report generated")
            c1, c2 = st.columns(2)
            c1.metric("Estimated Cost", "$0.0042")
            c2.metric("Latency Average", f"{elapsed}s")

        with tab4:
            file = "data/metrics/metrics.csv"
            if not os.path.exists(file):
                st.warning("No metrics data available yet")
            else:
                df = pd.read_csv(file)
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
                st.bar_chart(df.groupby("model")["latency"].mean())
                st.bar_chart(df.groupby("model")["response_length"].mean())
                st.line_chart(df.set_index("timestamp").resample("1min").count()["model"])


if __name__ == "__main__":
    main()
