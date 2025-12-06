import requests
import json

BASE_URL = "http://localhost:8000"

def test_article_filters():
    print("Testing Article Filters...")

    # 1. Test Date Range
    print("\n1. Testing Date Range (7d)...")
    response = requests.get(f"{BASE_URL}/articles", params={"date_range": "7d"})
    if response.status_code == 200:
        articles = response.json()
        print(f"Found {len(articles)} articles in last 7 days.")
        # Verify dates (optional, but good)
    else:
        print(f"Failed: {response.status_code} - {response.text}")

    # 2. Test Tier Filter
    print("\n2. Testing Tier Filter (Tier A -> 'A')...")
    response = requests.get(f"{BASE_URL}/articles", params={"tiers": ["A"]})
    if response.status_code == 200:
        articles = response.json()
        print(f"Found {len(articles)} Tier A articles.")
        for a in articles[:3]:
            print(f"  - {a['title']} ({a['tier']})")
            if a['tier'] != 'A':
                print("  ERROR: Wrong tier returned!")
    else:
        print(f"Failed: {response.status_code} - {response.text}")

    # 3. Test Status Filter
    print("\n3. Testing Status Filter (Confirmed News)...")
    response = requests.get(f"{BASE_URL}/articles", params={"news_status": ["Confirmed News"]})
    if response.status_code == 200:
        articles = response.json()
        print(f"Found {len(articles)} Confirmed News articles.")
        for a in articles[:3]:
            print(f"  - {a['title']} ({a['status']})")
    else:
        print(f"Failed: {response.status_code} - {response.text}")

    # 4. Test Sector Filter (Technology)
    # Note: This depends on having data with sectors. If no data, it returns empty list, which is valid but hard to verify.
    print("\n4. Testing Sector Filter (Technology)...")
    response = requests.get(f"{BASE_URL}/articles", params={"sectors": ["Technology"]})
    if response.status_code == 200:
        articles = response.json()
        print(f"Found {len(articles)} articles related to Technology.")
        for a in articles[:3]:
            print(f"  - {a['title']}")
    else:
        print(f"Failed: {response.status_code} - {response.text}")

    # 5. Test Entity Search (OpenAI)
    print("\n5. Testing Entity Search (OpenAI)...")
    response = requests.get(f"{BASE_URL}/articles", params={"entity_search": "OpenAI"})
    if response.status_code == 200:
        articles = response.json()
        print(f"Found {len(articles)} articles mentioning OpenAI.")
        for a in articles[:3]:
            print(f"  - {a['title']}")
    else:
        print(f"Failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_article_filters()
