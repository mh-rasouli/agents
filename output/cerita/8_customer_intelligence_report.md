# Customer Intelligence Folder Specification
## Trend Media — AI Agent Data Architecture

**Brand:** Cerita
**Parent Company:** شرکت پارس آزمای طب
**Website:** https://ceritateb.com/
**Generated:** 2026-02-17 08:45:28
**Data Source:** Google Sheets - Refrences
**Total Transactions:** 0
**Total Campaigns:** 0
**Report Version:** 1.0

---

## 8. CRM Record — CRM Data

**Source:** Google Sheets (Refrences)

```json
{
  "crm_record": {
    "sync_date": "2026-02-17T08:45:28Z",
    "crm_account_id": "Not Available",
    "source_system": "google_sheets"
  },
  "account": {
    "name": "Cerita",
    "name_fa": "Cerita",
    "account_type": "Not Available",
    "industry_vertical": "Not Available",
    "sub_vertical": "Not Available",
    "tier": "Not Available",
    "assigned_account_manager": "Not Available",
    "assigned_account_manager_id": "Not Available"
  },
  "contacts": [
  ],
  "deal_pipeline": {
    "active_deals": [],
    "lost_deals_last_12m": [],
    "won_deals_last_12m": "Not Available"
  },
  "relationship_timeline": {
    "first_engagement": "Not Available",
    "total_deals_won": 0,
    "total_deals_lost": "Not Available",
    "total_lifetime_revenue_tomans": 0,
    "last_campaign_end_date": "Not Available",
    "days_since_last_campaign": "Not Available",
    "renewal_status": "Not Available",
    "nps_score": null,
    "satisfaction_signals": [],
    "risk_signals": []
  }
}
```

---

## 9. Campaign History — All Past Campaigns

**Source:** Google Sheets (Refrences)

```json
{
  "campaign_history": {
    "sync_date": "2026-02-17T08:45:28Z",
    "brand_slug": "unknown",
    "total_campaigns": 0,
    "first_campaign": "Not Available",
    "last_campaign": "Not Available",
    "total_spend_tomans": 0
  },
  "campaigns": [
  ],
  "aggregate_metrics": {
    "avg_engagement_rate": "Not Available",
    "avg_cost_per_view": "Not Available",
    "best_performing_platform": "Not Available",
    "total_unique_creators_used": "Not Available",
    "seasonal_patterns": "Not Available"
  }
}
```

---

## 10. Creator Performance — Creator Data for This Client

**Source:** Google Sheets (Refrences)

```json
{
  "creator_performance": {
    "sync_date": "2026-02-17T08:45:28Z",
    "brand_slug": "Not Available",
    "total_creators_engaged": "Not Available",
    "analysis_period": "Not Available to Not Available"
  },
  "top_performers": [],
  "platform_breakdown": {
  },
  "recommended_for_next_campaign": [],
  "blacklisted_creators": []
}
```

---

## 11. Financial History — AR, Invoicing, Payment Behavior

**Source:** Google Sheets (Refrences)

```json
{
  "financial_history": {
    "sync_date": "2026-02-17T08:45:28Z",
    "brand_slug": "Not Available",
    "accounting_entity_id": "Not Available"
  },
  "revenue_summary": {
    "total_lifetime_revenue_tomans": 0,
    "revenue_by_year": {},
    "avg_deal_size_tomans": 0,
    "largest_deal_tomans": "Not Available",
    "payment_terms_standard": "Not Available"
  },
  "accounts_receivable": {
    "current_outstanding_tomans": "Not Available",
    "overdue_tomans": "Not Available"
  },
  "payment_behavior": {
    "avg_days_to_pay": "Not Available",
    "on_time_payment_rate": 0.00,
    "payment_risk_score": "high",
    "last_payment_date": "Not Available",
    "payment_trend": "Not Available"
  },
  "invoices_last_12m": [
  ],
  "creator_payout_summary": {
    "total_creator_payouts_for_client_tomans": 0,
    "avg_payout_per_creator_tomans": "Not Available",
    "payout_margin_realized": 0.00
  }
}
```

---

## 12. Communications Log — Key Communications

**Source:** Not Available (requires Telegram/WhatsApp integration)

```json
{
  "communications_log": {
    "sync_date": "2026-02-17T08:45:28Z",
    "brand_slug": "Not Available",
    "log_period": "Not Available",
    "total_interactions": "Not Available"
  },
  "recent_interactions": [],
  "communication_patterns": {
    "avg_response_time_hours": "Not Available",
    "preferred_channel": "Not Available",
    "ghosting_risk": "Not Available"
  }
}
```

---

## 13. Relationship Score — Agent-Computed Health Signals

**Source:** Computed from Refrences transaction data

```json
{
  "relationship_score": {
    "computed_date": "2026-02-17T08:45:28Z",
    "brand_slug": "Not Available",
    "model_version": "1.0"
  },
  "health_score": {
    "overall": 0,
    "components": {
      "recency": "Not Available",
      "frequency": 0,
      "monetary": 0,
      "satisfaction": "Not Available",
      "engagement": "Not Available",
      "payment_health": 0
    },
    "trend": "Not Available",
    "trend_reason": "Not Available"
  },
  "churn_risk": {
    "risk_level": "high",
    "probability": 0.60,
    "primary_risk_factors": [],
    "mitigating_factors": []
  },
  "upsell_opportunities": [],
  "recommended_actions": []
}
```

---

## 14. MMM Readiness — Marketing Mix Modeling Data Assessment

**Source:** Computed from Refrences data availability

```json
{
  "mmm_readiness": {
    "assessed_date": "2026-02-17",
    "brand_slug": "Not Available",
    "assessor": "customer_intelligence_agent"
  },
  "overall_readiness": "partial",
  "readiness_score": 45,
  "data_availability": {
    "sales_data": {
      "available": false,
      "notes": "Client sales data not provided"
    },
    "media_spend_data": {
      "available": true,
      "granularity": "transaction_level",
      "channels_covered": [],
      "history_months": "0 transactions"
    },
    "creator_media_pressure": {
      "available": true,
      "granularity": "transaction_level",
      "metrics": ["spend", "views", "impressions"]
    }
  },
  "recommended_next_steps": [
    "Request client sales/conversion data",
    "Request full media mix breakdown",
    "Enrich creator data with engagement metrics"
  ],
  "ideal_mmm_client": false,
  "ideal_mmm_client_reason": "Missing sales data and full media mix",
  "estimated_time_to_first_model": "3-4 months after data acquisition"
}
```

---

---

*Report generated by Customer Intelligence Agent on 2026-02-17 08:45:28*

**Data Source:** Google Sheets - Internal Operations Database (Refrences)