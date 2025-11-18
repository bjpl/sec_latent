"""
Data Fixtures
Sample filing data and test datasets
"""
from typing import Dict, Any, List


def sample_10k_filing() -> Dict[str, Any]:
    """Full 10-K filing sample for testing"""
    return {
        "cik": "0000789019",
        "company_name": "Microsoft Corporation",
        "form_type": "10-K",
        "filing_date": "2024-07-31",
        "fiscal_year_end": "0630",
        "accession_number": "0000789019-24-000456",
        "file_number": "001-37845",
        "text_content": """
        UNITED STATES SECURITIES AND EXCHANGE COMMISSION
        ANNUAL REPORT PURSUANT TO SECTION 13 OR 15(d) OF THE SECURITIES EXCHANGE ACT OF 1934

        For the fiscal year ended June 30, 2024

        ITEM 1. BUSINESS

        Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions.

        ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS

        Revenue increased 15% year-over-year to $245 billion, driven by cloud growth.
        Intelligent Cloud revenue grew 21% to $112 billion.
        Productivity and Business Processes revenue increased 12% to $82 billion.

        Operating income increased 20% to $110 billion, reflecting improved margins.
        Net income was $88 billion, up 18% from prior year.

        Cash flow from operations was $118 billion, up 25%.
        Free cash flow reached $98 billion, up 28%.

        ITEM 1A. RISK FACTORS

        We face intense competition across all our markets.
        Cybersecurity threats and cyberattacks could adversely affect our business.
        Government regulation of data privacy and security continues to evolve.
        Our international operations subject us to various legal and regulatory requirements.
        """,
        "sections": {
            "business": "Microsoft develops software and cloud services...",
            "risk_factors": "Competition, cybersecurity, regulatory risks...",
            "md_and_a": "Revenue up 15%, cloud growing 21%...",
            "financial_statements": "Balance sheet, income statement...",
            "exhibits": "Material contracts and agreements..."
        },
        "tables": [
            {
                "index": 0,
                "type": "income_statement",
                "fiscal_year": 2024,
                "data": [
                    ["Revenue", "245000000000", "213000000000"],
                    ["Cost of Revenue", "82000000000", "73000000000"],
                    ["Gross Profit", "163000000000", "140000000000"],
                    ["Operating Income", "110000000000", "92000000000"],
                    ["Net Income", "88000000000", "75000000000"]
                ],
                "headers": ["Item", "2024", "2023"]
            },
            {
                "index": 1,
                "type": "balance_sheet",
                "data": [
                    ["Total Assets", "512000000000"],
                    ["Total Liabilities", "245000000000"],
                    ["Total Equity", "267000000000"]
                ],
                "headers": ["Item", "2024"]
            },
            {
                "index": 2,
                "type": "cash_flow",
                "data": [
                    ["Operating Cash Flow", "118000000000"],
                    ["Investing Cash Flow", "-35000000000"],
                    ["Financing Cash Flow", "-65000000000"]
                ],
                "headers": ["Item", "2024"]
            }
        ],
        "metadata": {
            "page_count": 125,
            "word_count": 65000,
            "table_count": 45,
            "section_count": 15
        }
    }


def sample_10q_filing() -> Dict[str, Any]:
    """10-Q quarterly filing sample"""
    return {
        "cik": "0000789019",
        "company_name": "Microsoft Corporation",
        "form_type": "10-Q",
        "filing_date": "2024-10-31",
        "fiscal_period": "Q1",
        "accession_number": "0000789019-24-000789",
        "text_content": """
        QUARTERLY REPORT PURSUANT TO SECTION 13 OR 15(d)

        For the quarterly period ended September 30, 2024

        MANAGEMENT'S DISCUSSION AND ANALYSIS

        Q1 revenue was $65 billion, up 16% year-over-year.
        Cloud revenue grew 22% to $30 billion.
        Operating income increased 19% to $28 billion.
        """,
        "sections": {
            "md_and_a": "Q1 revenue up 16%, cloud growing...",
            "financial_statements": "Unaudited financial statements...",
            "controls": "Disclosure controls and procedures..."
        },
        "tables": [
            {
                "index": 0,
                "type": "income_statement",
                "data": [
                    ["Revenue", "65000000000", "56000000000"],
                    ["Operating Income", "28000000000", "23500000000"],
                    ["Net Income", "22000000000", "18500000000"]
                ],
                "headers": ["Item", "Q1 2025", "Q1 2024"]
            }
        ],
        "metadata": {
            "page_count": 45,
            "word_count": 22000,
            "table_count": 12,
            "section_count": 8
        }
    }


