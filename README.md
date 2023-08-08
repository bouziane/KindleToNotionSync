# KindleToNotionSync

A Python script to extract Kindle highlights and save them to a Notion database.

#### Features

- Extracts highlights from a Kindle's My Clippings.txt file
- Checks if the book already exists in the Notion database
- Updates the book's Notion page with new highlights if it exists
- Creates a new Notion page for the book if it doesn't exist

#### Setup

Clone this repository:

```shell script
https://github.com/bouziane/KindleToNotionSync.git
cd KindleToNotionSync
```

Install required packages:

```shell script
pip install -r requirements.txt
```

Create a .env file with:

```shell script
DATABASE_ID=<Your_Notion_Database_ID>
NOTION_TOKEN=<Your_Notion_Secret_Key>  
FILE_CLIPPINGS=<Path_to_clippings_file>
```

#### Usage

Run the main script: python3 kindle.py
