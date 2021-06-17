import datetime

from redminelib import Redmine
import calendar
import time
from datetime import date
import os
import sqlite3

stop = ""
choose = 0
today = date.today()
info = False
# Check if today is monday - used for valid "yesterday" when it's weekend:
if date.today().weekday() == 0:
    yesterday = today - datetime.timedelta(days=3)
else:
    yesterday = today - datetime.timedelta(days=1)


def get_started():
    global choose
    global info
    # Info variable is being used to show user a legend of possible options.
    if not info:
        choose = input(f"""
#######################################################################
#                                                                     #
#               CZASOINATOR - Wybierz co chcesz zrobić:               #
#                                                                     #
#                     1. Uruchom zliczanie czasu                      #
#                    2. Sprawdź dzisiejsze postępy                    #
#                    3. Sprawdź wczorajsze postępy                    #
#                  4. Dorzuć ręcznie czas do zadania                  #
#           5. Dorzuć ręcznie czas do bazy - własne zadanie           #
#                           6. Statystyki                             #
#                             7. Wyjście                              #
#                                                                     #
#######################################################################
    
Wybór > """)

        # Turn off info after showing legend once.
        info = True

    else:
        choose = input("\nWybór > ")
    # Make a connection to Redmine.
    redmine = Redmine("xxxx", key="xxxx")
    # Set up sqlite
    conn = sqlite3.connect(f"czasoinator.sqlite")
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS BAZA_DANYCH (DATA TEXT, NUMER_ZADANIA TEXT, NAZWA_ZADANIA TEXT, SPEDZONY_CZAS TEXT, KOMENTARZ TEXT);")
    return redmine, cursor, choose, conn


def issue_stopwatch(redmine, cursor, conn):
    # stop variable is used to stop the stopwatch.
    stop = ""
    issue_id = input("\nPodaj numer zadania > ")

    # Start stopwatch
    start_timestamp = int(calendar.timegm(time.gmtime()))

    # Get issue name
    issue_name = str(redmine.issue.get(issue_id))

    question = input(f"\nWybrano zadanie {issue_name}. Kontynuować? t/n > ")

    if question.lower() == "t":
        # Catch wrong name, problems with connection etc.
        try:
            print(f"\nRozpoczęto mierzenie czasu dla zadania #{issue_id} - {issue_name})")
        except exception as e:
            print(f"Wystąpił błąd: {e}")

        while stop != "k":
            stop = input("Gdy zakończysz pracę nad zadaniem wpisz \"k\" > ")

        # Stop stopwatch and calculate timestamp to hours eg. 2.63
        stop_timestamp = int(calendar.timegm(time.gmtime()))
        time_elapsed = round(((stop_timestamp - start_timestamp) / 60 / 60), 2)

        print(f"\nZakończono pracę nad #{issue_id}!\n"
              f"Spędzony czas: {time_elapsed} godzin.\n")

        comment = input("Dodaj komentarz > ")

        if input("Dodać czas do zadania w redmine? t/n > ").lower() == "t":
            # Catch problems with connection, permissions etc.
            try:
                redmine.time_entry.create(issue_id=issue_id, spent_on=date.today(),
                                          hours=time_elapsed, activity_id=8, comments=comment)
                print("\nGotowe!")
            except exception as e:
                print(f"Wystąpił błąd przy dodawaniu czasu do redmine - {e}")

        # Insert user work to database
        cursor.execute(f"INSERT INTO BAZA_DANYCH (DATA, NUMER_ZADANIA, NAZWA_ZADANIA, SPEDZONY_CZAS, KOMENTARZ) VALUES "
                       f"(?, ?, ?, ?, ?)", (today, issue_id, issue_name, time_elapsed, comment,))

        # Apply changes and close connection to sqlite database
        conn.commit()


def show_work_today(cursor):
    # Send query to get data from today
    cursor.execute("SELECT * FROM BAZA_DANYCH WHERE DATA=?", (today,))

    # Fetch data from query above
    rows = cursor.fetchall()

    # Empty rows variable means there's no SQL entries.
    if not rows:
        print(f"\n#######################################################################")
        print(f"#                                                                     #")
        print(f"#                           Brak postępów!:                           #")
        print(f"#                                                                     #")
        print(f"#######################################################################")
        return

    print(f"\n#######################################################################")
    print(f"#                                                                     #")
    print(f"#                     Postępy dnia {today}:                        #")

    # Display data
    for row in rows:
        print(f"#                                                                     #")
        print(f"#   Zadanie:        # {row[1]}")
        print(f"#   Tytuł:          {row[2]}")
        print(f"#   Spędzony czas:  {row[3]}h")
        print(f"#   Komentarz:  {row[4]}")
    print(f"#                                                                     #")
    print(f"#######################################################################")

    # Close connection to database
    conn.close()


