"""Customer Intelligence Agent - generates customer intelligence report from proprietary data."""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict
from agents.base_agent import BaseAgent
from models.state import BrandIntelligenceState
from utils.logger import get_logger
from utils.google_sheets_client import GoogleSheetsClient
from utils.helpers import sanitize_filename

logger = get_logger(__name__)


class CustomerIntelligenceAgent(BaseAgent):
    """Agent responsible for generating customer intelligence report from proprietary data."""

    def __init__(self, credentials_path: str, sheet_id: str):
        """Initialize the customer intelligence agent.

        Args:
            credentials_path: Path to Google service account credentials
            sheet_id: Google Sheets ID containing customer data
        """
        super().__init__("CustomerIntelligenceAgent")
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id
        self.sheets_client = None

    def execute(self, state: BrandIntelligenceState) -> BrandIntelligenceState:
        """Generate customer intelligence report.

        Args:
            state: Current workflow state

        Returns:
            Updated state with customer intelligence report path
        """
        self._log_start()

        brand_name = state["brand_name"]
        output_dir = self._get_output_dir(brand_name)

        try:
            # Initialize Google Sheets client
            logger.info("Initializing Google Sheets client...")
            self.sheets_client = GoogleSheetsClient(self.credentials_path)

            # Load brand metadata from Brand_Data sheet
            logger.info("Loading brand metadata from Brand_Data sheet...")
            brand_metadata = self._load_brand_metadata(brand_name)

            if not brand_metadata:
                logger.warning(f"Brand {brand_name} not found in Brand_Data sheet")
                state["customer_intelligence"] = {
                    "status": "not_found",
                    "message": f"Brand {brand_name} not found in Google Sheets"
                }
                self._log_end(success=False)
                return state

            # Load transaction data from Refrences sheet
            logger.info(f"Loading transaction data from Refrences sheet for {brand_name}...")
            transactions = self._load_transaction_data(brand_name)

            logger.info(f"Found {len(transactions)} transactions for {brand_name}")

            # Process data
            logger.info("Processing transaction data...")
            processed_data = self._process_transaction_data(transactions, brand_metadata)

            # Generate comprehensive markdown report
            logger.info("Generating customer intelligence markdown report...")
            report_path = self._generate_markdown_report(
                brand_name,
                brand_metadata,
                processed_data,
                output_dir
            )

            # Update state
            state["customer_intelligence"] = {
                "status": "completed",
                "report_path": str(report_path),
                "transaction_count": len(transactions),
                "campaign_count": processed_data.get("total_campaigns", 0),
                "total_revenue": processed_data.get("total_revenue", 0)
            }

            logger.info(f"[OK] Customer intelligence report saved: {report_path.name}")
            self._log_end(success=True)

        except Exception as e:
            logger.error(f"Failed to generate customer intelligence report: {e}")
            import traceback
            traceback.print_exc()
            self._add_error(state, f"Customer intelligence generation failed: {e}")
            state["customer_intelligence"] = {
                "status": "error",
                "message": str(e)
            }
            self._log_end(success=False)

        return state

    def _get_output_dir(self, brand_name: str) -> Path:
        """Get output directory for brand."""
        safe_name = sanitize_filename(brand_name)
        output_dir = Path("output") / safe_name
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _load_brand_metadata(self, brand_name: str) -> Dict[str, Any]:
        """Load brand metadata from Brand_Data sheet."""
        try:
            spreadsheet = self.sheets_client.client.open_by_key(self.sheet_id)
            sheet1 = spreadsheet.worksheet('Brand_Data')
            all_data = sheet1.get_all_values()

            # Search for brand
            for row in all_data[1:]:  # Skip header
                if len(row) >= 1 and row[0].strip() == brand_name:
                    return {
                        "brand_name": row[0].strip() if len(row) > 0 else "",
                        "website": row[1].strip() if len(row) > 1 else "Not Available",
                        "parent_company": row[2].strip() if len(row) > 2 else "Not Available"
                    }

            return None

        except Exception as e:
            logger.error(f"Error loading brand metadata: {e}")
            return None

    def _load_transaction_data(self, brand_name: str) -> List[Dict[str, Any]]:
        """Load transaction data from Refrences sheet."""
        try:
            spreadsheet = self.sheets_client.client.open_by_key(self.sheet_id)
            sheet2 = spreadsheet.worksheet('Refrences')
            all_data = sheet2.get_all_values()

            if len(all_data) < 2:
                return []

            headers = all_data[0]
            transactions = []

            # Find all rows for this brand
            for row in all_data[1:]:
                if len(row) > 8:
                    brand_col = row[7] if len(row) > 7 else ''
                    customer_col = row[8] if len(row) > 8 else ''

                    # Match brand
                    if brand_name.lower() in str(brand_col).lower() or \
                       brand_name.lower() in str(customer_col).lower():

                        # Build transaction dict
                        transaction = {}
                        for i, header in enumerate(headers):
                            transaction[header] = row[i] if i < len(row) else ""

                        transactions.append(transaction)

            return transactions

        except Exception as e:
            logger.error(f"Error loading transaction data: {e}")
            return []

    def _process_transaction_data(self, transactions: List[Dict], metadata: Dict) -> Dict[str, Any]:
        """Process and aggregate transaction data."""

        if not transactions:
            return {
                "total_campaigns": 0,
                "total_revenue": 0,
                "total_cost": 0,
                "total_transactions": 0
            }

        # Parse and aggregate
        campaigns = defaultdict(lambda: {
            "transactions": [],
            "total_cost": 0,
            "total_revenue": 0,
            "total_views": 0,
            "total_impressions": 0,
            "platforms": set(),
            "dates": [],
            "publish_types": set()
        })

        total_revenue = 0
        total_cost = 0
        total_views = 0
        total_normal_impressions = 0
        total_vip_impressions = 0
        platforms_used = defaultdict(lambda: {"cost": 0, "revenue": 0, "views": 0, "count": 0})
        sales_people = set()
        account_managers = set()
        operations_team = set()
        payment_statuses = []
        dates = []
        invoices = []
        year_revenue = defaultdict(float)

        for tx in transactions:
            # Campaign aggregation
            campaign_name = tx.get("Campaign Name", "").strip()
            if not campaign_name:
                campaign_name = "Unnamed Campaign"

            campaigns[campaign_name]["transactions"].append(tx)

            # Parse numeric values
            cost = self._parse_persian_number(tx.get("Total Cost", "0"))
            revenue = self._parse_persian_number(tx.get("Revenue", "0"))
            views = self._parse_persian_number(tx.get("View", "0"))
            normal_imp = self._parse_persian_number(tx.get("Normal Imp", "0"))
            vip_imp = self._parse_persian_number(tx.get("VIP Imp", "0"))

            campaigns[campaign_name]["total_cost"] += cost
            campaigns[campaign_name]["total_revenue"] += revenue
            campaigns[campaign_name]["total_views"] += views
            campaigns[campaign_name]["total_impressions"] += (normal_imp + vip_imp)

            # Platform
            platform = tx.get("Media", "").strip().upper()
            if platform:
                campaigns[campaign_name]["platforms"].add(platform)
                platforms_used[platform]["cost"] += cost
                platforms_used[platform]["revenue"] += revenue
                platforms_used[platform]["views"] += views
                platforms_used[platform]["count"] += 1

            # Publish type
            publish_type = tx.get("Publish type", "").strip()
            if publish_type:
                campaigns[campaign_name]["publish_types"].add(publish_type)

            # Dates
            date_str = tx.get("Date", "").strip()
            if date_str:
                campaigns[campaign_name]["dates"].append(date_str)

            # Overall aggregation
            total_cost += cost
            total_revenue += revenue
            total_views += views
            total_normal_impressions += normal_imp
            total_vip_impressions += vip_imp

            sale = tx.get("Sale", "").strip()
            if sale and sale != "-":
                sales_people.add(sale)

            account = tx.get("Account", "").strip()
            if account and account != "-":
                account_managers.add(account)

            operation = tx.get("Operation", "").strip()
            if operation and operation != "-":
                operations_team.add(operation)

            payment = tx.get("Payment status", "").strip()
            if payment:
                payment_statuses.append(payment)

            if date_str:
                dates.append(date_str)
                # Extract year for revenue breakdown
                try:
                    if len(date_str) == 8:  # Persian date format YYYYMMDD
                        year = date_str[:4]
                        year_revenue[year] += revenue
                except:
                    pass

            # Invoice tracking
            invoice_num = tx.get("Invoice Number", "").strip()
            if invoice_num:
                invoices.append({
                    "invoice_number": invoice_num,
                    "invoice_type": tx.get("Invoice Type", "").strip(),
                    "amount": revenue,
                    "payment_status": payment,
                    "date": date_str
                })

        # Calculate metrics
        profit = total_revenue - total_cost
        profit_margin = (profit / total_revenue * 100) if total_revenue > 0 else 0

        # Payment behavior
        paid_count = sum(1 for p in payment_statuses if p and ("paid" in p.lower() or "پرداخت" in p))
        payment_rate = (paid_count / len(payment_statuses)) if payment_statuses else 0

        # Date range
        first_date = min(dates) if dates else "Not Available"
        last_date = max(dates) if dates else "Not Available"

        # Platform metrics
        platform_breakdown = {}
        for platform, metrics in platforms_used.items():
            avg_cpv = metrics["cost"] / metrics["views"] if metrics["views"] > 0 else 0
            platform_breakdown[platform] = {
                "total_cost": metrics["cost"],
                "total_revenue": metrics["revenue"],
                "total_views": metrics["views"],
                "transactions": metrics["count"],
                "avg_cpv": avg_cpv
            }

        return {
            "total_campaigns": len(campaigns),
            "campaigns": dict(campaigns),
            "total_transactions": len(transactions),
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "total_profit": profit,
            "profit_margin": profit_margin,
            "total_views": total_views,
            "total_impressions": total_normal_impressions + total_vip_impressions,
            "platforms_used": list(platforms_used.keys()),
            "platform_breakdown": platform_breakdown,
            "sales_people": list(sales_people),
            "account_managers": list(account_managers),
            "operations_team": list(operations_team),
            "payment_rate": payment_rate,
            "first_transaction_date": first_date,
            "last_transaction_date": last_date,
            "avg_transaction_value": total_revenue / len(transactions) if transactions else 0,
            "invoices": invoices,
            "total_paid": paid_count,
            "total_unpaid": len(payment_statuses) - paid_count,
            "year_revenue": dict(year_revenue)
        }

    def _parse_persian_number(self, value: str) -> float:
        """Parse Persian number string to float."""
        try:
            # Remove commas and convert
            cleaned = str(value).replace(",", "").replace("٬", "").strip()
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0

    def _generate_markdown_report(
        self,
        brand_name: str,
        metadata: Dict,
        processed_data: Dict,
        output_dir: Path
    ) -> Path:
        """Generate comprehensive markdown report following template structure."""

        output_path = output_dir / "8_customer_intelligence_report.md"

        lines = []

        # Header
        lines.append("# Customer Intelligence Folder Specification")
        lines.append("## Trend Media — AI Agent Data Architecture")
        lines.append("")
        lines.append(f"**Brand:** {brand_name}")
        lines.append(f"**Parent Company:** {metadata.get('parent_company', 'Not Available')}")
        lines.append(f"**Website:** {metadata.get('website', 'Not Available')}")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Data Source:** Google Sheets - Refrences")
        lines.append(f"**Total Transactions:** {processed_data.get('total_transactions', 0)}")
        lines.append(f"**Total Campaigns:** {processed_data.get('total_campaigns', 0)}")
        lines.append(f"**Report Version:** 1.0")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Section 8: CRM Record
        lines.extend(self._generate_section_8(brand_name, metadata, processed_data))
        lines.append("")

        # Section 9: Campaign History
        lines.extend(self._generate_section_9(processed_data))
        lines.append("")

        # Section 10: Creator Performance
        lines.extend(self._generate_section_10(processed_data))
        lines.append("")

        # Section 11: Financial History
        lines.extend(self._generate_section_11(processed_data))
        lines.append("")

        # Section 12: Communications Log
        lines.extend(self._generate_section_12())
        lines.append("")

        # Section 13: Relationship Score
        lines.extend(self._generate_section_13(processed_data))
        lines.append("")

        # Section 14: MMM Readiness
        lines.extend(self._generate_section_14(processed_data))
        lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(f"*Report generated by Customer Intelligence Agent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")
        lines.append("**Data Source:** Google Sheets - Internal Operations Database (Refrences)")

        # Write file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        return output_path

    def _generate_section_8(self, brand_name: str, metadata: Dict, data: Dict) -> List[str]:
        """Generate Section 8: CRM Record (JSON schema in markdown)."""
        lines = []
        lines.append("## 8. CRM Record — CRM Data")
        lines.append("")
        lines.append("**Source:** Google Sheets (Refrences)")
        lines.append("")
        lines.append("```json")
        lines.append("{")
        lines.append('  "crm_record": {')
        lines.append(f'    "sync_date": "{datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}",')
        lines.append('    "crm_account_id": "Not Available",')
        lines.append('    "source_system": "google_sheets"')
        lines.append('  },')
        lines.append('  "account": {')
        lines.append(f'    "name": "{brand_name}",')
        lines.append(f'    "name_fa": "{brand_name}",')
        lines.append('    "account_type": "Not Available",')
        lines.append('    "industry_vertical": "Not Available",')
        lines.append('    "sub_vertical": "Not Available",')
        lines.append('    "tier": "Not Available",')

        account_managers = data.get("account_managers", [])
        if account_managers:
            lines.append(f'    "assigned_account_manager": "{", ".join(account_managers[:2])}",')
        else:
            lines.append('    "assigned_account_manager": "Not Available",')
        lines.append('    "assigned_account_manager_id": "Not Available"')
        lines.append('  },')

        lines.append('  "contacts": [')
        sales_people = data.get("sales_people", [])
        operations = data.get("operations_team", [])

        if sales_people or operations:
            all_contacts = list(sales_people[:2]) + list(operations[:1])
            for idx, person in enumerate(all_contacts):
                lines.append('    {')
                lines.append(f'      "name": "{person}",')
                lines.append('      "title": "Not Available",')
                role = "sales" if person in sales_people else "operations"
                lines.append(f'      "role": "{role}",')
                lines.append('      "email": "Not Available",')
                lines.append('      "phone": "Not Available",')
                lines.append('      "preferred_channel": "Not Available",')
                lines.append('      "last_contacted": "Not Available",')
                lines.append('      "notes": "Not Available"')
                if idx < len(all_contacts) - 1:
                    lines.append('    },')
                else:
                    lines.append('    }')
        lines.append('  ],')

        lines.append('  "deal_pipeline": {')
        lines.append('    "active_deals": [],')
        lines.append('    "lost_deals_last_12m": [],')
        lines.append('    "won_deals_last_12m": "Not Available"')
        lines.append('  },')

        lines.append('  "relationship_timeline": {')
        lines.append(f'    "first_engagement": "{data.get("first_transaction_date", "Not Available")}",')
        lines.append(f'    "total_deals_won": {data.get("total_campaigns", 0)},')
        lines.append('    "total_deals_lost": "Not Available",')
        lines.append(f'    "total_lifetime_revenue_tomans": {data.get("total_revenue", 0):.0f},')
        lines.append(f'    "last_campaign_end_date": "{data.get("last_transaction_date", "Not Available")}",')
        lines.append('    "days_since_last_campaign": "Not Available",')
        lines.append('    "renewal_status": "Not Available",')
        lines.append('    "nps_score": null,')
        lines.append('    "satisfaction_signals": [],')
        lines.append('    "risk_signals": []')
        lines.append('  }')
        lines.append("}")
        lines.append("```")
        lines.append("")
        lines.append("---")
        return lines

    def _generate_section_9(self, data: Dict) -> List[str]:
        """Generate Section 9: Campaign History."""
        lines = []
        lines.append("## 9. Campaign History — All Past Campaigns")
        lines.append("")
        lines.append("**Source:** Google Sheets (Refrences)")
        lines.append("")
        lines.append("```json")
        lines.append("{")
        lines.append('  "campaign_history": {')
        lines.append(f'    "sync_date": "{datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}",')
        lines.append(f'    "brand_slug": "{sanitize_filename(data.get("brand_name", "unknown"))}",')
        lines.append(f'    "total_campaigns": {data.get("total_campaigns", 0)},')
        lines.append(f'    "first_campaign": "{data.get("first_transaction_date", "Not Available")}",')
        lines.append(f'    "last_campaign": "{data.get("last_transaction_date", "Not Available")}",')
        lines.append(f'    "total_spend_tomans": {data.get("total_cost", 0):.0f}')
        lines.append('  },')
        lines.append('  "campaigns": [')

        campaigns = data.get('campaigns', {})
        campaign_list = list(campaigns.items())[:5]  # Show first 5 campaigns

        for idx, (campaign_name, campaign_data) in enumerate(campaign_list):
            lines.append('    {')
            lines.append(f'      "campaign_id": "CAMP-{idx+1:04d}",')
            lines.append(f'      "campaign_name": "{campaign_name}",')
            lines.append('      "status": "completed",')
            lines.append('      "objective": "Not Available",')

            dates = campaign_data.get('dates', [])
            if dates:
                lines.append(f'      "start_date": "{min(dates)}",')
                lines.append(f'      "end_date": "{max(dates)}",')
            else:
                lines.append('      "start_date": "Not Available",')
                lines.append('      "end_date": "Not Available",')

            lines.append(f'      "budget_tomans": {campaign_data["total_cost"]:.0f},')
            lines.append(f'      "actual_spend_tomans": {campaign_data["total_cost"]:.0f},')

            platforms = list(campaign_data.get('platforms', []))
            lines.append(f'      "platforms": {json.dumps(platforms)},')

            publish_types = list(campaign_data.get('publish_types', []))
            lines.append(f'      "content_formats": {json.dumps(publish_types)},')

            lines.append('      "total_creators_used": "Not Available",')
            lines.append(f'      "total_content_pieces": {len(campaign_data["transactions"])},')

            lines.append('      "performance": {')
            lines.append('        "total_reach": "Not Available",')
            lines.append(f'        "total_impressions": {campaign_data["total_impressions"]:.0f},')
            lines.append(f'        "total_views": {campaign_data["total_views"]:.0f},')
            lines.append('        "total_engagements": "Not Available",')
            lines.append('        "engagement_rate": "Not Available",')

            if campaign_data['total_views'] > 0:
                cpv = campaign_data['total_cost'] / campaign_data['total_views']
                lines.append(f'        "cost_per_view": {cpv:.0f}')
            else:
                lines.append('        "cost_per_view": "Not Available"')

            lines.append('      }')
            if idx < len(campaign_list) - 1:
                lines.append('    },')
            else:
                lines.append('    }')

        lines.append('  ],')
        lines.append('  "aggregate_metrics": {')
        lines.append('    "avg_engagement_rate": "Not Available",')

        total_views = data.get('total_views', 0)
        total_cost = data.get('total_cost', 0)
        if total_views > 0:
            avg_cpv = total_cost / total_views
            lines.append(f'    "avg_cost_per_view": {avg_cpv:.0f},')
        else:
            lines.append('    "avg_cost_per_view": "Not Available",')

        platforms = data.get('platforms_used', [])
        if platforms:
            lines.append(f'    "best_performing_platform": "{platforms[0]}",')
        else:
            lines.append('    "best_performing_platform": "Not Available",')

        lines.append('    "total_unique_creators_used": "Not Available",')
        lines.append('    "seasonal_patterns": "Not Available"')
        lines.append('  }')
        lines.append("}")
        lines.append("```")
        lines.append("")
        lines.append("---")
        return lines

    def _generate_section_10(self, data: Dict) -> List[str]:
        """Generate Section 10: Creator Performance."""
        lines = []
        lines.append("## 10. Creator Performance — Creator Data for This Client")
        lines.append("")
        lines.append("**Source:** Google Sheets (Refrences)")
        lines.append("")
        lines.append("```json")
        lines.append("{")
        lines.append('  "creator_performance": {')
        lines.append(f'    "sync_date": "{datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}",')
        lines.append('    "brand_slug": "Not Available",')
        lines.append('    "total_creators_engaged": "Not Available",')
        lines.append(f'    "analysis_period": "{data.get("first_transaction_date", "Not Available")} to {data.get("last_transaction_date", "Not Available")}"')
        lines.append('  },')
        lines.append('  "top_performers": [],')

        lines.append('  "platform_breakdown": {')
        platform_breakdown = data.get('platform_breakdown', {})
        platform_list = list(platform_breakdown.items())

        for idx, (platform, metrics) in enumerate(platform_list):
            lines.append(f'    "{platform.lower()}": {{')
            lines.append('      "creators_used": "Not Available",')
            lines.append('      "avg_engagement_rate": "Not Available",')
            lines.append(f'      "avg_cpv": {metrics["avg_cpv"]:.0f},')
            lines.append('      "best_format": "Not Available"')
            if idx < len(platform_list) - 1:
                lines.append('    },')
            else:
                lines.append('    }')

        lines.append('  },')
        lines.append('  "recommended_for_next_campaign": [],')
        lines.append('  "blacklisted_creators": []')
        lines.append("}")
        lines.append("```")
        lines.append("")
        lines.append("---")
        return lines

    def _generate_section_11(self, data: Dict) -> List[str]:
        """Generate Section 11: Financial History."""
        lines = []
        lines.append("## 11. Financial History — AR, Invoicing, Payment Behavior")
        lines.append("")
        lines.append("**Source:** Google Sheets (Refrences)")
        lines.append("")
        lines.append("```json")
        lines.append("{")
        lines.append('  "financial_history": {')
        lines.append(f'    "sync_date": "{datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}",')
        lines.append('    "brand_slug": "Not Available",')
        lines.append('    "accounting_entity_id": "Not Available"')
        lines.append('  },')

        lines.append('  "revenue_summary": {')
        lines.append(f'    "total_lifetime_revenue_tomans": {data.get("total_revenue", 0):.0f},')

        year_revenue = data.get('year_revenue', {})
        if year_revenue:
            lines.append('    "revenue_by_year": {')
            year_items = list(year_revenue.items())
            for idx, (year, revenue) in enumerate(year_items):
                if idx < len(year_items) - 1:
                    lines.append(f'      "{year}": {revenue:.0f},')
                else:
                    lines.append(f'      "{year}": {revenue:.0f}')
            lines.append('    },')
        else:
            lines.append('    "revenue_by_year": {},')

        lines.append(f'    "avg_deal_size_tomans": {data.get("avg_transaction_value", 0):.0f},')
        lines.append('    "largest_deal_tomans": "Not Available",')
        lines.append('    "payment_terms_standard": "Not Available"')
        lines.append('  },')

        lines.append('  "accounts_receivable": {')
        lines.append('    "current_outstanding_tomans": "Not Available",')
        lines.append('    "overdue_tomans": "Not Available"')
        lines.append('  },')

        lines.append('  "payment_behavior": {')
        lines.append('    "avg_days_to_pay": "Not Available",')
        payment_rate = data.get('payment_rate', 0)
        lines.append(f'    "on_time_payment_rate": {payment_rate:.2f},')

        if payment_rate >= 0.9:
            risk = "low"
        elif payment_rate >= 0.7:
            risk = "medium"
        else:
            risk = "high"
        lines.append(f'    "payment_risk_score": "{risk}",')
        lines.append(f'    "last_payment_date": "{data.get("last_transaction_date", "Not Available")}",')
        lines.append('    "payment_trend": "Not Available"')
        lines.append('  },')

        invoices = data.get('invoices', [])
        lines.append('  "invoices_last_12m": [')
        if invoices:
            for idx, invoice in enumerate(invoices[:5]):  # Show first 5 invoices
                lines.append('    {')
                lines.append(f'      "invoice_id": "{invoice.get("invoice_number", "Not Available")}",')
                lines.append(f'      "date_issued": "{invoice.get("date", "Not Available")}",')
                lines.append(f'      "amount_tomans": {invoice.get("amount", 0):.0f},')
                lines.append(f'      "status": "{invoice.get("payment_status", "Not Available")}",')
                lines.append(f'      "invoice_type": "{invoice.get("invoice_type", "Not Available")}"')
                if idx < min(5, len(invoices)) - 1:
                    lines.append('    },')
                else:
                    lines.append('    }')
        lines.append('  ],')

        lines.append('  "creator_payout_summary": {')
        lines.append(f'    "total_creator_payouts_for_client_tomans": {data.get("total_cost", 0):.0f},')
        lines.append('    "avg_payout_per_creator_tomans": "Not Available",')
        margin = data.get('profit_margin', 0) / 100
        lines.append(f'    "payout_margin_realized": {margin:.2f}')
        lines.append('  }')
        lines.append("}")
        lines.append("```")
        lines.append("")
        lines.append("---")
        return lines

    def _generate_section_12(self) -> List[str]:
        """Generate Section 12: Communications Log."""
        lines = []
        lines.append("## 12. Communications Log — Key Communications")
        lines.append("")
        lines.append("**Source:** Not Available (requires Telegram/WhatsApp integration)")
        lines.append("")
        lines.append("```json")
        lines.append("{")
        lines.append('  "communications_log": {')
        lines.append(f'    "sync_date": "{datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}",')
        lines.append('    "brand_slug": "Not Available",')
        lines.append('    "log_period": "Not Available",')
        lines.append('    "total_interactions": "Not Available"')
        lines.append('  },')
        lines.append('  "recent_interactions": [],')
        lines.append('  "communication_patterns": {')
        lines.append('    "avg_response_time_hours": "Not Available",')
        lines.append('    "preferred_channel": "Not Available",')
        lines.append('    "ghosting_risk": "Not Available"')
        lines.append('  }')
        lines.append("}")
        lines.append("```")
        lines.append("")
        lines.append("---")
        return lines

    def _generate_section_13(self, data: Dict) -> List[str]:
        """Generate Section 13: Relationship Score."""
        lines = []
        lines.append("## 13. Relationship Score — Agent-Computed Health Signals")
        lines.append("")
        lines.append("**Source:** Computed from Refrences transaction data")
        lines.append("")

        # Calculate health score
        total_campaigns = data.get('total_campaigns', 0)
        payment_rate = data.get('payment_rate', 0)
        total_revenue = data.get('total_revenue', 0)

        frequency_score = min(100, total_campaigns * 5)
        monetary_score = min(100, (total_revenue / 5000000000) * 100) if total_revenue > 0 else 0
        payment_score = payment_rate * 100

        overall_score = (frequency_score + monetary_score + payment_score) / 3

        lines.append("```json")
        lines.append("{")
        lines.append('  "relationship_score": {')
        lines.append(f'    "computed_date": "{datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}",')
        lines.append('    "brand_slug": "Not Available",')
        lines.append('    "model_version": "1.0"')
        lines.append('  },')

        lines.append('  "health_score": {')
        lines.append(f'    "overall": {overall_score:.0f},')
        lines.append('    "components": {')
        lines.append('      "recency": "Not Available",')
        lines.append(f'      "frequency": {frequency_score:.0f},')
        lines.append(f'      "monetary": {monetary_score:.0f},')
        lines.append('      "satisfaction": "Not Available",')
        lines.append('      "engagement": "Not Available",')
        lines.append(f'      "payment_health": {payment_score:.0f}')
        lines.append('    },')
        lines.append('    "trend": "Not Available",')
        lines.append('    "trend_reason": "Not Available"')
        lines.append('  },')

        lines.append('  "churn_risk": {')
        if overall_score >= 70:
            risk_level = "low"
            probability = 0.15
        elif overall_score >= 50:
            risk_level = "medium"
            probability = 0.35
        else:
            risk_level = "high"
            probability = 0.60

        lines.append(f'    "risk_level": "{risk_level}",')
        lines.append(f'    "probability": {probability:.2f},')
        lines.append('    "primary_risk_factors": [],')
        lines.append('    "mitigating_factors": []')
        lines.append('  },')

        lines.append('  "upsell_opportunities": [],')
        lines.append('  "recommended_actions": []')
        lines.append("}")
        lines.append("```")
        lines.append("")
        lines.append("---")
        return lines

    def _generate_section_14(self, data: Dict) -> List[str]:
        """Generate Section 14: MMM Readiness."""
        lines = []
        lines.append("## 14. MMM Readiness — Marketing Mix Modeling Data Assessment")
        lines.append("")
        lines.append("**Source:** Computed from Refrences data availability")
        lines.append("")
        lines.append("```json")
        lines.append("{")
        lines.append('  "mmm_readiness": {')
        lines.append(f'    "assessed_date": "{datetime.now().strftime("%Y-%m-%d")}",')
        lines.append('    "brand_slug": "Not Available",')
        lines.append('    "assessor": "customer_intelligence_agent"')
        lines.append('  },')

        lines.append('  "overall_readiness": "partial",')
        lines.append('  "readiness_score": 45,')

        lines.append('  "data_availability": {')
        lines.append('    "sales_data": {')
        lines.append('      "available": false,')
        lines.append('      "notes": "Client sales data not provided"')
        lines.append('    },')

        lines.append('    "media_spend_data": {')
        lines.append('      "available": true,')
        lines.append('      "granularity": "transaction_level",')
        platforms = data.get('platforms_used', [])
        lines.append(f'      "channels_covered": {json.dumps(platforms)},')
        lines.append(f'      "history_months": "{data.get("total_transactions", 0)} transactions"')
        lines.append('    },')

        lines.append('    "creator_media_pressure": {')
        lines.append('      "available": true,')
        lines.append('      "granularity": "transaction_level",')
        lines.append('      "metrics": ["spend", "views", "impressions"]')
        lines.append('    }')
        lines.append('  },')

        lines.append('  "recommended_next_steps": [')
        lines.append('    "Request client sales/conversion data",')
        lines.append('    "Request full media mix breakdown",')
        lines.append('    "Enrich creator data with engagement metrics"')
        lines.append('  ],')

        lines.append('  "ideal_mmm_client": false,')
        lines.append('  "ideal_mmm_client_reason": "Missing sales data and full media mix",')
        lines.append('  "estimated_time_to_first_model": "3-4 months after data acquisition"')
        lines.append("}")
        lines.append("```")
        lines.append("")
        lines.append("---")
        return lines
