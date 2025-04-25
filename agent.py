import streamlit as st
import pandas as pd
from google.ads.googleads.client import GoogleAdsClient

def fetch_campaign_data(customer_id: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch basic campaign metrics for a given customer ID within a date range."""
    config = {
        "developer_token": st.secrets["google_ads"]["developer_token"],
        "client_id": st.secrets["google_ads"]["client_id"],
        "client_secret": st.secrets["google_ads"]["client_secret"],
        "refresh_token": st.secrets["google_ads"]["refresh_token"],
        "login_customer_id": st.secrets["google_ads"]["login_customer_id"],
        "use_proto_plus": st.secrets["google_ads"]["use_proto_plus"]
    }
    client = GoogleAdsClient.load_from_dict(config)
    ga_service = client.get_service("GoogleAdsService")
    query = f"""
      SELECT
        campaign.id,
        campaign.name,
        metrics.impressions,
        metrics.clicks,
        metrics.conversions,
        metrics.cost_micros
      FROM campaign
      WHERE campaign.status != 'REMOVED'
      AND segments.date BETWEEN '{start_date}' AND '{end_date}'
    """
    response = ga_service.search(customer_id=customer_id, query=query)
    rows = []
    for row in response:
        c = row.campaign
        m = row.metrics
        rows.append({
            "campaign_id": c.id,
            "campaign_name": c.name,
            "impressions": m.impressions,
            "clicks": m.clicks,
            "conversions": m.conversions,
            "cost": m.cost_micros / 1e6,  # convert micros to currency
        })
    return pd.DataFrame(rows)

def fetch_keyword_data(customer_id: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch keyword-level metrics for a given customer ID within a date range."""
    config = {
        "developer_token": st.secrets["google_ads"]["developer_token"],
        "client_id": st.secrets["google_ads"]["client_id"],
        "client_secret": st.secrets["google_ads"]["client_secret"],
        "refresh_token": st.secrets["google_ads"]["refresh_token"],
        "login_customer_id": st.secrets["google_ads"]["login_customer_id"],
        "use_proto_plus": st.secrets["google_ads"]["use_proto_plus"]
    }
    client = GoogleAdsClient.load_from_dict(config)
    ga_service = client.get_service("GoogleAdsService")
    query = f"""
      SELECT
        campaign.id,
        campaign.name,
        ad_group.id,
        ad_group_criterion.keyword.text,
        metrics.impressions,
        metrics.clicks,
        metrics.conversions,
        metrics.cost_micros
      FROM keyword_view
      WHERE metrics.impressions > 0
      AND segments.date BETWEEN '{start_date}' AND '{end_date}'
    """
    response = ga_service.search(customer_id=customer_id, query=query)
    rows = []
    for row in response:
        rows.append({
            "campaign_id": row.campaign.id,
            "campaign_name": row.campaign.name,
            "ad_group_id": row.ad_group.id,
            "keyword": row.ad_group_criterion.keyword.text,
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "conversions": row.metrics.conversions,
            "cost": row.metrics.cost_micros / 1e6,
        })
    return pd.DataFrame(rows)

def generate_recommendations(camp_df: pd.DataFrame, kw_df: pd.DataFrame) -> list[str]:
    """Generate simple SEM recommendations based on CPA, CTR, and conversions."""
    recs: list[str] = []

    # 1. Campaign-level CPA
    camp_df["cpa"] = camp_df["cost"] / camp_df["conversions"].replace(0, float("inf"))
    high_cpa = camp_df[camp_df["cpa"] > camp_df["cpa"].mean()]
    for _, r in high_cpa.iterrows():
        recs.append(
            f"Campaign '{r.campaign_name}' has high CPA (${r.cpa:.2f}). "
            "Consider lowering bids or refining targeting."
        )

    # 2. Keywords with low CTR
    kw_df["ctr"] = kw_df["clicks"] / kw_df["impressions"]
    low_ctr = kw_df[kw_df["ctr"] < kw_df["ctr"].mean()].sort_values("ctr").head(5)
    for _, r in low_ctr.iterrows():
        recs.append(
            f"Keyword '{r.keyword}' in '{r.campaign_name}' has low CTR ({r.ctr:.1%}). "
            "Consider pausing, refining match type, or optimizing ad copy."
        )

    # 3. Top converting keywords
    top_conv = kw_df.sort_values("conversions", ascending=False).head(5)
    for _, r in top_conv.iterrows():
        recs.append(
            f"Keyword '{r.keyword}' in '{r.campaign_name}' drives {r.conversions} conversions. "
            "Consider increasing bids to capture more volume."
        )

    # 4. Budget allocation hint
    top_camps = camp_df.sort_values("conversions", ascending=False).head(3)
    recs.append("Top 3 campaigns by conversions:")
    for _, r in top_camps.iterrows():
        recs.append(f"  • {r.campaign_name}: {r.conversions} conv, ${r.cost:.2f} spent")

    return recs
