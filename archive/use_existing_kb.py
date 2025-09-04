import os
from dotenv import load_dotenv

load_dotenv()

def use_existing_kb():
    """Use your existing working KB"""
    
    kb_id = "VSLGATIOYT"  # Your existing S3 Vectors KB
    
    with open('.env', 'a') as f:
        f.write(f'\nKNOWLEDGE_BASE_ID={kb_id}\n')
    
    print(f"✅ Using existing KB: {kb_id}")
    print("✅ Ready to test: streamlit run app.py")

if __name__ == "__main__":
    use_existing_kb()