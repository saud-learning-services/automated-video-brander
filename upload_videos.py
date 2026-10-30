import os
import logging
import datetime
import codecs
from termcolor import cprint
from dotenv import load_dotenv
from helpers import load_specifications, get_video_attributes, send_notification, delivery_id_from_url
from panopto.panopto_oauth2 import PanoptoOAuth2
from panopto.panopto_interface import Panopto, UPLOAD_COMPLETED, PROCESSING, COMPLETE

# How long to wait for Panopto to finish processing the uploads
DEFAULT_PROCESSING_TIMEOUT_MINUTES = 60


def upload_videos():
    load_dotenv()

    root = os.path.dirname(os.path.abspath(__file__))

    specs = load_specifications(root + "/input")

    server = os.getenv("SERVER")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    oauth2 = PanoptoOAuth2(server, client_id, client_secret, True)

    msg = " INFO Beginning uploads"
    send_notification(msg,"INFO")

    panopto = Panopto(server, True, oauth2)
    uploads = {}  # upload_id: video title
    requested = len(specs.index)  # specs is reused for each row below
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
        course_code = specs["course"]
        video_title = specs["title"]
        instructor_name = specs["instructor"]
        src_url = specs["src_url"].strip()

        cprint(f"Starting upload for <row {index}>:", "yellow")
        logging.info(
            "Starting UPLOAD for <row %i> | %s - %s",
            index,
            video_title,
            instructor_name,
        )

        print(f"\nVIDEO TITLE: {video_title}")
        print(f"COURSE: {course_code}")
        print(f"INSTRUCTOR NAME: {instructor_name}")
        print(f"UNIQUE ID: {video_id}\n")

        # folder containing the streams to upload
        local_folder_path = f"output/{video_title}_{instructor_name}_{video_id}"

        if not instructor_name:
            local_folder_path = f"output/{video_title}_{video_id}"

        if not os.path.isdir(local_folder_path) or not os.listdir(local_folder_path):
            # an earlier step failed (already notified), nothing to upload
            logging.info("No branded video in %s. Skipping...", local_folder_path)
            continue

        # URL must be on our Panopto instance (SERVER in .env)
        if not src_url.startswith(f"https://{server}/"):
            cprint(
                f"\nThe source URL provided ({src_url}) is not on {server}",
                "red",
            )
            cprint(f'Skipping upload for video: "{video_title}"...\n', "red")
            logging.error(
                'The source URL provided: "%s" is not on %s. Skipping video: %s',
                src_url,
                server,
                video_title,
            )
            send_notification(f" ERROR Not UBC Panopto instance: {video_title}, URL: {src_url}", "ERROR")
            continue

        # delivery id is in last 36 characters of URL
        #delivery_id = src_url[-36:]
        delivery_id = delivery_id_from_url(src_url) # function uses regex pattern to find uuid in url supplied by user input 
                                                    # - users don't always submit correct link from sharing page.
        
        if delivery_id == 0: # there was no delivery id found in the url supplied by user input
            send_notification(f" ERROR no delivery id found to upload entry: {video_id}, {src_url}", "ERROR")
            continue
        elif delivery_id == 99: # there was more than 1 delivery id found in the url supplied by user input, should only be 1
            send_notification(f" ERROR too many delivery ids found to upload entry: {video_id}, {src_url}", "ERROR")
            continue

        try:
            panopto_folder_name, panopto_folder_id = panopto.get_containing_folder(
                delivery_id
            )
        except Exception as err:
            cprint(err, "red")
            send_notification(f" ERROR Could not find Panopto folder for {video_title}: {err}", "ERROR")
            continue

        # manifest cannot have '&' character in it

        manifest_title = f"{__normalize_title(video_title)}_branded"
        try:
            __create_manifest(local_folder_path, manifest_title)
        except Exception as err:
            cprint("\nERROR: Could not create manifest", "red")
            logging.error(
                "Could not create manifest for video: %s. Skipping...", video_title
            )
            logging.error(err)
            cprint(err, "red")
            print("")
            send_notification(f" ERROR Could not create manifest. Skipping video: {video_title}", "ERROR")
            continue

        cprint(
            f'Writing video: "{manifest_title}"" to Panopto folder: \n=> {panopto_folder_name}\n',
            "blue",
        )

        try:

            upload_id = panopto.upload_folder(local_folder_path, panopto_folder_id)
            uploads[upload_id] = video_title
            cprint("UPLOAD COMPLETED (Panopto is processing it)\n", "green")
            cprint(f"   video: {video_title}", "blue")
            cprint(f"   src folder: {local_folder_path}", "blue")
            cprint(f"   destination (panopto): {panopto_folder_name}", "blue")
        except FileNotFoundError as err:
            cprint(f"\nCould not find file for upload: {local_folder_path}", "red")
            cprint("Skipping video...\n", "red")
            logging.error(
                "Could not find file for upload: %s. Skipping video: %s...",
                local_folder_path,
                video_title,
            )
            send_notification(f" ERROR Upload file not found. Skipping video: {local_folder_path}, row: {video_title}", "ERROR")
        except Exception as err:
            cprint(f"\nUpload failed for {video_title}: {err}", "red")
            send_notification(f" ERROR Upload failed for {video_title}: {err}", "ERROR")
            continue

    processed = __wait_for_panopto(panopto, uploads)
    logging.info("Processed in Panopto: %i of %i", processed, requested)
    return processed, requested


