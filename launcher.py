import schedule
import time
import itertools, sys
import pprint
import logging
import traceback
from termcolor import cprint
from automated_brander import main_brander
from helpers import send_notification

def log_isRunning():
    pp = pprint.PrettyPrinter(width=41, compact=True)
    all_jobs = schedule.get_jobs()
    print("_____________________________")
    pp.pprint(all_jobs)
    print("_____________________________")
    cprint('\nAutomated scheduler running.... DO NOT CLOSE WINDOW', 'red')
    cprint('\nCtrl-C to quit', 'yellow', attrs=['bold'])

def job():
    # An error in one run must not stop the scheduler
    try:
        main_brander()
    except Exception as err:
        traceback.print_exc()
        logging.exception("Brander run failed")
        send_notification(f" ERROR Brander run failed: {err}. Scheduler still running.", "ERROR")
    log_isRunning()

def launcher():
    # Using 'pip install schedule'
    # see examples, https://schedule.readthedocs.io/en/stable/examples.html
    # Run job every day at specific HH:MM and next HH:MM:SS
    schedule.every().day.at("09:10").do(job)
    schedule.every().day.at("16:00").do(job)

    cprint('\nAutomated scheduler launched....', 'green')
    log_isRunning()
    spinner = itertools.cycle(['-', '/', '|', '\\']) # setup for Looping cursor to indicate working/waiting.

    while True:
        schedule.run_pending()            # run schedules created
        time.sleep(1)                     # slow things down a bit...
        if sys.stdout.isatty():           # no spinner when running under launchd (output goes to a log file)
            sys.stdout.write(next(spinner))   # write the next character for looping cursor
            sys.stdout.flush()                # flush stdout buffer (actual char display)
            sys.stdout.write('\b')            # erase the last written char

if __name__ == '__main__':
    launcher()
