import os
import shutil
import logging
from dotenv import load_dotenv
from termcolor import cprint
from panopto.panopto_oauth2 import PanoptoOAuth2
from panopto.panopto_interface import Panopto
from helpers import load_specifications, get_video_attributes, archive_folder_contents, delivery_id_from_url, send_notification


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
    if len(specs.index) > 0:
        msg = " Beginning Downloads"
        send_notification(msg,"INFO")
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
                send_notification(f" ERROR Invalid values in specs. Skipping video: {attempted_video_title}, row: {index}", "ERROR")
                continue

            video_id = specs["id"]
            course = specs["course"]
            title = specs["title"]
            instructor = specs["instructor"]
            src_url = specs["src_url"].strip()

            cprint(f"Starting download for <row {index}>:", "yellow")
            logging.info(
                "Starting DOWNLOAD for <row %i> | %s - %s", index, title, instructor
            )
            print(f"\nVIDEO TITLE: {title}")
            print(f"COURSE: {course}")
            print(f"INSTRUCTOR NAME: {instructor}")
            print(f"UNIQUE ID: {video_id}")
            print(f"DOWNLOAD URL: {src_url}")

            output_folder = f"{root}/input/body/{title}_{instructor}_{video_id}"

            if not instructor:
                # filepath if no instructor specified
                output_folder = f"{root}/input/body/{title}_{video_id}"

            delivery_id = delivery_id_from_url(src_url) # function uses regex pattern to find uuid in url supplied by user input
            print(f"SESSION ID: {delivery_id}")
        
            if delivery_id == 0: # there was no delivery id found in the url supplied by user input
                send_notification(f" ERROR no delivery id found in entry: {video_id}, {src_url}","ERROR")
                continue
            elif delivery_id == 99: # there was more than 1 delivery id found in the url supplied by user input, should only be 1
                send_notification(f" ERROR too many delivery ids found in entry: {video_id}, {src_url}", "ERROR")
                continue
            else: # we have only one delivery id, can now try to download the video
                try:
                    panopto.download_video(delivery_id, output_folder)
                except Exception as err:
                    # remove the empty folder so later steps skip this video
                    shutil.rmtree(output_folder, ignore_errors=True)
                    cprint(err, "red")
                    send_notification(f" ERROR Download failed for {title}: {err}", "ERROR")
                    continue
        send_notification(f" INFO Completed Downloads", "INFO")
        return True

    else:
        send_notification(f" INFO Nothing to download", "INFO")
        return False

if __name__ == "__main__":
    download_videos()
