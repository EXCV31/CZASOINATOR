import datetime

from redminelib import Redmine
import calendar
import time
from datetime import date
import os
import sqlite3
from rich import print as print
from rich.panel import Panel
from rich.text import Text
from rich.color import Color
from rich.console import Console

stop = ""
choose = 0
today = date.today()
info = False
console = Console()

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

        # Show rich panel
        print(Panel(Text("\nCZASOINATOR - Wybierz co chcesz zrobić:\n"
                         "\n1. Uruchom zliczanie czasu"
                         "\n2. Sprawdź dzisiejsze postępy"
                         "\n3. Sprawdź wczorajsze postępy"
                         "\n4. Dorzuć ręcznie czas do zadania"
                         "\n5. Dorzuć ręcznie czas do bazy - własne zadanie"
                         "\n6. Statystyki"
                         "\n7. Wyjście\n", justify="center"), title="[bold orange3]CZASOINATOR"))

        # Ask user to choose a module
        choose = input("\nWybór > ")

        # Turn off info after showing legend once.
        info = True

    else:
        choose = input("\nWybór > ")
    # Make a connection to Redmine.
    redmine = Redmine("http://demo.redmine.org/", key="xxxx")
    # Set up sqlite
    conn = sqlite3.connect(f"czasoinator.sqlite")
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS BAZA_DANYCH (DATA TEXT, NUMER_ZADANIA TEXT, "
        "NAZWA_ZADANIA TEXT, SPEDZONY_CZAS TEXT, KOMENTARZ TEXT);")
    return redmine, cursor, choose, conn


def issue_stopwatch(redmine, cursor, conn):

    # stop variable is used to stop the stopwatch.
    stop = ""

    issue_id = input("\nPodaj numer zadania > ")

    # Start stopwatch
    start_timestamp = int(calendar.timegm(time.gmtime()))

    # Get issue name
    issue_name = str(redmine.issue.get(issue_id))

    # Show rich panel
    print("", Panel(Text(f"\nWybrano zadanie: {issue_name}\n", justify="center"), title="[bold orange3]CZASOINATOR"))

    question = input("\nKontynuować? t/n > ")

    if question.lower() == "t":

        # Catch wrong name, problems with connection etc.
        try:
            # Show rich panel
            Panel(Text(f"Rozpoczęto mierzenie czasu dla zadania #{issue_id}", justify="center"),
                  title="[bold orange3]CZASOINATOR")
        except exception as e:
            print(f"Wystąpił błąd: {e}")

        while stop != "k":
            stop = input("\nGdy zakończysz pracę nad zadaniem wpisz \"k\" > ")

        # Stop stopwatch and calculate timestamp to hours eg. 2.63
        stop_timestamp = int(calendar.timegm(time.gmtime()))
        time_elapsed = round(((stop_timestamp - start_timestamp) / 60 / 60), 2)

        # Show rich panel
        print("", Panel(
            Text(f"\nZakończono pracę nad #{issue_id}!\n Spędzony czas: {time_elapsed} godzin.\n ", justify="center"),
            title="[bold orange3]CZASOINATOR"))

        comment = input("\nDodaj komentarz > ")

        if input("Dodać czas do zadania w redmine? t/n > ").lower() == "t":
            # Catch problems with connection, permissions etc.
            try:
                redmine.time_entry.create(issue_id=issue_id, spent_on=date.today(),
                                          hours=time_elapsed, activity_id=8, comments=comment)

                # Show rich panel
                print("", Panel(Text(f"\nDodano!"
                                     f"\n\nSpędzony czas: {time_elapsed}"
                                     f"\nKomentarz: {comment}\n"
                                     f"\nPamiętaj o git commit -m TASK#{issue_id}: {comment} && git push", justify="center"), title="[bold orange3]CZASOINATOR"))
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
        # Show rich panel
        print("", Panel(Text("\n Brak postępów! \n", justify="center"), title="[bold orange3]CZASOINATOR"))

        return

    string = f"\n Postępy dnia {yesterday}:\n"

    for row in rows:
        # row_1 = row[1] is for text-formatting purposes. eg # 20000 or "Brak numeru zadania"
        row_1 = row[1]
        if row_1 is None:
            row_1 = "Brak numeru zadania!"
        else:
            row_1 = "# " + row_1
        string += f"\n\n {row_1}" \
                  f"\n {row[2]}\n" \
                  f"\n Spędzony czas: {row[3]}h" \
                  f"\n Komentarz: {row[4]} \n"
        if len(rows) > 1:
            if row != rows[-1]:
                string += "\n----------------------------------------------------"

    # Show rich panel
    print("", Panel(Text(string, justify="center"), title="[bold orange3]CZASOINATOR"))

    # Close connection to database
    conn.close()


