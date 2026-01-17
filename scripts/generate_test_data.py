"""Generate synthetic FinTech documents for testing and demonstration.

Creates realistic documents covering:
- Compliance policies (AML, KYC, Basel III)
- Risk management frameworks
- Product specifications
- Regulatory updates.
"""

import secrets
from datetime import datetime
from pathlib import Path

COMPLIANCE_CONTENT = {
    "AML Policy": """
ANTI-MONEY LAUNDERING (AML) POLICY
Version 3.2 | Effective Date: January 2024

1. OVERVIEW
This policy establishes our framework for preventing money laundering and terrorist financing.

2. CUSTOMER DUE DILIGENCE (CDD)
All customers must undergo risk-based due diligence:
- Standard CDD: Identity verification, address confirmation
- Enhanced CDD: Source of wealth, purpose of account
- Simplified CDD: Low-risk customers (government entities)

3. TRANSACTION MONITORING
Automated systems monitor for suspicious patterns:
- Unusual transaction volumes (>$10,000 daily)
- Rapid movement of funds
- Transactions with high-risk jurisdictions
- Structured deposits (smurfing)

4. SUSPICIOUS ACTIVITY REPORTING (SAR)
Threshold: File SAR within 30 days of detection
Reportable activities:
- Structuring to avoid reporting requirements
- Unexplained wire transfers to offshore accounts
- Cash deposits inconsistent with business profile

5. SANCTIONS SCREENING
Real-time screening against:
- OFAC SDN List
- UN Sanctions List
- EU Consolidated List
Screen frequency: Transaction initiation, daily customer list refresh

6. RECORD RETENTION
- CDD documents: 5 years post-relationship
- Transaction records: 5 years
- SAR documentation: 5 years
""",
    "Basel III Capital Requirements": """
BASEL III CAPITAL ADEQUACY FRAMEWORK
Internal Risk Management Document | 2024

1. MINIMUM CAPITAL RATIOS
Common Equity Tier 1 (CET1): 4.5%
Tier 1 Capital: 6%
Total Capital: 8%

2. CAPITAL CONSERVATION BUFFER
Additional 2.5% CET1 buffer
Total CET1 requirement: 7%

3. COUNTERCYCLICAL BUFFER
Range: 0% to 2.5%
Current setting: 1.0% (reviewed quarterly)

4. LEVERAGE RATIO
Minimum: 3%
Our target: 5%

5. RISK-WEIGHTED ASSETS (RWA) CALCULATION
Credit Risk: Standardized Approach
- Corporate exposures: 100% risk weight
- Residential mortgages: 35% risk weight
- Sovereign exposures: 0-150% (credit rating dependent)

Market Risk: Internal Models Approach (IMA)
- Value at Risk (VaR): 99% confidence, 10-day holding period
- Stressed VaR: Historical stress scenarios

Operational Risk: Standardized Approach
- Gross income-based calculation
- 15% of average positive gross income

6. CAPITAL PLANNING
Annual ICAAP (Internal Capital Adequacy Assessment Process)
Stress testing: Baseline, adverse, severely adverse scenarios
Target buffer: Maintain 200bp above regulatory minimum
""",
    "KYC Procedures": """
KNOW YOUR CUSTOMER (KYC) PROCEDURES
Compliance Manual | Updated Q1 2024

1. CUSTOMER IDENTIFICATION PROGRAM (CIP)
Required information:
- Legal name
- Date of birth / Incorporation date
- Address (verified via utility bill <90 days)
- Tax Identification Number (TIN/EIN)
- Government-issued ID

2. BENEFICIAL OWNERSHIP
For legal entities, identify individuals owning ≥25%:
- Name, DOB, address
- Ownership percentage
- Control structure documentation

3. RISK CLASSIFICATION
Low Risk:
- Domestic salaried employees
- Established businesses (>5 years)
- Low transaction volumes (<$50k monthly)

Medium Risk:
- Self-employed individuals
- Foreign nationals (non-PEP)
- Cash-intensive businesses

High Risk:
- Politically Exposed Persons (PEPs)
- Money service businesses
- High-risk jurisdictions (FATF list)

4. REFRESH REQUIREMENTS
Low risk: Every 3 years
Medium risk: Every 2 years
High risk: Annual refresh

5. ENHANCED DUE DILIGENCE (EDD)
Triggers:
- Transaction volume increase >300%
- Adverse media mentions
- Country risk elevation

EDD Measures:
- Source of wealth documentation
- Senior management approval
- Increased monitoring frequency
""",
}

