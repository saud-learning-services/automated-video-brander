'''
stitch.py
Automated Video Branding Tool

Author: Marko Prodanovic
'''

# Standard imports
import os
import logging

# Moviepy (primary library)
# Docs: https://zulko.github.io/moviepy/index.html
from moviepy.editor import (
    VideoFileClip,
    concatenate_videoclips)

from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from moviepy.audio.fx.audio_fadeout import audio_fadeout
from moviepy.audio.fx.audio_fadein import audio_fadein


# Additional dependencies
from termcolor import cprint

# Local modules
from top.top import Top

from helpers import load_specifications, get_video_attributes, archive_folder_contents


def stitch():
    '''
    Stitch the top, body and tail clips together
    '''

    # project root directory
    root = os.path.dirname(os.path.abspath(__file__))

    cprint('\nLoading Specifications from CSV...', 'yellow')
    specs = load_specifications(root + '/input')

    cprint('Archiving & clearing output folder...', 'yellow')
    logging.info('Archiving & clearing output folder...')
    archive_folder_contents('output')

    for index, row in specs.iterrows():

        print('\n------------------------------------------\n')

        try:
            specs = get_video_attributes(row)
        except ValueError:
            cprint('Skipping video...', 'red')
            attempted_video_title = row['Title']
            logging.error(
                'Invalid values in specs. Skipping video: %s, row: %i', attempted_video_title, index)
            continue

        course = specs['course']
        section = specs['section']
        instructor = specs['instructor']
        title = specs['title']
        top_slate = specs['top_slate']

        cprint(f'Starting top/tail stitching for <row {index}>:', 'yellow')
        logging.info('Starting TOP/TAIL STITCHING for <row %i> | %s - %s',
                     index, title, instructor)
        print(f'\nVIDEO TITLE: {title}')
        print(f'COURSE: {course}')
        print(f'INSTRUCTOR NAME: {instructor}\n')

        top = Top(top_slate=top_slate, title=title, course=course,
                  section=section, instructor=instructor)
        top_rendered = top.get_video()

        # same tail for all videos
        tail = VideoFileClip(
            'input/tail/tail.mp4').fx(audio_fadein, duration=1.5)

        input_folder = f'input/body/PROCESSED/{title}_{instructor}'
        output_folder = f'output/{title}_{instructor}'

        if not instructor:
            input_folder = f'input/body/PROCESSED/{title}'
            output_folder = f'output/{title}'

        for clip_name in os.listdir(input_folder):
            try:
                body_video = (VideoFileClip(f'{input_folder}/{clip_name}')
                              .fx(fadein, duration=1, initial_color=[255, 255, 255])
                              .fx(fadeout, duration=1, final_color=[255, 255, 255])
                              .fx(audio_fadeout, duration=2)
                              .fx(audio_fadein, duration=1.5))
                final_clip = concatenate_videoclips(
                    [top_rendered, body_video, tail])

            except OSError:
                cprint(
                    f'Could not find specifiied clip: "{clip_name}" in folder: ', 'red')
                logging.error(
                    'Could not find specifiied clip: "%s" in folder: "%s". Skipping video...', clip_name, input_folder)
                cprint(input_folder, 'yellow')
                cprint('Skipping video...', 'red')
                continue

            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            cprint(
                f'Writing to output folder: \n=> {output_folder}\n', 'blue')

            output_video_path = f'{output_folder}/{clip_name}'

            try:
                final_clip.write_videofile(output_video_path,
                                           fps=30,
                                           threads=8,
                                           preset='ultrafast',
                                           temp_audiofile='temp-audio.m4a',
                                           remove_temp=True,
                                           codec='libx264',
                                           audio_codec='aac')
                cprint('\nSUCCESS', 'green')
            except Exception as error:
                logging.error(error)
                cprint(error, 'red')
                continue


if __name__ == '__main__':
    stitch()
