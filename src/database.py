# Has Read-only access to the SQLite database file: illinois_digital_laws.sqlite
#The AI is only able to review and choose laws from the included database.
#This is the single source of truth for which laws the Ai can utilize

#Imports built in library for reading SQLite database files 
import sqlite3
#Imports built in tool for building paths (work for Mac, Windows and Linux)
from pathlib import Path 

DB_PATH = Path(_file_) 


