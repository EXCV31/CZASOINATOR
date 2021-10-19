import datetime
import requests.exceptions
from redminelib import Redmine
import redminelib.exceptions
import calendar
import time
from datetime import date
import sys
import sqlite3
from rich import print as print
from rich.panel import Panel
from rich.text import Text
from rich.console import Console
from rich.table import Table
import configparser
from deep_translator import GoogleTranslator

stop = ""
choose = 0
info = False
console = Console()


def welcome_user(redmine_conf):
    global frame_title
    # Make a connection to Redmine.
    redmine = Redmine(redmine_conf["ADDRESS"], key=redmine_conf["API_KEY"])
    try:
        user = redmine.user.get('current')
    except requests.exceptions.ConnectionError:
        display_error("Wystąpił problem z połączeniem do Redmine. Sprawdź stan sieci!")
        input()
        sys.exit(0)
    except redminelib.exceptions.AuthError:
        display_error("Użyto nieprawidłowych danych logowania!")
        input()
        sys.exit(0)

    frame_title = f"[bold orange3]CZASOINATOR[/bold orange3] - [bold red]{redmine_conf['ADDRESS'].split('://')[1]}[/bold red]"

    print(Panel(Text("\nZalogowano pomyślnie!\n"
                     f"\nUżytkownik: {user.firstname} {user.lastname}"
                     f"\nNa redmine od: {str(user.created_on)}\n", justify="center", style="white")
                , style=get_color("green"), title=frame_title))

    return redmine


def display_error(text):
    global frame_title
    print("")
    print(Panel(Text(f"\n{text}\n", justify="center", style="white"), style=get_color("red"), title=frame_title))


def get_color(color):
    if color == "bold_red":
        return "bold #ff4242"
    if color == "red":
        return "#ff4242"
    if color == "bold_orange":
        return "bold #d99011"
    if color == "orange":
        return "#d99011"
    if color == "bold_green":
        return "bold #25ba14"
    if color == "green":
        return "#25ba14"
    if color == "bold_purple":
        return "bold #c071f5"
    if color == "bold_pink":
        return "bold #ff00ee"
    if color == "light_blue":
        return "#6bb0c9"
    if color == "bold_blue":
        return "bold #2070b2"


def get_time():
    # Get and format current date
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

    # Split current time from 2021-12-10 22:32:52 to 2021-12-10
    today = current_time.split(" ")[0]

    return current_time, yesterday, today


def init():
    # Set configparser, read config and setup redmine_conf variable
    config = configparser.ConfigParser()
    config.read("config.ini")
    redmine_conf = config['REDMINE']

    return redmine_conf


