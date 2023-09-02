# TODO

[![Downloads](https://img.shields.io/pypi/dm/mypy)](empty)
[![Stable Version](https://img.shields.io/pypi/v/mypy?color=blue)](empty)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![pypi](https://img.shields.io/pypi/v/ruff/0.0.287.svg)](empty)
[![license](https://img.shields.io/pypi/l/ruff/0.0.287.svg)](empty)
[![python versions](https://img.shields.io/pypi/pyversions/ruff/0.0.287.svg)](empty)
[![Actions status](https://github.com/astral-sh/ruff-pre-commit/workflows/main/badge.svg)](empty)
[![Build Status](https://github.com/python/mypy/actions/workflows/test.yml/badge.svg)](empty)
[![Documentation Status](https://readthedocs.org/projects/mypy/badge/?version=latest)](empty)

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
