import streamlit as st
from agent import fetch_campaign_data, fetch_keyword_data, generate_recommendations
from datetime import datetime, timedelta

st.title("SEM Strategy Advisor")

# Input for customer ID
customer_id = st.text_input("Enter Google Ads Customer ID (10-digit, no dashes)", "")

# Date range inputs
st.subheader("Select Date Range")
default_end_date = datetime.today().date()
default_start_date = default_end_date - timedelta(days=30)  # Default to last 30 days
start_date = st.date_input("Start Date", value=default_start_date)
end_date = st.date_input("End Date", value=default_end_date)

if st.button("Fetch Data and Generate Recommendations"):
    if not customer_id:
        st.error("Please enter a valid Customer ID.")
    elif not customer_id.isdigit() or len(customer_id) != 10:
        st.error("Customer ID must be a 10-digit number with no dashes.")
    elif start_date > end_date:
        st.error("Start Date cannot be after End Date.")
    else:
        try:
            # Format dates as YYYY-MM-DD for Google Ads API
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            # Display loading message
            with st.spinner("Fetching data..."):
                # Fetch campaign and keyword data with date range
                camp_df = fetch_campaign_data(customer_id, start_date_str, end_date_str)
                kw_df = fetch_keyword_data(customer_id, start_date_str, end_date_str)

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
            st.write("Please check the Customer ID, date range, or ensure the Google Ads account is accessible.")
