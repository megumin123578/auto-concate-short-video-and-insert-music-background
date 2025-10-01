import subprocess
import os
import tempfile

def mix_audio_with_bgm_ffmpeg(
    input_video: str,
    bgm_audio: str,
    output_video: str,
    bgm_volume: float = 0.5
):
    temp_output = output_video

    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,                    # 0:v, 0:a (video gốc)
        "-stream_loop", "-1", "-i", bgm_audio,  # 1:a (nhạc nền lặp vô hạn)
        "-filter_complex",
        f"[1:a]volume={bgm_volume}[a_bgm];[0:a][a_bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]",
        "-map", "0:v",                        # lấy video gốc
        "-map", "[aout]",                     # âm thanh đã trộn
        "-c:v", "copy",                       # không mã hóa lại video
        "-c:a", "aac",                        # mã hóa âm thanh
        "-shortest",                          # kết thúc khi video ngắn hơn
        temp_output
    ]

    try:
        subprocess.run(cmd, check=True)
        # Ghi đè ra file output gốc
        os.replace(temp_output, output_video)
    except subprocess.CalledProcessError as e:
        if os.path.exists(temp_output):
            os.remove(temp_output)  # xóa file tạm nếu lỗi
        print(f"FFmpeg lỗi: {e}")
        raise
