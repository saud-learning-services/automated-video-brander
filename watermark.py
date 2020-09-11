import os
import shutil
import logging
from shutil import copyfile

from termcolor import cprint

from body.body import Body

from helpers import load_specifications, get_video_attributes


def watermark():
    '''
    ARG: specs (Pandas Dataframe)
    Loops through all the rows in the CSV
    If a clip has a body, check if it has a watermark
    If a clip has a watermark, render it (with watermark) to body/PROCESSED folder
    It not, just move the clip over
    '''

    cprint('Deleting "PROCESSING" folder...', 'yellow')
    logging.info('Deleting "PROCESSING" folder...')
    __delete_processing_folder()

    cprint('Creating empty "PROCESSING" folder', 'yellow')
    logging.info('Creating empty "PROCESSING" folder')
    __make_processing_folder()

    root = os.path.dirname(os.path.abspath(__file__))
    specs = load_specifications(root + '/input')

    print(root)

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

        video_id = specs['id']
        course = specs['course']
        title = specs['title']
        instructor = specs['instructor']
        watermark = specs['watermark']
        wm_position = specs['wm_pos']

        cprint(f'Starting watermarking for <row {index}>:', 'yellow')
        logging.info('Starting WATERMARKING for <row %i> | %s - %s',
                     index, title, instructor)
        print(f'\nVIDEO TITLE: {title}')
        print(f'COURSE: {course}')
        print(f'INSTRUCTOR NAME: {instructor}')
        print(f'UNIQUE ID: {video_id}\n')

        input_folder = f'{root}/input/body/{title}_{instructor}_{video_id}'
        output_folder = f'{root}/input/body/PROCESSED/{title}_{instructor}_{video_id}'

        if not instructor:
            input_folder = f'{root}/input/body/{title}_{video_id}'
            output_folder = f'{root}/input/body/PROCESSED/{title}_{video_id}'

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        for filename in os.listdir(input_folder):
            input_video_file_path = f'{input_folder}/{filename}'
            output_video_file_path = f'{output_folder}/{filename}'
            if filename.endswith(".mp4"):
                if (watermark):
                    watermark_path = f'input/watermark/bottom-right/{watermark}'

                    if wm_position in ['l', 'L']:
                        watermark_path = f'input/watermark/bottom-left/{watermark}'

                    body_clip = Body(
                        filename, input_video_file_path, output_video_file_path, watermark_path)

                    body_clip.process_video()
                else:
                    cprint(
                        'Clip does not need watermark, moving raw clip to PROCESSING folder', 'yellow')
                    logging.warning(
                        'Clip does not need watermark, moving raw clip to PROCESSING folder')
                    copyfile(
                        input_video_file_path, output_video_file_path)
            else:
                cprint(f'Skipping {filename}, non-mp4 file in: {input_folder}')
                logging.error(
                    'Skipping %s, non-mp4 file in: %s', filename, input_folder)
                continue


def __make_processing_folder():
    '''
    Creates a temporary working folder for watermarked videos
    Returns the file path
    '''

    temp_dir_path = 'input/body/PROCESSED'

    if not os.path.isdir(temp_dir_path):
        os.mkdir(temp_dir_path)
    return 0


def __delete_processing_folder():
    '''
    Delete the temporary folder made by _make_temporary_working_folder()
    '''
    temp_dir_path = 'input/body/PROCESSED'
    if os.path.isdir(temp_dir_path):
        shutil.rmtree(temp_dir_path, ignore_errors=False, onerror=None)


if __name__ == '__main__':
    watermark()
