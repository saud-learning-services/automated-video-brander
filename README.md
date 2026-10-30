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

## Setup

Requires a Mac (watermarking uses the Mac's `h264_videotoolbox` hardware encoder) with Python 3.15 from [Miniforge](https://github.com/conda-forge/miniforge). Miniforge also installs ffmpeg into the environment.

### 1. Install Miniforge

Use the installer that matches the Mac. Check with `uname -m`: `arm64` means Apple Silicon (M1 or later).

> An Intel ("x86_64") Miniconda or Anaconda on an Apple Silicon Mac can't install the current packages. Install Miniforge alongside it; the old install keeps working.

Apple Silicon:

```
curl -L -o ~/Miniforge3.sh https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh
bash ~/Miniforge3.sh -b -p ~/miniforge3
```

(Intel Macs: use `Miniforge3-MacOSX-x86_64.sh` instead.)

`-b` installs without changing your shell setup, so the commands below use the full path `~/miniforge3/...`.

### 2. Create the environment

From the project folder:

```
~/miniforge3/bin/conda env create -f environment.yml
```

This creates the `automated-editor-py315` environment. To update it after `environment.yml` changes:

```
~/miniforge3/bin/conda env update -f environment.yml --prune
```

### 3. Configure

Copy `env.example.txt` to `.env` in the project folder and fill it in:

```
SERVER = ubc.ca.panopto.com            # your Panopto server
CLIENT_ID =                            # Panopto API client (System > API Clients)
CLIENT_SECRET =
GOOGLE_APPLICATION_CREDENTIALS = ./google_client/secrets.json
USER_REQUESTS_SPREADSHEET_TITLE = 'Post Production Branding Request form (Responses)'
NTFY_URL = https://ntfy.sh/your-private-topic   # push notifications; leave empty to only log
ARCHIVE_RETENTION_DAYS = 14            # days to keep zipped copies of processed videos
PROCESSING_TIMEOUT_MINUTES = 30        # see "Panopto processing" below
```

Also needed:

- `google_client/secrets.json`: the Google service account key for the request form's spreadsheet
- `google_client/LastRun.txt`: one line like `LastRun=10/30/2026 13:00:00` (MM/DD/YYYY HH:MM:SS). Form responses after this time are processed on the next run. The brander updates it each run.
- Assets in `input/top_slates`, `input/tail` and `input/watermark` (see Additional Inputs)
- The Whitney fonts (`WhitneyHTF`, `WhitneyHTF-SemiBoldCondensed`) installed on the Mac, for title cards; otherwise a default font is used

### 4. First Panopto login

Check the Panopto login (the first time, a browser opens to approve access):

```
source ~/miniforge3/bin/activate automated-editor-py315
python -c "from dotenv import load_dotenv; load_dotenv(); import automated_brander as a; a.__check_panopto_login()"
```

It should print `Panopto login OK`.

## Running

### Scheduled (normal use)

Double-click `start_brander.command` in Finder. A Terminal window opens, activates the `automated-editor-py315` environment and runs the brander every day at **09:10** and **16:00**. Leave the window open. To stop it, press Ctrl-C or close the window.

The first time, macOS may say the file can't be opened: right-click it, choose **Open**, then **Open** again.

Or from a terminal, in the project folder:

```
source ~/miniforge3/bin/activate automated-editor-py315
python launcher.py
```

To change the times, edit the `schedule.every().day.at(...)` lines in `launcher.py` and restart it.

If a run is still going at the next scheduled time, that run starts as soon as the current one finishes. An error in one run is reported and doesn't stop the scheduler.

### Run once now

```
source ~/miniforge3/bin/activate automated-editor-py315
python automated_brander.py
```

Only one brander runs at a time: a run started while another is in progress (e.g. from a second Terminal window) is skipped.

### What to expect

Each run sends ntfy notifications and writes `logs/<date time>.log`. It ends with a summary such as:

- `Branding COMPLETED: 2 of 2 videos uploaded` (green)
- `Branding FINISHED WITH ERRORS: 1 of 2 videos uploaded. See logs/...` (red), plus an error notification saying what went wrong

Before processing anything, a run checks that ffmpeg is available, that the Panopto login works and that `LastRun.txt` is valid. If any of these fail, nothing is processed and the form requests are picked up again on the next run.

### Panopto processing

After uploading, a run waits up to `PROCESSING_TIMEOUT_MINUTES` (default 30) for Panopto to process the videos. A file Panopto can't process fails within that time and is reported as an error.

Long videos (1.5 hours or more) usually take longer to process. They're reported as "still processing", saved in `pending_uploads.json`, and checked at the start of each later run. You get a notification when each is ready, or an error if processing fails or it still isn't ready after 24 hours. Panopto keeps processing regardless of what the brander does.

### Running with launchd (optional)

Instead of a Terminal window, launchd can run the brander in the background, start it at login and restart it if it stops.

1. Edit `launchd/ca.ubc.sauder.video-brander.plist` and replace the `/PATH/TO/...` values. With the setup above, the environment's python is `~/miniforge3/envs/automated-editor-py315/bin/python` (write the full path, launchd doesn't expand `~`).
2. `cp launchd/ca.ubc.sauder.video-brander.plist ~/Library/LaunchAgents/`
3. `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ca.ubc.sauder.video-brander.plist`

Output goes to `logs/launchd.out.log`. To stop it: `launchctl bootout gui/$(id -u)/ca.ubc.sauder.video-brander`.
Don't run `start_brander.command` at the same time.

## Upgrading from the Python 3.8 version

The old environment (`automated-editor`, in the old Miniconda/Anaconda) isn't changed, so you can switch back.

1. Get this version: `git fetch origin` and `git switch legacy-login-and-py315` (or `git pull` once it's merged into `main`)
2. Follow Setup steps 1, 2 and 4. Add `NTFY_URL` to `.env`; `ASPXAUTH` is no longer needed.
3. Stop the old brander (Ctrl-C in its Terminal window)
4. Start the new one with `start_brander.command`
5. Once you're happy, remove the old install (for example `rm -rf /opt/miniconda3`), then run `~/miniforge3/bin/conda init zsh` so plain `conda` uses Miniforge

To roll back: stop the brander, check out the previous version (`git switch main`), activate the old environment and run `python launcher.py`.
`environment-legacy-py38.yml` recreates the old environment if it has been removed.

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
- Long videos still processing in Panopto at the end of a run are tracked in `pending_uploads.json` (see Panopto processing)
- Source clip (specified in Source URL in specs.) should be a single video clip with _approx. 3_ seconds before/after the speaker speaks
- Watermark position defaults to bottom-right. Bottom left only if Watermark Position is **l** (in CSV)
- Only supports single line titles (titles can not exceed 45 characters)
- If no slate is specified, the tool will default to Sauder's standard intro slate `sauder_slate.mp4`
- Videos are identified using the string `"{Title}_{Instructor}"`. Videos with the same title and instructor combo may overwrite one another
