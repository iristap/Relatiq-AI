import requests
import json

# Fetch articles first to get valid titles
try:
    articles_resp = requests.get("http://localhost:8000/articles")
    if articles_resp.status_code == 200:
        articles = articles_resp.json()
        if articles:
            # Use the first few article titles
            titles = [a['title'] for a in articles[:3]]
            print(f"Testing with titles: {titles}")
            
            # Call analysis endpoint
            # Note: FastAPI expects list query params as ?article_titles=t1&article_titles=t2
            params = [('article_titles', t) for t in titles]
            response = requests.get("http://localhost:8000/analysis/companies", params=params)
            
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                print("Success!")
                print(json.dumps(response.json(), indent=2))
            else:
                print(f"Failed: {response.text}")
        else:
            print("No articles found to test with.")
    else:
        print("Failed to fetch articles.")
except Exception as e:
    print(f"Error: {e}")
