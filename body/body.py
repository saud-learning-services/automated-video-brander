import os
import ffmpeg
import cv2
from ffprobe import FFProbe
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

    def process_video(self):
        """
        Renders a video to temporary working (PROCESSED) folder that consists of body overlayed with watermark. Videos rendered with ffmpeg-python (way faster than moviepy)
        """

        overlay_file = ffmpeg.input(self.watermark)
        print('INPUT FILE: ' + self.input_src)
        print('OUTPUT PATH: ' + self.output_src)

        try:

            # 1. Check the video dimensions using opencv
            vid = cv2.VideoCapture(self.input_src)
            height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
            width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)

            # 2. Check if video has audio using FFProbe
            metadata = FFProbe(self.input_src)
            cprint(metadata.streams, 'green')

            has_audio = False

            # iterate through streams to check if there is an audio stream
            for stream in metadata.streams:
                if stream.is_audio():
                    has_audio = True

            # 3. FITTING TO 1920x1080 (16:9)
            # the smaller the  number, the larger the width/height
            difference_in_height = 1080 - height
            difference_in_width = 1920 - width

            raw = ffmpeg.input(self.input_src)

            if difference_in_width <= difference_in_height:
                # fit width
                output_width = 1920
                output_height = -1  # -1 maintains aspect ratio
                processing = (
                    raw
                    .filter('scale', width=output_width, height=output_height)
                    .filter('pad', width=1920, height=1080, y='1080 - in_h / 2')
                    .overlay(overlay_file)
                )
            else:
                # fit height
                output_width = -1
                output_height = 1080

                processing = (
                    raw
                    .filter('scale', width=output_width, height=output_height)
                    # .filter('pad', width=1920, height=1080, x=x_offset_for_padding, y=y_offset_for_padding)
                    .filter('pad', width=1920, height=1080, x='1920 - in_w / 2')
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
            print(err)

        return self.output_src
