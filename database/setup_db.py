import sqlite3


def setup_connection_and_cursor():
    """
    Setup and create database.

    Returns:

    """
    # Set up sqlite
    conn = sqlite3.connect("database/czasoinator.sqlite")
    cursor = conn.cursor()

    # Create table
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS BAZA_DANYCH (DATA TEXT, NUMER_ZADANIA TEXT, "
        "NAZWA_ZADANIA TEXT, SPEDZONY_CZAS TEXT, KOMENTARZ TEXT);")
    return conn, cursor


conn, cursor = setup_connection_and_cursor()
