import streamlit as st
from agent import fetch_campaign_data, fetch_keyword_data, generate_recommendations

st.title("SEM Strategy Advisor")

# Input for customer ID
customer_id = st.text_input("Enter Google Ads Customer ID (10-digit, no dashes)", "")

if st.button("Fetch Data and Generate Recommendations"):
    if not customer_id:
        st.error("Please enter a valid Customer ID.")
    elif not customer_id.isdigit() or len(customer_id) != 10:
        st.error("Customer ID must be a 10-digit number with no dashes.")
    else:
        try:
            # Display loading message
            with st.spinner("Fetching data..."):
                # Fetch campaign and keyword data
                camp_df = fetch_campaign_data(customer_id)
                kw_df = fetch_keyword_data(customer_id)

            # Display campaign data
            st.subheader("Campaign Data")
            st.dataframe(camp_df)

            # Display keyword data
            st.subheader("Keyword Data")
            st.dataframe(kw_df)

            # Generate and display recommendations
            st.subheader("Recommendations")
            recommendations = generate_recommendations(camp_df, kw_df)
            for rec in recommendations:
                st.write(f"- {rec}")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.write("Please check the Customer ID or ensure the Google Ads account is accessible.")
