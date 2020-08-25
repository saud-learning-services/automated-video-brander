"""
UBC Sauder School of Business
Automated Video Branding Tool

Author: Marko Prodanovic
"""

# Standard imports
import shutil
# import sys
import os

# Moviepy (primary library)
# Docs: https://zulko.github.io/moviepy/index.html
from moviepy.editor import (
    VideoFileClip,
    # ImageClip,
    # CompositeVideoClip,
    concatenate_videoclips)
# import moviepy.video.fx.all as vfx
# import moviepy.audio.fx.all as sfx

from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from moviepy.audio.fx.audio_fadeout import audio_fadeout
from moviepy.audio.fx.audio_fadein import audio_fadein


# Additional dependencies
from termcolor import cprint

# Local modules
from top.top import Top

from helpers import load_specifications, get_video_attributes, has_value


def main():
    """ Main entry point for Automated Video Branding Tool
    """

    # settings object for global variables
    settings = {
        'root': os.path.dirname(os.path.abspath(__file__))
    }

    print('\n🚚 Loading Specifications from CSV...')
    specs = load_specifications(settings['root'] + '/input')

    print('🧹 Clearing output folder...')
    _clear_folder_contents(settings['root'] + '/output')

    print('🔨 Building course folders in output folder...')
    _make_course_folders(settings['root'] + '/output', specs)

    # ==== STITCH VIDEOS TOGETHER ====

    for index, row in specs.iterrows():

        print(
            '\n========================================================================\n')
        course = row['Course']
        title = row['Title']
        print(f'🎥 {course} | {title} | Row {index + 1}')

        try:
            video = get_video_attributes(row)
            course = video['course']
            section = video['section']
            instructor = video['instructor']
            title = video['title']
            top_slate = video['top_slate']
            body = video['body']
        except ValueError:
            cprint('Skipping video...', 'red')
            continue

        top = Top(top_slate=top_slate, title=title, course=course,
                  section=section, instructor=instructor)
        top_rendered = top.get_video()

        # same tail for all videos
        tail = VideoFileClip(
            'input/tail/tail.mp4').fx(audio_fadein, duration=1.5)

        if (has_value(body)):
            body_path = f'input/body/PROCESSED/{body}'

            try:
                body_video = (VideoFileClip(body_path)
                              .fx(fadein, duration=1, initial_color=[255, 255, 255])
                              .fx(fadeout, duration=1, final_color=[255, 255, 255])
                              .fx(audio_fadeout, duration=2)
                              .fx(audio_fadein, duration=1.5))
                #   .fx(audio_fadeout, duration=1.5))
                final_clip = concatenate_videoclips(
                    [top_rendered, body_video, tail])

            except OSError:
                cprint('Could not find specifiied body clip in path: ', 'red')
                cprint(body_path, 'yellow')
                cprint('Skipping video...', 'red')
                continue
        else:
            final_clip = concatenate_videoclips([top_rendered, tail])

        print(f'📁 Writing to output folder {course}...')

        final_video_path = f'output/{course}/{title}.mp4'

        if course is None:
            final_video_path = f'output/other/{title}.mp4'

        try:
            final_clip.write_videofile(final_video_path,
                                       fps=30,
                                       threads=8,
                                       preset='ultrafast',
                                       temp_audiofile='temp-audio.m4a',
                                       remove_temp=True,
                                       codec='libx264',
                                       audio_codec='aac')
            cprint('\nSUCCESS', 'green')
        except Exception as error:
            cprint(error, 'red')
            continue


def _make_course_folders(destination_path, specs):
    """TODO Docstring
    """
    unique_courses = set()
    for index, row in specs.iterrows():
        if not has_value(row['Course']):
            # if no course value and no "other" folder yet, make it
            other_dir_path = f'{destination_path}/other'
            if not os.path.isdir(other_dir_path):
                os.mkdir(other_dir_path)
            continue
        unique_courses.add(row['Course'])

    for course in unique_courses:
        path = f'{destination_path}/{course}'
        try:
            os.mkdir(path)
        except OSError as error:
            print(error)


def _clear_folder_contents(folder_path):
    """Clears directory contents

    Args:
        folder_path: Path of the folder to clear
    """

    for subdir in os.listdir(folder_path):
        if subdir not in ('.gitkeep', '.DS_Store'):
            subdir_path = f'{folder_path}/{subdir}'
            shutil.rmtree(subdir_path, ignore_errors=False, onerror=None)


if __name__ == '__main__':
    main()
