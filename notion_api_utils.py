import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
import locale

load_dotenv()
DATABASE_ID = os.environ.get("DATABASE_ID")
SECRET_KEY = os.environ.get("NOTION_TOKEN")
HEADERS = {
    "Accept": "application/json",
    "Notion-Version": "2022-02-22",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {SECRET_KEY}",
}


def get_pageid_for_title(title):
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {
        "page_size": 100,
        "filter": {"property": "Title", "rich_text": {"starts_with": title}},
    }
    response = requests.post(url, json=payload, headers=HEADERS)
    data = response.json()

    if data["results"]:
        return data["results"][0]["id"]
    return None


def get_list_of_paragraphs_for_page_with_title(title):
    page_id = get_pageid_for_title(title)
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    paragraphs = []
    for item in data["results"]:
        block_type = None
        text_content = None

        if "quote" in item:
            block_type = "highlight"
            text_content = item["quote"]["rich_text"][0]["plain_text"]
        elif "callout" in item:
            block_type = "note"
            text_content = item["callout"]["rich_text"][0]["plain_text"]

        if block_type and text_content:
            paragraphs.append((text_content, block_type))

    return paragraphs


def create_payload_for_page(paragraphs):
    children_list = []
    for text, p_type in paragraphs:
        if p_type == "highlight":
            block_type = "quote"
        else:
            block_type = "callout"
            icon = {"emoji": "⭐"}

        children_list.append(
            {
                "type": block_type,
                block_type: {
                    "rich_text": [{"type": "text", "text": {"content": text}}],
                    "color": "default",
                    **(icon if block_type == "callout" else {}),
                },
            }
        )
    return children_list


def append_items_to_page(title, items):
    children_list = create_payload_for_page(items)
    page_id = get_pageid_for_title(title)
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    response = requests.patch(url, json={"children": children_list}, headers=HEADERS)


def create_page(book):
    children_list = []
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    for highlight in book.highlights:
        children_list.extend(
            [
                {
                    "type": "quote",
                    "quote": {
                        "rich_text": [
                            {"type": "text", "text": {"content": highlight.text}}
                        ],
                        "color": "default",
                    },
                },
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"Page: {highlight.page} | Date: {datetime.strptime(highlight.date, '%A %d %B %Y %H:%M:%S').strftime('%d/%m/%Y %H:%M')}"
                                },
                            }
                        ]
                    },
                },
            ]
        )

    initial_payload = {
        "children": children_list[:100],
        "icon": {"emoji": "📘"},
        "parent": {"type": "database_id", "database_id": DATABASE_ID},
        "properties": {
            "Title": {"title": [{"type": "text", "text": {"content": book.title}}]},
            "Author": {
                "rich_text": [{"type": "text", "text": {"content": book.author}}]
            },
        },
    }
    response = requests.post(
        "https://api.notion.com/v1/pages", json=initial_payload, headers=HEADERS
    )
    page_id = response.json().get("id")

    block_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    for i in range(100, len(children_list), 100):
        payload = {"children": children_list[i : i + 100]}
        requests.patch(block_url, json=payload, headers=HEADERS)


def get_existing_blocks(page_id):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    response = requests.get(url, headers=HEADERS)
    return response.json().get("results", [])


def block_exists(new_block, existing_blocks):
    for block in existing_blocks:
        if "quote" in block and "quote" in new_block:
            if (
                new_block["quote"]["rich_text"][0]["text"]["content"]
                == block["quote"]["rich_text"][0]["text"]["content"]
            ):
                return True
    return False


def update_page(book, page_id):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    existing_blocks = get_existing_blocks(page_id)
    children_list = []

    for highlight in book.highlights:
        new_block = {
            "type": "quote",
            "quote": {
                "rich_text": [{"type": "text", "text": {"content": highlight.text}}],
                "color": "default",
            },
        }
        location_date_text = f"Location: {highlight.page}, Date: {highlight.date}"
        new_location_date_block = {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": location_date_text}}]
            },
        }

        if not block_exists(new_block, existing_blocks):
            children_list.append(new_block)
            children_list.append(new_location_date_block)

    requests.patch(url, json={"children": children_list}, headers=HEADERS)
