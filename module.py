from datetime import datetime
import os
import random
import re
import subprocess

ROOT_DIR = r"\\192.168.1.92\Ổ Sever Mới\Định\Satisfy ASMR\SHORT AI\ASMR\Quay mới"
SAVE_FOLDER = r"\\192.168.1.92\Ổ Sever Mới\Định\Satisfy ASMR\SHORT AI\ASMR\1.HOÀN THIỆN\AI ghép\Đã ghép"

def get_today_date_str():
    dt = datetime.now().strftime("%d-%m-%y")
    dt = dt.replace('-','.')
    return dt


import os

def list_all_mp4_files(folder_path):
    if not os.path.isdir(folder_path):
        raise ValueError(f"Không tìm thấy thư mục: {folder_path}")
    
    mp4_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".mp4"):
                full_path = os.path.join(root, file)
                mp4_files.append(full_path)
    return mp4_files

def list_all_mp3_files(folder_path):
    if not os.path.isdir(folder_path):
        raise ValueError(f"Không tìm thấy thư mục: {folder_path}")
    
    mp3_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".mp3"):
                full_path = os.path.join(root, file)
                mp3_files.append(full_path)
    return mp3_files

def get_all_random_video_groups(folder_path, group_size=6):
    all_videos = list_all_mp4_files(folder_path)
    random.shuffle(all_videos)

    groups = []
    for i in range(0, len(all_videos), group_size):
        group = all_videos[i:i+group_size]
        if len(group) == group_size:
            groups.append(group)
    return groups


def get_next_output_filename(folder: str) -> str:
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
    temp_output = 'temp.mp4'

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
        output_video
    ]

    try:
        with open("log/insert_mp3.txt", "w", encoding="utf-8") as log_file:
            subprocess.run(
                cmd,
                check=True,
                stdout=log_file,
                stderr=log_file
            )
    except subprocess.CalledProcessError as e:
        if os.path.exists(temp_output):
            os.remove(temp_output)
        print(f"FFmpeg lỗi: {e}")
        raise
    
    print(f'Đã thêm nhạc vào video : {output_video}')
    return output_video





