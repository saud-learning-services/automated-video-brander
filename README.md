# Top and Tail Stitcher

🚨 PRIVATE REPO DO NOT SHARE 🚨
This repo will be publicly published when we have a stable **Version 1**

## 📋 TODO
- [x] get the Elicia video for COMM 101
- [x] Do fades to white programmatically on top assets (tail is constant)
- [x] Bring specifications table up to new standard
- [x] Get all video assets needed for new testing
- [x] Body needs a fade from white ALWAYS
- [x] Fix Watermark - edges 
- [x] Add ability to specify Watermark location
- [x] get it on GitHub and add everyone:
- [ ] Make titles dynamic
    - [x] Create blank slide on Premiere Pro (make sure Audio fades out completely)
    - [x] Add text overlay
    - [x] Get color right
    - [x] Get font right
    - [x] Animate title (using gizeh?)
    - [ ] Fix slate (audio needs to fade more gradually)
    - [x] Implement new titles feature into rest of script

## Next Steps
- [ ] Integrate with Panopto to upload to sessions according to Altan and Jonathan's specifications
- [ ] Error Handling
    - [ ] Logs at the end of each run
- [ ] See if we can use GPU for rendering
- [ ] "Processed" or "Completed" folder for **body** files

## ⚠️ Important Use Case Information 
* Editors will need to ensure that tops are created ~6s (working on automating this part as well)
* Only works with **1920x1080 (MP4)**
* `/output` directory will be cleared at the start of each run
* Body should be a single video clip with ~3 seconds before/after the spaeker speaks
* Watermark position defaults to bottom-right -- bottom left only if WatermarkPosition is **L** or **l** (in CSV)
* Only supports single line titles (titles can not exceed 45 characters)

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
