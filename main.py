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
from rich import box
from rich import progress_bar
from rich.progress import track, TimeElapsedColumn
import configparser
import logging
from timeit import default_timer as timer

logging.basicConfig(filename='czasoinator.log', encoding='utf-8', level=logging.DEBUG, format='[%(asctime)s] %(levelname)s: %(message)s')

stop = ""
choose = 0
info = False
console = Console()

logging.info("Aplikacja została uruchomiona")


def exit_program():
    '''Store logs about exit and... just exit'''

    logging.info("Wyjście z aplikacji")
    sys.exit(0)


def welcome_user(redmine_conf):
    ''' Make a connection to redmine, and greet user.'''

    global frame_title
    frame_title = f"[bold orange3]CZASOINATOR[/bold orange3] - [bold red]{redmine_conf['ADDRESS'].split('://')[1]}[/bold red]"

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

    logging.info(f"Połączenie zakończone sukcesem. Zalogowany jako {user.firstname} {user.lastname}")
    print(Panel(Text("\nZalogowano pomyślnie!\n"
                     f"\nUżytkownik: {user.firstname} {user.lastname}"
                     f"\nNa Redmine od: {str(user.created_on)}\n", justify="center", style="white")
                , style=get_color("green"), title=frame_title))
    return redmine


def display_error(text):
    '''
    Function used for displaying errors - normal and critical. Often used before exit_program().

    Keyword arguments:
    text -- Text of error displayed in frame.
    '''
    global frame_title
    print("")
    print(Panel(Text(f"\n{text}\n", justify="center", style="white"), style=get_color("red"), title=frame_title))
    logging.error(text)


def get_color(color):
    ''' 
    Function is called when there's need for color, especially for rendering tables.

    Keyword arguments:
    color -- Used in matching color with hex code below.
    '''

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
    '''
    Return current time, yesterday and today. If today is Monday,
    function will return Friday as yesterday.
    '''
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
    '''Set configparser, read config and setup redmine_conf variable'''

    logging.info("Parsowanie config.ini...")
    config = configparser.ConfigParser()
    config.read("config.ini")
    redmine_conf = config['REDMINE']
    logging.info("Parsowanie ukończone.")
    return redmine_conf


def get_started(frame_title):
    '''
    Point where program start with user interaction.

    Keyword arguments:
    frame_title -- The part of the frame that displays in the middle of it. 
    It contains information such as the name of the program and the address of the redmine it is connected to.
    '''
    global choose
    global info

    # Info variable is being used to show user a legend of possible options.
    if not info:
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


def issue_stopwatch(redmine, cursor, conn):
    '''
    The function is responsible for measuring the time for the task selected by the user. 
    After the measurement is completed, it places the collected data in the database.

    Keyword arguments:
    redmine -- Connection to redmine.
    cursor  -- Cursor for executing SQL commands.
    conn    -- Connection to database.
    '''

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

    print("", Panel(Text(f"\nWybrano zadanie: {issue_name}\n", justify="center", style="white"),
                    style=get_color("light_blue"), title="[bold orange3]CZASOINATOR"),
          "")
    logging.info(f"Rozpoczęto mierzenie czasu dla zadania #{issue_id}")
    # Wait for input from user, to stop the stopwatch.
    while stop != "k":
        stop = console.input(
            f'[{get_color("bold_green")}]Rozpoczęto mierzenie czasu![/{get_color("bold_green")}] \n\nGdy zakończysz pracę nad zadaniem wpisz [{get_color("bold_green")}]k[/{get_color("bold_green")}], lub [{get_color("bold_red")}]x[/{get_color("bold_red")}] aby anulować > ')
        if stop.lower() == "x":
            return
    logging.info(f"Zakończono mierzenie czasu dla zadania #{issue_id}")

    # Stop stopwatch and calculate timestamp to hours eg. 2.63.
    stop_timestamp = int(calendar.timegm(time.gmtime()))
    time_elapsed = round(((stop_timestamp - start_timestamp) / 60 / 60), 2)

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
        except Exception as e:
            print(f"Wystąpił błąd przy dodawaniu czasu do redmine - {e}")
            logging.error(e)
            return

        logging.info(f"Dodano czas do redmine dla zadania #{issue_id}.")

        print("", Panel(Text(f"\nDodano!"
                            f"\n\nSpędzony czas: {time_elapsed}"
                            f"\nKomentarz: {comment}\n",
                            justify="center", style="white"), style=get_color("green"),
                            title="[bold orange3]CZASOINATOR"))

    current_time, _, _ = get_time()

    # Insert user work to database.
    cursor.execute(f"INSERT INTO BAZA_DANYCH (DATA, NUMER_ZADANIA, NAZWA_ZADANIA, SPEDZONY_CZAS, KOMENTARZ) VALUES "
                   f"(?, ?, ?, ?, ?)", (current_time, issue_id, issue_name, time_elapsed, comment))
    logging.info("Umieszczono przepracowany czas w bazie danych.")

    # Apply changes and close connection to sqlite database.
    conn.commit()
    logging.info("Zacommitowano zmiany w bazie danych.")


