from rich.console import Console
import logging

# File imports
from helpers.get_today_or_yesterday import get_time
from helpers.exit_handler import exit_program
from helpers.options import show_options
from modules.days_off import show_days_off
from modules.issue_stopwatch import start_issue_stopwatch
from modules.show_today_or_yesterday_work import show_work
from modules.add_work_to_redmine import add_manually_to_redmine
from modules.show_work import show_assigned_to_user
from modules.stats import show_stats
from helpers.greet_user import welcome

logging.basicConfig(filename='czasoinator.log', encoding='utf-8', level=logging.DEBUG, format='[%(asctime)s] %('
                                                                                              'levelname)s: %('
                                                                                              'message)s')
info = False
console = Console()
logging.info("Aplikacja została uruchomiona")

if __name__ == "__main__":
    welcome()

    # Main loop of script. Here we have "info" variable, which store True/False about showing options to choose.
    while True:
        if info is False:
            show_options()
            info = True
    
        choose = input("\nWybór > ")
        
        if choose == str(1):
            start_issue_stopwatch()
        if choose == str(2):
            _, _, day = get_time()
            show_work(day)
        if choose == str(3):
            _, yesterday, _ = get_time()
            show_work(yesterday)
        if choose == str(4):
            add_manually_to_redmine()
        if choose == str(5):
            show_assigned_to_user()
        if choose == str(6):
            show_days_off()
        if choose == str(7):
            show_stats()
        if choose == str(8):
            exit_program(0)
        if choose == "?":
            info = False
