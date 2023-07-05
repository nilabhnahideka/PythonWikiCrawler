import requests
from bs4 import BeautifulSoup
import sqlite3

conn = sqlite3.connect('german_words.db')
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS german_words (word TEXT, article TEXT)")

def fetch_german_words():
    url = "https://de.wiktionary.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "allpages",
        "apnamespace": "0",
        "apfrom": get_resume_word()
    }

    crawled_count = 0

    try:
        print("Crawler running...")
        while True:
            response = requests.get(url, params=params)
            data = response.json()
            words = data['query']['allpages']

            for word in words:
                article = extract_first_article(word['title'])
                store_word(word['title'], article)
                crawled_count += 1

            if 'continue' not in data:
                break

            params['apcontinue'] = data['continue']['apcontinue']
            
    except KeyboardInterrupt:
        total_crawled_count = get_total_crawled_count()
        print(f"Crawler paused. Words crawled: {crawled_count}, Total words crawled: {total_crawled_count}")

# Function to extract the first article associated with a German noun
def extract_first_article(word):
    url = "https://de.wiktionary.org/wiki/" + word

    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    table = soup.find("table", class_="wikitable")

    if table:
        rows = table.find_all("tr")

        for row in rows:
            header = row.find("th")
            if header and header.text.strip() in ["Nominativ", "Genitiv"]:
                td_element = row.find("td")
                if td_element:
                    article = td_element.text.strip().split()[0]
                    return article

    return None

def store_word(word, article):
    if article is not None:
        cursor.execute("INSERT INTO german_words VALUES (?, ?)", (word, article))
    else:
        cursor.execute("INSERT INTO german_words (word) VALUES (?)", (word,))

    conn.commit()

def get_resume_word():
    cursor.execute("SELECT word FROM german_words ORDER BY rowid DESC LIMIT 1")
    last_word = cursor.fetchone()
    return last_word[0] if last_word else None

def get_total_crawled_count():
    cursor.execute("SELECT COUNT(*) FROM german_words")
    count = cursor.fetchone()[0]
    return count

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='german_words'")
table_exists = cursor.fetchone()

if table_exists:
    print("Resuming crawler...")
    fetch_german_words()
else:
    print("Starting crawler...")
    fetch_german_words()

conn.close()
