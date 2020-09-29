import os
import logging
import ffmpeg
import cv2
# from ffprobe import FFProbe
from termcolor import cprint


class Body:
    """
    Describes the body of the video: content and watermark
    """

    def __init__(self, body_file_name, input_video_file_path, output_video_file_path, watermark_path):
        self.body_file_name = body_file_name
        self.input_src = input_video_file_path
        self.output_src = output_video_file_path
        self.watermark = watermark_path

    root = os.path.dirname(os.path.abspath(__file__))

    def process_video(self, with_watermark):
        """
        Renders a video to temporary working (PROCESSED) folder that consists of body overlayed with watermark. Videos rendered with ffmpeg-python (way faster than moviepy)
        """

        print('INPUT FILE: ' + self.input_src)
        print('OUTPUT PATH: ' + self.output_src)

        try:

            # 1. Check the video dimensions using opencv
            vid = cv2.VideoCapture(self.input_src)
            height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
            width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)

            # 2. Check if video has audio using FFProbe
            # metadata = FFProbe(self.input_src)  # ERROR THROWN HERE
            # cprint(metadata.streams, 'green')

            p = ffmpeg.probe(self.input_src, select_streams='a')

            has_audio = False

            # If p['streams'] is not empty, clip has an audio stream
            if p['streams']:
                has_audio = True

            height_ratio = 1080 / height
            width_ratio = 1920 / width

            raw = ffmpeg.input(self.input_src)

            if height_ratio >= width_ratio:
                # fit width
                output_width = 1920
                output_height = -1  # -1 maintains aspect ratio
                processing = (
                    raw
                    .filter('scale', width=output_width, height=output_height)
                    .filter('pad', width=1920, height=1080, y='1080 - in_h / 2')
                    # .overlay(overlay_file)
                )
            else:
                # fit height
                output_width = -1
                output_height = 1080

                processing = (
                    raw
                    .filter('scale', width=output_width, height=output_height)
                    .filter('pad', width=1920, height=1080, x='1920 - in_w / 2')
                    # .overlay(overlay_file)
                )

            if with_watermark:
                overlay_file = ffmpeg.input(self.watermark)
                processing = (
                    processing
                    .overlay(overlay_file)
                )

            if has_audio:
                audio = raw.audio
                processing = (
                    processing
                    .output(audio, self.output_src, vcodec='h264_videotoolbox', maxrate='9.0M', bufsize='9.0M', video_bitrate='4055k')
                )
            else:
                processing = (
                    processing
                    .output(self.output_src, vcodec='h264_videotoolbox', maxrate='9.0M', bufsize='9.0M', video_bitrate='4055k')
                )

            processing.run()

        except Exception as err:
            logging.error(err)
            print(err)

        return self.output_src
