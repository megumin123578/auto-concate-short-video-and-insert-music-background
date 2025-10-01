import subprocess
import os
import re

def get_next_output_filename(folder: str) -> str:
    """
    Trả về đường dẫn file tiếp theo dạng số.mp4 trong thư mục (ví dụ: 101.mp4 nếu lớn nhất là 100.mp4)
    """
    max_index = 0
    pattern = re.compile(r"(\d+)\.mp4$", re.IGNORECASE)

    for filename in os.listdir(folder):
        match = pattern.match(filename)
        if match:
            index = int(match.group(1))
            if index > max_index:
                max_index = index

    next_index = max_index + 1
    return os.path.join(folder, f"{next_index}.mp4")

def mix_audio_with_bgm_ffmpeg(
    input_video: str,
    bgm_audio: str,
    output_dir: str,
    bgm_volume: float = 0.5
):
    output_video = get_next_output_filename(output_dir)
    temp_output = output_video + ".temp.mp4"

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
        os.replace(temp_output, output_video)
        print(f"Đã lưu video mới: {output_video}")
    except subprocess.CalledProcessError as e:
        if os.path.exists(temp_output):
            os.remove(temp_output)
        print(f"FFmpeg lỗi: {e}")
        raise

print(get_next_output_filename(r'\\192.168.1.92\Ổ Sever Mới\Định\Satisfy ASMR\SHORT AI\ASMR\1.HOÀN THIỆN\AI ghép\Đã ghép\347.mp4'))