def get_started(frame_title):
    global choose
    global info

    # Info variable is being used to show user a legend of possible options.
    if not info:
        # Show rich panel
        print(Panel(Text("\nWybierz co chcesz zrobić:\n"
                         "\n1. Uruchom zliczanie czasu"
                         "\n2. Sprawdź dzisiejsze postępy"
                         "\n3. Sprawdź wczorajsze postępy"
                         "\n4. Dorzuć ręcznie czas do zadania"
                         "\n5. Dorzuć ręcznie czas do bazy - własne zadanie"
                         "\n6. Sprawdź zadania przypisane do Ciebie"
                         "\n7. Statystyki"
                         "\n8. Wyjście\n", justify="center", style="white"), style=get_color("light_blue"),
                    title=frame_title))

        # Turn off info after showing legend once.
        info = True

    # Ask user to choose a module
    choose = input("\nWybór > ")

    # Set up sqlite
    conn = sqlite3.connect(f"czasoinator.sqlite")
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS BAZA_DANYCH (DATA TEXT, NUMER_ZADANIA TEXT, "
        "NAZWA_ZADANIA TEXT, SPEDZONY_CZAS TEXT, KOMENTARZ TEXT);")
    return cursor, choose, conn


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
        display_error("403 - Brak dostępu do wybranego zadania!")
        return
    except redminelib.exceptions.ResourceNotFoundError:
        display_error("404 - Wybrane zadanie nie istnieje!")
        return

    # Show rich panel
    print("", Panel(Text(f"\nWybrano zadanie: {issue_name}\n", justify="center", style="white"),
                    style=get_color("light_blue"), title="[bold orange3]CZASOINATOR"),
          "")

    # Wait for input
    while stop != "k":
        stop = console.input(
            f'[{get_color("bold_green")}]Rozpoczęto mierzenie czasu![/{get_color("bold_green")}] \n\nGdy zakończysz pracę nad zadaniem wpisz [{get_color("bold_green")}]k[/{get_color("bold_green")}], lub [{get_color("bold_red")}]x[/{get_color("bold_red")}] aby anulować > ')
        if stop.lower() == "x":
            return

    # Stop stopwatch and calculate timestamp to hours eg. 2.63
    stop_timestamp = int(calendar.timegm(time.gmtime()))
    time_elapsed = round(((stop_timestamp - start_timestamp) / 60 / 60), 2)

    # Show rich panel
    print("", Panel(
        Text(f"\nZakończono pracę nad #{issue_id}!\n Spędzony czas: {time_elapsed} godzin.\n ", justify="center",
             style="white"), style=get_color("light_blue"),
        title="[bold orange3]CZASOINATOR"))

    comment = input("\nDodaj komentarz > ")

    if input("Dodać czas do zadania w redmine? t/n > ").lower() == "t":

        # Catch problems with connection, permissions etc.
        try:
            redmine.time_entry.create(issue_id=issue_id, spent_on=date.today(),
                                      hours=time_elapsed, activity_id=8, comments=comment)

            # Translate comment from user input above
            translated_comment = GoogleTranslator(source="auto", target="en").translate(comment)

            # Show rich panel
            print("", Panel(Text(f"\nDodano!"
                                 f"\n\nSpędzony czas: {time_elapsed}"
                                 f"\nKomentarz: {comment}\n"
                                 f"\nPamiętaj o git commit -m \"TASK#{issue_id}: {translated_comment}\" && git push\n",
                                 justify="center", style="white"), style=get_color("green"),
                            title="[bold orange3]CZASOINATOR"))
        except Exception as e:
            print(f"Wystąpił błąd przy dodawaniu czasu do redmine - {e}")

    current_time, _, _ = get_time()

    # Insert user work to database
    cursor.execute(f"INSERT INTO BAZA_DANYCH (DATA, NUMER_ZADANIA, NAZWA_ZADANIA, SPEDZONY_CZAS, KOMENTARZ) VALUES "
                   f"(?, ?, ?, ?, ?)", (current_time, issue_id, issue_name, time_elapsed, comment))

    # Apply changes and close connection to sqlite database
    conn.commit()