def sample_signals_full() -> Dict[str, List[Dict[str, Any]]]:
    """Complete set of 150 signals"""
    return {
        "financial": [
            {"name": "revenue_growth_yoy", "value": 0.15, "confidence": 0.95},
            {"name": "revenue_growth_qoq", "value": 0.04, "confidence": 0.93},
            {"name": "gross_margin", "value": 0.665, "confidence": 0.97},
            {"name": "operating_margin", "value": 0.449, "confidence": 0.96},
            {"name": "net_margin", "value": 0.359, "confidence": 0.95},
            {"name": "roa", "value": 0.172, "confidence": 0.94},
            {"name": "roe", "value": 0.330, "confidence": 0.93},
            {"name": "current_ratio", "value": 1.85, "confidence": 0.96},
            {"name": "quick_ratio", "value": 1.65, "confidence": 0.95},
            {"name": "debt_to_equity", "value": 0.42, "confidence": 0.97},
            {"name": "interest_coverage", "value": 15.2, "confidence": 0.94},
            {"name": "cash_flow_operating", "value": 118000000000, "confidence": 0.98},
            {"name": "free_cash_flow", "value": 98000000000, "confidence": 0.97},
            {"name": "capex_ratio", "value": 0.17, "confidence": 0.95},
            {"name": "working_capital", "value": 45000000000, "confidence": 0.96},
            # ... 35 more financial signals
        ] + [{"name": f"financial_{i}", "value": 0.75, "confidence": 0.90} for i in range(35)],
        "sentiment": [
            {"name": "md_and_a_sentiment", "value": 0.72, "confidence": 0.85},
            {"name": "forward_looking_sentiment", "value": 0.68, "confidence": 0.82},
            {"name": "risk_section_tone", "value": -0.35, "confidence": 0.80},
            {"name": "management_confidence", "value": 0.75, "confidence": 0.83},
            {"name": "keyword_sentiment", "value": 0.65, "confidence": 0.88},
            {"name": "comparative_sentiment", "value": 0.58, "confidence": 0.81},
            {"name": "outlook_sentiment", "value": 0.70, "confidence": 0.84},
            {"name": "challenge_mentions", "value": 0.25, "confidence": 0.86},
            {"name": "opportunity_mentions", "value": 0.80, "confidence": 0.87},
            {"name": "growth_language", "value": 0.85, "confidence": 0.89},
            # ... 20 more sentiment signals
        ] + [{"name": f"sentiment_{i}", "value": 0.65, "confidence": 0.85} for i in range(20)],
        "risk": [
            {"name": "market_risk_score", "value": 0.55, "confidence": 0.88},
            {"name": "regulatory_risk_score", "value": 0.62, "confidence": 0.86},
            {"name": "operational_risk_score", "value": 0.48, "confidence": 0.87},
            {"name": "financial_risk_score", "value": 0.35, "confidence": 0.90},
            {"name": "litigation_risk", "value": 0.40, "confidence": 0.85},
            {"name": "cybersecurity_risk", "value": 0.70, "confidence": 0.89},
            {"name": "competition_intensity", "value": 0.85, "confidence": 0.91},
            {"name": "regulatory_mentions", "value": 45, "confidence": 0.92},
            {"name": "legal_proceedings", "value": 12, "confidence": 0.88},
            {"name": "risk_factor_count", "value": 38, "confidence": 0.95},
            # ... 30 more risk signals
        ] + [{"name": f"risk_{i}", "value": 0.55, "confidence": 0.88} for i in range(30)],
        "management": [
            {"name": "management_changes", "value": 1, "confidence": 0.95},
            {"name": "board_changes", "value": 0, "confidence": 0.93},
            {"name": "compensation_growth", "value": 0.08, "confidence": 0.87},
            {"name": "insider_transactions", "value": 25, "confidence": 0.89},
            {"name": "executive_tenure_avg", "value": 7.5, "confidence": 0.92},
            {"name": "board_independence", "value": 0.85, "confidence": 0.90},
            {"name": "diversity_score", "value": 0.42, "confidence": 0.86},
            {"name": "succession_planning", "value": 0.75, "confidence": 0.83},
            {"name": "strategic_vision_clarity", "value": 0.82, "confidence": 0.84},
            {"name": "execution_track_record", "value": 0.88, "confidence": 0.87},
            # ... 20 more management signals
        ] + [{"name": f"management_{i}", "value": 0.70, "confidence": 0.87} for i in range(20)]
    }


def sample_complex_filing() -> Dict[str, Any]:
    """Complex filing with edge cases"""
    return {
        "cik": "0001234567",
        "company_name": "Complex Industries Inc.",
        "form_type": "10-K",
        "filing_date": "2024-12-31",
        "text_content": "A" * 100000,  # Very long content
        "sections": {f"section_{i}": f"Content {i}" for i in range(50)},  # Many sections
        "tables": [{"index": i, "data": []} for i in range(100)],  # Many tables
        "metadata": {
            "page_count": 500,
            "word_count": 250000,
            "table_count": 100,
            "section_count": 50,
            "complexity_score": 0.95
        }
    }
