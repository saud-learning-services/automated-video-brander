import os
import logging
import copy
import time
import boto3  # AWS SDK (boto3)
from botocore.config import Config
from botocore.exceptions import ClientError
import requests

from termcolor import cprint

# Size of each part of multipart upload.
# This must be between 5MB and 25MB. Panopto server may fail if the size is more than 25MB.
PART_SIZE = 5 * 1024 * 1024

# How many times a request is retried after refreshing the access token (401/403)
MAX_AUTH_RETRIES = 2

# How many times finishing an upload is retried after a network error
MAX_FINISH_RETRIES = 3

# Give up waiting for Panopto to accept an upload after this many seconds
MONITOR_TIMEOUT_SECONDS = 2 * 60 * 60

# sessionUpload "State" values (Panopto PublicAPI/REST/sessionUpload)
UPLOAD_COMPLETED = 1
UPLOAD_CANCELLED = 2
PROCESSING = 3
COMPLETE = 4
PROCESSING_ERROR = 5


class Panopto:
    """
    Main interface for doing anything Panopto related

    MODIFIED VERSION OF: https://github.com/Panopto/upload-python-sample/tree/master/simplest
    Contributors (GitHub): Hiroshi Ohno, Zac Rumford
    Apache-2.0 License

    *modified to suit our specific use-case*
    """

    def __init__(self, server, ssl_verify, oauth2):
        """
        Constructor of uploader instance.
        This goes through authorization step of the target server.
        """
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
        """
        This method invokes OAuth2 Authorization Code Grant authorization flow.
        It goes through browser UI for the first time.
        It refreshes the access token after that and no user interfaction is requested.
        This is called at the initialization of the class, as well as when 401/403 is returned.
        """
        access_token = self.oauth2.get_access_token()
        self.requests_session.headers.update(
            {"Authorization": "Bearer " + access_token}
        )
        self.current_token = access_token

    def __request(self, method, url, **kwargs):
        """
        Make a request with the OAuth2 session.
        On 401 (Unauthorized) or 403 (Forbidden) the access token is refreshed and the
        request retried, up to MAX_AUTH_RETRIES times. Any other failure raises.
        """
        for attempt in range(MAX_AUTH_RETRIES + 1):
            resp = self.requests_session.request(method, url, **kwargs)
            if resp.status_code not in (401, 403) or attempt == MAX_AUTH_RETRIES:
                break
            print(f"{resp.status_code} from Panopto. Access token may have expired. Refreshing...")
            logging.warning(
                "%s from %s. Refreshing access token and retrying.", resp.status_code, url
            )
            self.__setup_or_refresh_access_token()

        resp.raise_for_status()
        return resp

    def get_aspxauth_cookie(self):
        """
        Exchange the OAuth2 access token for a .ASPXAUTH cookie using the
        /api/v1/auth/legacyLogin endpoint. The cookie is needed for pages that
        do not accept a bearer token (DeliveryInfo.aspx and podcast downloads).

        Falls back to an ASPXAUTH value in .env if legacyLogin does not return a cookie.
        """
        url = f"https://{self.server}/Panopto/api/v1/auth/legacyLogin"

        for attempt in range(MAX_AUTH_RETRIES + 1):
            resp = self.requests_session.get(url)
            for cookie in resp.cookies:
                if cookie.name.upper() == ".ASPXAUTH" and cookie.value:
                    return cookie.value

            # An empty response usually means the access token has expired
            logging.warning(
                "legacyLogin returned %s without a .ASPXAUTH cookie (attempt %i)",
                resp.status_code,
                attempt + 1,
            )
            self.__setup_or_refresh_access_token()

        fallback = os.getenv("ASPXAUTH")
        if fallback:
            logging.warning("legacyLogin failed. Using ASPXAUTH from .env instead.")
            cprint("legacyLogin failed. Using ASPXAUTH from .env instead.", "yellow")
            return fallback

        raise RuntimeError(
            f"Could not get a .ASPXAUTH cookie from legacyLogin (last status {resp.status_code})"
        )

    def download_video(self, session_id, output_folder):
        """
        Download's video file from Panopto session (session_id) to output folder
        """
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 12.4; rv:101.0) Gecko/20100101 Firefox/101.0",
            "Cookie": ".ASPXAUTH=" + self.get_aspxauth_cookie(),
        }

        url = f"https://{self.server}/Panopto/Pages/Viewer/DeliveryInfo.aspx"
        params = {"deliveryId": session_id, "responseType": "json"}
        resp = requests.get(url=url, params=params, headers=headers)

        if resp.status_code != 200:
            raise RuntimeError(
                f"DeliveryInfo response came with status code {resp.status_code} for session {session_id}"
            )
        delivery_info = resp.json()
        if "ErrorMessage" in delivery_info.keys():
            message = delivery_info["ErrorMessage"]
            raise RuntimeError(
                f"DeliveryInfo response came with message: {message} (session {session_id})"
            )

        # CHANGED BEHAVIOUR JAN 2022
        # Whereas we used to download each stream individually, API changes have
        # made this difficult. We now download each sessions "podcast" file.
        download_url = f"https://{self.server}/Panopto/Podcast/Download/{session_id}.mp4?mediaTargetType=videoPodcast"
        print(f"DOWNLOAD_URL: {download_url}")
        print("Downloading single stream...")
        dest_filename = os.path.join(output_folder, "primary.mp4")

        try:
            with requests.get(url=download_url, headers=headers, allow_redirects=True, stream=True) as r:
                r.raise_for_status()
                with open(dest_filename, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        f.write(chunk)
        except Exception as err:
            if os.path.exists(dest_filename):
                os.remove(dest_filename)
            raise RuntimeError(
                f"Could not download podcast file for session {session_id}. "
                f"Ensure that podcast is enabled for video under Overview > Downloads. ({err})"
            ) from err

    def __get_session(self, session_id):
        """
        Call GET /api/v1/sessions/{id} API and return the response
        """
        url = "https://{0}/Panopto/api/v1/sessions/{1}".format(self.server, session_id)
        return self.__request("GET", url).json()

    def get_containing_folder(self, delivery_id):
        """
        Given a sessions delivery_id, make the necessary calls to get its folder id
        """

        session = self.__get_session(delivery_id)
        details = session["FolderDetails"]

        folder_id = details["Id"]
        folder_name = details["Name"]

        return (folder_name, folder_id)

    def upload_folder(self, local_folder, folder_id):
        """
        Main upload method to go through all required steps.
        """
        # step 1 - Create a session
        session_upload = self.__create_session(folder_id)
        upload_id = session_upload["ID"]
        upload_target = session_upload["UploadTarget"]

        print("UPLOAD TARGET: " + upload_target)

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
        """
        Return the list of files in the specified folder. Not to traverse sub folders.
        """
        print("")
        files = []
        for entry in os.listdir(folder):
            path = os.path.join(folder, entry)
            if os.path.isdir(path):
                continue
            files.append(path)
            print("  {0}".format(path))

        return files

    def __create_session(self, folder_id):
        """
        Create an upload session. Return sessionUpload object.
        """
        print("")
        print("Calling POST PublicAPI/REST/sessionUpload endpoint")
        url = "https://{0}/Panopto/PublicAPI/REST/sessionUpload".format(self.server)
        payload = {"FolderId": folder_id}
        session_upload = self.__request("POST", url, json=payload).json()
        print("  ID: {0}".format(session_upload["ID"]))
        print("  target: {0}".format(session_upload["UploadTarget"]))
        return session_upload

    def __multipart_upload_single_file(self, upload_target, file_path):
        """
        Upload a single file by using Multipart upload protocol.
        We use AWS SDK (boto3) underneath for this step.
        """
        # Upload target which is returned by sessionUpload API consists of:
        # https://{service endpoint}/{bucket}/{prefix}
        # where {bucket} and {prefix} are single element (without delimiter) individually.
        elements = upload_target.split("/")
        service_endpoint = "/".join(elements[0:-2:])
        bucket = elements[-2]
        prefix = elements[-1]
        object_key = "{0}/{1}".format(prefix, os.path.basename(file_path))

        print("")
        print("Upload {0} with multipart upload protocol".format(file_path))
        print("  endpoint URL: {0}".format(service_endpoint))
        print("  bucket name : {0}".format(bucket))
        print("  object key  : {0}".format(object_key))

        # Create S3 client with custom endpoint on Panopto server.
        # Panopto server does not refer access key or secret, but the library needs
        # some values to start, otherwise no credentials error is thrown.
        # boto3 >= 1.36 adds checksums by default and sends uploads "aws-chunked";
        # Panopto's endpoint doesn't support that and ends up with unusable files
        # ("No streams"). "when_required" restores the plain uploads of older boto3.
        s3 = boto3.session.Session().client(
            service_name="s3",
            endpoint_url=service_endpoint,
            verify=self.ssl_verify,
            aws_access_key_id="dummy",
            aws_secret_access_key="dummy",
            config=Config(
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

        # Initiate multipart upload.
        mpu = s3.create_multipart_upload(Bucket=bucket, Key=object_key)
        mpu_id = mpu["UploadId"]

        # Iterate through parts
        parts = []
        uploaded_bytes = 0
        total_bytes = os.stat(file_path).st_size
        with open(file_path, "rb") as f:
            i = 1
            while True:
                data = f.read(PART_SIZE)
                if not len(data):
                    break
                part = s3.upload_part(
                    Body=data,
                    Bucket=bucket,
                    Key=object_key,
                    UploadId=mpu_id,
                    PartNumber=i,
                )
                parts.append({"PartNumber": i, "ETag": part["ETag"]})
                uploaded_bytes += len(data)
                print(
                    "  -- {0} of {1} bytes uploaded".format(uploaded_bytes, total_bytes)
                )
                i += 1

        # Complete (one retry)
        for attempt in range(2):
            try:
                s3.complete_multipart_upload(
                    Bucket=bucket,
                    Key=object_key,
                    UploadId=mpu_id,
                    MultipartUpload={"Parts": parts},
                )
                break
            except ClientError as err:
                cprint(err, "red")
                if attempt == 1:
                    cprint("FAILED -- Tried multipart upload twice", "red")
                    raise RuntimeError(f"Could not upload to {upload_target}") from err
                cprint("Retrying operation...", "yellow")

        print("  -- complete called.")

    def __finish_upload(self, session_upload):
        """
        Finish upload.
        """
        upload_id = session_upload["ID"]

        print("Calling PUT PublicAPI/REST/sessionUpload/{0} endpoint".format(upload_id))
        url = "https://{0}/Panopto/PublicAPI/REST/sessionUpload/{1}".format(
            self.server, upload_id
        )
        payload = copy.copy(session_upload)
        payload["State"] = UPLOAD_COMPLETED

        for attempt in range(MAX_FINISH_RETRIES):
            try:
                self.__request("PUT", url, json=payload)
                break
            except requests.exceptions.RequestException as err:
                # This gets triggered if the video takes a long time to upload
                # Regenerating the token resolves it
                cprint(err, "red")
                logging.warning("Finishing upload failed (%s). Regenerating token", err)
                if attempt == MAX_FINISH_RETRIES - 1:
                    raise
                self.__setup_or_refresh_access_token()
        print("  done")

    def __monitor_progress(self, upload_id):
        """
        Polling status API until Panopto has accepted the upload.
        We stop at PROCESSING rather than waiting for processing to complete.
        """
        print("")
        url = "https://{0}/Panopto/PublicAPI/REST/sessionUpload/{1}".format(
            self.server, upload_id
        )
        deadline = time.time() + MONITOR_TIMEOUT_SECONDS
        while time.time() < deadline:
            time.sleep(5)
            print("Calling GET PublicAPI/REST/sessionUpload/{0} endpoint".format(upload_id))
            state = self.__request("GET", url).json()["State"]
            print("  State: {0}".format(state))

            if state in (PROCESSING, COMPLETE):
                logging.info("Successfully uploaded video!")
                return
            if state in (UPLOAD_CANCELLED, PROCESSING_ERROR) or state > COMPLETE:
                raise RuntimeError(f"Panopto upload {upload_id} failed with state {state}")

        raise RuntimeError(
            f"Timed out waiting for Panopto to accept upload {upload_id}"
        )
