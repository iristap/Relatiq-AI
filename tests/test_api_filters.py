import requests
import json

BASE_URL = "http://localhost:8000"

def test_sectors():
    print("Testing /sectors...")
    try:
        response = requests.get(f"{BASE_URL}/sectors")
        response.raise_for_status()
        sectors = response.json()
        print(f"Sectors found: {len(sectors)}")
        print(f"Sample sectors: {sectors[:5]}")
    except Exception as e:
        print(f"Failed to fetch sectors: {e}")

def test_articles():
    print("\nTesting /articles...")
    try:
        response = requests.get(f"{BASE_URL}/articles?limit=5")
        response.raise_for_status()
        articles = response.json()
        print(f"Articles found: {len(articles)}")
        if articles:
            print(f"Sample Article: {articles[0]}")
            if 'tier' in articles[0] and 'status' in articles[0]:
                print("SUCCESS: Article contains 'tier' and 'status'")
            else:
                print("FAILURE: Article missing 'tier' or 'status'")
    except Exception as e:
        print(f"Failed to fetch articles: {e}")

def test_network_filters():
    print("\nTesting /graph/network with filters...")
    try:
        # Test Date Filter
        params = {"date_range": "30d"}
        response = requests.get(f"{BASE_URL}/graph/network", params=params)
        print(f"Date Filter (30d) - Nodes: {len(response.json()['nodes'])}")

        # Test Tier Filter
        params = {"tiers": ["Tier A"]}
        response = requests.get(f"{BASE_URL}/graph/network", params=params)
        print(f"Tier Filter (Tier A) - Nodes: {len(response.json()['nodes'])}")

        # Test Entity Search
        params = {"entity_search": "Nvidia"}
        response = requests.get(f"{BASE_URL}/graph/network", params=params)
        print(f"Entity Search (Nvidia) - Nodes: {len(response.json()['nodes'])}")
        
    except Exception as e:
        print(f"Failed to fetch network: {e}")

if __name__ == "__main__":
    test_sectors()
    test_articles()
    test_network_filters()
