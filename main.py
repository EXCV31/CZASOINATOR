import datetime
import requests.exceptions
from redminelib import Redmine
import redminelib.exceptions
import calendar
import time
from datetime import date
import sys
import sqlite3
from rich.panel import Panel
from rich.text import Text
from rich.console import Console
from rich.table import Table
from rich import box
from rich.progress import BarColumn, Progress, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
import configparser
import logging
from timeit import default_timer as timer
import re
import platform
import subprocess

logging.basicConfig(filename='czasoinator.log', encoding='utf-8', level=logging.DEBUG, format='[%(asctime)s] %('
                                                                                              'levelname)s: %('
                                                                                              'message)s')

stop = ""
choose = 0
info = False
console = Console()

logging.info("Aplikacja została uruchomiona")


def welcome_user():
    """Parse config, log into redmine and greet user."""

    global frame_title
    global redmine_conf
    console.rule(
        f"[{get_color('bold_orange')}]CZASOINATOR[/{get_color('bold_orange')}] - Trwa ładowanie aplikacji...", )

    # Set configparser and read config.
    logging.info("Parsowanie config.ini...")
    config = configparser.ConfigParser()
    config.read("config.ini")
    redmine_conf = config['REDMINE']
    logging.info("Parsowanie ukończone.")

    # Setup frame title: display CZASOINATOR - {split address from config}
    frame_title = f"[{get_color('bold_orange')}]CZASOINATOR[/{get_color('bold_orange')}] - [bold red]{redmine_conf['ADDRESS'].split('://')[1]}[/bold red]"

    # Make a connection to Redmine.
    logging.info(f"Próba połączenia z serwerem {redmine_conf['ADDRESS']}...")
    redmine = Redmine(redmine_conf["ADDRESS"], key=redmine_conf["API_KEY"])
    try:
        user = redmine.user.get('current')
    except requests.exceptions.ConnectionError:
        display_error("Wystąpił problem z połączeniem do Redmine. Sprawdź stan sieci!")
        input("\nWciśnij ENTER aby zakończyć działanie programu... > ")
        exit_program()
    except redminelib.exceptions.AuthError:
        display_error("Użyto nieprawidłowych danych logowania!")
        input("\nWciśnij ENTER aby zakończyć działanie programu... > ")
        exit_program()
    except redminelib.exceptions.ForbiddenError:
        display_error("Brak dostępu do danych API! Skontaktuj się z administratorem sieci.")
        input("\nWciśnij ENTER aby zakończyć działanie programu... > ")
        exit_program()

    # Clear terminal
    if platform.system() == "Linux" or platform.system() == "Darwin":
        subprocess.run("clear")
    else:
        subprocess.run("cls")

    logging.info(f"Połączenie zakończone sukcesem. Zalogowany jako {user.firstname} {user.lastname}")

    console.print(Panel(Text("\nZalogowano pomyślnie!\n"
                             f"\nUżytkownik: {user.firstname} {user.lastname}"
                             f"\nNa Redmine od: {str(user.created_on)}\n", justify="center", style="white")
                        , style=get_color("green"), title=frame_title))

    # It just better look with that.
    time.sleep(0.5)
    return redmine


def display_error(text):
    """
    Function used for displaying errors - normal and critical. Often used before exit_program().

    Keyword arguments:
    text -- Text of error displayed in frame.
    """
    print("")
    console.print(
        Panel(Text(f"\n{text}\n", justify="center", style="white"), style=get_color("red"), title=frame_title))
    logging.error(text)


def get_color(color):
    """
    Function is called when there's need for color, especially for rendering tables.

    Keyword arguments:
    color -- Used in matching color with hex code below.
    """

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
    """
    Return current time, yesterday and today. If today is Monday,
    function will return Friday as yesterday.
    """
    # Get and format current date
    now = datetime.datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    # Check if today is monday - used for valid "yesterday" when it's weekend. If today is monday, yesterday is friday.
    if now.weekday() == 0:
        yesterday = now - datetime.timedelta(days=3)
        yesterday = str(yesterday).split(" ")[0]
    else:
        yesterday = now - datetime.timedelta(days=1)
        yesterday = str(yesterday).split(" ")[0]

    # Split current time from 2021-12-10 22:32:52 to 2021-12-10
    today = current_time.split(" ")[0]

    return current_time, yesterday, today


