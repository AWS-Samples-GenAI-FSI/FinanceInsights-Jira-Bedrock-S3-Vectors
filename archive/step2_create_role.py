import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

def step2_create_role():
    """Step 2: Create IAM role"""
    
    region = os.getenv('AWS_REGION', 'us-east-1')
    account_id = boto3.client('sts').get_caller_identity()['Account']
    iam = boto3.client('iam')
    
    # Read collection details
    with open('collection_details.txt', 'r') as f:
        lines = f.readlines()
        collection_name = lines[0].strip().split('=')[1]
        collection_id = lines[1].strip().split('=')[1]
    
    role_name = f'BedrockKB-{collection_name.split("-")[1]}'
    collection_arn = f"arn:aws:aoss:{region}:{account_id}:collection/{collection_id}"
    
    print(f"Step 2: Creating role {role_name}")
    
    # Create role
    iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "bedrock.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        })
    )
    
    # Add policy
    iam.put_role_policy(
        RoleName=role_name,
        PolicyName='BedrockKBPolicy',
        PolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": ["bedrock:InvokeModel"], "Resource": f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1"},
                {"Effect": "Allow", "Action": ["s3:GetObject", "s3:ListBucket"], "Resource": ["arn:aws:s3:::jira-tickets-s3-kb", "arn:aws:s3:::jira-tickets-s3-kb/*"]},
                {"Effect": "Allow", "Action": ["aoss:APIAccessAll"], "Resource": collection_arn}
            ]
        })
    )
    
    print("✅ Role created")
    
    # Update details file
    with open('collection_details.txt', 'a') as f:
        f.write(f"ROLE_NAME={role_name}\n")
        f.write(f"ROLE_ARN=arn:aws:iam::{account_id}:role/{role_name}\n")
    
    print("✅ Step 2 complete. Run step3_create_access_policy.py next")
    return role_name

if __name__ == "__main__":
    step2_create_role()