import requests
from bs4 import BeautifulSoup
import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('german_words.db')
cursor = conn.cursor()

# Create a table to store German words and their articles
cursor.execute("CREATE TABLE IF NOT EXISTS german_words (word TEXT, article TEXT)")

# Function to fetch German words using the Wiktionary API
def fetch_german_words():
    url = "https://de.wiktionary.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "allpages",
        "aplimit": "500",
        "apnamespace": "0",
        "apprefix": "Aa"  # Starting letter for the words (change as needed)
    }

    while True:
        response = requests.get(url, params=params)
        data = response.json()
        words = data['query']['allpages']

        for word in words:
            article = extract_first_article(word['title'])
            store_word(word['title'], article)

        if 'continue' not in data:
            break

        params['apcontinue'] = data['continue']['apcontinue']

# Function to extract the first article associated with a German noun
def extract_first_article(word):
    url = "https://de.wiktionary.org/wiki/" + word

    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the table containing the articles
    table = soup.find("table", class_="wikitable")

    if table:
        # Find the first article in the table
        article = table.find("td").text.strip()
        return article

    return None

# Function to store a German word and its article in the database
def store_word(word, article):
    if article is not None:
        cursor.execute("INSERT INTO german_words VALUES (?, ?)", (word, article))
    else:
        cursor.execute("INSERT INTO german_words (word) VALUES (?)", (word,))

    conn.commit()

# Fetch German words and their articles
fetch_german_words()

# Close the database connection
conn.close()
