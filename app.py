"""
TOP & TAIL STITCHER: app.py

Author: @markoprodanovic

last edit:
Thursday, August 6, 2020
"""

# Standard imports
import shutil
import sys
import os

# Moviepy (primary library)
# Docs: https://zulko.github.io/moviepy/index.html
from moviepy.editor import (
    VideoFileClip,
    ImageClip,
    CompositeVideoClip,
    concatenate_videoclips)
import moviepy.video.fx.all as vfx
import moviepy.audio.fx.all as sfx

# Additional dependencies
from termcolor import cprint
import pandas as pd
from pandas.errors import EmptyDataError, ParserError

# Local modules
from src.top_maker import create_top


def main():
    """ Main entry point for Top & Tail Stitcher Script
    """

    # settings object for global variables
    settings = {
        'root': os.path.dirname(os.path.abspath(__file__))
    }

    print('\n🚚 Loading Specifications from CSV...')
    specs = _load_specifications(settings['root'] + '/input')

    print('🧹 Clearing output folder...')
    _clear_folder_contents(settings['root'] + '/output')

    print('🔨 Building course folders in output folder...')
    _make_course_folders(settings['root'] + '/output', specs)

    # ==== STITCH VIDEOS TOGETHER ====

    for index, row in specs.iterrows():

        print('\n====================================\n')
        course = row['Course']
        title = row['Title']
        print(f'🎥 {course} | {title} | Row {index + 1}')

        try:
            course, section, instructor, title, top_slate, body, watermark, wm_position = _get_video_attributes(
                row)
        except ValueError:
            cprint('Skipping video...', 'red')
            continue

        top = create_top(course, section, instructor, title, top_slate)
        top = top.fx(vfx.fadeout, duration=1.5,
                     final_color=[255, 255, 255])
        top_with_fade = top.fx(sfx.audio_fadeout, duration=1)

        # same tail for all videos
        tail = VideoFileClip('input/tail/tail.mp4')

        if (_has_value(body)):
            raw_body = (VideoFileClip(f'input/body/{body}')
                        .fx(vfx.fadein, duration=1, initial_color=[255, 255, 255]))
            if (_has_value(watermark)):

                watermark_path = f'input/watermark/bottom-right/{watermark}'

                if wm_position in ['l', 'L']:
                    watermark_path = f'input/watermark/bottom-left/{watermark}'

                watermark_img = (ImageClip(watermark_path)
                                 .set_duration(raw_body.duration))

                body_wm = CompositeVideoClip([raw_body, watermark_img])
                body = body_wm.fx(vfx.fadeout, duration=1,
                                  final_color=[255, 255, 255])

                body = body.fx(sfx.audio_fadeout, duration=1)

            else:
                body = raw_body.fx(vfx.fadeout, duration=1,
                                   final_color=[255, 255, 255])
            final_clip = concatenate_videoclips(
                [top_with_fade, body, tail])
        else:
            final_clip = concatenate_videoclips([top_with_fade, tail])

        print(f'📁 Writing to output folder {course}...')
        final_clip.write_videofile(f'output/{course}/{title}.mp4',
                                   temp_audiofile='temp-audio.m4a',
                                   remove_temp=True,
                                   codec='libx264',
                                   audio_codec='aac')

        cprint('\nSUCCESS', 'green')


def _get_video_attributes(row):
    """
    """

    course = str(row['Course'])
    section = str(row['Section'])
    instructor = str(row['Instructor'])
    title = str(row['Title'])
    top_slate = str(row['Top Slate'])
    body = str(row['Body'])
    watermark = str(row['Watermark'])
    wm_pos = str(row['Watermark Position'])

    vals = [course, section, instructor, title,
            top_slate, body, watermark, wm_pos]

    # Course, Section, Instructor, Title, Top Slate must be included at minimum
    if not all(map(_has_value, [course, section, instructor, title, top_slate])):
        cprint(
            '\nERROR: Spec must have Course, Section, Instructor, Title and Top Slate value for each row',
            'red')
        raise ValueError()

    # all fields must not contain invalid characters
    if all(map(_has_invalid_char, vals)):
        cprint('\nERROR: Contains illegal character', 'red')
        raise ValueError()

    # top slate must finish with mp4
    if top_slate[-4:] != '.mp4':
        cprint('\nERROR: Must include value for slate that ends in .mp4', 'red')
        raise ValueError()

    if len(title) > 45:
        cprint('\nERROR: Does not support titles with more than 45 characters', 'red')
        raise ValueError()

    # body must finish with .mp4 (if included)
    if _has_value(body) and body[-4:] != '.mp4':
        cprint('\nERROR: If body is included, csv value must end in .mp4', 'red')
        raise ValueError()

    # watermark must end in .png
    if (_has_value(watermark) and watermark[-4:] != '.png'):
        cprint('\nERROR: If watermark included, csv value must end in .png', 'red')
        raise ValueError()

    return (
        course,
        section,
        instructor,
        title,
        top_slate,
        body,
        watermark,
        wm_pos
    )


def _has_invalid_char(str_val):

    invalid_chars = ['/', '|', '@', '^']

    for char in invalid_chars:
        if str_val.find(char) != -1:
            return True

    return False


def _make_course_folders(destination_path, specs):
    """TODO Docstring
    """
    unique_courses = set()
    for index, row in specs.iterrows():
        if not _has_value(row['Course']):
            # if no course value don't make a folder
            continue
        unique_courses.add(row['Course'])

    for course in unique_courses:
        path = f'{destination_path}/{course}'
        try:
            os.mkdir(path)
        except OSError as error:
            print(error)


def _load_specifications(path):
    """TODO docstring
    """
    try:
        specs = pd.read_csv(path + '/specs.csv', dtype={'Section': 'str'})
    except IOError as error:
        cprint('\nError loading CSV:', 'red')
        cprint(f'{error}\n', 'red', attrs=['dark'])
        sys.exit()
    except ParserError:
        cprint('\nERROR: Could not parse specs.csv, ensure correctly formatted.', 'red')
        sys.exit()
    except EmptyDataError:
        cprint('\nERROR: Ensure specs.csv has data.', 'red')
        sys.exit()

    expected_cols = {'Course', 'Section', 'Instructor', 'Title', 'Top Slate',
                     'Body', 'Watermark', 'Watermark Position'}

    actual_cols = set(list(specs))

    # Check that we have all the columns we expect
    if expected_cols != actual_cols:
        cprint('\nERROR: Missing or incorrect columns in specs.csv', 'red')
        cprint(f'Expected columns: {expected_cols}\n')
        sys.exit()

    return specs


def _clear_folder_contents(folder_path):
    """Clears directory contents

    Args:
        folder_path: Path of the folder to clear
    """

    for subdir in os.listdir(folder_path):
        if subdir not in ('.gitkeep', '.DS_Store'):
            subdir_path = f'{folder_path}/{subdir}'
            shutil.rmtree(subdir_path, ignore_errors=False, onerror=None)


def _has_value(cell):
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
    if (cell.lower() == 'none' or cell.lower() == 'null' or
            cell.lower() == 'nan' or cell == '0'):
        return False

    return True


if __name__ == "__main__":
    main()
