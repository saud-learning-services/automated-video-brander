import os
import shutil
import re
import time
import logging
import requests
from zipfile import ZipFile
from termcolor import cprint
from datetime import datetime

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


def name_normalize(name):
    """
    Replaces "/" characters with "-" to
    """
    if name is None:
        return name

    return name.replace("/", "-")


def load_specifications(path):
    """
    Loads in the specs.csv file using pandas and checks that it has the necesary columns.
    Returns the specs as a pandas dataframe.
    """
    try:
        specs = pd.read_csv(path + "/specs.csv", dtype={"Section": "str"})
    except IOError as error:
        raise RuntimeError(f"Error loading specs.csv: {error}") from error
    except ParserError as error:
        raise RuntimeError("Could not parse specs.csv, ensure correctly formatted.") from error
    except EmptyDataError as error:
        raise RuntimeError("Ensure specs.csv has data.") from error

    expected_cols = {
        "Id",
        "Course",
        "Section",
        "Instructor",
        "Title",
        "Top Slate",
        "Tail",
        "Watermark",
        "Watermark Position",
        "Source URL",
    }

    actual_cols = set(list(specs))

    # Check that we have all the columns we expect
    if expected_cols != actual_cols:
        raise RuntimeError(
            f"Missing or incorrect columns in specs.csv. Expected columns: {expected_cols}"
        )

    return specs


def get_video_attributes(row):
    """
    Loads the cell values from the dataframe row into a dictionary
    Performs a series of checks to ensure values math certain expected criteria (described below)
    """

    # casting uid to string regardless
    uid = __parse_value(str(row["Id"]))
    course = __parse_value(row["Course"])
    section = __parse_value(row["Section"])
    instructor = __parse_value(row["Instructor"])
    title = __parse_value(row["Title"])
    top_slate = __parse_value(row["Top Slate"])
    tail = __parse_value(row["Tail"])
    watermark = __parse_value(row["Watermark"])
    wm_pos = __parse_value(row["Watermark Position"])
    src_url = __parse_value(row["Source URL"])

    # These three values are used to make filepaths therefore cannot contain "/"
    course = name_normalize(course)
    instructor = name_normalize(instructor)
    title = name_normalize(title)

    # Course, Section, Instructor, Title, Top Slate must be included at minimum
    if title is None:
        cprint("\nERROR: Spec must include at least a title", "red")
        raise ValueError()

    if section is not None and course is None:
        cprint(
            "\nERROR: A row cannot specify section code without course code (specs.csv)",
            "red",
        )
        raise ValueError

    # if top slate is specified must finish with mp4
    if top_slate is not None and str(top_slate)[-4:] != ".mp4":
        cprint("\nERROR: Must include value for slate that ends in .mp4", "red")
        raise ValueError()

    if len(title) > 45:
        cprint("\nERROR: Does not support titles with more than 45 characters", "red")
        raise ValueError()

    # instructor name(s) must not exceed 50 characters
    if instructor is not None and len(instructor) > 50:
        cprint(
            "\nERROR: Does not support instructor name(s) with more than 50 characters",
            "red",
        )
        raise ValueError()

    # watermark must end in .png
    if watermark is not None and watermark[-4:] != ".png":
        cprint("\nERROR: If watermark included, csv value must end in .png", "red")
        raise ValueError()

    return {
        "id": uid,
        "course": course,
        "section": section,
        "instructor": instructor,
        "title": title,
        "top_slate": top_slate,
        "tail": tail,
        "watermark": watermark,
        "src_url": src_url,
        "wm_pos": wm_pos,
    }


def __parse_value(val):
    """
    Returns the value if it passess value check
    Otherwise returns None
    """
    return val if __has_value(val) else None


def __has_value(cell):
    """Checks if a cell value from a Pandas dataframe is a valid string

    The following are treated as invalid:
    * empty cell (None)
    * empty string ('')
    * zero (0)
    * type = nan OR type = None
    * 'null' OR 'NULL'
    * 'none' OR 'NONE'

    Args:
        cell (Any): Value of a cell from pandas dataframe

    Returns:
        Boolean: Whether or not value is valid string
    """

    # Falsy values are FALSE
    if not cell:
        return False

    # nan values FALSE
    if not isinstance(cell, str):
        return False

    # strings == 'none' or 'null' or '0' are also FALSE
    if (
        cell.lower() == "none"
        or cell.lower() == "null"
        or cell.lower() == "nan"
        or cell == "0"
    ):
        return False

    return True


