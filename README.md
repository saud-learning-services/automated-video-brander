# Sauder Automated Video Editor
Python script that automates post-processiing for educational video content at Sauder

_In development_

## TODO
* Summary
* Setup
    * with venv and pip
    * wich conda
* How to use, project structure, etc

## Important Information 
* Only supports **1920x1080**
* `/output` directory will be cleared at the start of each run (this behaviour will likely change)
* Body should be a single video clip with _approx. 3_ seconds before/after the spaeker speaks
* Watermark position defaults to bottom-right -> bottom left only if Watermark Position is **l** (in CSV)
* Only supports single line titles (titles can not exceed 45 characters)
* If no "body" (actual instructional content) is specified, but top and tail are, they will get stitched together with a fade to white in between
* If no slate is specified, the tool will default to Sauder's standard intro slate `sauder_slate.mp4`
* If no course code is provided your video will render to a folder titled "Other" ***
* Videos with the same title will overwrite eachother in the output folder (ensure unique titles for each video)
* If the same body clip is used more than once the script will prompt user to overwrite when watermarking (Don't include the same body twice)

## TODO LIST
- [x] change outputs to something like: {title}_branded.mp4
- [x] add column to table for source url (make it pass all the tests)
- [] create another script called `upload_videos.py`
    - [] interface with the panopto modules to upload all the videos in your output folder to Panopto
    - [x] add a check to see if url starts with 'https://ubc.ca.panopto.com'

* add logging
* you should not have to not include / in your input, we should sanitize the input on our end