import requests
import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('german_words.db')
cursor = conn.cursor()

# Create a table to store German words
cursor.execute("CREATE TABLE IF NOT EXISTS german_words (word TEXT)")

# Function to fetch German words using the Wiktionary API
def fetch_german_words():
    url = "https://de.wiktionary.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": "Kategorie:Deutsch",
        "cmlimit": "500"
    }

    while True:
        response = requests.get(url, params=params)
        data = response.json()
        words = data['query']['categorymembers']

        for word in words:
            store_word(word['title'])

        if 'continue' not in data:
            break

        params['cmcontinue'] = data['continue']['cmcontinue']

# Function to store a German word in the database
def store_word(word):
    cursor.execute("INSERT INTO german_words VALUES (?)", (word,))
    conn.commit()

# Fetch German words using the Wiktionary API
fetch_german_words()

# Close the database connection
conn.close()
