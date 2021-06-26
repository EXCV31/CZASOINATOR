import datetime
from redminelib import Redmine
import redminelib.exceptions
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
import configparser

stop = ""
choose = 0
info = False
console = Console()


def get_time():
    now = datetime.datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    # Check if today is monday - used for valid "yesterday" when it's weekend:
    if now.weekday() == 0:
        yesterday = now - datetime.timedelta(days=3)
        yesterday = str(yesterday).split(" ")[0]
    else:
        # If today is monday, yesterday is friday.
        yesterday = now - datetime.timedelta(days=1)
        yesterday = str(yesterday).split(" ")[0]

    today = current_time.split(" ")[0]

    return current_time, yesterday, today


def init():
    config = configparser.ConfigParser()
    config.read("config.ini")
    redmine_conf = config['REDMINE']

    return redmine_conf


def get_started(redmine_conf):
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

        # Turn off info after showing legend once.
        info = True

    else:
        # Ask user to choose a module
        choose = input("\nWybór > ")
    # Make a connection to Redmine.
    redmine = Redmine(redmine_conf["ADDRESS"], key=redmine_conf["API_KEY"])
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
    try:
        issue_name = str(redmine.issue.get(issue_id))
    except redminelib.exceptions.ForbiddenError:
        print("", Panel(Text(f"\n403 - Brak dostępu do wybranego zadania!\n", justify="center"),
                        title="[bold orange3]CZASOINATOR"))
        return
    except redminelib.exceptions.ResourceNotFoundError:
        print(Panel(Text(f"\n404 - Wybrane zadanie nie istnieje!\n", justify="center"),
                    title="[bold orange3]CZASOINATOR"))
        return

    # Show rich panel
    print("", Panel(Text(f"\nWybrano zadanie: {issue_name}\n", justify="center"), title="[bold orange3]CZASOINATOR"),
          "")

    question = input("Kontynuować? t/n > ")

    if question.lower() == "t":

        # Show rich panelimport redminelib.exceptions"
        Panel(Text(f"Rozpoczęto mierzenie czasu dla zadania #{issue_id}", justify="center"),
              title="[bold orange3]CZASOINATOR")

        # Wait for input
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
                                     f"\nPamiętaj o git commit -m \"TASK#{issue_id}: {comment}\" && git push",
                                     justify="center"), title="[bold orange3]CZASOINATOR"))
            except Exception as e:
                print(f"Wystąpił błąd przy dodawaniu czasu do redmine - {e}")

        current_time, _, _ = get_time()

        # Insert user work to database
        cursor.execute(f"INSERT INTO BAZA_DANYCH (DATA, NUMER_ZADANIA, NAZWA_ZADANIA, SPEDZONY_CZAS, KOMENTARZ) VALUES "
                       f"(?, ?, ?, ?, ?)", (current_time, issue_id, issue_name, time_elapsed, comment))

        # Apply changes and close connection to sqlite database
        conn.commit()


def show_work_today(cursor, redmine_conf):
    # This variable store information about doing anything before daily
    info_daily = False
    before_daily_counter = 0
    after_daily_counter = 0
    # Replace 11:00:00 from config.ini to 110000
    daily = redmine_conf["DAILY"].replace(":", "")
    _, _, today = get_time()

    # Send query to get data from today
    cursor.execute("SELECT * FROM BAZA_DANYCH WHERE DATA LIKE ?", (f"%{today}%",))

    # Fetch data from query above
    rows = cursor.fetchall()

    # Empty rows variable means there's no SQL entries.
    if not rows:
        # Show rich panel
        print("", Panel(Text("\n Brak postępów! \n", justify="center"), title="[bold orange3]CZASOINATOR"))

        return

    for row in rows:

        # Split row with date: 24-11-2021 14:20:52 -> 14:20:52
        # Drop ":" from splitted data above, and compare it with daily variable
        # Also check if "daily lines" are displayed before
        if row[0].split(" ")[1].replace(":", "") < daily:
            if before_daily_counter < 1:
                string = f"\n Postępy dnia {today} - przed daily:\n"

            # row_1 = row[1] is for text-formatting purposes. eg # 20000 or "Brak numeru zadania"
            row_1 = row[1]
            if row_1 is None:
                row_1 = "Brak numeru zadania!"
            else:
                row_1 = "# " + row_1
            string += f"\n\n\n {row_1}" \
                      f"\n {row[2]}\n" \
                      f"\n Spędzony czas: {row[3]}h" \
                      f"\n Komentarz: {row[4]} \n"
            info_daily = True

            before_daily_counter += 1

        else:
            if info_daily:
                # Show rich panel with data from "if" above
                print("", Panel(Text(string, justify="center"), title="[bold orange3]CZASOINATOR"))
                info_daily = False

            if after_daily_counter < 1:
                string = f"\n Postępy dnia {today} - po daily:\n"

            # row_1 = row[1] is for text-formatting purposes. eg # 20000 or "Brak numeru zadania"
            row_1 = row[1]
            if row_1 is None:
                row_1 = "Brak numeru zadania!"
            else:
                row_1 = "# " + row_1
            string += f"\n\n\n {row_1}" \
                      f"\n {row[2]}\n" \
                      f"\n Spędzony czas: {row[3]}h" \
                      f"\n Komentarz: {row[4]}\n"

            after_daily_counter += 1

    # Show rich panel
    print("", Panel(Text(string, justify="center"), title="[bold orange3]CZASOINATOR"))

    # Close connection to database
    conn.close()


