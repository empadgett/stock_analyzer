import requests

def get_robots_txt(url):
    try:
        response = requests.get(url + "/robots.txt")
        if response.status_code == 200:
            return response.text
        else:
            return f"Failed to fetch robots.txt. Status code: {response.status_code}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Fetch robots.txt for iShares
ishares_robots_txt = get_robots_txt("https://www.etfdb.com")
print(ishares_robots_txt)

