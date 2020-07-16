"""
TOP & TAIL STITCHER: stitch.py

authors:
@markoprodanovic

last edit:
Thursday, July 16, 2020
"""

# Standard imports
import shutil
import os

# Moviepy (primary library)
# Docs: https://zulko.github.io/moviepy/index.html
from moviepy.editor import (
    VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips)
import moviepy.video.fx.all as vfx

# Additional dependencies
from termcolor import cprint
import pandas as pd

# Local modules
from top_maker import create_top

root_path = os.path.dirname(os.path.abspath(__file__))

print('\n🚚 Loading Specifications from CSV...')
specs = pd.read_csv(root_path + '/input/specifications.csv')


def hasValue(cell):

    # Falsy values are FALSE
    if (not cell):
        return False

    # nan values FALSE
    if (not isinstance(cell, str)):
        return False

    # strings == 'none' or 'null' or '0' are also FALSE
    if (cell.lower() == 'none' or cell.lower() == 'null' or
            cell.lower() == 'nan' or cell == '0'):
        return False

    return True

# ===== DELETE OUTPUT CONTENTS =====


def clear_output_contents():
    """
    Clears output directory contents
    """

    for subdir in os.listdir(root_path + '/output'):
        if subdir != '.gitkeep' and subdir != '.DS_Store':
            path = f'{root_path}/output/{subdir}'
            shutil.rmtree(path, ignore_errors=False, onerror=None)


print('🗑  Clearing output folder...')
clear_output_contents()

# ====== MAKE COURSE FOLDERS =====

# set ensures we don't make redundant course folders
unique_courses = set()
for index, row in specs.iterrows():
    unique_courses.add(row['Course'])

for course in unique_courses:
    path = f'output/{course}'
    try:
        os.mkdir(path)
    except OSError as error:
        print(error)

# ==== STITCH VIDEOS TOGETHER ====

for index, row in specs.iterrows():
    course = row['Course']
    title = row['Title']
    top_slate = row['Top Slate']
    body = row['Body']
    watermark = row['Watermark']
    wm_position = row['Watermark Position']

    print('\n==========')
    print(f'🎥 {course} | {title}')

    ### SOME DEBUGGING PRINTOUTS ###
    # print(f'body: {body} | has: {hasValue(body)}')
    # print(f'watermark: {watermark} | has: {hasValue(watermark)}')
    # print(f'position: {wm_position} | has: {hasValue(wm_position)}')
    # ======== #

    top = create_top(title, top_slate)
    top_with_fade = top.fx(vfx.fadeout, duration=1.5,
                           final_color=[255, 255, 255])

    # same tail for all videos
    tail = VideoFileClip('input/tail/tail.mp4')

    if (hasValue(body)):
        raw_body = (VideoFileClip(f'input/body/{body}')
                    .fx(vfx.fadein, duration=1, initial_color=[255, 255, 255]))
        if (hasValue(watermark)):

            # DEFAULT (bottom right)
            left_margin = 1575

            # bottom left if specified
            if (wm_position == 'L' or wm_position == 'l'):
                left_margin = 50

            watermark = (ImageClip(f'input/watermark/{watermark}')
                         .set_opacity(0.8)
                         .set_duration(raw_body.duration)
                         .resize(height=70)
                         .margin(left=left_margin, top=975, opacity=0))

            body_wm = CompositeVideoClip([raw_body, watermark])
            body = body_wm.fx(vfx.fadeout, duration=1,
                              final_color=[255, 255, 255])
        else:
            body = raw_body.fx(vfx.fadeout, duration=1,
                               final_color=[255, 255, 255])
        final_clip = concatenate_videoclips([top_with_fade, body, tail])
    else:
        final_clip = concatenate_videoclips([top_with_fade, tail])

    print(f'📁 Writing to output folder {course}...')
    final_clip.write_videofile(f'output/{course}/{title}.mp4', temp_audiofile='temp-audio.m4a',
                               remove_temp=True, codec='libx264', audio_codec='aac')

    # TODO: need to do some checking here
    cprint('\nSUCCESS', 'green')
