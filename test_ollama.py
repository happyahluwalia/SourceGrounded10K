import requests
import json

def test_ollama():
    """Test Ollama API connection."""
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": "gemma3:1b",
        "prompt": "Explain RAG in one sentence.",
        "stream": False
    }
    
    print("Testing Ollama connection...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Ollama is working!")
        print(f"\nResponse: {result['response']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_ollama()