RISK_CONTENT = {
    "Market Risk Framework": """
MARKET RISK MANAGEMENT FRAMEWORK
Risk Department | Version 2.1

1. RISK APPETITE
Maximum Value at Risk (VaR): $50M (99% confidence)
Maximum loss in stress scenario: $200M
Position concentration limits: 10% per issuer

2. VAR METHODOLOGY
Historical Simulation: 250-day lookback
Confidence level: 99%
Holding period: 10 days
Back-testing: Daily P&L vs VaR

3. STRESS TESTING
Scenarios:
- 2008 Financial Crisis replay
- Interest rate shock (+200bp)
- Credit spread widening (+300bp)
- Equity market crash (-30%)

Frequency: Monthly
Escalation: Breaches reported to Risk Committee

4. LIMITS FRAMEWORK
Desk-level VaR limits
Sector concentration limits
Country exposure limits
Duration limits (Fixed Income)

5. MARKET RISK REPORTING
Daily: VaR, P&L, limit utilization
Weekly: Risk factor decomposition
Monthly: Stress test results, backtesting
""",
    "Credit Risk Policy": """
CREDIT RISK MANAGEMENT POLICY
Version 4.0 | Effective March 2024

1. CREDIT APPROVAL AUTHORITY
Tier 1 ($0-$5M): Credit Officer
Tier 2 ($5M-$25M): Senior Credit Officer + Risk
Tier 3 (>$25M): Credit Committee

2. CREDIT SCORING
Internal rating scale: 1-10
1-3: Investment grade
4-6: Sub-investment grade
7-9: Distressed
10: Default

Rating drivers:
- Financial ratios (leverage, coverage)
- Industry outlook
- Management quality
- Collateral adequacy

3. PROBABILITY OF DEFAULT (PD)
Rating 1: 0.05%
Rating 3: 0.50%
Rating 5: 3.00%
Rating 7: 15.00%

4. LOSS GIVEN DEFAULT (LGD)
Secured: 25-40%
Unsecured: 60-75%
Subordinated: 85-95%

5. EXPECTED CREDIT LOSS (ECL)
ECL = EAD × PD × LGD
12-month ECL: Stage 1 loans
Lifetime ECL: Stage 2/3 loans

6. CONCENTRATION LIMITS
Single obligor: 10% of capital
Industry: 25% of portfolio
Geographic: 40% single country (ex-domestic)
""",
}

PRODUCT_CONTENT = {
    "Trading Platform Specification": """
ELECTRONIC TRADING PLATFORM
Product Requirements Document | v3.0

1. FUNCTIONAL REQUIREMENTS

Order Types:
- Market orders
- Limit orders
- Stop-loss orders
- Fill-or-kill (FOK)
- Good-till-cancel (GTC)

Asset Classes:
- Equities (US, European, Asian)
- Fixed Income (Government, Corporate)
- FX Spot & Forwards
- Commodities futures

2. PERFORMANCE REQUIREMENTS
Order latency: <100ms (p95)
Market data latency: <50ms
System uptime: 99.95%
Concurrent users: 10,000

3. RISK CONTROLS
Pre-trade checks:
- Credit limit verification
- Position limit enforcement
- Restricted securities screening
- Best execution verification

4. REGULATORY COMPLIANCE
MiFID II: Transaction reporting
Reg NMS: Order protection rule
Dodd-Frank: Swap reporting

5. SECURITY
TLS 1.3 encryption
Multi-factor authentication
API rate limiting: 1000 req/min
Session timeout: 15 minutes inactivity
""",
    "Digital Wallet Features": """
DIGITAL WALLET PRODUCT SPECIFICATION
Release 2.5 | Q1 2024

1. CORE FEATURES
- Multi-currency support (USD, EUR, GBP, JPY)
- Instant P2P transfers
- Bill payment integration
- Merchant payment acceptance
- Loyalty program integration

2. TRANSACTION LIMITS
Daily send limit: $10,000
Monthly send limit: $50,000
Per-transaction max: $5,000

KYC-enhanced users:
Daily: $25,000
Monthly: $100,000
Per-transaction: $10,000

3. FEE STRUCTURE
P2P transfers: Free (same currency)
Currency conversion: 1.5% spread
ATM withdrawal: $2.50 + 2%
Merchant payments: Free to consumer

4. SECURITY FEATURES
- Biometric authentication (Touch/Face ID)
- Device binding
- Transaction notifications (real-time)
- Suspicious activity alerts
- Card freeze/unfreeze

5. REGULATORY COMPLIANCE
- E-money institution license (EU)
- State money transmitter licenses (US)
- PSD2 strong customer authentication
- GDPR data protection
""",
}


