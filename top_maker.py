from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import moviepy.video.fx.all as vfx
import gizeh as gz
from moviepy.video.VideoClip import VideoClip


def _make_frame(t, txt):
    surface = gz.Surface(1920, 1080)
    text = gz.text(txt, fontsize=90, fontfamily='WhitneyHTF-SemiBoldCondensed',
                   fill=(0, 0.13, 0.27), xy=(960, 540))
    text = text.scale(1+0.02*t, center=[960, 540])
    text.draw(surface)
    return surface.get_npimage(transparent=True)


def create_top(title_text, slate):

    slate = VideoFileClip(f'input/top_slates/{slate}')

    text_clip_mask = VideoClip(lambda t: _make_frame(t, title_text)[
                               :, :, 3] / 255.0, duration=slate.duration, ismask=True)
    text_clip = VideoClip(lambda t: _make_frame(t, title_text)[
                          :, :, :3], duration=slate.duration).set_mask(text_clip_mask)
    # text_clip = VideoClip(make_frame, duration=slate.duration)

    text_clip = text_clip.fx(vfx.fadein, duration=1,
                             initial_color=[255, 255, 255])
    text_clip = text_clip.fx(vfx.fadeout, duration=1,
                             final_color=[255, 255, 255])

    final_clip = CompositeVideoClip([slate, text_clip])

    return final_clip
    # final_clip.write_videofile(f'output/title_test.mp4', temp_audiofile='temp-audio.m4a', codec='libx264', fps=29.97, remove_temp=True, audio_codec='aac')


# TO SEE ALL POSSIBLE FONTS
# font_list = TextClip.list('font')
# print(font_list)

# screensize = (1920,1080)

# slate = VideoFileClip(f'input/sauder_top_slate.mp4')

# text_clip = (
#     TextClip(txt='Hello World!', font='WhitneyHTF-SemiBoldCondensed', color='#002145', fontsize=900)
#     .resize(lambda t : 0.1 * (1+0.03*t))
#     .set_duration(slate.duration)
#     .set_pos('center')
# )

# final_clip = CompositeVideoClip([slate, text_clip])

# final_clip.write_videofile(f'output/title_test.mp4', bitrate="15000k", temp_audiofile='temp-audio.m4a', codec='mpeg4', fps=29.97, remove_temp=True, audio_codec='aac')
