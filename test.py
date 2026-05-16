import os
import requests
from dotenv import load_dotenv

# Load the secrets from your .env file
load_dotenv()
API_KEY = os.getenv("IBM_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")

def test_watsonx_connection():
    print("1. Authenticating with IBM Cloud...")
    
    # Get the temporary token
    token_response = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": API_KEY}
    )
    
    if token_response.status_code != 200:
        print("Authentication Failed!")
        print(token_response.text)
        return
        
    access_token = token_response.json().get("access_token")
    print("Authentication Successful!\n")
    
    print("2. Sending simple prompt to Llama 3.3 70B Instruct...\n")

    # A very simple test prompt
    prompt = "Hi! Please reply with a short, simple greeting."
    
    url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    body = {
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 50,
            "repetition_penalty": 1.2
        },
        "model_id": "meta-llama/llama-3-3-70b-instruct",
        "project_id": PROJECT_ID
    }
    
    response = requests.post(url, headers=headers, json=body)
    
    if response.status_code == 200:
        result = response.json()['results'][0]['generated_text'].strip()
        print("="*60)
        print("SUCCESS! Here is the AI's Response:")
        print("="*60)
        print(result)
        print("="*60)
    else:
        print("API Call Failed!")
        print(response.text)

if __name__ == "__main__":
    test_watsonx_connection()