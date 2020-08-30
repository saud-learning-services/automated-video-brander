import os
from dotenv import load_dotenv
from termcolor import cprint
from panopto.panopto_oauth2 import PanoptoOAuth2
from panopto.panopto_interface import Panopto
from helpers import load_specifications, get_video_attributes, archive_folder_contents


def download_videos():
    load_dotenv()

    root = os.path.dirname(os.path.abspath(__file__))

    specs = load_specifications(root + '/input')

    server = os.getenv('SERVER')
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    oauth2 = PanoptoOAuth2(server, client_id, client_secret, True)
    panopto = Panopto(server, True, oauth2)

    cprint('\nArchiving & clearing input/body folder...', 'yellow')
    archive_folder_contents('input/body')

    for index, row in specs.iterrows():
        print('\n------------------------------------------\n')

        try:
            specs = get_video_attributes(row)
        except ValueError:
            cprint('Skipping video...', 'red')
            continue

        course = specs['course']
        title = specs['title']
        instructor = specs['instructor']
        src_url = specs['src_url']

        cprint(f'Starting download for <row {index}>:', 'yellow')
        print(f'\nVIDEO TITLE: {title}')
        print(f'COURSE: {course}')
        print(f'INSTRUCTOR NAME: {instructor}\n')

        filename = f'{title}_{instructor}.mp4'

        output_folder = f'{root}/input/body/{title}_{instructor}'

        if not instructor:
            # filepath if no instructor specified
            output_folder = f'{root}/input/body/{title}'

        delivery_id = src_url[-36:]

        try:
            panopto.download_video(delivery_id, output_folder)
        except RuntimeError as err:
            cprint(err, 'red')
            continue