def show_work(cursor, redmine_conf, day):
    """
    Some magic happeened here!
    With user input from get_started() day variable is set to today or yesterday.
    It's set by choosing in "if __name__ == __main__" by get_time function
    which returns current time, yesterday and today.
    """
    # This variable store information about doing anything before daily
    info_daily = False
    # Replace 11:00:00 from config.ini to 110000
    daily = redmine_conf["DAILY"].replace(":", "")

    # Send query to get data from today
    cursor.execute("SELECT * FROM BAZA_DANYCH WHERE DATA LIKE ?", (f"%{day}%",))

    # Fetch data from query above
    rows = cursor.fetchall()

    # Empty rows variable means there's no SQL entries.
    if not rows:
        # Show rich panel
        print("", Panel(Text("\n Brak postępów! \n", justify="center", style="white"), style=get_color("orange"),
                        title="[bold orange3]CZASOINATOR"))

        return

    # Generate column to show data from sql
    table = Table(show_header=True, header_style=get_color("bold_purple"),
                  title=f'[{get_color("bold_blue")}]POSTĘPY DNIA {day}', show_lines=True)
    table.add_column("Data rozpoczęcia", justify="center")
    table.add_column("Nazwa zadania", justify="center")
    table.add_column("Spędzony czas", justify="center")
    table.add_column("Komentarz", justify="center")
    table.add_column("Numer zadania", justify="center")

    for row in rows:

        # Set up colors for spent time.
        # 00:00-02:00 - Green
        # 02:00-04:00 - Orange
        # 04:00+ - Red
        if float(row[3]) <= 2.00:
            color = get_color("bold_green")
        elif float(row[3]) <= 4.00:
            color = get_color("bold_orange")
        else:
            color = get_color("bold_red")

        # Split row with date: 24-11-2021 14:20:52 -> 14:20:52
        # Drop ":" from splitted data above, and compare it with daily variable
        # Also check if "daily lines" are displayed before
        if row[0].split(" ")[1].replace(":", "") > daily and info_daily is False:
            table.add_row(f'{day} {redmine_conf["DAILY"]}',
                          f'[{get_color("bold_pink")}]Daily![/{get_color("bold_pink")}]', '', '',
                          f'')
            info_daily = True

        # row_1 = row[1] is for text-formatting purposes. eg # 20000 or "Empty issue number"
        row_1 = row[1]

        # Same as above, eg 4.86 -> 04:51.
        time = float(row[3])
        minutes = 60 * (time % 1)
        time = "0%d:%02d" % (time, minutes)

        # Append row to table with recognizing that info about work has issue number
        if row_1 is None:
            table.add_row(row[0], row[2], f"[{color}]{time}[/{color}]", row[4],
                          f"[{get_color('bold_red')}]Brak![/{get_color('bold_red')}]")
        else:
            table.add_row(row[0], row[2], f"[{color}]{time}[/{color}]", row[4],
                          f"[{get_color('light_blue')}][link={redmine_conf['ADDRESS']}/issues/{row[1]}]#{row[1]}[/link][/{get_color('light_blue')}]")

    # Show table with work time
    console.print(table)

    # Close connection to database
    conn.close()


def add_manually_to_database(redmine, cursor):
    current_time, _, today = get_time()
    issue_id = input("\nPodaj numer zadania > ")

    # Get issue name
    try:
        issue_name = str(redmine.issue.get(issue_id))

    except redminelib.exceptions.ForbiddenError:
        display_error("403 - Brak dostępu do wybranego zadania!")
        return

    except redminelib.exceptions.ResourceNotFoundError:
        display_error("404 - Wybrane zadanie nie istnieje!")
        return

    # Show rich panel
    print("",
          Panel(Text(f"\nWybrano zadanie: {issue_name}\n", justify="center", style="white"),
                style=get_color("light_blue"), title="[bold orange3]CZASOINATOR"))

    question = input("\nKontynuować? t/n > ")

    if question.lower() == "t":

        try:
            time_elapsed = float(input("\nPodaj czas spędzony nad zadaniem - oddzielony kropką np 2.13 > "))
        except ValueError:
            display_error("Nieprawidłowa wartość dla pola: Spędzony czas")
            return

        comment = input("Dodaj komentarz > ")
        # Catch problems with connection, permissions etc.
        try:
            redmine.time_entry.create(issue_id=issue_id, spent_on=today,
                                      hours=time_elapsed, activity_id=8, comments=comment)
        except Exception as e:
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
                             f"\nKomentarz: {comment}\n", justify="center", style="white"), style=get_color("green"),
                        title="[bold orange3]CZASOINATOR"))


def add_own_to_database(cursor):
    current_time, _, _ = get_time()

    issue_name = input("\nPodaj nazwę zadania > ")
    try:
        time_elapsed = float(input("\nPodaj czas spędzony nad zadaniem - oddzielony kropką np 2.13 > "))
    except ValueError:
        display_error("Nieprawidłowa wartość dla pola: Spędzony czas")
        return
    comment = input("\nDodaj komentarz > ")
    # Insert user work to database.
    cursor.execute(f"INSERT INTO BAZA_DANYCH (DATA, NAZWA_ZADANIA, SPEDZONY_CZAS, KOMENTARZ) VALUES "
                   f"(?, ?, ?, ?)", (current_time, issue_name, time_elapsed, comment,))

    # Apply changes and close connection to sqlite database.
    conn.commit()
    conn.close()

    # Show rich panel
    print("", Panel(Text(f"\nDodano!"
                         f"\n\nNazwa Zadania: {issue_name}"
                         f"\nSpędzony czas: {time_elapsed}\n", justify="center", style="white"),
                    style=get_color("green"), title="[bold orange3]CZASOINATOR"))


