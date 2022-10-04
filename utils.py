from datetime import datetime


def log(message):
    """
    Print log message to stdout with current time.
    :param message: string
    """
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message)
