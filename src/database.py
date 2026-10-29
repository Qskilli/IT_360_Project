# Has Read-only access to the SQLite database file: illinois_digital_laws.sqlite
#The AI is only able to review and choose laws from the included database.
#This is the single source of truth for which laws the Ai can utilize

#Imports built in library for reading SQLite database files 
import sqlite3
#Imports built in tool for building paths (work for Mac, Windows and Linux)
from pathlib import Path 

# The database lives in the project's data/ folder, one level above src/.
# (__file__ is this file; .parent.parent goes up from src/ to the project folder.)
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "illinois_digital_laws.sqlite"


# One row per law, with all of its tags joined into a single comma-separated string.
# NULLIF treats empty text as missing, and COALESCE swaps in a default, so the prompt never shows a blank.
LAWS_QUERY = """
    SELECT
        laws.id,                                              -- the law's ID number the AI refers to
        laws.title,                                           -- the law's name
        COALESCE(NULLIF(laws.citation, ''), 'no citation') AS citation,  -- citation, or "no citation" if blank
        laws.jurisdiction,                                    -- "Illinois" or "Federal"
        COALESCE(laws.summary, '')                  AS summary,  -- short summary, or empty text if missing
        laws.full_text,                                       -- the complete text shown to the user
        COALESCE(GROUP_CONCAT(law_tags.tag, ', '), '') AS tags  -- all of the law's tags joined into one string
    FROM laws                                                 -- read from the main laws table
    LEFT JOIN law_tags ON law_tags.law_id = laws.id           -- attach each law's tags (keeps laws that have none)
    GROUP BY laws.id                                          -- combine a law's tag rows back into one row
    ORDER BY laws.id                                          -- return laws in ID order
"""