def float_to_hhmm(float_time):
    """
    Change float time to HH:MM format.

    Keyword arguments:
    float_time -- time in float format e.g  1.75
    """

    # Multiply float time by 60 to get minutes, split into hours and minutes
    float_time = float_time * 60
    hours, minutes = divmod(float_time, 60)

    # Drop floating points numbers e.g. 41.39999999999998 -> 41,
    # then cast to str to add trailing or leading zero - to get always 2-digit minutes.
    minutes = str(int(minutes))
    if len(minutes) == 1 and minutes.startswith("0"):
        minutes += "0"
    elif len(minutes) == 1 and int(minutes) > 0:
        minutes = "0" + minutes

    return f"{int(hours)}:{minutes}"


def get_started(frame_title):
    """
    Point where program start with user interaction.

    Keyword arguments:
    frame_title -- The part of the frame that displays in the middle of it.
    It contains information such as the name of the program and the address of the redmine it is connected to.
    """
    global choose
    global info

    # Info variable is being used to show user a legend of possible options.
    if not info:
        console.print(Panel(Text("\nWybierz co chcesz zrobić:\n"
                                 "\n1. Uruchom zliczanie czasu"
                                 "\n2. Sprawdź dzisiejsze postępy"
                                 "\n3. Sprawdź wczorajsze postępy"
                                 "\n4. Dorzuć ręcznie czas do zadania"
                                 "\n5. Sprawdź zadania przypisane do Ciebie"
                                 "\n6. Statystyki"
                                 "\n7. Wyjście\n", justify="center", style="white"), style=get_color("light_blue"),
                            title=frame_title))
        logging.info("Pokazano listę opcji do wyboru.")

        # Turn off info after showing legend once.
        info = True

    # Ask user to choose a module
    choose = input("\nWybór > ")

    # Set up sqlite
    conn = sqlite3.connect("czasoinator.sqlite")
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS BAZA_DANYCH (DATA TEXT, NUMER_ZADANIA TEXT, "
        "NAZWA_ZADANIA TEXT, SPEDZONY_CZAS TEXT, KOMENTARZ TEXT);")
    return cursor, choose, conn


def exit_program():
    """Store logs about exit and... just exit"""

    logging.info("Wyjście z aplikacji")
    sys.exit(0)


def issue_stopwatch(redmine, cursor, conn):
    """
    The function is responsible for measuring the time for the task selected by the user.
    After the measurement is completed, it places the collected data in the database.

    Keyword arguments:
    redmine -- Connection to redmine.
    cursor  -- Cursor for executing SQL commands.
    conn    -- Connection to database.
    """

    # Stop variable is used to stop the stopwatch.
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

    console.print("", Panel(Text(f"\nWybrano zadanie: {issue_name}\n", justify="center", style="white"),
                            style=get_color("light_blue"), title="[bold orange3]CZASOINATOR"),
                  "")
    logging.info(f"Rozpoczęto mierzenie czasu dla zadania #{issue_id}")

    # Wait for input from user, to stop the stopwatch.
    console.print(f'[{get_color("bold_green")}]Rozpoczęto mierzenie czasu![/{get_color("bold_green")}]')
    while stop != "k":
        stop = console.input(
            f'\nGdy zakończysz pracę nad zadaniem wpisz [{get_color("bold_green")}]k[/{get_color("bold_green")}], lub [{get_color("bold_red")}]x[/{get_color("bold_red")}] aby anulować > ')
        if stop.lower() == "x":
            return
    logging.info(f"Zakończono mierzenie czasu dla zadania #{issue_id}")

    # Stop stopwatch and calculate timestamp to hours e.g 2.63.
    stop_timestamp = int(calendar.timegm(time.gmtime()))
    float_time_elapsed = round(((stop_timestamp - start_timestamp) / 60 / 60), 2)
    time_elapsed = float_to_hhmm(float_time_elapsed)

    console.print("", Panel(
        Text(f"\nZakończono pracę nad #{issue_id}!\n Spędzony czas: {time_elapsed}\n ", justify="center",
             style="white"), style=get_color("light_blue"),
        title="[bold orange3]CZASOINATOR"))

    comment = input("\nDodaj komentarz > ")

    decision = input("Dodać czas do zadania w redmine? T/n > ")
    if decision.lower() == "t" or decision == "":

        # Catch problems with connection, permissions etc.
        try:
            redmine.time_entry.create(issue_id=issue_id, spent_on=date.today(),
                                      hours=time_elapsed, activity_id=8, comments=comment)
        except Exception as e:
            print(f"Wystąpił błąd przy dodawaniu czasu do redmine - {e}")
            logging.error(e)
            return

        logging.info(f"Dodano czas do redmine dla zadania #{issue_id}.")

        console.print("", Panel(Text(f"\nDodano!"
                                     f"\n\nSpędzony czas: {time_elapsed}"
                                     f"\nKomentarz: {comment}\n",
                                     justify="center", style="white"), style=get_color("green"),
                                title="[bold orange3]CZASOINATOR"))

        current_time, _, _ = get_time()

        # Insert user work to database.
        cursor.execute(f"INSERT INTO BAZA_DANYCH (DATA, NUMER_ZADANIA, NAZWA_ZADANIA, SPEDZONY_CZAS, KOMENTARZ) VALUES "
                    f"(?, ?, ?, ?, ?)", (current_time, issue_id, issue_name, float_time_elapsed, comment))
        logging.info("Umieszczono przepracowany czas w bazie danych.")

        # Apply changes and close connection to sqlite database.
        conn.commit()
        logging.info("Zacommitowano zmiany w bazie danych.")


