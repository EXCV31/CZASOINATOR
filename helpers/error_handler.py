import logging

logging.basicConfig(filename='czasoinator.log', encoding='utf-8', level=logging.DEBUG, format='[%(asctime)s] %('
                                                                                              'levelname)s: %('
                                                                                              'message)s')

def display_error(text):
    """
    Function used for displaying errors - normal and critical. Often used before exit_program().

    Keyword arguments:
    text -- Text of error displayed in frame.
    """
    print("")
    console.print(
        Panel(Text(f"\n{text}\n", justify="center", style="white"), style=get_color("red")))
    logging.error(text)