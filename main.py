'''
UBC Sauder School of Business
Automated Video Branding Tool

Author: Marko Prodanovic

Main entry point for the Automated Branding Tool
Runs all 4 steps (described below)
'''

from termcolor import cprint
from download_videos import download_videos
from watermark import watermark
from stitch import stitch
from upload_videos import upload_videos

if __name__ == '__main__':

    # 1
    # Downloads all streams of video specified in Source URL column (in specs.csv)
    download_videos()

    # 2
    # Watermarks clips (to specifications) and writes to PROCESSESSING folder
    # Will watermark both streams for multi-stream content
    watermark()

    # 3
    # Reads clips from PROCESSESING folder, creates tops (with titles) and stitches top & tail on clip
    # Tops & tails both streams (if multiple)
    # Writes to output folder
    stitch()

    # 4
    # Uploads all processed clips to Panopto to same folder as source session
    # Can handle single and multi-stream content (primary and secondary video)
    upload_videos()

    # Completion printouts
    cprint('\nCOMPLETED', 'green')
    cprint('\nMade by Marko Prodanovic\n', 'yellow')
