import httpx
import asyncio

async def check():
    headers = {
        "User-Agent": "ThermocultureResearchBot/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    keywords = [
        "climate change",
        "global warming",
        "net zero",
        "carbon",
        "flooding",
        "heatwave",
        "energy bills",
        "insulation",
    ]
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        for k in keywords:
            try:
                resp = await client.get('https://www.bbc.co.uk/search', params={'q': k, 'd': 'news_gnl'})
                print(f"BBC {k}: {resp.status_code}")
            except Exception as e:
                print(f"BBC {k}: Error {e}")

if __name__ == "__main__":
    asyncio.run(check())
