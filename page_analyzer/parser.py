from bs4 import BeautifulSoup


def parse_html(response_text):
    soup = BeautifulSoup(response_text, 'html.parser')
    h1 = soup.h1.string if soup.h1 else None
    title = soup.title.string if soup.title else None
    description = None
    description_meta = soup.find('meta', attrs={'name': 'description'})
    if description_meta:
        description = description_meta.get('content')
    return h1, title, description
