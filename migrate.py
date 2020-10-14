import os

from panopto.panopto_oauth2 import PanoptoOAuth2
from panopto.panopto_interface import Panopto

import pandas as pd
import pprint as pp

from dotenv import load_dotenv


def migrate_vidos():
    load_dotenv()
    # root = os.path.dirname(os.path.abspath(__file__))

    server = os.getenv('SERVER')
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    oauth2 = PanoptoOAuth2(server, client_id, client_secret, True)

    panopto = Panopto(server, True, oauth2)

    # Create the specs DataFrame with necessary columns
    columns = ['Id', 'Course', 'Section', 'Instructor', 'Title',
               'Top Slate', 'Watermark', 'Watermark Position', 'Source URL']
    specs = pd.DataFrame(columns=columns)

    folder_id = 'c91127d3-6eb2-4723-b1df-ac410107a30c'

    unique_id = 1

    sessions = panopto.get_sessions(folder_id)
    for session in sessions:
        url = session['Urls']['ViewerUrl']
        data = {
            'Id': str(unique_id),
            'Course': '',
            'Section': '',
            'Instructor': '',
            'Source Folder': session['FolderDetails']['Name'],
            'Title': session['Name'],
            'Top Slate': 'sauder_slate.mp4',
            'Watermark': '',
            'Watermark Position': '',
            'Source URL': url
        }
        specs = specs.append(data, ignore_index=True)
        unique_id += 1

    print('Writing output csv!')
    specs.to_csv('input/specs.csv', index=False)


if __name__ == '__main__':
    migrate_vidos()
