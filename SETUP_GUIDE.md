# 🚀 Complete Setup Guide

## Step-by-Step Instructions

### Prerequisites Checklist
- [ ] AWS Account with admin access
- [ ] Jira Cloud instance
- [ ] Python 3.8+ installed
- [ ] Git installed

### 1. AWS Setup (5 minutes)

#### Enable Bedrock Models
1. Go to AWS Console → Bedrock → Model Access
2. Request access to:
   - `amazon.titan-embed-text-v2:0`
   - `anthropic.claude-3-sonnet-20240229-v1:0`
3. Wait for approval (usually instant)

#### Configure AWS CLI
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key  
# Default region: us-east-1
# Default output format: json
```

### 2. Jira Setup (3 minutes)

#### Get API Token
1. Login to Jira → Profile → Account Settings
2. Security → Create and manage API tokens
3. Create token → Copy token value

#### Find Your Jira URL
- Format: `https://yourcompany.atlassian.net`
- Get from browser address bar when logged into Jira

### 3. Application Setup (2 minutes)

```bash
# Clone repository
git clone https://github.com/AWS-Samples-GenAI-FSI/FinanceInsights-Jira-Bedrock-S3-Vectors.git
cd FinanceInsights-Jira-Bedrock-S3-Vectors

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
```

#### Edit .env file:
```env
AWS_REGION=us-east-1

JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=paste-your-token-here
```

### 4. Initialize Data Pipeline (5 minutes)

```bash
# Run the complete pipeline
python3 jira_pipeline.py
```

**What this does:**
- Extracts your Jira tickets
- Creates AWS S3 buckets
- Generates AI embeddings
- Sets up vector search
- Adds financial context

### 5. Launch Application (1 minute)

```bash
streamlit run main_app.py
```

**Your app will open at:** `http://localhost:8501`

### 6. First Use

1. Click "Load Pipeline Data" in sidebar
2. Try sample question: "What compliance risks need attention?"
3. Explore the AI-powered analysis!

## Troubleshooting

### Issue: "NoSuchBucket" Error
**Solution:** Run the pipeline first: `python3 jira_pipeline.py`

### Issue: Bedrock Access Denied
**Solution:** 
1. Check model access in AWS Console
2. Verify region is us-east-1
3. Ensure AWS credentials have Bedrock permissions

### Issue: Jira Connection Failed
**Solution:**
1. Verify Jira URL format (include https://)
2. Check API token is correct
3. Ensure email matches Jira account

### Issue: No Tickets Found
**Solution:**
1. Check if you have tickets in Jira
2. Verify Jira permissions allow API access
3. Try running: `python3 jira_bulk_loader.py` to create test data

## Customization

### For Your Company
Edit `config/financial_context.json`:
- Change `app_name` to your company name
- Update `critical_systems` for your infrastructure
- Modify `sample_questions` for your use cases

### Different Industries
The app is designed for financial services but can be adapted:
- Banking: Focus on compliance and fraud
- Fintech: Emphasize payment processing
- Trading: Highlight market risk systems
- Insurance: Prioritize claims and regulatory issues

## Next Steps

1. **Customize**: Update configuration for your organization
2. **Scale**: Add more Jira projects to the pipeline
3. **Integrate**: Connect to your existing monitoring systems
4. **Extend**: Add custom business logic for your specific needs

## Support

- **GitHub Issues**: Report bugs and request features
- **AWS Documentation**: Bedrock and S3 Vector guides
- **Community**: Share your customizations and improvements