def show_work(cursor, redmine_conf, day):
    '''
    Some magic happeened here!
    With user input from get_started() day variable is set to today or yesterday.
    It's set by choosing in "if __name__ == __main__" by get_time function
    which returns current time, yesterday and today.
    '''

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
        print("", Panel(Text("\n Brak postępów! \n", justify="center", style="white"), style=get_color("orange"),
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
        # Drop ":" from splitted data above, and compare it with daily variable.
        # Also check if "daily lines" are displayed before.
        if row[0].split(" ")[1].replace(":", "") > daily and info_daily is False:
            table.add_row(f'{day} {redmine_conf["DAILY"]}',
                          f'[{get_color("bold_pink")}]Daily![/{get_color("bold_pink")}]', '', '',
                          f'')
            info_daily = True

        # row_1 = row[1] is for text-formatting purposes. eg # 20000 or "Empty issue number".
        row_1 = row[1]

        # Same as above, eg 4.86 -> 04:51.
        time_spent = float(row[3])
        minutes = 60 * (time_spent % 1)
        time_spent = "0%d:%02d" % (time_spent, minutes)

        # Append row to table with recognizing that info about work has issue number.
        if row_1 is None:
            table.add_row(row[0], row[2], f"[{color}]{time_spent}[/{color}]", row[4],
                          f"[{get_color('bold_red')}]Brak![/{get_color('bold_red')}]")
        else:
            table.add_row(row[0], row[2], f"[{color}]{time_spent}[/{color}]", row[4],
                          f"[{get_color('light_blue')}][link={redmine_conf['ADDRESS']}/issues/{row[1]}]#{row[1]}[/link][/{get_color('light_blue')}]")
    
    table.caption = f"Sumaryczny czas w tym dniu: {total_hours} godzin"
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

        logging.info(f"Dodano manualnie przepracowany czas do redmine pod zadaniem #{issue_id} - {time_elapsed} godzin.")
        # Insert user work to database.
        cursor.execute("INSERT INTO BAZA_DANYCH (DATA, NUMER_ZADANIA, NAZWA_ZADANIA, SPEDZONY_CZAS, KOMENTARZ) VALUES "
                       "(?, ?, ?, ?, ?)", (current_time, issue_id, issue_name, time_elapsed, comment,))
        logging.info(f"Umieszczono w bazie danych dodany manualnie przepracowany czas pod zadaniem #{issue_id} - {time_elapsed} godzin.")

        # Apply changes and close connection to sqlite database.
        conn.commit()
        logging.info("Zakommitowano zmiany w bazie danych.")
        conn.close()

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
    logging.info(f"Umieszczono w bazie danych dodany manualnie przepracowany czas - bez zadania - {time_elapsed} godzin.")


    # Apply changes and close connection to sqlite database.
    conn.commit()
    logging.info("Zakommitowano zmiany w bazie danych.")
    conn.close()

    print("", Panel(Text(f"\nDodano!"
                         f"\n\nNazwa Zadania: {issue_name}"
                         f"\nSpędzony czas: {time_elapsed}\n", justify="center", style="white"),
                    style=get_color("green"), title="[bold orange3]CZASOINATOR"))


def show_assigned_to_user(redmine, redmine_conf):
    '''
    The function is to connect to redmine, and retrieve all tasks 
    in "Open" status that are assigned to the user. 
    The function also includes a filter that skips tasks that are
    in projects defined in config.ini, in the "EXCLUDE" section.

    Keyword arguments:
    redmine -- Connection to redmine.
    redmine_conf -- config.ini stored in variable, used for pbtaining EXCLUDE key.
    '''

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

    logging.info("Rozpoczęto przetwawrzanie zadań przypisanych do użytkownika...")
    start = timer()
    
    # Filter issues with "open" status assigned to use, excluding groups.
    issues = redmine.issue.filter(assigned_to_id=user_id)

    if len(issues) > 0:

        progress_bar.ProgressBar(completed=0, width=None, pulse=False, style='bar.back',
        complete_style='bar.complete', finished_style='bar.finished', pulse_style='bar.pulse', animation_time=None)
        for issue in track(issues, description="Pobieranie danych..."):
            time.sleep(0.01)
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

            # Add a row to the table to display it after data collection.
            table.add_row(f"{issue.tracker['name']}",
                          f"{issue.subject}",
                          f"[{priority_color}]{issue.priority}[/{priority_color}]",
                          f"[{status_color}]{str(issue.status)}[/{status_color}]",
                          f"[{done_color}]{str(issue.done_ratio)}[/{done_color}]", f"{str(round(total, 2))}",
                          f"[{get_color('light_blue')}][link={redmine_conf['ADDRESS']}/issues/{issue.id}]#{issue.id}[/link][/{get_color('light_blue')}]")

            # Reset variable for next issue.
            total = 0

        end = timer()
        logging.info(f"Zakończono przetwarzanie zadań przypisanych do usera. Czas operacyjny: {end - start} sekund")        

        # Show table with issues.
        console.print(table)
        

    else:
        end = timer()
        logging.info(f"Zakończono przetwarzanie zadań przypisanych do usera. Brak danych do wyświetlenia.")
        print("", Panel(Text(f"\nBrak zadań przypisanych do: {user_name}, {user_id}\n", justify="center",
                             style=get_color("bold_red")),
                        title="[bold orange3]CZASOINATOR"))


def stats(cursor):
    '''
    Show stats about usage to user - data is taken from database, not from redmine.

    Keyword arguments:
    cursor  -- Cursor for executing SQL commands.
    '''
    cursor.execute("SELECT SPEDZONY_CZAS FROM BAZA_DANYCH")
    rows = cursor.fetchall()
    total_hours = 0

    for row in rows:
        total_hours += float(row[0])
    total_hours = round(total_hours, 2)

    print("", Panel(Text(f"\n Czas spędzony z CZASOINATOREM: {total_hours} godzin \n", justify="center", style="white"),
                    style=get_color("light_blue"), title="[bold orange3]CZASOINATOR"))


if __name__ == "__main__":
    redmine_conf = init()
    redmine = welcome_user(redmine_conf)
    while True:
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
            add_manually_to_redmine(redmine, cursor)
        if choose == str(5):
            add_own_to_database(cursor)
        if choose == str(6):
            show_assigned_to_user(redmine, redmine_conf)
        if choose == str(7):
            stats(cursor)
        if choose == str(8):
            exit_program()
        if choose == "?":
            info = False
