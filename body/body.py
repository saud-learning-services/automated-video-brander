import os
import logging
import ffmpeg


class Body:
    """
    Describes the body of the video: content and watermark
    """

    def __init__(
        self,
        body_file_name,
        input_video_file_path,
        output_video_file_path,
        watermark_path,
    ):
        self.body_file_name = body_file_name
        self.input_src = input_video_file_path
        self.output_src = output_video_file_path
        self.watermark = watermark_path

    root = os.path.dirname(os.path.abspath(__file__))

    def process_video(self, with_watermark):
        """
        Renders a video to temporary working (PROCESSED) folder that consists of body overlayed with watermark. Videos rendered with ffmpeg-python (way faster than moviepy)
        Raises RuntimeError if ffmpeg fails.
        """

        print("INPUT FILE: " + self.input_src)
        print("OUTPUT PATH: " + self.output_src)

        # 1. Check the video dimensions and whether it has audio using ffprobe
        probe = ffmpeg.probe(self.input_src)
        video_stream = next(
            s for s in probe["streams"] if s["codec_type"] == "video"
        )
        height = int(video_stream["height"])
        width = int(video_stream["width"])
        has_audio = any(s["codec_type"] == "audio" for s in probe["streams"])

        height_ratio = 1080 / height
        width_ratio = 1920 / width

        raw = ffmpeg.input(self.input_src)

        # Scale to fit inside 1920x1080 and pad (centred) to fill the frame.
        # -2 keeps the aspect ratio with an even size, which the h264 encoder needs.
        if height_ratio >= width_ratio:
            # fit width
            processing = raw.filter("scale", width=1920, height=-2)
        else:
            # fit height
            processing = raw.filter("scale", width=-2, height=1080)
        processing = processing.filter(
            "pad", width=1920, height=1080, x="(ow-iw)/2", y="(oh-ih)/2"
        )

        if with_watermark:
            overlay_file = ffmpeg.input(self.watermark)
            processing = processing.overlay(overlay_file)

        streams = [processing, raw.audio] if has_audio else [processing]
        processing = ffmpeg.output(
            *streams,
            self.output_src,
            vcodec="h264_videotoolbox",
            maxrate="9.0M",
            bufsize="9.0M",
            video_bitrate="4055k",
        )

        try:
            processing.run(overwrite_output=True, capture_stderr=True)
        except ffmpeg.Error as err:
            stderr = err.stderr.decode("utf-8", errors="replace")[-1000:]
            logging.error("ffmpeg failed for %s: %s", self.input_src, stderr)
            raise RuntimeError(f"ffmpeg failed for {self.input_src}") from err

        return self.output_src
