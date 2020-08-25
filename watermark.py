import os
import shutil
from shutil import copyfile

from termcolor import cprint

from body.body import Body

from helpers import load_specifications, get_video_attributes, has_value


def process_body_clips():
    """
    ARG: specs (Pandas Dataframe)
    Loops through all the rows in the CSV
    If a clip has a body, check if it has a watermark
    If a clip has a watermark, render it (with watermark) to body/PROCESSED folder
    It not, just move the clip over
    """

    print('🗑  Deleting PROCESSING folder')
    _delete_temporary_working_folder()

    root = os.path.dirname(os.path.abspath(__file__))

    print('📁 Recreating empty PROCESSING folder')
    _make_temporary_working_folder()

    specs = load_specifications(root + '/input')

    for index, row in specs.iterrows():
        print(
            '\n========================================================================\n')
        course = row['Course']
        title = row['Title']
        print(f'🎥 {course} | {title} | Row {index + 1}')

        try:
            video = get_video_attributes(row)
            body = video['body']
            watermark = video['watermark']
            wm_position = video['wm_pos']
        except ValueError:
            cprint('Skipping video...', 'red')
            continue

        if (has_value(body)):

            body_path = f'input/body/{body}'

            if (has_value(watermark)):
                watermark_path = f'input/watermark/bottom-right/{watermark}'

                if wm_position in ['l', 'L']:
                    watermark_path = f'input/watermark/bottom-left/{watermark}'

                # _make_temporary_working_folder()

                body_clip = Body(body, body_path, watermark_path)

                body_path = body_clip.get_video()
            else:
                cprint(
                    'Clip does not need watermark, moving raw clip to PROCESSING folder', 'yellow')
                copyfile(body_path, f'input/body/PROCESSED/{body}')


# PRIVATE HELPERS:

def _make_temporary_working_folder():
    """
    Creates a temporary working folder for watermarked videos
    Returns the file path
    """

    temp_dir_path = 'input/body/PROCESSED'

    if not os.path.isdir(temp_dir_path):
        os.mkdir(temp_dir_path)
    return 0


def _delete_temporary_working_folder():
    """
    Delete the temporary folder made by _make_temporary_working_folder()
    """
    temp_dir_path = 'input/body/PROCESSED'
    if os.path.isdir(temp_dir_path):
        shutil.rmtree(temp_dir_path, ignore_errors=False, onerror=None)


if __name__ == '__main__':
    process_body_clips()
