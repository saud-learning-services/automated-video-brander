from moviepy.editor import VideoClip, VideoFileClip, CompositeVideoClip
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from moviepy.audio.fx.audio_fadeout import audio_fadeout
from helpers import clear_folder_contents
import gizeh as gz
import os


class Top:
    """
    Responsible for handling all operations to do with creating/rendering top slates
    Uses Gizeh and MoviePy for text animations
    """

    def __init__(
        self,
        top_slate="sauder_slate.mp4",
        title=None,
        course=None,
        section=None,
        instructor=None,
    ):
        """
        Sets our properties to the Top object
        Defaults to sauder top slate
        """
        self.top_slate = top_slate if top_slate is not None else "sauder_slate.mp4"
        self.title = title
        self.course = course
        self.section = section
        self.instructor = instructor

    def get_video(self):
        """
        Returns a 6 second top as mp4
        """

        # read in the top slate video file
        slate = VideoFileClip(f"input/top_slates/{self.top_slate}")

        text_clip_mask = VideoClip(
            lambda t: self._make_frame(t)[:, :, 3] / 255.0,
            duration=slate.duration,
            ismask=True,
        )
        text_clip = VideoClip(
            lambda t: self._make_frame(t)[:, :, :3], duration=slate.duration
        ).set_mask(text_clip_mask)

        # add fadein and fadeout (to white)
        text_clip = text_clip.fx(fadein, duration=1, initial_color=[255, 255, 255])
        text_clip = text_clip.fx(fadeout, duration=1, final_color=[255, 255, 255])

        final_clip = CompositeVideoClip([slate, text_clip])

        final_clip = final_clip.fx(fadeout, duration=1.5, final_color=[255, 255, 255])
        final_clip = final_clip.fx(audio_fadeout, duration=1)

        return final_clip

    def _print_properties(self):
        """TODO
        Docstring - utility function for debugging
        """

        print("\n=====TOP ATTRIBUTES=====")
        print(f"COURSE: {self.course}")
        print(f"SECTION: {self.section}")
        print(f"INSTRUCTOR: {self.instructor}")
        print(f"TITLE: {self.title}")
        print(f"SLATE: {self.top_slate}")
        print("========================\n")

    def _make_frame(self, time):
        """
        Creates a single frame of the scaling text as a function of t (time)
        """

        # define the canvas
        surface = gz.Surface(1920, 1080)

        # all tops need at least a title

        # ** GENERIC UBC BRANDING WORKAROUND **
        if self.top_slate == "ubc_slate.mp4":
            primary_fill = (0.047, 0.14, 0.27)
            secondary_fill = (0, 0.65, 0.88)
        else:
            primary_fill = (0, 0.13, 0.27)
            secondary_fill = (0.47, 0.75, 0.26)

        title = gz.text(
            self.title,
            fontsize=90,
            fontfamily="WhitneyHTF-SemiBoldCondensed",
            fill=primary_fill,
            xy=(960, 490),
        )

        text_lines = [title]

        if self.course is not None:
            if self.section is not None:
                codes = f"{self.course} {self.section}"
            else:
                codes = self.course

            codes_line = gz.text(
                codes,
                fontsize=40,
                fontfamily="WhitneyHTF",
                fill=primary_fill,
                xy=(960, 410),
            )

            text_lines.append(codes_line)

        if self.instructor is not None:
            instructor = gz.text(
                self.instructor,
                fontsize=65,
                fontfamily="WhitneyHTF-SemiBoldCondensed",
                fill=secondary_fill,
                xy=(960, 600),
            )
            text_lines.append(instructor)

        for line in text_lines:
            line = line.scale(1 + 0.02 * time, center=[960, 540])
            line.draw(surface)
        return surface.get_npimage(transparent=True)
