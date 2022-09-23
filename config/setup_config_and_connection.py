import configparser
import logging
from helpers.colors import get_color
from redminelib import Redmine

logging.basicConfig(filename='czasoinator.log', encoding='utf-8', level=logging.DEBUG, format='[%(asctime)s] %('
                                                                                              'levelname)s: %('
                                                                                              'message)s')
                                                                                              
def parse_config():
    # Set configparser and read config.
    logging.info("Parsowanie config.ini...")
    config = configparser.ConfigParser()
    config.read("config/config.ini")
    redmine_conf = config['REDMINE']
    logging.info("Parsowanie ukończone.")

    # Setup frame title: display CZASOINATOR - {split address from config}
    frame_title = f"[{get_color('bold_orange')}]CZASOINATOR[/{get_color('bold_orange')}] - [bold red]{redmine_conf['ADDRESS'].split('://')[1]}[/bold red]"

    # Make a connection to Redmine.
    logging.info(f"Próba połączenia z serwerem {redmine_conf['ADDRESS']}...")
    redmine = Redmine(redmine_conf["ADDRESS"], key=redmine_conf["API_KEY"])

    return redmine, redmine_conf, frame_title