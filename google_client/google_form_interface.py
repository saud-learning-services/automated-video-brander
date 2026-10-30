import os
from datetime import datetime
import gspread
from dotenv import load_dotenv
import google.auth
import pandas as pd
import logging

from .google_spec_helpers import (
    requires_more_edits,
    translate_video_properties,
    remove_previously_run_videos,
    archive_previous_specs,
    save_last_run_time
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

        # Create the specs with necessary columns
        columns = ['Id', 'Course', 'Section', 'Instructor', 'Title',
                   'Top Slate', 'Tail', 'Watermark', 'Watermark Position', 'Source URL']
        rows = []

        # Load the google-form data as DataFrame
        run_started = datetime.now()
        form_data = self.__get_form_df()

        archive_previous_specs()
        form_data = remove_previously_run_videos(form_data)

        for index, video in form_data.iterrows():

            # Skip row if it requires an editor
            if requires_more_edits(video):
                logging.error(
                    'Video requires editor. Automated process skipping...')
                print('Video requires editor')
                print('Skipping video...')
                continue

            props = translate_video_properties(video)

            if props['src_url'].startswith('https://sauderlearningservices.hosted.panopto.com/'):
                logging.error(
                    'Wrong instance (using OLD learning services Panopto)')
                print('Skipping video...')
                continue

            data = {
                'Id': props['id'],
                'Course': props['course_code'],
                'Section': props['section_number'],
                'Instructor': props['instructor'],
                'Title': props['title'],
                'Top Slate': props['top_slate'],
                'Tail': props['tail'],
                'Watermark': props['watermark'],
                'Watermark Position': props['wm_pos'],
                'Source URL': props['src_url']
            }

            rows.append(data)

        print('Writing output csv!')
        logging.info('Writing google form data to specs.csv...')
        pd.DataFrame(rows, columns=columns).to_csv('input/specs.csv', index=False)

        return run_started

    def save_last_run(self, run_started):
        '''
        Mark form responses up to run_started as handled.
        Called by the brander once Panopto login has been confirmed, so a login
        failure doesn't silently drop that run's requests.
        '''
        save_last_run_time(run_started)

    def __get_form_df(self):
        '''
        '''
        sheet = self.client.open(self.spreadsheed).sheet1
        df = pd.DataFrame(sheet.get_all_records())
        return df


if __name__ == '__main__':
    # Preview only: writes specs.csv without marking the requests as handled
    google = GoogleFormInterface()
    google.generate_specs()
