# FinanceInsights - Jira RAG Assistant

This sample demonstrates how to build a Retrieval-Augmented Generation (RAG) application for financial services that analyzes Jira tickets using Amazon Bedrock, S3 Vector Engine, and AI-powered insights for risk management and compliance analysis.

## Overview

FinanceInsights is a comprehensive solution that helps financial services organizations analyze their Jira tickets using natural language queries. The application leverages AWS services to provide intelligent insights into compliance risks, fraud patterns, and operational issues.

### Key Features

- **Jira Integration**: Automatic ticket extraction and synchronization
- **Hybrid Search**: S3 Vector Engine with direct semantic search fallback
- **Natural Language Queries**: Ask questions in plain English about your tickets
- **Serverless Architecture**: S3 Vector Engine for scalable vector storage
- **AI-Powered Analysis**: Amazon Bedrock for embeddings and intelligent responses
- **Financial Risk Intelligence**: Compliance, fraud, and regulatory risk analysis
- **Modern UI**: Streamlit interface with professional styling



## Architecture

```
Jira API → Data Pipeline → S3 Storage → S3 Vector Engine → Bedrock AI → Streamlit UI
```

- **Jira API**: Ticket extraction with business context enhancement
- **S3 Pipeline Bucket**: Raw ticket storage with financial metadata
- **S3 Vector Engine**: Serverless vector storage and similarity search
- **Amazon Bedrock**: Titan embeddings + Claude for analysis
- **Streamlit**: Interactive web interface

## Prerequisites

- AWS Account with Bedrock access (us-east-1 region)
- Jira Cloud instance with API access
- Python 3.8+
- AWS CLI configured with appropriate permissions

### AWS Services Used

- **Amazon Bedrock**: For embeddings generation and AI analysis
  - `amazon.titan-embed-text-v2:0` - Text embeddings
  - `anthropic.claude-3-sonnet-20240229-v1:0` - Text generation
- **Amazon S3**: For data storage and vector storage
- **S3 Vector Engine**: For serverless vector search (Preview)
- **AWS CLI**: For configuration and deployment

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- An AWS account with appropriate permissions
- AWS CLI configured with credentials
- Python 3.8 or later installed
- A Jira Cloud instance with API access
- Access to Amazon Bedrock models in us-east-1 region

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/AWS-Samples-GenAI-FSI/FinanceInsights-Jira-Bedrock-S3-Vectors.git
cd FinanceInsights-Jira-Bedrock-S3-Vectors
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
AWS_REGION=us-east-1

# Jira Configuration
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token
```

4. **Initialize the data pipeline**
```bash
python3 jira_pipeline.py
```

This will:
- ✅ Extract Jira tickets with financial context
- ✅ Create S3 buckets (`financial-jira-vectors-pipeline`, `financial-vectors-kb`)
- ✅ Generate embeddings using Bedrock Titan
- ✅ Store vectors in S3 Vector Engine
- ✅ Add financial services organizational context

5. **Launch the application**
```bash
streamlit run main_app.py
```

## Usage

### Example Queries

Once the application is running, you can ask questions such as:
- "What compliance risks need immediate attention?"
- "Show me fraud-related incidents this week"
- "Which trading system issues are trending?"
- "Find regulatory compliance violations"
- "What payment processing errors occurred?"

### How to Use
1. **Load Data**: Click "Load Pipeline Data" to fetch processed tickets
2. **Ask Questions**: Use natural language queries about your financial operations
3. **Get Analysis**: Receive AI-powered risk analysis with ticket recommendations
4. **Review Results**: Examine related tickets with urgency scoring and business impact

## Project Structure

```
├── main_app.py              # Streamlit web application
├── jira_pipeline.py          # Complete data pipeline
├── jira_bulk_loader.py       # Bulk ticket creation tool
├── kb_setup.py              # Knowledge base utilities
├── config/
│   └── financial_context.json # Industry-specific configuration
├── src/
│   ├── jira/jira_client.py   # Jira API integration
│   ├── vector_store/s3_vectors.py # S3 Vector Engine client
│   ├── bedrock/bedrock_helper.py # Bedrock utilities
│   └── utils/               # Text processing utilities
└── scripts/                 # Setup and utility scripts
```

## Configuration

### Customizing for Your Organization
Edit `config/financial_context.json` to customize for your organization:

```json
{
  "industry": "Financial Services",
  "app_name": "YourCompany Insights",
  "business_context": {
    "critical_systems": ["Payment processing", "Trading platforms"],
    "risk_indicators": {
      "high_priority_keywords": ["fraud", "compliance", "regulatory"]
    }
  }
}
```

### Setting up Jira API Access
1. Go to Jira → Account Settings → Security → API Tokens
2. Create new token
3. Add to `.env` file

## Advanced Features

### Generating Test Data
Generate test data for development:
```bash
python3 jira_bulk_loader.py
```

### Business Intelligence Features
The pipeline automatically adds financial context:
- **Urgency Scoring**: 1-10 based on regulatory/customer impact
- **Risk Assessment**: Marketplace, customer, compliance impact analysis
- **Escalation Patterns**: Automatic priority classification

## Troubleshooting

### Common Issues and Solutions

**S3 Vector Engine Access**
- Ensure S3 Vector Engine is available in us-east-1
- Check AWS permissions for S3 and Bedrock services

**Jira Connection**
- Verify API token and permissions
- Check Jira URL format (include https://)

**Bedrock Models**
- Request access to Titan and Claude models in AWS Console
- Ensure models are available in us-east-1 region

### Verification Commands
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Test Jira connection
python3 -c "from src.jira.jira_client import JiraClient; print('Jira OK')"
```

## Contributing

See [CONTRIBUTING](CONTRIBUTING.md) for more information.

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Use Cases

### Industry Applications
- **Banks**: Compliance monitoring, fraud detection, customer issue analysis
- **Fintech**: Payment system monitoring, regulatory compliance tracking
- **Trading Firms**: Market risk analysis, system performance monitoring
- **Insurance**: Claims processing, regulatory compliance, risk assessment

### Benefits
- **Regulatory Compliance**: Automated compliance risk detection
- **Operational Efficiency**: Quick identification of system issues
- **Risk Management**: Proactive fraud and security monitoring
- **Customer Impact**: Prioritized resolution of customer-affecting issues

## Additional Resources

- **Issues**: [GitHub Issues](https://github.com/AWS-Samples-GenAI-FSI/FinanceInsights-Jira-Bedrock-S3-Vectors/issues)
- **Documentation**: [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- **S3 Vectors**: [S3 Vector Engine Guide](https://docs.aws.amazon.com/s3/latest/userguide/vector-search.html)

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.