# Sauder Automated Video Branding Tool

Python application that automates branding post-processing for educational video content at UBC Sauder.

## Problem to solve

The change to online delivery of classes due to COVID-19 has led to the desire to brand videos used for course content delivery. Video content and branding processes, including an intro, outro, and watermarking of the video content is required. This process, if edited manually for the anticipated hundreds of hours of content, would take a tremendous amount of effort to produce. An automated process is required to ensure the content can be produced in a timely manner. We have identified a process in conjunction with our selected video platform, Panopto, to automate the download, process, and return of branded content.

This process makes use of the Panopto SOAP and RESTful API's to download, brand, and upload the branded content.

## Solution Process

Run at consistent intervals to support video-automation process where:

1. Faculty members at Sauder create and upload single-stream or dual-stream video content to Panopto
2. Faculty members submit a Google Form specifying what kind of branding treatment they'd like to recieve
3. Within 24 hours, a personalized and branded version of the video is auto-generated and available in the same folder in Panopto.

## Environment

Requires macOS (watermarking uses the `h264_videotoolbox` hardware encoder) and [Miniforge/conda](https://github.com/conda-forge/miniforge).

After cloning the repo, copy `env.example.txt` to `.env` in the root folder and fill it in:

```
SERVER = ubc.ca.panopto.com            # your Panopto server
CLIENT_ID =                            # Panopto API client (System > API Clients)
CLIENT_SECRET =
GOOGLE_APPLICATION_CREDENTIALS = ./google_client/secrets.json
USER_REQUESTS_SPREADSHEET_TITLE = 'Post Production Branding Request form (Responses)'
NTFY_URL = https://ntfy.sh/your-private-topic   # push notifications; leave empty to only log
ARCHIVE_RETENTION_DAYS = 14            # days to keep zipped copies of processed videos
```

Optional settings are described in `env.example.txt`.

### Create the environment (Python 3.15)

```
conda env create -f environment.yml
conda activate automated-editor-py315
```

### Upgrading an existing install

The previous Python 3.8 environment (`automated-editor`) is left untouched, so you can switch back if needed.

1. `git pull` to get this version
2. `conda env create -f environment.yml` (creates `automated-editor-py315` alongside the old one)
3. Stop the running brander (Ctrl-C in its Terminal window)
4. Start it again with `start_brander.command`, which uses the new environment
5. Once you're happy, remove the old environment with `conda env remove -n automated-editor`

To roll back: stop the brander, `conda activate automated-editor`, check out the previous version, then run `python launcher.py`.
`environment-legacy-py38.yml` recreates the old environment if it has been removed.

To update packages later: `conda env update -f environment.yml --prune`

### Fonts

Title cards use the Whitney fonts (`WhitneyHTF`, `WhitneyHTF-SemiBoldCondensed`). They must be installed on the Mac, otherwise a default font is used.

## Running

### Scheduled (normal use)

Double-click `start_brander.command` in Finder. A Terminal window opens and runs the brander at 09:10 and 16:00 every day. Leave the window open. To stop it, press Ctrl-C or close the window.

The first time, macOS may say the file can't be opened: right-click it, choose **Open**, then **Open** again.

Or from a terminal:

```
conda activate automated-editor-py315
python launcher.py
```

### Run once now

```
conda activate automated-editor-py315
python automated_brander.py
```

Only one brander runs at a time. A second run started while one is in progress is skipped.

### Running with launchd (optional)

Instead of a Terminal window, launchd can run the brander in the background, start it at login and restart it if it stops.

1. Edit `launchd/ca.ubc.sauder.video-brander.plist` and replace the `/PATH/TO/...` values
2. `cp launchd/ca.ubc.sauder.video-brander.plist ~/Library/LaunchAgents/`
3. `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ca.ubc.sauder.video-brander.plist`

Output goes to `logs/launchd.out.log`. To stop it: `launchctl bootout gui/$(id -u)/ca.ubc.sauder.video-brander`.
Don't run `start_brander.command` at the same time.

## Panopto authentication

- **API calls and uploads** use OAuth2. The first run opens a browser to approve access. After that, a cached refresh token (`token_*.cache`, never commit it) renews access without a browser.
- **Downloads** need a `.ASPXAUTH` cookie. The brander gets one automatically from Panopto's `/api/v1/auth/legacyLogin` endpoint using the OAuth2 token. You no longer need to copy a cookie from a browser.
- If the refresh token stops working, the brander tries a password login with `PANOPTO_USERNAME`/`PANOPTO_PASSWORD`. That only works if the API client type is **User Based Server Application**. Otherwise it sends a notification and opens a browser login, which someone at the Mac must approve within 15 minutes.
- Each run checks the Panopto login first. If it fails, nothing is processed and the form requests are picked up again on the next run.

## Input

The behaviour of the tool is specified in `specs.csv` in the `/input` folder. Each row in this CSV defines the properties of a single video. The following columns are included in a valid input CSV:

> Columns that requre values for each video have a \*

- **Course** _(COMM 100)_
- **Section** _(101)_
- **Instructor** _(Dr. Lee)_
- **\*Title** _(Introduction to Balance Sheets)_
- **\*Top Slate** _(my-slate.mp4)_
- **Watermar**k _(sauder-watermark.png)_
- **Watermark Position** _(R)_
- **\*Source URL** _(https://www.link-to-my-raw-unbranded-video.panopto.com)_ This uses the "Share Link" URL from Panopto

For our process at Sauder, faculty members fill out a Google form. Each run, `google_client/google_form_interface.py` writes the responses submitted since the last run (`google_client/LastRun.txt`) to specs.csv.

### Additional Inputs

#### Watermarks (1920x1080 transparent PNGs)

Watermarking will require watermark assets created at 1920x1080 (16:9) .png images with watermark positioned in desired location
Put these files in folders titled `/bottom-left` and `/bottom-right` in the `/watermark` folder

#### Top Slate (MP4)

A top slate should be branded 10s video file that will serve as the background for the title at the start. Put this in the `/top_slates` folder

#### Tail (MP4)

The tail for the end of the video goes in the `/tail` folder

> To test out using Sauder's assets contact Marko Prodanovic (marko.prodanovic@sauder.ubc.ca)

## Architecture and Control Flow

The tool is designed to integrate with Panopto and provide faculty with a simple automated-video-branding service through a 4 step process:

1. **Downloading:** The tool pulls raw video content (.mp4 files) from Panopto, specified through a Source URL (in specs.csv). It supports single-stream and multi-stream, both of which will be downloaded through podcast files.
2. **Watermarking:** The tool adds watermark to the user's specification (in specs.csv)
3. **Stitching:** The tool creates a custom top to the user's specification including `[Title*, Instructor name, Course code, Section number]`. Stitches top, content and tail together with fades between.
4. **Uploading:** The tool uploads the video content back to the same folder on Panopto as the source content

Each of these steps can be run individually by calling its respective python module:

```
$ python download_videos.py
$ python watermark.py
$ python stitch.py
$ python upload_videos.py
```

Or to run all four at once, call:

```
$ python automated_brander.py
```

All logic for interfacing with panopto is in `panopto/panopto_interface.py`, except for OAuth2 authentication which is handled by `panopto/panopto_oauth2.py`

## Future Development

- Refactor 4 main scripts to repeat as little shared logic as possible (ex. We load and check the CSV in each step, this could be done once)
- **Slim down dependencies.** Currently our project uses three video libraries: [ffmpeg-python](https://github.com/kkroening/ffmpeg-python), [moviepy](https://zulko.github.io/moviepy/) (v2) and [gizeh](https://github.com/Zulko/gizeh). This was done because initially we didn't know all the functionality we needed, so we used different libraries where necessary. All video processing should be doable with ffmpeg-python therefore we want to make this our only video-editing library.
- Assuming we do all video transformations using ffmpeg-python, make watermarking and stitching a single step (only multiple because they use different libraries at the moment)
- Record success/failure for each request (e.g. a status column in the response sheet), so failed requests can be retried automatically

## Important Information

- All videos will be rendered to **1920x1080**
- `/output` directory contents will be cleared on step 3 and its contents will be zipped in `/output/archive` (timestamped)
- `/input/body` directory contents will be cleared on step 1 and its contents will be zipped in `/input/body/archive` (timestamped)
- Archives older than `ARCHIVE_RETENTION_DAYS` (default 14) are deleted at the end of each run
- Source clip (specified in Source URL in specs.) should be a single video clip with _approx. 3_ seconds before/after the speaker speaks
- Watermark position defaults to bottom-right. Bottom left only if Watermark Position is **l** (in CSV)
- Only supports single line titles (titles can not exceed 45 characters)
- If no slate is specified, the tool will default to Sauder's standard intro slate `sauder_slate.mp4`
- Videos are identified using the string `"{Title}_{Instructor}"`. Videos with the same title and instructor combo may overwrite one another
