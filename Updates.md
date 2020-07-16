# Top and Tail Stitcher Script

## New Features Since Last Time

* Added ability to add body video (optional) - if one isn't specified in the CSV it'll just stitch the top&tail like before
* Added ability to add a watermark
* Added ability to specify left or right corner for watermark

## In Progress/Next Steps

* Dynamic titles (**Thursday, July 16th**):
    * titles that get rendered in by the script
    * would remove editors from the process entirely (the script does everything)
    * I will need to add a word or character limit for titles to make sure they can render on 1 or 2 lines

* Panopto integration (**Monday, July 20th**):
    * Will be its own script: `$ python stitch.py` will create all the videos in output and `$ python panopto-upload.py` will get evertything on panopto (according to your specifications)
    * Two different scripts give the user a chance to review the videos before they get uploaded
    * It also means we can use *just* the video tool or *just* the panopto tool if we need to

* Testing and error handling (**Wednesday, July 22nd**):
    * Need to refactor, add more error handling, and do a bunch of stability testing