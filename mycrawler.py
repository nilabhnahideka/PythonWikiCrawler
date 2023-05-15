import requests
from bs4 import BeautifulSoup
import sqlite3

# Load the German word list from a file
with open("german_word_list.txt", "r", encoding="utf-8") as f:
    german_word_list = [line.strip() for line in f]

# Make a request to the Wiki API to retrieve a list of German pages
response = requests.get("https://de.wiktionary.org/w/api.php?action=query&generator=random&grnnamespace=0&grnlimit=100&prop=info&inprop=url&format=json")

# Create a connection to the database
conn = sqlite3.connect("german_words.db")

# Create a table to store the German words
conn.execute("CREATE TABLE IF NOT EXISTS words (word TEXT)")

# Extract the German words and their articles from the API response and store the German words in the database
for page_id, page in response.json()["query"]["pages"].items():
    # Check if the page is a German word
    if page["title"] in german_word_list:
        # Extract the article content
        article_response = requests.get(page["fullurl"])
        article_soup = BeautifulSoup(article_response.content, "html.parser")
        german_article_words = [word.string for word in article_soup.find_all(string=True) if word.string.strip() in german_word_list]
        # Insert the German words into the database
        for german_word in german_article_words:
            conn.execute("INSERT INTO words (word) VALUES (?)", (german_word,))

# Commit the changes and close the connection
conn.commit()
conn.close()