def __wait_for_panopto(panopto, uploads):
    """
    Wait for Panopto to finish processing the uploads ({upload_id: title}).
    Notifies about any that fail or are still processing at the time limit.
    Returns how many finished processing.
    """
    if not uploads:
        return 0

    timeout_minutes = int(os.getenv("PROCESSING_TIMEOUT_MINUTES", DEFAULT_PROCESSING_TIMEOUT_MINUTES))
    cprint(
        f"\nWaiting for Panopto to process {len(uploads)} video(s) (up to {timeout_minutes} minutes)...",
        "yellow",
    )
    states = panopto.wait_for_processing(list(uploads), timeout_minutes * 60)

    processed = 0
    for upload_id, title in uploads.items():
        state = states[upload_id]
        if state == COMPLETE:
            processed += 1
            cprint(f"   Ready in Panopto: {title}", "green")
            logging.info("Ready in Panopto: %s (upload %s)", title, upload_id)
        elif state in (PROCESSING, UPLOAD_COMPLETED, None):
            send_notification(
                f" ERROR {title} is still not processed after {timeout_minutes} minutes."
                f" Check it in Panopto (upload {upload_id}).",
                "ERROR",
            )
        else:
            send_notification(
                f" ERROR Panopto could not process {title} (state {state}, upload {upload_id})."
                f" The session will show no content.",
                "ERROR",
            )
    return processed



def __create_manifest(target_folder, video_title):
    num_items = len(os.listdir(target_folder))

    if num_items == 1:
        __create_single_stream_manifest(target_folder, video_title)
    elif num_items == 2:
        __create_multi_stream_manifest(target_folder, video_title)
    else:
        raise RuntimeError(
            f"Unexpected number of items ({num_items}) in target folder: {target_folder}"
        )


def __create_single_stream_manifest(target_folder, title):

    single_stream_manifestest_template = (
        "panopto/manifest_templates/single_stream_manifest_template.xml"
    )

    with open(single_stream_manifestest_template) as fr:
        template = fr.read()
    content = (
        template.replace("{Title}", title)
        .replace(
            "{Description}",
            "This video was processed by the Sauder Automated Video Branding Tool",
        )
        .replace("{Filename}", "primary.mp4")
        .replace(
            "{Date}", datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f-00:00")
        )
    )
    with codecs.open(f"{target_folder}/single_stream_manifest.xml", "w", "utf-8") as fw:
        fw.write(content)


def __create_multi_stream_manifest(target_folder, title):
    single_stream_manifestest_template = (
        "panopto/manifest_templates/multi_stream_manifest_template.xml"
    )

    with open(single_stream_manifestest_template) as fr:
        template = fr.read()
    content = (
        template.replace("{Title}", title)
        .replace(
            "{Description}",
            "This video was processed by the Sauder Automated Video Branding Tool",
        )
        .replace("{PrimaryFilename}", "primary.mp4")
        .replace("{SecondaryFilename}", "secondary.mp4")
        .replace(
            "{Date}", datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f-00:00")
        )
    )
    with codecs.open(f"{target_folder}/multi_stream_manifest.xml", "w", "utf-8") as fw:
        fw.write(content)


def __normalize_title(title):
    return title.replace("&", "and")


if __name__ == "__main__":
    upload_videos()
