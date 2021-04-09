import os
import logging
from dotenv import load_dotenv
from termcolor import cprint
from panopto.panopto_oauth2 import PanoptoOAuth2
from panopto.panopto_interface import Panopto
from helpers import load_specifications, get_video_attributes, archive_folder_contents


def download_videos():
    load_dotenv()

    root = os.path.dirname(os.path.abspath(__file__))

    specs = load_specifications(root + "/input")

    server = os.getenv("SERVER")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    oauth2 = PanoptoOAuth2(server, client_id, client_secret, True)
    panopto = Panopto(server, True, oauth2)

    cprint("\nArchiving & clearing input/body folder...", "yellow")
    logging.info("Archiving & clearing input/body folder...")
    archive_folder_contents("input/body")

    for index, row in specs.iterrows():
        print("\n------------------------------------------\n")

        try:
            specs = get_video_attributes(row)
        except ValueError:
            cprint("Skipping video...", "red")
            attempted_video_title = row["Title"]
            logging.error(
                "Invalid values in specs. Skipping video: %s, row: %i",
                attempted_video_title,
                index,
            )
            continue

        video_id = specs["id"]
        course = specs["course"]
        title = specs["title"]
        instructor = specs["instructor"]
        src_url = specs["src_url"]

        cprint(f"Starting download for <row {index}>:", "yellow")
        logging.info(
            "Starting DOWNLOAD for <row %i> | %s - %s", index, title, instructor
        )
        print(f"\nVIDEO TITLE: {title}")
        print(f"COURSE: {course}")
        print(f"INSTRUCTOR NAME: {instructor}")
        print(f"UNIQUE ID: {video_id}\n")

        output_folder = f"{root}/input/body/{title}_{instructor}_{video_id}"

        if not instructor:
            # filepath if no instructor specified
            output_folder = f"{root}/input/body/{title}_{video_id}"

        delivery_id = src_url[-36:]

        try:
            panopto.download_video(delivery_id, output_folder)
        except RuntimeError as err:
            logging.error("Runtime error: %s", err)
            cprint(err, "red")
            continue


if __name__ == "__main__":
    download_videos()
