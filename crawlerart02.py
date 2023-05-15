import requests
from bs4 import BeautifulSoup
import sqlite3

# Load the German word list from a file
with open("german_word_list.txt", "r", encoding="utf-8") as f:
    german_word_list = [line.strip() for line in f]

found_words = []

# Make a request to the Wiki API to retrieve a list of German pages
response = requests.get("https://de.wiktionary.org/w/api.php?action=query&generator=random&grnnamespace=0&grnlimit=100&prop=info&inprop=url&format=json")

# Extract the German words and their articles from the API response
for page_id, page in response.json()["query"]["pages"].items():
    # Extract the article content
    article_response = requests.get(page["fullurl"])
    article_soup = BeautifulSoup(article_response.content, "html.parser")
    article_content = article_soup.find("div", class_="mw-parser-output").get_text(strip=True)
    # Find all the German articles in the article content
    german_articles = [article for article in ["das", "die", "der"] if article in article_content]
    # Find all the German words in the article content
    german_words = []
    found_words_set = set(found_words)
    for word in article_content.split():
        if word in german_word_list and word not in german_articles and word not in ["das", "die", "der"] and word not in found_words_set:
            german_words.append(word)
            found_words.append(word)
            found_words_set.add(word)
    # Insert the German words and their articles into the database
    conn = sqlite3.connect("german_words.db")
    conn.execute("CREATE TABLE IF NOT EXISTS words (word TEXT, article TEXT)")
    for word in german_words:
        article = None
        for german_article in german_articles:
            if f"{german_article} {word}" in article_content:
                article = german_article
                break
        conn.execute("INSERT INTO words (word, article) VALUES (?, ?)", (word, article))
    conn.commit()
    conn.close()

# Print the number of words found and the number of words still not crawled
print(f"Words found: {len(found_words)}")
print(f"Words still not crawled: {len(german_word_list) - len(found_words)}")
