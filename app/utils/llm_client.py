# backend/app/utils/llm_client.py
import httpx
import json

class OllamaClient:
    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host
        self.timeout = 120.0  # Augmenté pour les modèles lourds

    async def generate(self, prompt: str, model: str = "llama3:latest") -> str:
        url = f"{self.host}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json"  # <--- C'EST LA CLÉ ! Force la sortie JSON valide
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
        except httpx.ConnectError:
            raise Exception("Impossible de se connecter à Ollama. Vérifiez qu'il tourne (ollama serve).")
        except Exception as e:
            raise Exception(f"Erreur lors de l'appel à Ollama : {str(e)}")