def archive_folder_contents(folder_path):
    """
    Zips all existing folders into file titled by the curent datetime
    Writes to archive folder
    """
    file_paths = __get_all_file_paths(folder_path)

    now = datetime.now().strftime("%Y-%m-%dT%H.%M.%S")
    output_filename = f"{now}.zip"

    archive_folder = f"{folder_path}/archive"
    if not os.path.exists(archive_folder):
        os.makedirs(archive_folder)

    with ZipFile(f"{archive_folder}/{output_filename}", "w") as zip:
        # writing each file one by one
        for file in file_paths:
            zip.write(file, file)

    cprint(f"Previous contents successfully zipped to: {archive_folder}", "green")
    clear_folder_contents(folder_path)


def __get_all_file_paths(directory):
    """
    Returns a list of all file paths in a given directory
    Except those in the /archive folder
    """

    # initializing empty file paths list
    file_paths = []

    # crawling through directory and subdirectories
    for root, directories, files in os.walk(directory):
        for filename in files:

            # join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)

            # ignore archive folder
            if "/archive" in filepath:
                continue

            file_paths.append(filepath)

    # returning all file paths
    return file_paths


def clear_folder_contents(folder_path):
    """
    Clears directory contents
    Ignores: archive, .DS_Store, .gitkeep
    Args:
        folder_path: Path of the folder to clear
    """
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # We don't want to delete any of the following files or directories
        if filename in (".gitkeep", ".DS_Store", "archive"):
            continue

        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (file_path, e))

def send_notification(payload, status_level):
    """Send a push notification via ntfy.sh (or your own ntfy server)

    The topic URL is read from NTFY_URL in .env. Notifications are best-effort:
    a failure is logged but never stops the brander.

    Args:
        payload (text): Message to send to notification
        status_level (text): Status of message to notify; currently INFO, and ERROR

    Returns:
        0: INFO status notified
        1: ERROR status notified
        99: UNKNOWN status notified
    """
    tags = {"INFO": "heavy_check_mark", "ERROR": "warning"}
    codes = {"INFO": 0, "ERROR": 1}
    if status_level not in tags:
        status_level = "UNKNOWN"

    logging.log(logging.ERROR if status_level != "INFO" else logging.INFO, payload.strip())

    ntfy_url = os.getenv("NTFY_URL")
    if not ntfy_url:
        return codes.get(status_level, 99)

    now_formatted = datetime.now().strftime("  %Y-%m-%d %H:%M:%S")
    try:
        response = requests.post(
            ntfy_url,
            data=payload.encode("utf-8"),
            headers={
                "Title": status_level + now_formatted,
                "Tags": tags.get(status_level, "rotating_light"),
            },
            timeout=15,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        logging.warning("Could not send notification: %s", err)

    return codes.get(status_level, 99)


def delete_old_archives(folder_path, days):
    """
    Deletes .zip files in {folder_path}/archive older than {days} days.
    Keeps the archives of downloaded/branded videos from filling the disk.
    """
    archive_folder = f"{folder_path}/archive"
    if not os.path.isdir(archive_folder):
        return

    cutoff = time.time() - days * 24 * 60 * 60
    for filename in os.listdir(archive_folder):
        file_path = os.path.join(archive_folder, filename)
        if filename.endswith(".zip") and os.path.getmtime(file_path) < cutoff:
            os.remove(file_path)
            logging.info("Deleted old archive: %s", file_path)


def delivery_id_from_url(src_url):
    """
    Find UUID in text of URL submitted and return just the UUID if found

    Args:
        src_url: Source URL submitted by user. Should contain Panopto session delivery id in uuidv4 format.

    Returns:
        0:  UUID not found in url/embed code. 
        99: more than 1 UUID found in url/embed code. 
        UUID: If only 1 uuid found, returns the text of the uuid found in url or embed code submitted
    """
    str = src_url
    var_r = ""
    p = '[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}' #UUID v1-5 regular expression pattern
    r = re.findall ( p, str) #check how many uuid's we find in user submission
    if len(r)==0:
        return 0
    elif len(r)>1:
        return 99
    else: #we have only one and we can use to attempt the download
        var_r = r[0]
        return var_r
