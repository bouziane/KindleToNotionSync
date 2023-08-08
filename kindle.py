import os
import re
from dotenv import load_dotenv
from notion_api_utils import create_page
from notion_api_utils import get_pageid_for_title, create_page, update_page


class Highlight:
    def __init__(self, text, page, date):
        self.text = text.strip()
        self.page = page
        self.date = date

    def __str__(self):
        return f"Page: {self.page}, Date: {self.date}, Text: {self.text}"


class Book:
    def __init__(self, title, author):
        self.title = title
        self.author = author
        self.highlights = []

    def add_highlight(self, text, page, date):
        self.highlights.append(Highlight(text, page, date))


def parse_clippings(content):
    parsed_data = []

    book_title, book_author, highlight_info, highlight_content = None, None, None, None

    for index, line in enumerate(content):
        if "(" in line and ")" in line:
            book_title, book_author = line.split("(")
            book_author = book_author.replace(")", "").strip()

        elif line.startswith("- Votre surlignement"):
            highlight_info = line

        elif book_title and not highlight_content:
            highlight_content = line

        elif line.startswith("==========") or index == len(content) - 1:
            if all([book_title, book_author, highlight_info, highlight_content]):
                location = re.search(r"emplacement (\d+-?\d*)", highlight_info)
                date = re.search(
                    r"Ajouté le (.*\d{4} \d{2}:\d{2}:\d{2})", highlight_info
                )

                parsed_data.append(
                    {
                        "title": book_title.strip(),
                        "author": book_author,
                        "highlight": highlight_content,
                        "location": location.group(1) if location else None,
                        "date": date.group(1) if date else None,
                    }
                )

                book_title, book_author, highlight_info, highlight_content = (
                    None,
                    None,
                    None,
                    None,
                )

    return parsed_data


def clippings_to_books(content):
    blocks = "\n".join(content).split("==========")
    books = {}

    for block in blocks:
        # lines = [
        #     line.replace("\ufeff", "").strip()
        #     for line in block.split("\n")
        #     if line.strip()
        # ]
        lines = [line.replace("\ufeff", "") for line in block.split("\n")]
        lines = [line.strip() for line in lines if line.strip()]

        if not lines:
            continue

        title, author = lines[0].rsplit("(", 1)
        author = author.replace(")", "").strip()

        book = books.get(title, Book(title, author))
        books[title] = book

        location = re.search(r"emplacement (\d+-?\d*)", lines[1])
        date = re.search(r"Ajouté le (.*\d{4} \d{2}:\d{2}:\d{2})", lines[1])
        text = " ".join(lines[2:])

        book.add_highlight(
            text,
            location.group(1) if location else None,
            date.group(1) if date else None,
        )

    return list(books.values())


def parse_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = [line.strip() for line in file.readlines()]

    return clippings_to_books(content)


if __name__ == "__main__":
    load_dotenv()
    file_path = os.environ.get("FILE_CLIPPINGS")

    books = parse_file(file_path)
    print(books)

    for book in books:
        page_id = get_pageid_for_title(book.title)
        print(page_id)

        if page_id is None:
            create_page(book)
        else:
            update_page(book, page_id)
