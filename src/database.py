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



