import os
from termcolor import cprint
from dotenv import load_dotenv
from helpers import load_specifications, get_video_attributes
from panopto.panopto_oauth2 import PanoptoOAuth2
from panopto.panopto_interface import Panopto

load_dotenv()

root = os.path.dirname(os.path.abspath(__file__))

specs = load_specifications(root + '/input')

server = os.getenv('SERVER')
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

oauth2 = PanoptoOAuth2(server, client_id, client_secret, True)

panopto = Panopto(server, True, oauth2)

for index, row in specs.iterrows():
    print(
        '\n========================================================================\n')

    row = get_video_attributes(row)
    course = row['course']
    title = row['title']
    print(f'🎥 {course} | {title} | Row {index + 1}')

    video_title = row['title']
    output_filename = f'{video_title}_branded.mp4'
    src_url = row['src_url']

    # URL must begin with 'https://ubc.ca.panopto.com'
    panopto_instance = src_url[:27]
    if panopto_instance != 'https://ubc.ca.panopto.com/':
        cprint(
            f'\nThe source URL provided ({src_url}) is not a UBC panopto instance', 'red')
        cprint(
            f'Skipping upload for video: "{video_title}_branded.mp4"...\n', 'red')
        continue

    # delivery id is in last 36 characters of URL
    delivery_id = src_url[-36:]

    folder_name, folder_id = panopto.get_containing_folder(delivery_id)

    cprint(
        f'Starting upload of video: "{video_title}" to folder: "{folder_name}"" on Panopto', 'yellow')
    filepath = f'output/{course}/{output_filename}'

    # check if course is nan and change filepath to target 'other' folder
    if course is None:
        filepath = f'output/other/{output_filename}'
    try:

        panopto.upload_video(filepath, folder_id)
        cprint(
            f'Video: "{video_title}" should now be processing in folder: "{folder_name}"" on Panopto\n', 'green')
    except FileNotFoundError as err:
        cprint(f'\nCould not find file for upload: {filepath}', 'red')
        cprint('Skipping video...\n', 'red')
