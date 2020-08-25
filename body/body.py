import os
import ffmpeg
import cv2


class Body:
    """
    Describes the body of the video: content and watermark
    """

    def __init__(self, body_file_name, body_clip_path, watermark_path):
        self.body_file_name = body_file_name
        self.body_path = body_clip_path
        self.watermark = watermark_path

    root = os.path.dirname(os.path.abspath(__file__))

    def get_video(self):
        """
        Renders a video to temporary working folder that consists of body overlayed with watermark. Videos rendered with ffmpeg-python (way faster than moviepy)
        """

        overlay_file = ffmpeg.input(self.watermark)
        output_path = f'input/body/PROCESSED/{self.body_file_name}'
        print('OUTPUT PATH: ' + output_path)

        try:

            raw = ffmpeg.input(self.body_path)

            # for some reason I need to explicitly get audio and include in output function
            audio = raw.audio

            # Check the video dimensions using opencv
            vid = cv2.VideoCapture(self.body_path)
            height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
            width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)

            # the smaller the  number, the larger the width/height
            difference_in_height = 1080 - height
            difference_in_width = 1920 - width

            if difference_in_width <= difference_in_height:
                # fit width
                output_width = 1920
                output_height = -1  # -1 maintains aspect ratio

                (
                    raw
                    .filter('scale', width=output_width, height=output_height)
                    .filter('pad', width=1920, height=1080, y='1080 - in_h / 2')
                    .overlay(overlay_file)
                    .output(audio, output_path, vcodec='h264_videotoolbox', maxrate='9.0M', bufsize='9.0M', video_bitrate='4055k')
                    .run()
                )
            else:
                # fit height
                output_width = -1
                output_height = 1080

                (
                    raw
                    .filter('scale', width=output_width, height=output_height)
                    # .filter('pad', width=1920, height=1080, x=x_offset_for_padding, y=y_offset_for_padding)
                    .filter('pad', width=1920, height=1080, x='1920 - in_w / 2')
                    .overlay(overlay_file)
                    .output(audio, output_path, vcodec='h264_videotoolbox', maxrate='9.0M', bufsize='9.0M', video_bitrate='4055k')
                    .run()
                )
        except Exception as err:
            print(err)

        return output_path
