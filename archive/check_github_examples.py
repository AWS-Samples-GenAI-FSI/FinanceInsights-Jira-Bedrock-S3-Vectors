import requests
import json

def search_github_examples():
    """Search GitHub for Bedrock Knowledge Base creation examples"""
    
    queries = [
        "bedrock create_knowledge_base opensearch serverless",
        "bedrock-agent create_knowledge_base python",
        "aws bedrock knowledge base programmatic creation",
        "opensearch serverless bedrock knowledge base boto3"
    ]
    
    for query in queries:
        print(f"\n🔍 Searching: {query}")
        
        # GitHub API search
        url = f"https://api.github.com/search/code?q={query.replace(' ', '+')}&sort=indexed&order=desc"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('items', [])[:3]:  # Top 3 results
                    print(f"📁 {item['repository']['full_name']}")
                    print(f"   {item['html_url']}")
                    print(f"   {item['name']}")
                    
            else:
                print(f"   ❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    search_github_examples()