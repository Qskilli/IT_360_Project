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


# This is a custom error type for database problems. So the front end can catch it and show the message
class DatabaseError(Exception):
    """Raised for any database problem; the message is safe to show to the user."""


# This is the main function the front end calls to load every law the AI may choose from
def get_all_laws(db_path: Path = DB_PATH) -> list[dict]:
    """Return every law in the database as a list of dictionaries."""
    # This checks for the file first. Otherwise SQLite would silently create an empty one.
    if not db_path.exists():
        # This stops with a clear message saying where the database was expected
        raise DatabaseError(f"Law database not found at {db_path}.")

    # This catches any SQLite problem (such as a damaged file) in the block below
    try:
        # mode=ro opens the database read-only, so the app can never change the law data.
        conn = sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row  # lets each row be turned into a dictionary
        # This makes sure the connection gets closed even if the query fails
        try:
            # This runs the query and collects every resulting row
            rows = conn.execute(LAWS_QUERY).fetchall()
        # This always closes the database connection when finished
        finally:
            conn.close()
