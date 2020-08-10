from moviepy.editor import VideoClip, VideoFileClip, CompositeVideoClip
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
import gizeh as gz


def _make_frame(t, course, section, instructor, title):

    course_sect = f'{course} {section}'

    surface = gz.Surface(1920, 1080)
    course_and_section = gz.text(course_sect, fontsize=40, fontfamily='WhitneyHTF',
                                 fill=(0, 0.13, 0.27), xy=(960, 410))
    title = gz.text(title, fontsize=90, fontfamily='WhitneyHTF-SemiBoldCondensed',
                    fill=(0, 0.13, 0.27), xy=(960, 490))
    instructor = gz.text(instructor, fontsize=65, fontfamily='WhitneyHTF-SemiBoldCondensed',
                         fill=(0.47, 0.75, 0.26), xy=(960, 600))

    for line in [course_and_section, title, instructor]:
        line = line.scale(1+0.02*t, center=[960, 540])
        line.draw(surface)
    return surface.get_npimage(transparent=True)


def create_top(course, section, instructor, title, slate):

    slate = VideoFileClip(f'input/top_slates/{slate}')

    text_clip_mask = VideoClip(lambda t: _make_frame(t, course, section, instructor, title)[
                               :, :, 3] / 255.0, duration=slate.duration, ismask=True)
    text_clip = VideoClip(lambda t: _make_frame(t, course, section, instructor, title)[
                          :, :, :3], duration=slate.duration).set_mask(text_clip_mask)
    # text_clip = VideoClip(make_frame, duration=slate.duration)

    text_clip = text_clip.fx(fadein, duration=1,
                             initial_color=[255, 255, 255])
    text_clip = text_clip.fx(fadeout, duration=1,
                             final_color=[255, 255, 255])

    final_clip = CompositeVideoClip([slate, text_clip])

    return final_clip