def show_assigned_to_user(redmine, redmine_conf):
    # "total" variable is used to represent hours spent on each issue.
    total = 0

    # Get user ID from redmine by api key
    user = redmine.user.get('current')
    user_name = str(user)
    user_id = user["id"]

    # Filter issues with "open" status assigned to use, excluding groups.
    issues = redmine.issue.filter(assigned_to_id=user_id)

    # Generate column to show data from redmine
    table = Table(show_header=True, header_style=get_color("bold_purple"),
                  title=f'[{get_color("bold_blue")}]Zadania przypisane do: {user_name}, ID: {user_id}', show_lines=True)
    table.add_column("Typ zadania", justify="center")
    table.add_column("Nazwa zadania", justify="center")
    table.add_column("Priorytet", justify="center")
    table.add_column("% ukończenia", justify="center")
    table.add_column("Spędzony czas", justify="center")
    table.add_column("Numer zadania", justify="center")
    if len(issues) > 0:

        for issue in issues:

            # Skip project name if any mentioned in config.ini
            if issue.project["name"] in [redmine_conf["EXCLUDE"]]:
                continue

            # Color matching by priority
            if str(issue.priority) == "Niski":
                priority_color = get_color("bold_green")
            elif str(issue.priority) == "Normalny":
                priority_color = get_color("bold_orange")
            else:
                priority_color = get_color("bold_red")

            # Color matching by % of completion
            if issue.done_ratio >= 66:
                done_color = get_color("bold_green")
            elif issue.done_ratio >= 33:
                done_color = get_color("bold_orange")
            else:
                done_color = get_color("bold_red")

            # Get data about hours worked and put in total variable
            for time in issue.time_entries:
                info = redmine.time_entry.get(time)
                total += info.hours

            # Add a row to the table to display it after data collection
            table.add_row(f"{issue.tracker['name']}", f"{issue.subject}",
                          f"[{priority_color}]{issue.priority}[/{priority_color}]",
                          f"[{done_color}]{str(issue.done_ratio)}[/{done_color}]", f"{str(round(total, 2))}",
                          f"[{get_color('light_blue')}][link={redmine_conf['ADDRESS']}/issues/{issue.id}]#{issue.id}[/link][/{get_color('light_blue')}]")

            # Reset variable for next issue
            total = 0

        # Show table with issues
        console.print(table)
    else:
        print("", Panel(Text(f"\nBrak zadań przypisanych do: {user_name}, {user_id}\n", justify="center",
                             style=get_color("bold_red")),
                        title="[bold orange3]CZASOINATOR"))


def stats(cursor):
    cursor.execute("SELECT SPEDZONY_CZAS FROM BAZA_DANYCH")
    rows = cursor.fetchall()
    total_hours = 0

    for row in rows:
        total_hours += float(row[0])
    total_hours = round(total_hours, 2)

    # Show rich panel
    print("", Panel(Text(f"\n Czas spędzony z CZASOINATOREM: {total_hours} godzin \n", justify="center", style="white"),
                    style=get_color("light_blue"), title="[bold orange3]CZASOINATOR"))


if __name__ == "__main__":
    redmine_conf = init()
    redmine = welcome_user(redmine_conf)
    while choose != str(8):
        cursor, choose, conn = get_started(frame_title)
        if choose == str(1):
            issue_stopwatch(redmine, cursor, conn)
        if choose == str(2):
            _, _, day = get_time()
            show_work(cursor, redmine_conf, day)
        if choose == str(3):
            _, day, _ = get_time()
            show_work(cursor, redmine_conf, day)
        if choose == str(4):
            add_manually_to_database(redmine, cursor)
        if choose == str(5):
            add_own_to_database(cursor)
        if choose == str(6):
            show_assigned_to_user(redmine, redmine_conf)
        if choose == str(7):
            stats(cursor)
        if choose == "?":
            info = False
