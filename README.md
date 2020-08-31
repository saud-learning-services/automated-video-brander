# Sauder Automated Video Branding Tool
Python application that automates branding post-processing for educational video content at UBC Sauder.

## Problem to solve

The change to online delivery of classes due to COVID-19 has led to the desire to brand videos used for course content delivery. Video content and branding processes, including an intro, outro, and watermarking of the video content is required. This process, if edited manually for the anticipated hundreds of hours of content, would take a tremendous amount of effort to produce. An automated process is required to ensure the content can be produced in a timely manner. We have identified a process in conjunction with our selected video platform, Panopto, to automate the download, process, and return of branded content.

This process makes use of the Panopto SOAP and RESTful API's to download, brand, and upload the branded content. 

## Solution Process

Run at consistant intervals to support video-automation process where: 
1. Faculty members at Sauder create and upload single-stream or dual-stream video content to Panopto
2. Faculty members submit a Google Form specifying what kind of branding treatment they'd like to recieve
3. Within 24 hours, a personalized and branded version of the video is auto-generated and available in the same folder in Panopto.

## Status

This project is *still under development*. While the application works, it is far from completed -- there are already performance improvments, architectural changes and refactorings that we are planning. It is being shared publicly due to interest from colleagues and institutions with similar video-content challenges.

## Environment

After cloning the repo, create a `.env` in the root folder with the following properties:

```
SERVER =           # example: ubc.ca.panopto.com
CLIENT_ID =        # generated via Panopto User Settings
CLIENT_SECRET =    # generated via Panopto User Settings
ASPXAUTH =         # can be found in cookies of authenticated Panopto session
```

Install and run environment (via Anaconda)
1. `$ conda env create -f environment.yml`
1. `$ conda activate automated_video_branding_tool_env`
1. Run desired script (ex. `$ python main.py`)

## Input

The behaviour of the tool is specified in `specs.csv` in the `/input` folder. Each row in this CSV defines the properties of a single video. The following columns are included in a valid input CSV:

> Columns that requre values for each video have a *

* **Course** _(COMM 100)_
* **Section** _(101)_
* **Instructor** _(Dr. Lee)_
* ***Title** _(Introduction to Balance Sheets)_
* ***Top Slate** _(my-slate.mp4)_
* **Watermar**k _(sauder-watermark.png)_
* **Watermark Position** _(R)_
* ***Source URL** _(https://www.link-to-my-raw-unbranded-video.panopto.com)_ This uses the "Share Link" URL from Panopto 

For our process at Sauder, we have faculty members fill out a Google form with all relevant information. This is then manually entered into specs.csv (for now)

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

1. **Downloading:** The tool pulls raw video content (.mp4 files) from Panopto, specified through a Source URL (in specs.csv). It supports single-stream and dual-stream video content, which allows us to accomodate for screencapture and other multi-source presentation styles.
2. **Watermarking:** The tool adds watermark to the user's specification (in specs.csv)
3. **Stitching:** The tool creates a custom top to the user's specification including `[Title*, Instructor name, Course code, Section number]`. Stitches top, content and tail together with fades between.
4. **Uploading:** The tool uploads the video content (single or multi-stream) back to the same folder on Panopto as the source content

Each of these steps can be run individually by calling its respective python module:

```
$ python download_videos.py
$ python watermark.py
$ python stitch.py
$ python upload_videos.py
```

Or to run all four at once, call: 
```
$ python main.py
```

All logic for interfacing with panopto is in `panpto/panopto_interface.py`, except for authentication which is handled by `panopto/panopto_auth2.py`

## Future Development
* Refactor 4 main scripts to repeat as little shared logic as possible (ex. We load and check the CSV in each step, this could be done once)
* **Slim down dependencies.** Currently our project uses three video libraries: [ffmpeg-python](https://github.com/kkroening/ffmpeg-python), [moviepy](https://zulko.github.io/moviepy/) and [gizeh](https://github.com/Zulko/gizeh). This was done because initially we didn't know all the functionality we needed, so we used different libraries where necessary. All video processing should be doable with ffmpeg-python therefore we want to make this our only video-editing library.
* Assuming we do all video transformations using ffmpeg-python, make watermarking and stitching a single step (only multiple because they use different libraries at the moment)
* Add log file to keep track of success/failure of each video and record error messages
* Add connection to web form (currently Google Forms) used to collect requests for branding to automate from request to processing. Error checking, logging, and notification is required to implement.

## Important Information 

* All videos will be rendered to **1920x1080**
* `/output` directory contents will be cleared on step 3 and its contents will be zipped in `/ouput/archive` (timestamped)
* `/input/body` directory contents will be cleared on step 1 and its contents will be zipped in `/input/body/archive` (timestamped)
* Source clip (specified in Source URL in specs.) should be a single video clip with _approx. 3_ seconds before/after the speaker speaks
* Watermark position defaults to bottom-right. Bottom left only if Watermark Position is **l** (in CSV)
* Only supports single line titles (titles can not exceed 45 characters)
* If no slate is specified, the tool will default to Sauder's standard intro slate `sauder_slate.mp4`
* Videos are identified using the string `"{Title}_{Instructor}"`. Videos with the same title and instructor combo may overwrite one another
