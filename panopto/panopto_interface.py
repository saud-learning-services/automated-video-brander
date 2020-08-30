#!python3
from dotenv import load_dotenv
import os
import json
import copy
import codecs
import time
from datetime import datetime
import boto3  # AWS SDK (boto3)
import requests
import youtube_dl

# import webbrowser

# import youtube_dl

# from helpers import name_normalize

# Modified class from:
# => https://github.com/Panopto/upload-python-sample/tree/master/simplest
# Apache-2.0 License

# Size of each part of multipart upload.
# This must be between 5MB and 25MB. Panopto server may fail if the size is more than 25MB.
PART_SIZE = 5 * 1024 * 1024

# Template for manifest XML file.
MANIFEST_FILE_TEMPLATE = 'panopto/upload_manifest_template.xml'

# Filename of manifest XML file. Any filename is acceptable.
MANIFEST_FILE_NAME = 'panopto/upload_manifest_generated.xml'


class Panopto:
    def __init__(self, server, ssl_verify, oauth2):
        '''
        Constructor of uploader instance.
        This goes through authorization step of the target server.
        '''
        self.server = server
        self.ssl_verify = ssl_verify
        self.oauth2 = oauth2
        self.current_token = None

        # Use requests module's Session object in this example.
        # This is not mandatory, but this enables applying the same settings (especially
        # OAuth2 access token) to all calls and also makes the calls more efficient.
        # ref. https://2.python-requests.org/en/master/user/advanced/#session-objects
        self.requests_session = requests.Session()
        self.requests_session.verify = self.ssl_verify

        self.__setup_or_refresh_access_token()

    def __setup_or_refresh_access_token(self):
        '''
        This method invokes OAuth2 Authorization Code Grant authorization flow.
        It goes through browser UI for the first time.
        It refreshes the access token after that and no user interfaction is requetsed.
        This is called at the initialization of the class, as well as when 401 (Unaurhotized) is returend.
        '''
        access_token = self.oauth2.get_access_token_authorization_code_grant()
        self.requests_session.headers.update(
            {'Authorization': 'Bearer ' + access_token})
        self.current_token = access_token

    def __inspect_response_is_retry_needed(self, response):
        '''
        Inspect the response of a requets' call.
        True indicates the retry needed, False indicates success. Othrwise an exception is thrown.
        Reference: https://stackoverflow.com/a/24519419

        This method detects 403 (Forbidden), refresh the access token, and returns as 'is retry needed'.
        This example focuses on the usage of upload API and OAuth2, and any other error handling is not implemented.
        Prodcution code should handle other failure cases and errors as appropriate.
        '''
        if response.status_code // 100 == 2:
            # Success on 2xx response.
            return False

        if response.status_code == requests.codes.forbidden:
            print('Forbidden. This may mean token expired. Refresh access token.')
            self.__setup_or_refresh_access_token()
            return True

        # Throw unhandled cases.
        response.raise_for_status()

    def download_video(self, session_id, output_folder):
        load_dotenv()
        server = os.getenv('SERVER')
        # session = self.__get_session(session_id)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        self.requests_session.headers.update(
            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Safari/605.1.15',
             'Content-Type': 'video/mp4'})
        self.requests_session.cookies = requests.utils.cookiejar_from_dict(
            {'.ASPXAUTH': os.getenv('ASPXAUTH')})

        url = f'https://{server}/Panopto/Pages/Viewer/DeliveryInfo.aspx'
        params = {
            "deliveryId": session_id,
            "responseType": "json"
        }
        delivery_info = self.requests_session.post(url=url, params=params)
        delivery_info = json.loads(delivery_info.text)
        streams = delivery_info["Delivery"]["Streams"]
        # print(streams)
        for i in range(len(streams)):
            filename = "{:02d}_{}.mp4".format(i, streams[i]["Tag"])
            if streams[i]['StreamType'] == 1:
                filename = 'primary.mp4'
            elif streams[i]['StreamType'] == 2:
                filename = 'secondary.mp4'
            else:
                raise ValueError
            # filename = "{:02d}_{}.mp4".format(i, streams[i]["Tag"])
            dest_filename = os.path.join(output_folder, filename)
            print("Downloading:", dest_filename)
            ydl_opts = {
                "outtmpl": dest_filename,
                "quiet": True
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([streams[i]["StreamUrl"]])

    def __get_session(self, session_id):
        '''
        Call GET /api/v1/sessions/{id} API and return the response
        '''
        while True:
            url = 'https://{0}/Panopto/api/v1/sessions/{1}'.format(

                self.server, session_id)
            resp = self.requests_session.get(url=url)
            if self.__inspect_response_is_retry_needed(resp):
                continue
            data = resp.json()
            break
        return data

    def get_containing_folder(self, delivery_id):
        '''
        Given a sessions delivery_id, make the necessary calls to get its folder id
        '''

        session = self.__get_session(delivery_id)
        details = session['FolderDetails']

        folder_id = details['Id']
        folder_name = details['Name']

        return (folder_name, folder_id)

    def upload_video(self, file_path, folder_id):
        '''
        Main upload method to go through all required steps.
        '''
        # step 1 - Create a session
        session_upload = self.__create_session(folder_id)
        upload_id = session_upload['ID']
        upload_target = session_upload['UploadTarget']

        print('UPLOAD TARGET: ' + upload_target)

        # step 2 - upload the video file
        self.__multipart_upload_single_file(upload_target, file_path)

        # step 3 - create manifest file and uplaod it
        self.__create_manifest_for_video(file_path, MANIFEST_FILE_NAME)
        self.__multipart_upload_single_file(upload_target, MANIFEST_FILE_NAME)

        # step 4 - finish the upload
        self.__finish_upload(session_upload)

        # step 5 - monitor the progress of processing
        self.__monitor_progress(upload_id)

    def upload_folder(self, local_folder, folder_id):
        '''
        Main upload method to go through all required steps.
        '''
        # step 1 - Create a session
        session_upload = self.__create_session(folder_id)
        upload_id = session_upload['ID']
        upload_target = session_upload['UploadTarget']

        print('UPLOAD TARGET: ' + upload_target)

        # step 2 - Enumerate files under the local folder
        files = self.__enumerate_files(local_folder)

        # step 3 - upload the files
        for file_path in files:
            self.__multipart_upload_single_file(upload_target, file_path)

        # step 4 - finish the upload
        self.__finish_upload(session_upload)

        # step 5 - monitor the progress of processing
        self.__monitor_progress(upload_id)

    def __enumerate_files(self, folder):
        '''
        Return the list of files in the specified folder. Not to traverse sub folders.
        '''
        print('')
        files = []
        for entry in os.listdir(folder):
            path = os.path.join(folder, entry)
            if os.path.isdir(path):
                continue
            files.append(path)
            print('  {0}'.format(path))

        return files

    def __create_session(self, folder_id):
        '''
        Create an upload session. Return sessionUpload object.
        '''
        print('')
        while True:
            print('Calling POST PublicAPI/REST/sessionUpload endpoint')
            url = 'https://{0}/Panopto/PublicAPI/REST/sessionUpload'.format(
                self.server)
            payload = {'FolderId': folder_id}
            headers = {'content-type': 'application/json'}
            resp = self.requests_session.post(
                url=url, json=payload, headers=headers)
            if not self.__inspect_response_is_retry_needed(resp):
                break

        session_upload = resp.json()
        print('  ID: {0}'.format(session_upload['ID']))
        print('  target: {0}'.format(session_upload['UploadTarget']))
        return session_upload

    def __multipart_upload_single_file(self, upload_target, file_path):
        '''
        Upload a single file by using Multipart upload protocol.
        We use AWS SDK (boto3) underneath for this step.
        '''
        # Upload target which is returned by sessionUpload API consists of:
        # https://{service endpoint}/{bucket}/{prefix}
        # where {bucket} and {prefix} are single element (without delimiter) individually.
        elements = upload_target.split('/')
        service_endpoint = '/'.join(elements[0:-2:])
        bucket = elements[-2]
        prefix = elements[-1]
        object_key = '{0}/{1}'.format(prefix, os.path.basename(file_path))

        print('')
        print('Upload {0} with multipart upload protocol'.format(file_path))
        print('  endpoint URL: {0}'.format(service_endpoint))
        print('  bucket name : {0}'.format(bucket))
        print('  object key  : {0}'.format(object_key))

        # Create S3 client with custom endpoint on Panopto server.
        # Panopto server does not refer access key or secret, but the library needs
        # some values to start, otherwise no credentials error is thrown.
        s3 = boto3.session.Session().client(
            service_name='s3',
            endpoint_url=service_endpoint,
            verify=self.ssl_verify,
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy')

        # Initiate multipart upload.
        mpu = s3.create_multipart_upload(Bucket=bucket, Key=object_key)
        mpu_id = mpu['UploadId']

        # Iterate through parts
        parts = []
        uploaded_bytes = 0
        total_bytes = os.stat(file_path).st_size
        with open(file_path, 'rb') as f:
            i = 1
            while True:
                data = f.read(PART_SIZE)
                if not len(data):
                    break
                part = s3.upload_part(
                    Body=data, Bucket=bucket, Key=object_key, UploadId=mpu_id, PartNumber=i)
                parts.append({'PartNumber': i, "ETag": part['ETag']})
                uploaded_bytes += len(data)
                print(
                    '  -- {0} of {1} bytes uploaded'.format(uploaded_bytes, total_bytes))
                i += 1

        # Copmlete
        result = s3.complete_multipart_upload(
            Bucket=bucket, Key=object_key, UploadId=mpu_id, MultipartUpload={"Parts": parts})
        print('  -- complete called.')

    def __create_manifest_for_video(self, file_path, manifest_file_name):
        '''
        Create manifest XML file for a single video file, based on template.
        '''
        print('')
        print('Writing manifest file: {0}'.format(manifest_file_name))

        file_name = os.path.basename(file_path)

        with open(MANIFEST_FILE_TEMPLATE) as fr:
            template = fr.read()
        content = template\
            .replace('{Title}', file_name[:-4])\
            .replace('{Description}', 'This video was processed by the Sauder Automated Video Branding Tool')\
            .replace('{Filename}', file_name)\
            .replace('{Date}', datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f-00:00'))
        with codecs.open(manifest_file_name, 'w', 'utf-8') as fw:
            fw.write(content)

    def __finish_upload(self, session_upload):
        '''
        Finish upload.
        '''
        upload_id = session_upload['ID']
        upload_target = session_upload['UploadTarget']

        print('')
        while True:
            print(
                'Calling PUT PublicAPI/REST/sessionUpload/{0} endpoint'.format(upload_id))
            url = 'https://{0}/Panopto/PublicAPI/REST/sessionUpload/{1}'.format(
                self.server, upload_id)
            payload = copy.copy(session_upload)
            payload['State'] = 1  # Upload Completed
            headers = {'content-type': 'application/json'}
            resp = self.requests_session.put(
                url=url, json=payload, headers=headers)
            if not self.__inspect_response_is_retry_needed(resp):
                break
        print('  done')

    def __monitor_progress(self, upload_id):
        '''
        Polling status API until process completes.
        '''
        print('')
        while True:
            time.sleep(5)
            print(
                'Calling GET PublicAPI/REST/sessionUpload/{0} endpoint'.format(upload_id))
            url = 'https://{0}/Panopto/PublicAPI/REST/sessionUpload/{1}'.format(
                self.server, upload_id)
            resp = self.requests_session.get(url=url)
            if self.__inspect_response_is_retry_needed(resp):
                # If we get Unauthorized and token is refreshed, ignore the response at this time and wait for next time.
                continue
            session_upload = resp.json()
            print('  State: {0}'.format(session_upload['State']))

            # original value below was 4
            # I'm changing this to 3 because I don't want to wait for videos to completely process
            if session_upload['State'] == 3:
                break
