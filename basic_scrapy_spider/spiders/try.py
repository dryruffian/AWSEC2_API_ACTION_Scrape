import requests
from bs4 import BeautifulSoup


def fetch_content_by_id(url, content_id):
    try:
        # Send a GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the webpage content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the element with the given ID
        content = soup.find(id=content_id)

        if content:
            return content.get_text(strip=True)
        else:
            return f"No element found with ID: {content_id}"

    except requests.RequestException as e:
        return f"An error occurred while fetching the URL: {e}"


# Example usage
url = 'https://example.com'
content_id = 'example_id'
print(fetch_content_by_id(url, content_id))