def show_work(cursor, day):
    """
    Some magic happeened here!
    With user input from get_started() day variable is set to today or yesterday.
    It's set by choosing in "if __name__ == __main__" by get_time function
    which returns current time, yesterday and today.
    """

    total_hours = 0

    # This variable store information about doing anything before daily.
    info_daily = False

    # Replace 11:00:00 from config.ini to 110000. It's needed for comparing time, used to render "daily" row in table.
    daily = redmine_conf["DAILY"].replace(":", "")

    # Send query to get data from today.
    cursor.execute("SELECT * FROM BAZA_DANYCH WHERE DATA LIKE ?", (f"%{day}%",))

    # Fetch data from query above.
    rows = cursor.fetchall()
    logging.info("Pobrano dane z bazy danych dotyczące przepracowanych godzin dzisiejszego lub wczorajszego dnia.")

    # Empty rows variable means there's no SQL entries.
    if not rows:
        console.print("",
                      Panel(Text("\n Brak postępów! \n", justify="center", style="white"), style=get_color("orange"),
                            title="[bold orange3]CZASOINATOR"))

        return

    # Generate column to show data from SQL.
    table = Table(show_header=True, header_style=get_color("bold_purple"),
                  title=f'[{get_color("bold_blue")}]POSTĘPY DNIA {day}', show_lines=True, box=box.DOUBLE, expand=True)

    table.add_column("Data rozpoczęcia", justify="center")
    table.add_column("Nazwa zadania", justify="center")
    table.add_column("Spędzony czas", justify="center")
    table.add_column("Komentarz", justify="center")
    table.add_column("Numer zadania", justify="center")

    for row in rows:
        total_hours += float(row[3])

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

        # Split row with date: 24-11-2021 14:20:52 -> 14:20:52.
        # Drop ":" from split data above, and compare it with daily variable.
        # Also check if "daily lines" are displayed before.
        if row[0].split(" ")[1].replace(":", "") > daily and info_daily is False:
            table.add_row(f'{day} {redmine_conf["DAILY"]}',
                          f'[{get_color("bold_pink")}]Daily![/{get_color("bold_pink")}]', '', '',
                          f'')
            info_daily = True

        # row_1 = row[1] is for text-formatting purposes. eg # 20000 or "Empty issue number".
        row_1 = row[1]

        # Same as above, eg 4.86 -> 04:51.
        time_spent = float_to_hhmm(float(row[3]))

        # Append row to table with recognizing that info about work has issue number.
        if row_1 is None:
            table.add_row(row[0], row[2], f"[{color}]{time_spent}[/{color}]", row[4],
                          f"[{get_color('bold_red')}]Brak![/{get_color('bold_red')}]")
        else:
            table.add_row(row[0], row[2], f"[{color}]{time_spent}[/{color}]", row[4],
                          f"[{get_color('light_blue')}][link={redmine_conf['ADDRESS']}/issues/{row[1]}]#{row[1]}[/link][/{get_color('light_blue')}]")
    total_hours = float_to_hhmm(total_hours)
    table.caption = f"Sumaryczny czas w tym dniu: {total_hours.split(':')[0]} godzin, {total_hours.split(':')[1]} minut"
    # Show table with work time.
    console.print(table)

    # Close connection to database.
    conn.close()


