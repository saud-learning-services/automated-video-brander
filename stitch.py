from moviepy.editor import VideoFileClip, concatenate_videoclips
import moviepy.video.fx.all as vfx
from termcolor import cprint
import pandas as pd
import shutil
import os

root_path = os.path.dirname(os.path.abspath(__file__))

print('\n🚚 Loading Specifications from CSV...')
specs = pd.read_csv(root_path + '/input/specifications.csv')

# ===== DELETE OUTPUT CONTENTS =====
def clear_output_contents():
    """
    Clears output directory contents
    """

    for subdir in os.listdir(root_path + '/output'):
        if subdir != '.gitkeep' and subdir != '.DS_Store':
            path = f'{root_path}/output/{subdir}'
            shutil.rmtree(path, ignore_errors=False, onerror=None)

print('🗑  Clearing output folder...')
clear_output_contents()

# ================================

# ====== MAKE COURSE FOLDERS =====

# set ensures we don't make redundant course folders
unique_courses = set()
for index, row in specs.iterrows():
    unique_courses.add(row['Course'])

for course in unique_courses:
    path = f'output/{course}'
    try:  
        os.mkdir(path)  
    except OSError as error:  
        print(error)

# ================================

# ==== STITCH VIDEOS TOGETHER ====

for index, row in specs.iterrows():
    course = row['Course']
    title = row['Title']
    top = row['Top']
    \
    print('\n==========')
    print(f'🎥 {course} | {title}')

    top = VideoFileClip(f'input/tops/{top}')
    top_with_fade = top.fx(vfx.fadeout, duration=1.5, final_color=[255,255,255])

    tail = VideoFileClip('input/tail/tail.mp4')
    final_clip = concatenate_videoclips([top_with_fade, tail])

    print(f'📁 Writing to output folder {course}...')
    final_clip.write_videofile(f'output/{course}/{title}.mp4', temp_audiofile='temp-audio.m4a', remove_temp=True, codec='libx264', audio_codec='aac')

    cprint('\nSUCCESS', 'green')