def generate_documents(output_dir: Path, num_docs_per_category: int = 5):
    """
    Generate synthetic documents.

    Args:
        output_dir: Directory to save documents
        num_docs_per_category: Number of documents per category
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    categories = {
        "compliance": COMPLIANCE_CONTENT,
        "risk": RISK_CONTENT,
        "products": PRODUCT_CONTENT,
    }

    total_generated = 0

    for category, content_dict in categories.items():
        category_dir = output_dir / category
        category_dir.mkdir(exist_ok=True)

        for doc_name, content in content_dict.items():
            # Generate base document
            filename = f"{doc_name.replace(' ', '_').lower()}.txt"
            filepath = category_dir / filename

            with open(filepath, "w") as f:
                f.write(content)

            print(f"✓ Generated: {filepath}")
            total_generated += 1

            # Generate variations with slight modifications
            for i in range(num_docs_per_category - 1):
                variant_name = f"{doc_name.replace(' ', '_').lower()}_v{i+2}.txt"
                variant_path = category_dir / variant_name

                # Add version-specific content
                variant_content = content + f"\n\n--- VERSION {i+2} NOTES ---\n"
                variant_content += f"Last reviewed: {datetime.now().strftime('%B %Y')}\n"
                # Non-security-sensitive variation using cryptographically secure choice
                variant_content += f"Minor updates to section {secrets.choice(range(1, 7))}\n"

                with open(variant_path, "w") as f:
                    f.write(variant_content)

                print(f"✓ Generated: {variant_path}")
                total_generated += 1

    # Generate README
    readme_content = f"""
# FinTech Test Documents

This directory contains {total_generated} synthetic documents for testing the RAG system.

## Categories

### Compliance ({len(COMPLIANCE_CONTENT) * num_docs_per_category} docs)
- AML Policy
- Basel III Capital Requirements
- KYC Procedures

### Risk ({len(RISK_CONTENT) * num_docs_per_category} docs)
- Market Risk Framework
- Credit Risk Policy

### Products ({len(PRODUCT_CONTENT) * num_docs_per_category} docs)
- Trading Platform Specification
- Digital Wallet Features

## Usage

Ingest these documents:
```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \\
  -H "Content-Type: application/json" \\
  -d '{{"directory_path": "./data/raw", "recursive": true}}'
```

## Sample Queries

- "What are our AML transaction monitoring thresholds?"
- "What is the minimum CET1 ratio under Basel III?"
- "What are the KYC refresh requirements for high-risk customers?"
- "What is our maximum Value at Risk limit?"
- "What are the transaction limits for the digital wallet?"

Generated: {datetime.now().isoformat()}
"""

    readme_path = output_dir / "README.md"
    with open(readme_path, "w") as f:
        f.write(readme_content)

    print(f"\n{'='*60}")
    print(f"✓ Successfully generated {total_generated} documents")
    print(f"✓ Output directory: {output_dir.absolute()}")
    print(f"{'='*60}")


if __name__ == "__main__":
    # Generate documents
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    generate_documents(data_dir, num_docs_per_category=3)