def add_manually_to_redmine(redmine, cursor):
    """
    A function used to add manually to redmine hours worked.

    Keyword arguments:
    redmine -- Connection to redmine.
    cursor  -- Cursor for executing SQL commands.
    """
    current_time, _, today = get_time()
    issue_id = input("\nPodaj numer zadania > ")

    # Get issue name
    try:
        issue_name = str(redmine.issue.get(issue_id))

    except redminelib.exceptions.ForbiddenError:
        display_error(f"403 - Brak dostępu do zadania {issue_id}!")
        return

    except redminelib.exceptions.ResourceNotFoundError:
        display_error(f"404 - zadanie {issue_id} nie istnieje!")
        return

    console.print("",
                  Panel(Text(f"\nWybrano zadanie: {issue_name}\n", justify="center", style="white"),
                        style=get_color("light_blue"), title="[bold orange3]CZASOINATOR"))

    question = input("\nKontynuować? T/n > ")

    if question.lower() == "t" or question == "":

        # This variable is used in database.
        time_elapsed = input("\nPodaj czas spędzony nad zadaniem w formacie H:MM - np 2:13 > ")

        # Check if user pass time in correct format.
        if not bool(re.match(r"\d:\d\d", time_elapsed)):
            display_error("Nieprawidłowa wartość dla pola: Spędzony czas")
            return

        # Convert H:MM to float - eg 0:45 -> 0.80
        hours, minutes = time_elapsed.split(":")
        float_time_elapsed = round((int(hours) + float(minutes) / 60), 2)

        comment = input("Dodaj komentarz > ")
        # Catch problems with connection, permissions etc.
        try:
            redmine.time_entry.create(issue_id=issue_id, spent_on=today,
                                      hours=float_time_elapsed, activity_id=8, comments=comment)
        except Exception as e:
            console.print(f"Wystąpił błąd przy dodawaniu czasu do redmine - {e}")

        logging.info(
            f"Dodano manualnie przepracowany czas do redmine pod zadaniem #{issue_id} - {time_elapsed} godzin.")
        # Insert user work to database.
        cursor.execute("INSERT INTO BAZA_DANYCH (DATA, NUMER_ZADANIA, NAZWA_ZADANIA, SPEDZONY_CZAS, KOMENTARZ) VALUES "
                       "(?, ?, ?, ?, ?)", (current_time, issue_id, issue_name, float_time_elapsed, comment,))
        logging.info(
            f"Umieszczono w bazie danych dodany manualnie przepracowany czas pod zadaniem #{issue_id} - {float_time_elapsed} godzin.")

        # Apply changes and close connection to sqlite database.
        conn.commit()
        logging.info("Zakommitowano zmiany w bazie danych.")
        conn.close()

        console.print("", Panel(Text(f"\nDodano!"
                                     f"\n\nSpędzony czas: {hours} godzin, {minutes} minut."
                                     f"\nKomentarz: {comment}\n", justify="center", style="white"),
                                style=get_color("green"),
                                title="[bold orange3]CZASOINATOR"))


