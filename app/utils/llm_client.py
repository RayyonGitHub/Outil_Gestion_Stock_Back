import httpx


class OllamaClient:
    def __init__(self, url: str = "http://localhost:11434/api/generate"):
        self.url = url

    async def generate(self, prompt: str, model: str = "llama3:latest"):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60.0
            )

            print("DEBUG Ollama raw response:", response.text)

            try:
                return response.json().get("response", "")
            except Exception:
                return response.text