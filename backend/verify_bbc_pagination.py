import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from collectors.news_collector import BBCNewsCollector

async def test_pagination():
    # Setup logging to see what's happening
    logging.basicConfig(level=logging.INFO)
    
    collector = BBCNewsCollector()
    print("Starting test collection with pagination...")
    
    # Test with just one keyword to keep it fast
    keywords = ["flood"]
    # Set a higher limit to force pagination (each page usually has 10 results)
    max_per_keyword = 25
    
    items = await collector.collect(keywords=keywords, max_results_per_keyword=max_per_keyword)
    
    print(f"\nCollected {len(items)} items for '{keywords[0]}'")
    for i, item in enumerate(items[:5]):
        print(f"{i+1}. {item.title}")
    
    if len(items) > 10:
        print("\nSUCCESS: Pagination worked (gathered > 10 items)!")
    else:
        print("\nFAILURE or NO MORE DATA: Only gathered 10 or fewer items.")

if __name__ == "__main__":
    asyncio.run(test_pagination())
