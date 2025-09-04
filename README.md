# 🏦 FinanceInsights - Jira RAG Assistant

A powerful RAG (Retrieval-Augmented Generation) application for financial services that analyzes Jira tickets using Amazon Bedrock, S3 Vector Engine, and AI-powered insights for risk management and compliance analysis.

![FinanceInsights Demo](https://img.shields.io/badge/AWS-Bedrock-orange) ![S3 Vectors](https://img.shields.io/badge/S3-Vectors-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-App-red)

## 🚀 Features

- **🎫 Jira Integration**: Automatic ticket extraction and synchronization
- **🔍 Hybrid Search**: S3 Vector Engine + Direct semantic search fallback
- **💬 Natural Language Queries**: Ask questions in plain English about your tickets
- **☁️ Serverless Architecture**: S3 Vector Engine for scalable vector storage
- **🤖 AI-Powered Analysis**: Amazon Bedrock for embeddings and intelligent responses
- **📊 Financial Risk Intelligence**: Compliance, fraud, and regulatory risk analysis
- **🎨 Modern UI**: Stylish interface with professional typography

## 🏗️ Architecture

```
Jira API → Data Pipeline → S3 Storage → S3 Vector Engine → Bedrock AI → Streamlit UI
```

- **Jira API**: Ticket extraction with business context enhancement
- **S3 Pipeline Bucket**: Raw ticket storage with financial metadata
- **S3 Vector Engine**: Serverless vector storage and similarity search
- **Amazon Bedrock**: Titan embeddings + Claude for analysis
- **Streamlit**: Interactive web interface

## 📋 Prerequisites

- AWS Account with Bedrock access (us-east-1 region)
- Jira Cloud instance with API access
- Python 3.8+
- AWS CLI configured with appropriate permissions

### Required AWS Services
- Amazon Bedrock (Titan Embeddings, Claude models)
- S3 Vector Engine (Preview)
- S3 Storage

## 🛠️ Quick Setup

### 1. Clone Repository
```bash
git clone https://github.com/AWS-Samples-GenAI-FSI/FinanceInsights-Jira-Bedrock-S3-Vectors.git
cd FinanceInsights-Jira-Bedrock-S3-Vectors
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
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

### 4. Setup Data Pipeline
```bash
python3 jira_pipeline.py
```

This will:
- ✅ Extract Jira tickets with financial context
- ✅ Create S3 buckets (`financial-jira-vectors-pipeline`, `financial-vectors-kb`)
- ✅ Generate embeddings using Bedrock Titan
- ✅ Store vectors in S3 Vector Engine
- ✅ Add financial services organizational context

### 5. Launch Application
```bash
streamlit run main_app.py
```

## 🎯 Usage

### Sample Financial Services Questions
- "What compliance risks need immediate attention?"
- "Show me fraud-related incidents this week"
- "Which trading system issues are trending?"
- "Find regulatory compliance violations"
- "What payment processing errors occurred?"

### Application Workflow
1. **Load Data**: Click "Load Pipeline Data" to fetch processed tickets
2. **Ask Questions**: Use natural language queries about your financial operations
3. **Get Analysis**: Receive AI-powered risk analysis with ticket recommendations
4. **Review Results**: Examine related tickets with urgency scoring and business impact

## 📁 Project Structure

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

## ⚙️ Configuration

### Financial Context Customization
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

### Jira API Token Setup
1. Go to Jira → Account Settings → Security → API Tokens
2. Create new token
3. Add to `.env` file

## 🔧 Advanced Features

### Bulk Data Loading
Generate test data for development:
```bash
python3 jira_bulk_loader.py
```

### Custom Business Logic
The pipeline automatically adds financial context:
- **Urgency Scoring**: 1-10 based on regulatory/customer impact
- **Risk Assessment**: Marketplace, customer, compliance impact analysis
- **Escalation Patterns**: Automatic priority classification

## 🚨 Troubleshooting

### Common Issues

**S3 Vector Engine Access**
- Ensure S3 Vector Engine is available in us-east-1
- Check AWS permissions for S3 and Bedrock services

**Jira Connection**
- Verify API token and permissions
- Check Jira URL format (include https://)

**Bedrock Models**
- Request access to Titan and Claude models in AWS Console
- Ensure models are available in us-east-1 region

### Error Resolution
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Test Jira connection
python3 -c "from src.jira.jira_client import JiraClient; print('Jira OK')"
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏢 Use Cases

### Financial Services Applications
- **Banks**: Compliance monitoring, fraud detection, customer issue analysis
- **Fintech**: Payment system monitoring, regulatory compliance tracking
- **Trading Firms**: Market risk analysis, system performance monitoring
- **Insurance**: Claims processing, regulatory compliance, risk assessment

### Key Benefits
- **Regulatory Compliance**: Automated compliance risk detection
- **Operational Efficiency**: Quick identification of system issues
- **Risk Management**: Proactive fraud and security monitoring
- **Customer Impact**: Prioritized resolution of customer-affecting issues

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/AWS-Samples-GenAI-FSI/FinanceInsights-Jira-Bedrock-S3-Vectors/issues)
- **Documentation**: [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- **S3 Vectors**: [S3 Vector Engine Guide](https://docs.aws.amazon.com/s3/latest/userguide/vector-search.html)

---

**Built with ❤️ for Financial Services by AWS**