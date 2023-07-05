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
        "apnamespace": "0",
 #       "apprefix": "Aa"  # Starting letter for the words (change as needed)
    }

    try:
        print("Crawler running...")
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
            
    except KeyboardInterrupt:
        print("Crawler paused.")

def extract_first_article(word):
    url = "https://de.wiktionary.org/wiki/" + word

    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the table containing the articles
    table = soup.find("table", class_="wikitable")

    if table:
        # Find all rows in the table
        rows = table.find_all("tr")

        for row in rows:
            # Check if the row contains a header indicating it's a noun
            header = row.find("th")
            if header and header.text.strip() in ["Nominativ", "Genitiv"]:
                # Find the first article in the row and extract only the article text
                td_element = row.find("td")
                if td_element:
                    article = td_element.text.strip().split()[0]
                    return article

    return None


# Function to store a German word and its article in the database
def store_word(word, article):
    if article is not None:
        cursor.execute("INSERT INTO german_words VALUES (?, ?)", (word, article))
    else:
        cursor.execute("INSERT INTO german_words (word) VALUES (?)", (word,))

    conn.commit()

# Check if the database already exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='german_words'")
table_exists = cursor.fetchone()

if table_exists:
    print("Resuming crawler...")
    fetch_german_words()
else:
    print("Starting crawler...")
    fetch_german_words()

# Close the database connection
conn.close()