def show_work_yesterday(cursor, redmine_conf):
    # This variable store information about doing anything before daily
    info_daily = False
    before_daily_counter = 0
    after_daily_counter = 0
    # Replace 11:00:00 from config.ini to 110000
    daily = redmine_conf["DAILY"].replace(":", "")
    _, yesterday, _ = get_time()

    # Send query to get data from yesterday
    cursor.execute("SELECT * FROM BAZA_DANYCH WHERE DATA LIKE ?", (f"%{yesterday}%",))

    # Fetch data from query above
    rows = cursor.fetchall()

    # Empty rows variable means there's no SQL entries.
    if not rows:
        # Show rich panel
        print("", Panel(Text("\n Brak postępów! \n", justify="center"), title="[bold orange3]CZASOINATOR"))

        return

    for row in rows:

        # Split row with date: 24-11-2021 14:20:52 -> 14:20:52
        # Drop ":" from splitted data above, and compare it with daily variable
        # Also check if "daily lines" are displayed before
        if row[0].split(" ")[1].replace(":", "") < daily:
            if before_daily_counter < 1:
                string = f"\n Postępy dnia {yesterday} - przed daily:\n"

            # row_1 = row[1] is for text-formatting purposes. eg # 20000 or "Brak numeru zadania"
            row_1 = row[1]
            if row_1 is None:
                row_1 = "Brak numeru zadania!"
            else:
                row_1 = "# " + row_1
            string += f"\n\n\n {row_1}" \
                      f"\n {row[2]}\n" \
                      f"\n Spędzony czas: {row[3]}h" \
                      f"\n Komentarz: {row[4]} \n"
            info_daily = True

            before_daily_counter += 1

        else:
            if info_daily:
                # Show rich panel with data from "if" above
                print("", Panel(Text(string, justify="center"), title="[bold orange3]CZASOINATOR"))
                info_daily = False

            if after_daily_counter < 1:
                string = f"\n Postępy dnia {yesterday} - po daily:\n"

            # row_1 = row[1] is for text-formatting purposes. eg # 20000 or "Brak numeru zadania"
            row_1 = row[1]
            if row_1 is None:
                row_1 = "Brak numeru zadania!"
            else:
                row_1 = "# " + row_1
            string += f"\n\n\n {row_1}" \
                      f"\n {row[2]}\n" \
                      f"\n Spędzony czas: {row[3]}h" \
                      f"\n Komentarz: {row[4]}\n"

            after_daily_counter += 1

    # Show rich panel
    print("", Panel(Text(string, justify="center"), title="[bold orange3]CZASOINATOR"))

    # Close connection to database
    conn.close()


def add_manually_to_database(redmine, cursor):
    current_time, _, today = get_time()
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
        print(current_time, today)
        try:
            redmine.time_entry.create(issue_id=issue_id, spent_on=today,
                                      hours=time_elapsed, activity_id=8, comments=comment)
        except exception as e:
            print(f"Wystąpił błąd przy dodawaniu czasu do redmine - {e}")

        # Insert user work to database.
        cursor.execute(f"INSERT INTO BAZA_DANYCH (DATA, NUMER_ZADANIA, NAZWA_ZADANIA, SPEDZONY_CZAS, KOMENTARZ) VALUES "
                       f"(?, ?, ?, ?, ?)", (current_time, issue_id, issue_name, time_elapsed, comment,))

        # Apply changes and close connection to sqlite database.
        conn.commit()
        conn.close()

        # Show rich panel
        print("", Panel(Text(f"\nDodano!"
                             f"\n\nSpędzony czas: {time_elapsed}"
                             f"\nKomentarz: {comment}\n", justify="center"), title="[bold orange3]CZASOINATOR"))


def add_own_to_database(cursor):
    current_time, _, _ = get_time()

    issue_name = input("\nPodaj nazwę zadania > ")
    time_elapsed = input("Podaj czas spędzony nad zadaniem - oddzielony kropką np 2.13 > ")

    # Insert user work to database.
    cursor.execute(f"INSERT INTO BAZA_DANYCH (DATA, NAZWA_ZADANIA, SPEDZONY_CZAS) VALUES "
                   f"(?, ?, ?)", (current_time, issue_name, time_elapsed,))

    # Apply changes and close connection to sqlite database.
    conn.commit()
    conn.close()

    # Show rich panel
    print("", Panel(Text(f"\nDodano!"
                         f"\n\nNazwa Zadania: {issue_name}"
                         f"\nSpędzony czas: {time_elapsed}\n", justify="center"), title="[bold orange3]CZASOINATOR"))


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
    redmine_conf = init()
    while choose != str(7):
        redmine, cursor, choose, conn = get_started(redmine_conf)
        if choose == str(1):
            issue_stopwatch(redmine, cursor, conn)
        if choose == str(2):
            show_work_today(cursor, redmine_conf)
        if choose == str(3):
            show_work_yesterday(cursor, redmine_conf)
        if choose == str(4):
            add_manually_to_database(redmine, cursor)
        if choose == str(5):
            add_own_to_database(cursor)
        if choose == str(6):
            stats(cursor)

        if choose == "?":
            info = False
