import argparse
import pandas as pd
from google.ads.googleads.client import GoogleAdsClient

def fetch_campaign_data(customer_id: str) -> pd.DataFrame:
    """Fetch basic campaign metrics for a given customer ID."""
    client    = GoogleAdsClient.load_from_storage("google-ads.yaml")
    ga_service = client.get_service("GoogleAdsService")
    query = """
      SELECT
        campaign.id,
        campaign.name,
        metrics.impressions,
        metrics.clicks,
        metrics.conversions,
        metrics.cost_micros
      FROM campaign
      WHERE campaign.status != 'REMOVED'
    """
    response = ga_service.search(customer_id=customer_id, query=query)
    rows = []
    for row in response:
        c = row.campaign
        m = row.metrics
        rows.append({
            "campaign_id":   c.id,
            "campaign_name": c.name,
            "impressions":   m.impressions,
            "clicks":        m.clicks,
            "conversions":   m.conversions,
            "cost":          m.cost_micros / 1e6,  # convert micros to currency
        })
    return pd.DataFrame(rows)

def fetch_keyword_data(customer_id: str) -> pd.DataFrame:
    """Fetch keyword-level metrics for a given customer ID."""
    client    = GoogleAdsClient.load_from_storage("google-ads.yaml")
    ga_service = client.get_service("GoogleAdsService")
    query = """
      SELECT
        campaign.id,
        campaign.name,
        ad_group.id,
        segments.keyword.text,
        metrics.impressions,
        metrics.clicks,
        metrics.conversions,
        metrics.cost_micros
      FROM keyword_view
      WHERE metrics.impressions > 0
    """
    response = ga_service.search(customer_id=customer_id, query=query)
    rows = []
    for row in response:
        rows.append({
            "campaign_id":   row.campaign.id,
            "campaign_name": row.campaign.name,
            "ad_group_id":   row.ad_group.id,
            "keyword":       row.segments.keyword.text,
            "impressions":   row.metrics.impressions,
            "clicks":        row.metrics.clicks,
            "conversions":   row.metrics.conversions,
            "cost":          row.metrics.cost_micros / 1e6,
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

def main():
    parser = argparse.ArgumentParser(description="SEM Strategy Advisor Agent")
    parser.add_argument(
        "--customer-id", required=True,
        help="10-digit Google Ads customer ID (no dashes)"
    )
    args = parser.parse_args()

    print(f"\n🔍 Fetching data for customer {args.customer_id}...\n")
    camp_df = fetch_campaign_data(args.customer_id)
    kw_df   = fetch_keyword_data(args.customer_id)

    print("💡 Generating recommendations:\n")
    for rec in generate_recommendations(camp_df, kw_df):
        print("- " + rec)
    print()

if __name__ == "__main__":
    main()
