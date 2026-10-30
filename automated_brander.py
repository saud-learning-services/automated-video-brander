"""
UBC Sauder School of Business
Automated Video Branding Tool

Author: Marko Prodanovic

Main entry point for the Automated Branding Tool
Runs all 4 steps (described below)
Note: Each step is setup for independent running of their intended use.
"""

import os
import fcntl
import logging
from datetime import datetime
from termcolor import cprint
from dotenv import load_dotenv
from download_videos import download_videos
from watermark import watermark
from stitch import stitch
from upload_videos import upload_videos
from google_client.google_form_interface import GoogleFormInterface
from panopto.panopto_oauth2 import PanoptoOAuth2
from panopto.panopto_interface import Panopto
from helpers import send_notification, delete_old_archives, missing_video_tools

ROOT = os.path.dirname(os.path.abspath(__file__))

# Zipped copies of downloaded/branded videos older than this are deleted
DEFAULT_ARCHIVE_RETENTION_DAYS = 14


def main_brander():
    # All paths in the steps are relative to the project folder
    os.chdir(ROOT)
    load_dotenv()

    # Only one brander at a time (e.g. launcher.py plus a manual run)
    lock_file = open(os.path.join(ROOT, "brander.lock"), "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        cprint("Automated brander is already running. Skipping this run.", "yellow", attrs=["bold"])
        lock_file.close()
        return

    try:
        __run()
    finally:
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        lock_file.close()


def __run():
    # LOG SETUP
    now_formatted = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # force=True: launcher.py calls this repeatedly in one process, each run gets its own log file
    logging.basicConfig(
        format="%(asctime)s: %(levelname)s - %(message)s",
        filename=f"logs/{now_formatted}.log",
        level=logging.INFO,
        force=True,
    )

    if not os.getenv("NTFY_URL"):
        cprint("WARNING: NTFY_URL is not set in .env - errors will only be written to the log", "yellow", attrs=["bold"])
        logging.warning("NTFY_URL is not set in .env - notifications disabled")

    # 0
    # Check the video tools and the Panopto login before touching the form,
    # so a setup problem doesn't mark this run's requests as done
    missing_tools = missing_video_tools()
    if missing_tools:
        cprint(f"\n{', '.join(missing_tools)} not found. Install ffmpeg in the environment (see README).", "red")
        send_notification(f" ERROR {', '.join(missing_tools)} not found, nothing processed. Requests will be retried next run.", "ERROR")
        return

    try:
        __check_panopto_login()
    except Exception as err:
        cprint(f"\nPanopto login failed: {err}", "red")
        send_notification(f" ERROR Panopto login failed, nothing processed. Requests will be retried next run. ({err})", "ERROR")
        return

    # Get data from google forms - archive previous spec sheet
    try:
        google = GoogleFormInterface()
        run_started = google.generate_specs()
    except Exception as err:
        cprint(f"\nCould not read the Google Form responses: {err}", "red")
        send_notification(f" ERROR Could not read the Google Form responses, nothing processed. ({err})", "ERROR")
        return
    google.save_last_run(run_started)

    # 1
    # Downloads all streams of video specified in Source URL column (in specs.csv)
    if not download_videos():
    # Then there were no videos submitted for download
        cprint("\nNo videos waiting to download - COMPLETED", "green")

    else:
    # proceed only if there were videos downloaded
        # 2
        # Watermarks clips (to specifications) and writes to PROCESSESSING folder
        # Will watermark both streams for multi-stream content
        watermark()

        # 3
        # Reads clips from PROCESSESING folder, creates tops (with titles) and stitches top & tail on clip
        # Tops & tails both streams (if multiple)
        # Writes to output folder
        stitch()

        # 4
        # Uploads all processed clips to Panopto to same folder as source session
        # Can handle single and multi-stream content (primary and secondary video)
        uploaded, requested = upload_videos()

        if uploaded == requested:
            cprint(f"\nBranding COMPLETED: {uploaded} of {requested} videos ready in Panopto", "green")
            send_notification(f" INFO Branding completed: {uploaded} of {requested} videos ready in Panopto", "INFO")
        else:
            cprint(
                f"\nBranding FINISHED WITH ERRORS: {uploaded} of {requested} videos ready in Panopto."
                f" See logs/{now_formatted}.log",
                "red",
                attrs=["bold"],
            )
            send_notification(
                f" ERROR Branding finished with errors: {uploaded} of {requested} videos ready in Panopto."
                f" See logs/{now_formatted}.log",
                "ERROR",
            )

    retention_days = int(os.getenv("ARCHIVE_RETENTION_DAYS", DEFAULT_ARCHIVE_RETENTION_DAYS))
    delete_old_archives("input/body", retention_days)
    delete_old_archives("output", retention_days)

    # Completion printouts
    cprint("\nMade by Marko Prodanovic\n", "yellow")
    cprint("\n❤️\n", "yellow")


def __check_panopto_login():
    """
    Get an access token and a .ASPXAUTH cookie. Raises if either fails.
    """
    server = os.getenv("SERVER")
    oauth2 = PanoptoOAuth2(server, os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET"), True)
    Panopto(server, True, oauth2).get_aspxauth_cookie()
    cprint("Panopto login OK", "green")


if __name__ == "__main__":
    main_brander()