def show_assigned_to_user(redmine):
    """
    The function is to connect to redmine, and retrieve all tasks
    in "Open" status that are assigned to the user.
    The function also includes a filter that skips tasks that are
    in projects defined in config.ini, in the "EXCLUDE" section.

    Keyword arguments:
    redmine      -- Connection to redmine.
    """

    progress_columns = (
        "[progress.description]{task.description}",
        BarColumn(),
        TaskProgressColumn(),
        "Minęło:",
        TimeElapsedColumn(),
        "Pozostało:",
        TimeRemainingColumn(),
    )

    # "total" variable is used to represent hours spent on each issue.
    total = 0

    # Get user ID from redmine by api key
    user = redmine.user.get('current')
    user_name = str(user)
    user_id = user["id"]

    # Generate column to show data from redmine
    table = Table(show_header=True, header_style=get_color("bold_purple"),
                  title=f'[{get_color("bold_blue")}]Zadania przypisane do: {user_name}, ID: {user_id}',
                  show_lines=True, box=box.DOUBLE, expand=True)

    table.add_column("Typ zadania", justify="center")
    table.add_column("Nazwa zadania", justify="center")
    table.add_column("Priorytet", justify="center")
    table.add_column("Status", justify="center")
    table.add_column("% ukończenia", justify="center")
    table.add_column("Spędzony czas", justify="center")
    table.add_column("Numer zadania", justify="center")

    logging.info("Rozpoczęto przetwarzanie zadań przypisanych do użytkownika...")
    start = timer()

    # Filter issues with "open" status assigned to use, excluding groups.
    issues = redmine.issue.filter(assigned_to_id=user_id)

    if len(issues) > 0:
        # Progress bar section. Progress bar has two attributes:
        # task   -- is one and only progress bar.
        # update -- function used to update progress bar in each iteration over list of issues.
        with Progress(*progress_columns, expand=True) as progress_bar:

            # Formatting :)
            console.print("")

            # Add a proggress bar.
            task = progress_bar.add_task("[blue]Pobieranie danych...", total=len(issues))
            for issue in issues:

                # Updating progress bar before processing issue, because of EXCLUDE "if" below.
                progress_bar.update(task, advance=1)

                # Delay for progress bar pretty-print.
                time.sleep(0.005)

                # Skip project name if any mentioned in config.ini.
                if issue.project["name"] in redmine_conf["EXCLUDE"].split("\n"):
                    continue

                # Color matching by priority.
                if str(issue.priority) == "Niski":
                    priority_color = get_color("bold_green")
                elif str(issue.priority) == "Normalny":
                    priority_color = get_color("bold_orange")
                else:
                    priority_color = get_color("bold_red")

                # Color matching by % of completion.
                if issue.done_ratio >= 66:
                    done_color = get_color("bold_green")
                elif issue.done_ratio >= 33:
                    done_color = get_color("bold_orange")
                else:
                    done_color = get_color("bold_red")

                # Color matching by issue status.
                if str(issue.status) == "Zablokowany":
                    status_color = get_color("bold_red")
                else:
                    status_color = "white"

                # Get data about hours worked and put in total variable.
                for time_entry in issue.time_entries:
                    info = redmine.time_entry.get(time_entry)
                    total += info.hours

                # Convert float time to HH:MM
                time_spent = float_to_hhmm(round(total, 2))

                # Add a row to the table to display it after data collection.
                table.add_row(f"{issue.tracker['name']}",
                              f"{issue.subject}",
                              f"[{priority_color}]{issue.priority}[/{priority_color}]",
                              f"[{status_color}]{str(issue.status)}[/{status_color}]",
                              f"[{done_color}]{str(issue.done_ratio)}[/{done_color}]",
                              f"{time_spent}",
                              f"[{get_color('light_blue')}][link={redmine_conf['ADDRESS']}/issues/{issue.id}]#{issue.id}[/link][/{get_color('light_blue')}]")

                # Reset variable for next issue.
                total = 0

            end = timer()
            logging.info(f"Zakończono przetwarzanie zadań przypisanych do usera. Czas operacyjny: {end - start} sekund")

            # Show table with issues.
        console.print("", table)

    else:
        end = timer()
        logging.info(
            f"Zakończono przetwarzanie zadań przypisanych do usera. Brak danych do wyświetlenia. Czas operacyjny: {end - start} sekund")
        console.print("", Panel(Text(f"\nBrak zadań przypisanych do: {user_name}, {user_id}\n", justify="center",
                                     style=get_color("bold_red")),
                                title="[bold orange3]CZASOINATOR"))


def stats(cursor):
    """
    Show stats about usage to user - data is taken from database, not from redmine.

    Keyword arguments:
    cursor  -- Cursor for executing SQL commands.
    """
    cursor.execute("SELECT SPEDZONY_CZAS FROM BAZA_DANYCH")
    rows = cursor.fetchall()
    total_hours = 0

    for row in rows:
        total_hours += float(row[0])

    # Convert float time to HH:MM
    total_hours = float_to_hhmm(total_hours)

    console.print("", Panel(Text(
        f"\n Czas spędzony z CZASOINATOREM: {total_hours.split(':')[0]} godzin, {total_hours.split(':')[1]} minut\n",
        justify="center", style="white"),
        style=get_color("light_blue"), title="[bold orange3]CZASOINATOR"))


if __name__ == "__main__":
    redmine = welcome_user()
    while True:
        cursor, choose, conn = get_started(frame_title)
        if choose == str(1):
            issue_stopwatch(redmine, cursor, conn)
        if choose == str(2):
            _, _, day = get_time()
            show_work(cursor, day)
        if choose == str(3):
            _, day, _ = get_time()
            show_work(cursor, day)
        if choose == str(4):
            add_manually_to_redmine(redmine, cursor)
        if choose == str(5):
            show_assigned_to_user(redmine)
        if choose == str(6):
            stats(cursor)
        if choose == str(7):
            exit_program()
        if choose == "?":
            info = False
