import requests
from bs4 import BeautifulSoup
import sqlite3
import spacy

# Load the German word list
with open("german_word_list.txt", "r", encoding="utf-8") as f:
    german_word_list = [line.strip() for line in f]

found_words = []
existing_words = []

conn = sqlite3.connect("german_words.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
table_exists = cursor.fetchone()

if not table_exists:
    cursor.execute("CREATE TABLE words (word TEXT, pos TEXT, gender TEXT, number TEXT, word_case TEXT, article TEXT)")
else:
    cursor.execute("SELECT word FROM words")
    existing_words = [row[0] for row in cursor.fetchall()]
    found_words.extend(existing_words)

nlp = spacy.load("de_core_news_sm")

# Define a function to determine the appropriate article for a noun based on gender, number, and case
def determine_article(gender, number, word_case):
    if gender == ['Masc']:
        if number == ['Sing']:
            if word_case == ['Nom']:
                return "der"
            elif word_case == ['Gen']:
                return "des"
            elif word_case == ['Dat']:
                return "dem"
            elif word_case == ['Acc']:
                return "den"
        elif number == ['Plur']:
            if word_case == ['Nom']:
                return "die"
            elif word_case == ['Gen']:
                return "der"
            elif word_case == ['Dat']:
                return "den"
            elif word_case == ['Acc']:
                return "die"
    elif gender == ['Fem']:
        if number == ['Sing']:
            if word_case == ['Nom']:
                return "die"
            elif word_case == ['Gen']:
                return "der"
            elif word_case == ['Dat']:
                return "der"
            elif word_case == ['Acc']:
                return "die"
        elif number == ['Plur']:
            if word_case == ['Nom']:
                return "die"
            elif word_case == ['Gen']:
                return "der"
            elif word_case == ['Dat']:
                return "den"
            elif word_case == ['Acc']:
                return "die"
    elif gender == ['Neut']:
        if number == ['Sing']:
            if word_case == ['Nom']:
                return "das"
            elif word_case == ['Gen']:
                return "des"
            elif word_case == ['Dat']:
                return "dem"
            elif word_case == ['Acc']:
                return "das"
        elif number == ['Plur']:
            if word_case == ['Nom']:
                return "die"
            elif word_case == ['Gen']:
                return "der"
            elif word_case == ['Dat']:
                return "den"
            elif word_case == ['Acc']:
                return "die"
    return ""

try:
    # Make a request to the Wiki API to retrieve a list of German pages
    for word in german_word_list:
        # Check if the word has already been found or stored
        if word not in found_words and word not in existing_words:
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
                article_response = requests.get(page_info["fullurl"])
                article_soup = BeautifulSoup(article_response.content, "html.parser")
                article_content = article_soup.find("div", class_="mw-parser-output").get_text(strip=True)
                german_words = []
                found_words_set = set(found_words)
                for token in nlp(article_content):
                    if token.text.lower() in german_word_list and token.text.lower() not in found_words_set and token.text.lower() not in existing_words:
                        german_words.append(token)
                        found_words.append(token.text.lower())
                        found_words_set.add(token.text.lower())
                # Extract the gender, number, and case information for the German words
                for token in german_words:
                    gender = token.morph.get("Gender")
                    number = token.morph.get("Number")
                    word_case = token.morph.get("Case")
                    article = determine_article(gender, number, word_case)
                    cursor.execute("INSERT INTO words (word, pos, gender, number, word_case, article) VALUES (?, ?, ?, ?, ?, ?)",
                                   (token.text.lower(), str(token.pos_), str(gender), str(number), str(word_case), article))
                    conn.commit()

except KeyboardInterrupt:
    total_crawled = len(found_words)
    remaining_words = len(german_word_list) - total_crawled
    print(f"Total words crawled: {total_crawled}")
    print(f"Remaining words to be crawled: {remaining_words}")
    print("Crawling paused.")

conn.close()
