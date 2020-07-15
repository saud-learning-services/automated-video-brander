# Top and Tail Stitcher

## ⚠️ Important Use Case Information 
* Editors will need to ensure that tops are created ~6s (no fades)
* Only works with **1920x1080 (MP4)**
* `/output` directory will be cleared at the start of each run
* Body should be a single video clip with ~3 seconds before/after the spaeker speaks
* Watermark position defaults to bottom-right -- bottom left only if WatermarkPosition is **L** or **l** (in CSV)

## 📋 TODO
- [x] get the Elicia Salzberg video for COMM 101
- [x] Do fades to white programmatically on top assets (tail is constant)
- [x] Bring specifications table up to new standard
- [x] Get all video assets needed for new testing
- [x] Body needs a fade from white ALWAYS
- [x] Fix Watermark - edges doing crazy shit
- [x] Add ability to specify Watermark location
- [] Make titles dynamic
    - [] Create blank slide on Premiere Pro (make sure Audio fades out completely)
    - [] Add text overlay and animation using moviepy
- [] get it on GitHub and add everyone:
    - [] shoekey4811
    - [] unabridgedxcrpt

## Next Steps
- [] Second script does the Panopto part of everything, first script just makes the video files
- [] Integrate with Panopto to upload to sessions according to Altan and Jonathan's specifications
- [] ERROR HANDLING

## CSV
Any of the following values will be treated as NULL on CSV:

* empty cell
* empty string: '' (FALSY)
* zero: 0 (FALSY)
* type = nan OR type = None
* 'null' OR 'NULL'
* 'none' OR 'NONE'

## Whoever is runing should have a basic understanding of:

* How to run a python script via the command line (for whatever OS you're using)
* How to setup and manage an environment using conda given a `environment.yml`
* How to keep their version up-to-date using GitHub (or GitHub Desktop)
    * Note you don't need to use GitHub but then you're responsible for keeping your version up to date manually

These are the same expectations when delivering a script to OPS. Marko will not be offering one-on-one support for anyting Anaconda/Conda related (Except for one session if there is interest)

