import httpx
from src.ecommerce_mcp.config import settings

class EcommerceMCPClient:
    def __init__(self, base_url: str = settings.fastapi_base_url):
        self.base_url = base_url
        self.timeout = httpx.Timeout(10.0, connect=5.0,read=30.0,pool=5.0)


    async def get(self, endpoint: str, params: dict = None) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()

    async def post(self, endpoint: str, data: dict = None) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()
    async def put(self, endpoint: str, data: dict = None) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.put(endpoint, json=data)
            response.raise_for_status()
            return response.json()

    async def delete(self, endpoint: str) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.delete(endpoint)
            response.raise_for_status()
            return response.json()


api_client = EcommerceMCPClient()
