"""
Test fixtures for sample documents and queries.
"""

from langchain.schema import Document


# Sample documents for testing
SAMPLE_DOCUMENTS = [
    Document(
        page_content="""
        ANTI-MONEY LAUNDERING POLICY
        
        Transaction Monitoring Thresholds:
        - Unusual transaction volumes: >$10,000 daily
        - Rapid movement of funds
        - Transactions with high-risk jurisdictions
        
        Suspicious Activity Reporting (SAR):
        File SAR within 30 days of detection.
        """,
        metadata={
            "source": "aml_policy.pdf",
            "page": 1,
            "category": "compliance"
        }
    ),
    
    Document(
        page_content="""
        BASEL III CAPITAL REQUIREMENTS
        
        Minimum Capital Ratios:
        - Common Equity Tier 1 (CET1): 4.5%
        - Tier 1 Capital: 6%
        - Total Capital: 8%
        
        Capital Conservation Buffer: 2.5% CET1
        Total CET1 requirement: 7%
        """,
        metadata={
            "source": "basel_iii.pdf",
            "page": 1,
            "category": "compliance"
        }
    ),
    
    Document(
        page_content="""
        KYC PROCEDURES
        
        Required Customer Information:
        - Legal name
        - Date of birth
        - Address (verified via utility bill <90 days)
        - Tax Identification Number
        - Government-issued ID
        
        Risk Classification:
        - Low Risk: Domestic salaried employees
        - High Risk: Politically Exposed Persons (PEPs)
        """,
        metadata={
            "source": "kyc_procedures.pdf",
            "page": 1,
            "category": "compliance"
        }
    ),
]


# Sample test queries with expected answers
TEST_QUERIES = [
    {
        "question": "What is the AML transaction monitoring threshold?",
        "expected_keywords": ["$10,000", "daily", "unusual"],
        "relevant_docs": ["aml_policy.pdf"]
    },
    {
        "question": "What is the minimum CET1 ratio under Basel III?",
        "expected_keywords": ["4.5%", "CET1", "Common Equity"],
        "relevant_docs": ["basel_iii.pdf"]
    },
    {
        "question": "What documents are needed for KYC?",
        "expected_keywords": ["ID", "address", "utility bill"],
        "relevant_docs": ["kyc_procedures.pdf"]
    },
]


# Ground truth for evaluation
GROUND_TRUTH = {
    "What is the AML transaction monitoring threshold?": {
        "answer": "$10,000 daily for unusual transaction volumes",
        "sources": ["aml_policy.pdf"],
        "pages": [1]
    },
    "What is the minimum CET1 ratio under Basel III?": {
        "answer": "4.5% minimum, with 2.5% buffer totaling 7%",
        "sources": ["basel_iii.pdf"],
        "pages": [1]
    },
}