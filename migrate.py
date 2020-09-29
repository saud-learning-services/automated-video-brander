import os
from dotenv import load_dotenv

from panopto.panopto_oauth2 import PanoptoOAuth2
from panopto.panopto_interface import Panopto

import pandas as pd
import pprint as pp


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

    folder_id = '84504582-395c-4878-9898-a931013c1dd6'

    # Get a list of child folders from the given parent
    child_folders = panopto.get_child_folders(folder_id)

    # For each subfolder
    for result in child_folders['Results']:
        # Get a list of sessions in the given folder
        subfolder_id = result['Id']
        # print(subfolder_id)
        sessions = panopto.get_sessions(subfolder_id)
        for session in sessions:
            # print(session)
            # pp.pprint(session)
            url = session['Urls']['ViewerUrl']
            data = {
                'Id': '666',
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

    print('Writing output csv!')
    specs.to_csv('input/specs.csv', index=False)


if __name__ == '__main__':
    migrate_vidos()
