import asyncio
from httpx import AsyncClient
from app.main import app

async def test():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.get("/api/status")
        print(res.json())

asyncio.run(test())
