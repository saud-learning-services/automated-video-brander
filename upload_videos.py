import os
import logging
import datetime
import codecs
from termcolor import cprint
from dotenv import load_dotenv
from helpers import load_specifications, get_video_attributes
from panopto.panopto_oauth2 import PanoptoOAuth2
from panopto.panopto_interface import Panopto


def upload_videos():
    load_dotenv()

    root = os.path.dirname(os.path.abspath(__file__))

    specs = load_specifications(root + '/input')

    server = os.getenv('SERVER')
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    oauth2 = PanoptoOAuth2(server, client_id, client_secret, True)

    panopto = Panopto(server, True, oauth2)
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
        course_code = specs['course']
        video_title = specs['title']
        instructor_name = specs['instructor']
        src_url = specs['src_url']

        cprint(f'Starting upload for <row {index}>:', 'yellow')
        logging.info('Starting UPLOAD for <row %i> | %s - %s',
                     index, video_title, instructor_name)

        print(f'\nVIDEO TITLE: {video_title}')
        print(f'COURSE: {course_code}')
        print(f'INSTRUCTOR NAME: {instructor_name}')
        print(f'UNIQUE ID: {video_id}\n')

        # URL must begin with 'https://ubc.ca.panopto.com'
        panopto_instance = src_url[:27]
        if panopto_instance != 'https://ubc.ca.panopto.com/':
            cprint(
                f'\nThe source URL provided ({src_url}) is not a UBC panopto instance', 'red')
            cprint(
                f'Skipping upload for video: "{video_title}"...\n', 'red')
            logging.error(
                'The source URL provided: "%s" is not a UBC panopto instance. Skipping video: %s', src_url, video_title)
            continue

        # delivery id is in last 36 characters of URL
        delivery_id = src_url[-36:]

        panopto_folder_name, panopto_folder_id = panopto.get_containing_folder(
            delivery_id)

        # folder containing the streams to upload
        local_folder_path = f'output/{video_title}_{instructor_name}_{video_id}'

        if not instructor_name:
            local_folder_path = f'output/{video_title}_{video_id}'

        # manifest cannot have '&' character in it

        # manifest_title = f'{__normalize_title(video_title)}_branded'
        manifest_title = f'{__normalize_title(video_title)}'
        try:
            __create_manifest(local_folder_path, manifest_title)
        except RuntimeError as err:
            cprint('\nERROR: Could not create manifest', 'red')
            logging.error(
                'Could not create manifest for video: %s. Skipping...', video_title)
            logging.error(err)
            cprint(err, 'red')
            print('')
            continue

        cprint(
            f'Writing video: "{manifest_title}"" to Panopto folder: \n=> {panopto_folder_name}\n', 'blue')

        try:

            panopto.upload_folder(local_folder_path, panopto_folder_id)
            cprint('UPLOAD COMPLETED\n', 'green')
            cprint(f'   video: {video_title}', 'blue')
            cprint(f'   src folder: {local_folder_path}', 'blue')
            cprint(f'   destination (panopto): {panopto_folder_name}', 'blue')
        except FileNotFoundError as err:
            cprint(
                f'\nCould not find file for upload: {local_folder_path}', 'red')
            cprint('Skipping video...\n', 'red')
            logging.error(
                'Could not find file for upload: %s. Skipping video: %s...', local_folder_path, video_title)


def __create_manifest(target_folder, video_title):
    num_items = len(os.listdir(target_folder))

    if num_items == 1:
        __create_single_stream_manifest(target_folder, video_title)
    elif num_items == 2:
        __create_multi_stream_manifest(target_folder, video_title)
    else:
        raise RuntimeError(
            f'Unexpected number of items ({num_items}) in target folder: {target_folder}')


def __create_single_stream_manifest(target_folder, title):

    single_stream_manifestest_template = 'panopto/manifest_templates/single_stream_manifest_template.xml'

    with open(single_stream_manifestest_template) as fr:
        template = fr.read()
    content = template\
        .replace('{Title}', title)\
        .replace('{Description}', 'Migrated from old Sauder Learning Services Panopto server')\
        .replace('{Filename}', 'primary.mp4')\
        .replace('{Date}', datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f-00:00'))
    with codecs.open(f'{target_folder}/single_stream_manifest.xml', 'w', 'utf-8') as fw:
        fw.write(content)


def __create_multi_stream_manifest(target_folder, title):
    single_stream_manifestest_template = 'panopto/manifest_templates/multi_stream_manifest_template.xml'

    with open(single_stream_manifestest_template) as fr:
        template = fr.read()
    content = template\
        .replace('{Title}', title)\
        .replace('{Description}', 'This video was processed by the Sauder Automated Video Branding Tool')\
        .replace('{PrimaryFilename}', 'primary.mp4')\
        .replace('{SecondaryFilename}', 'secondary.mp4')\
        .replace('{Date}', datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f-00:00'))
    with codecs.open(f'{target_folder}/multi_stream_manifest.xml', 'w', 'utf-8') as fw:
        fw.write(content)


def __normalize_title(title):
    return title.replace('&', 'and')


if __name__ == '__main__':
    upload_videos()
