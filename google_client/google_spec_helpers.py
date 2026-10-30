# Helper functions for google form interface
import os
import logging
from datetime import datetime
from termcolor import cprint
import uuid


def requires_more_edits(video):
    """
    """
    needs_edits = str(
        video[
            "Do you require more editing than just branding?  (If yes, you will be asked for the timecodes of the edits in the next step. Requests for the automated branding of videos will be completed in 24 hours, content edits may require extra processing time.)"
        ]
    )

    return needs_edits == "Yes"


def translate_video_properties(video):
    """
    """
    wm_location = str(
        video[
            "Location of watermark? This watermark will be superimposed for the duration of the video in the location chosen. Required.)"
        ]
    )
    watermark = str(
        video[
            "Version of watermark. Please indicate the version of watermark. Additional watermark options will be available in future updates. (Required)"
        ]
    )

    if watermark == "UBC Sauder":
        watermark = "ubc-sauder.png"
    elif watermark == "UBC Sauder RHL":
        watermark = "sauder-rhl.png"
    elif watermark == "UBC Sauder & Ch'nook":
        watermark = "ubc-sauder-chnook.png"

    if wm_location == "Bottom Right":
        wm_location = "R"

    if wm_location == "Bottom Left":
        wm_location = "L"

    src_url = str(
        video[
            "Panopto video location where we can find your video? After uploading your video to Panopto, please copy the Share Link as illustrated in the image below. (Required)"
        ]
    )

    src_url = src_url.split('&')[0]

    course = str(
        video['Course (Choose "Other" to customize, Maximum 15 characters; Optional)']
    )
    code = str(video["Course Code (e.g. 101; Optional)"])
    course_code = str(course) + " " + str(code)
    section_number = str(
        video[
            "Section Number (Course code is required if you enter this section number)"
        ]
    )
    title = str(
        video[
            "Video Title. This is the title of the video as it should appear on the video intro. (Example above. Required. Maximum characters: 45)"
        ]
    )
    instructor_name = str(
        video["Preferred Instructor(s) Name(s) (Optional. Maximum characters: 50)"]
    )

    uid = str(uuid.uuid4())

    # ** WORKAROUND SOLUTION FOR GENERIC UBC BRANDING **

    top_slate = "sauder_slate.mp4"
    tail = "sauder_tail.mp4"

    if watermark == "UBC Only":
        watermark = "ubc.png"
        top_slate = "ubc_slate.mp4"
        tail = "ubc_tail.mp4"

    return {
        "id": uid,
        "course_code": course_code,
        "section_number": section_number,
        "title": title,
        "instructor": instructor_name,
        "watermark": watermark,
        "top_slate": top_slate,
        "tail": tail,
        "wm_pos": wm_location,
        "src_url": src_url,
    }


def remove_previously_run_videos(videos):
    """
    Keep only form responses submitted after the last run.
    Does not update LastRun.txt; call save_last_run_time() once the run is safe to commit.
    """
    last_run = __get_last_run_time()

    if videos.empty:
        return videos

    is_new = videos["Timestamp"].map(lambda ts: __parse_timestamp(str(ts)) > last_run)
    return videos[is_new]


def archive_previous_specs():
    last_run = __get_last_run_time()
    last_run_formatted = last_run.strftime("%m-%d-%Y %H:%M:%S")

    input_target = f"input/specs.csv"
    output_target = f"input/specs_archive/specs_({last_run_formatted}).csv"

    if not os.path.exists(input_target):
        return

    cprint(f"Archiving specs from: {last_run_formatted}", "yellow")
    logging.info("Archiving specs from: %s", last_run_formatted)
    os.makedirs("input/specs_archive", exist_ok=True)
    os.replace(input_target, output_target)


def __get_last_run_time():
    """
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    with open(f"{current_dir}/LastRun.txt", "r") as f:
        timestamp_string = f.read()
    timestamp_string = timestamp_string.split("=")[1].strip()
    return __parse_timestamp(timestamp_string)


def save_last_run_time(now):
    """
    Record {now} as the last run. Form responses up to this time won't be picked up again.
    """
    now_formatted = now.strftime("%m/%d/%Y %H:%M:%S")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(f"{current_dir}/LastRun.txt", "w") as text_file:
        print(f"LastRun={now_formatted}", file=text_file)


def __parse_timestamp(timestamp_string):
    """
    """

    datetime_elements = timestamp_string.split()
    date = datetime_elements[0]
    time = datetime_elements[1]

    date_elements = date.split("/")
    month = date_elements[0]
    day = date_elements[1]
    year = date_elements[2]

    time_elements = time.split(":")
    hours = time_elements[0]
    minutes = time_elements[1]
    seconds = time_elements[2]

    # datetime(year, month, day, hour, minute, second, microsecond)
    timestamp = datetime(
        int(year), int(month), int(day), int(hours), int(minutes), int(seconds)
    )

    return timestamp
