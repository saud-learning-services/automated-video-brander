import os
import gspread
from dotenv import load_dotenv
import google.auth
import pandas as pd
import logging

from .google_spec_helpers import (
    requires_more_edits,
    translate_video_properties,
    remove_previously_run_videos,
    archive_previous_specs
)

SCOPES = ['https://spreadsheets.google.com/feeds',
          'https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive.file',
          'https://www.googleapis.com/auth/drive']


class GoogleFormInterface:
    '''
    '''

    def __init__(self):
        '''
        '''
        load_dotenv()

        # default method will automatically use GOOGLE_APPLICATION_CREDENTIALS from env
        # it will load credentials from sercrets.json
        credentials, project = google.auth.default(scopes=SCOPES)

        self.spreadsheed = os.getenv('USER_REQUESTS_SPREADSHEET_TITLE')
        self.credentials = credentials
        self.client = gspread.authorize(credentials)

    def generate_specs(self):
        '''
        '''

        # Create the specs DataFrame with necessary columns
        columns = ['Course', 'Section', 'Instructor', 'Title',
                   'Top Slate', 'Watermark', 'Watermark Position', 'Source URL']
        specs = pd.DataFrame(columns=columns)

        # Load the google-form data as DataFrame
        form_data = self.__get_form_df()

        archive_previous_specs()
        form_data = remove_previously_run_videos(form_data)

        for index, video in form_data.iterrows():

            if requires_more_edits(video):
                logging.error(
                    'Video requires editor. Automated process skipping...')
                print('Video requires editor')
                print('Skipping video...')
                continue

            props = translate_video_properties(video)

            data = {
                'Course': props['course_code'],
                'Section': props['section_number'],
                'Instructor': props['instructor'],
                'Title': props['title'],
                'Top Slate': 'sauder_slate.mp4',
                'Watermark': props['watermark'],
                'Watermark Position': props['wm_pos'],
                'Source URL': props['src_url']
            }

            specs = specs.append(data, ignore_index=True)

        print('Writing output csv!')
        logging.info('Writing google form data to specs.csv...')
        specs.to_csv('input/specs.csv', index=False)

    def __get_form_df(self):
        '''å
        '''
        sheet = self.client.open(self.spreadsheed).sheet1
        df = pd.DataFrame(sheet.get_all_records())
        return df


if __name__ == '__main__':
    google = GoogleFormInterface()
    google.generate_specs()
