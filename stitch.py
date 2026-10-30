"""
stitch.py
Automated Video Branding Tool

Author: Marko Prodanovic
"""

# Standard imports
import os
import logging

# Moviepy (primary library)
# Docs: https://zulko.github.io/moviepy/index.html
from moviepy import VideoFileClip, concatenate_videoclips, vfx, afx


# Additional dependencies
from termcolor import cprint

# Local modules
from top.top import Top

from helpers import load_specifications, get_video_attributes, archive_folder_contents, send_notification

def stitch():
    """
    Stitch the top, body and tail clips together
    """
    # project root directory
    root = os.path.dirname(os.path.abspath(__file__))

    cprint("\nLoading Specifications from CSV...", "yellow")
    specs = load_specifications(root + "/input")

    cprint("Archiving & clearing output folder...", "yellow")
    logging.info("Archiving & clearing output folder...")
    archive_folder_contents("output")
    send_notification(f" Beginning - Stitching Top and Tail", "INFO")


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
        section = specs["section"]
        instructor = specs["instructor"]
        title = specs["title"]
        tail = specs["tail"]
        top_slate = specs["top_slate"]

        cprint(f"Starting top/tail stitching for <row {index}>:", "yellow")
        logging.info(
            "Starting TOP/TAIL STITCHING for <row %i> | %s - %s",
            index,
            title,
            instructor,
        )
        print(f"\nVIDEO TITLE: {title}")
        print(f"COURSE: {course}")
        print(f"INSTRUCTOR NAME: {instructor}")
        print(f"UNIQUE ID: {video_id}\n")

        input_folder = f"input/body/PROCESSED/{title}_{instructor}_{video_id}"
        output_folder = f"output/{title}_{instructor}_{video_id}"

        if not instructor:
            input_folder = f"input/body/PROCESSED/{title}_{video_id}"
            output_folder = f"output/{title}_{video_id}"

        if not os.path.isdir(input_folder):
            # download or watermark failed (already notified), nothing to stitch
            logging.info("No processed video in %s. Skipping...", input_folder)
            continue

        try:
            top = Top(
                top_slate=top_slate,
                title=title,
                course=course,
                section=section,
                instructor=instructor,
            )
            top_rendered = top.get_video()

            tail_clip = VideoFileClip(f"input/tail/{tail}").with_effects(
                [afx.AudioFadeIn(1.5)]
            )
        except Exception as error:
            cprint(error, "red")
            send_notification(f"ERROR Could not load top slate or tail for {title}: {error}", "ERROR")
            continue

        for clip_name in os.listdir(input_folder):
            try:
                body_video = VideoFileClip(f"{input_folder}/{clip_name}").with_effects(
                    [
                        vfx.FadeIn(1, initial_color=[255, 255, 255]),
                        vfx.FadeOut(1, final_color=[255, 255, 255]),
                        afx.AudioFadeOut(2),
                        afx.AudioFadeIn(1.5),
                    ]
                )
                final_clip = concatenate_videoclips([top_rendered, body_video, tail_clip])

            except OSError:
                cprint(
                    f'Could not find specifiied clip: "{clip_name}" in folder: ', "red"
                )
                logging.error(
                    'Could not find specifiied clip: "%s" in folder: "%s". Skipping video...',
                    clip_name,
                    input_folder,
                )
                cprint(input_folder, "yellow")
                cprint("Skipping video...", "red")
                send_notification(f"ERROR Could not find specified clip. Skipping video: {clip_name}, in folder: {input_folder}", "ERROR")
                continue

            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            cprint(f"Writing to output folder: \n=> {output_folder}\n", "blue")

            output_video_path = f"{output_folder}/{clip_name}"

            try:
                final_clip.write_videofile(
                    output_video_path,
                    fps=30,
                    threads=8,
                    preset="ultrafast",
                    temp_audiofile="temp-audio.m4a",
                    remove_temp=True,
                    codec="libx264",
                    audio_codec="aac",
                )
                cprint("\nSUCCESS", "green")
            except Exception as error:
                cprint(error, "red")
                send_notification(f"ERROR Stitching failed for {title}: {error}", "ERROR")
                # remove the partial render so it is not uploaded
                if os.path.exists(output_video_path):
                    os.remove(output_video_path)
                continue
            finally:
                # free the ffmpeg readers; they leak between videos otherwise
                body_video.close()
                final_clip.close()

        top_rendered.close()
        tail_clip.close()


if __name__ == "__main__":
    stitch()