def show_work_yesterday(cursor):
    # Send query to get data from today
    cursor.execute("SELECT * FROM BAZA_DANYCH WHERE DATA=?", (yesterday,))

    # Fetch data from query above
    rows = cursor.fetchall()

    # Empty rows variable means there's no SQL entries.
    if not rows:
        print(f"\n#######################################################################")
        print(f"#                                                                     #")
        print(f"#                           Brak postępów!:                           #")
        print(f"#                                                                     #")
        print(f"#######################################################################")
        return

    # Display data
    print(f"\n#######################################################################")
    print(f"#                                                                     #")
    print(f"#                     Postępy dnia {yesterday}:                        #")

    # Display data
    for row in rows:
        print(f"#                                                                     #")
        print(f"#   Zadanie:        # {row[1]}")
        print(f"#   Tytuł:          {row[2]}")
        print(f"#   Spędzony czas:  {row[3]}h")
        print(f"#   Komentarz:  {row[4]}")
    print(f"#                                                                     #")
    print(f"#######################################################################")

    # Close connection to database
    conn.close()


def add_manually_to_database(redmine, cursor):
    issue_id = input("\nPodaj numer zadania > ")

    # Get issue name
    try:
        issue_name = str(redmine.issue.get(issue_id))
        question = input(f"Wybrano zadanie {issue_name}. Kontynuować? t/n > ")
    except exception as e:
        print(f"Wystąpił błąd przy pobieraniu nazwy zadania - {e}")
        return

    if question.lower() == "t":

        time_elapsed = input("Podaj czas spędzony nad zadaniem - oddzielony kropką np 2.13 > ", )
        comment = input("Dodaj komentarz > ")

        # Catch problems with connection, permissions etc.
        try:
            redmine.time_entry.create(issue_id=issue_id, spent_on=date.today(),
                                      hours=time_elapsed, activity_id=8, comments=comment)
        except exception as e:
            print(f"Wystąpił błąd przy dodawaniu czasu do redmine - {e}")

        # Insert user work to database.
        cursor.execute(f"INSERT INTO BAZA_DANYCH (DATA, NUMER_ZADANIA, NAZWA_ZADANIA, SPEDZONY_CZAS, KOMENTARZ) VALUES "
                       f"(?, ?, ?, ?, ?)", (today, issue_id, issue_name, time_elapsed, comment, ))

        # Apply changes and close connection to sqlite database.
        conn.commit()
        conn.close()

        print("\nGotowe!")


def add_own_to_database(cursor):
    issue_name = input("\nPodaj nazwę zadania > ")
    time_elapsed = input("Podaj czas spędzony nad zadaniem - oddzielony kropką np 2.13 > ", )

    # Insert user work to database.
    cursor.execute(f"INSERT INTO BAZA_DANYCH (DATA, NAZWA_ZADANIA, SPEDZONY_CZAS) VALUES "
                   f"(?, ?, ?)", (today, issue_name, time_elapsed,))

    # Apply changes and close connection to sqlite database.
    conn.commit()
    conn.close()


def stats(cursor):
    cursor.execute("SELECT SPEDZONY_CZAS FROM BAZA_DANYCH")
    rows = cursor.fetchall()
    total_hours = 0

    for row in rows:
        total_hours += float(row[0])
    total_hours = round(total_hours, 2)

    print(f"\n#######################################################################")
    print(f"#                                                                     #")
    print(f"#               Spędzone godziny z CZASOINATOREM: {total_hours}                #")
    print(f"#                                                                     #")
    print(f"#######################################################################")


if __name__ == "__main__":
    while choose != str(7):
        redmine, cursor, choose, conn = get_started()
        if choose == str(1):
            issue_stopwatch(redmine, cursor, conn)
        if choose == str(2):
            show_work_today(cursor)
        if choose == str(3):
            show_work_yesterday(cursor)
        if choose == str(4):
            add_manually_to_database(redmine, cursor)
        if choose == str(5):
            add_own_to_databse(cursor)
        if choose == str(6):
            stats(cursor)

        # ? shows legend
        if choose == "?":
            info = False
