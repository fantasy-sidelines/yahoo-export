# TODO

1. Data Loader:
    - Get Data from the yahoo api
    - Split accross seperate "Loaders" within Mage
    - Export Raw Json to Supabase
2. Transform Raw Json:
    - Transform data from raw json to parsed json
    - Export parsed json
3. Transform Parsed Json:
    - Transform parsed json to tabular form
    - Export to public schema

## Process

- Query yahoo api
  - DONE
- TODO:
  - Split across multiple "blocks" for each "live" api connection needed
    - Could use multiple api keys to help with rate limiting and speed
  - Once queried, data should load to database immediately
    - Jsonb format in postgresql
    - yahoo_data.raw_json
  - Transformation 1
    - Convert data to "parsed_json"
    - Upload to yahoo_data.parsed_json
  - Transformation 2
    - Convert to tabular format
    - Upload to yahoo_data.public

## Need to knows

- How to use the yahoo_api package created within Mage?
- Should I be using SQLAlchemy or could is suffice with psycopg (perferably v3, but can use v2 if needed)
  - Should this be Async?
  - Would multiple api calls/inserts affect ACID/locks?
  - If so, probably should use ORM?
