import requests
from bs4 import BeautifulSoup
import sqlite3
import spacy

# Load the German word list from a file
with open("german_word_list.txt", "r", encoding="utf-8") as f:
    german_word_list = [line.strip() for line in f]

found_words = []
existing_words = []

# Connect to the database
conn = sqlite3.connect("german_words.db")
cursor = conn.cursor()

# Check if the 'words' table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
table_exists = cursor.fetchone()

# If the 'words' table doesn't exist, create it
if not table_exists:
    cursor.execute("CREATE TABLE words (word TEXT, pos TEXT)")
else:
    # Fetch the existing words from the database
    cursor.execute("SELECT word FROM words")
    existing_words = [row[0] for row in cursor.fetchall()]
    found_words.extend(existing_words)

# Define the batch size and the starting index for the current batch
batch_size = 10000
start_index = 0

try:
    # Make a request to the Wiki API to retrieve a list of German pages
    for word in german_word_list:
        # Check if the word has already been found or stored
        if word not in found_words and word not in existing_words:
            # Make a request to the Wiki API for the specific word
            params = {
                "action": "query",
                "titles": word,
                "format": "json",
                "prop": "info",
                "inprop": "url",
            }
            response = requests.get("https://de.wiktionary.org/w/api.php", params=params)
            page = response.json()["query"]["pages"]
            # Check if the word exists in the response
            if "-1" not in page:
                page_info = list(page.values())[0]
                page_id = page_info["pageid"]
                # Extract the article content
                article_response = requests.get(page_info["fullurl"])
                article_soup = BeautifulSoup(article_response.content, "html.parser")
                article_content = article_soup.find("div", class_="mw-parser-output").get_text(strip=True)
                # Find all the German words in the article content along with their part-of-speech tags
                german_words = []
                found_words_set = set(found_words)
                for word in article_content.split():
                    if word in german_word_list and word not in found_words_set and word not in existing_words:
                        german_words.append(word)
                        found_words.append(word)
                        found_words_set.add(word)
                # Use spaCy to determine the part-of-speech tags for the German words
                nlp = spacy.load("de_core_news_sm")
                pos_tags = []
                for word in german_words:
                    doc = nlp(word)
                    pos_tags.append(doc[0].pos_)
                # Insert the German words and their part-of-speech tags into the database
                for word, pos in zip(german_words, pos_tags):
                    cursor.execute("INSERT INTO words (word, pos) VALUES (?, ?)", (word, pos))
                    conn.commit()

except KeyboardInterrupt:
    # Print the number of words crawled and the number of words remaining
    total_crawled = len(found_words)
    remaining_words = len(german_word_list) - total_crawled
    print(f"Total words crawled: {total_crawled}")
    print(f"Remaining words to be crawled: {remaining_words}")
    print("Crawling paused.")

# Close the database connection
conn.close()