def show_work_yesterday(cursor):
    # Send query to get data from today
    cursor.execute("SELECT * FROM BAZA_DANYCH WHERE DATA=?", (yesterday,))

    # Fetch data from query above
    rows = cursor.fetchall()

    # Empty rows variable means there's no SQL entries.
    if not rows:
        print("", Panel(Text("\n Brak postępów! \n", justify="center"), title="[bold orange3]CZASOINATOR"))
        return
    string = f"\n Postępy dnia {yesterday}:\n"

    for row in rows:

        # row_1 = row[1] is for text-formatting purposes. eg # 20000 or "Brak numeru zadania"
        row_1 = row[1]

        if row_1 is None:
            row_1 = "Brak numeru zadania!"
        else:
            row_1 = "# " + row_1
        string += f"\n\n {row_1}" \
                  f"\n {row[2]}\n" \
                  f"\n Spędzony czas: {row[3]}h" \
                  f"\n Komentarz: {row[4]} \n"
        if len(rows) > 1:
            if row != rows[-1]:
                string += "\n----------------------------------------------------"

    # Show rich panel
    print("", Panel(Text(string, justify="center"), title="[bold orange3]CZASOINATOR"))

    # Close connection to database
    conn.close()


def add_manually_to_database(redmine, cursor):
    issue_id = input("\nPodaj numer zadania > ")

    # Get issue name
    try:
        issue_name = str(redmine.issue.get(issue_id))

        # Show rich panel
        print("",
              Panel(Text(f"\nWybrano zadanie: {issue_name}\n", justify="center"), title="[bold orange3]CZASOINATOR"))

        question = input("\nKontynuować? t/n > ")
    except exception as e:
        print(f"Wystąpił błąd przy pobieraniu nazwy zadania - {e}")
        return

    if question.lower() == "t":

        time_elapsed = input("\nPodaj czas spędzony nad zadaniem - oddzielony kropką np 2.13 > ")
        comment = input("Dodaj komentarz > ")
        # Catch problems with connection, permissions etc.
        try:
            redmine.time_entry.create(issue_id=issue_id, spent_on=date.today(),
                                      hours=time_elapsed, activity_id=8, comments=comment)
        except exception as e:
            print(f"Wystąpił błąd przy dodawaniu czasu do redmine - {e}")

        # Insert user work to database.
        cursor.execute(f"INSERT INTO BAZA_DANYCH (DATA, NUMER_ZADANIA, NAZWA_ZADANIA, SPEDZONY_CZAS, KOMENTARZ) VALUES "
                       f"(?, ?, ?, ?, ?)", (today, issue_id, issue_name, time_elapsed, comment,))

        # Apply changes and close connection to sqlite database.
        conn.commit()
        conn.close()

        # Show rich panel
        print("", Panel(Text(f"\nDodano!"
                             f"\n\nSpędzony czas: {time_elapsed}"
                             f"\nKomentarz: {comment}\n", justify="center"), title="[bold orange3]CZASOINATOR"))


def add_own_to_database(cursor):
    issue_name = input("\nPodaj nazwę zadania > ")
    time_elapsed = input("Podaj czas spędzony nad zadaniem - oddzielony kropką np 2.13 > ")

    # Show rich panel
    print("", Panel(Text(f"\nDodano!"
                         f"\n\nNazwa Zadania: {issue_name}"
                         f"\nSpędzony czas: {time_elapsed}\n", justify="center"), title="[bold orange3]CZASOINATOR"))

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

    # Show rich panel
    print("", Panel(Text(f"\n Czas spędzony z CZASOINATOREM: {total_hours} \n", justify="center"),
                    title="[bold orange3]CZASOINATOR"))


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
            add_own_to_database(cursor)
        if choose == str(6):
            stats(cursor)

        if choose == "?":
            info = False
