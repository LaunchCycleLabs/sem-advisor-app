import streamlit as st
import yaml
from agent import (
    fetch_campaign_data,
    fetch_keyword_data,
    generate_recommendations,
)

# — Write out google-ads.yaml from Streamlit secrets at runtime —
cfg = {
    "developer_token":   st.secrets["google_ads"]["developer_token"],
    "client_id":         st.secrets["google_ads"]["client_id"],
    "client_secret":     st.secrets["google_ads"]["client_secret"],
    "refresh_token":     st.secrets["google_ads"]["refresh_token"],
    "login_customer_id": st.secrets["google_ads"]["login_customer_id"],
    "use_proto_plus":    True,
}
with open("google-ads.yaml", "w") as f:
    yaml.dump(cfg, f)

# — Streamlit UI —
st.set_page_config(page_title="SEM Strategy Advisor", layout="centered")
st.title("🚀 SEM Strategy Advisor")

customer_id = st.text_input(
    "Enter Google Ads Customer ID (no dashes)", value=""
)

if st.button("Get Recommendations"):
    if not customer_id.strip():
        st.error("Please enter a valid customer ID.")
    else:
        with st.spinner("🔍 Fetching data…"):
            camp_df = fetch_campaign_data(customer_id)
            kw_df   = fetch_keyword_data(customer_id)
        st.success("✅ Data fetched! Generating recommendations…")
        recs = generate_recommendations(camp_df, kw_df)

        st.subheader("💡 Recommendations")
        for r in recs:
            st.write("•", r)
