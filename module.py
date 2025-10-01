from datetime import datetime
import os
import random
import re
import subprocess

ROOT_DIR = r"\\nasfmc\Ổ Sever Mới\Định\Satisfy ASMR\SHORT AI\ASMR\Quay mới"
SAVE_FOLDER = r"\\nasfmc\Ổ Sever Mới\Định\Satisfy ASMR\SHORT AI\ASMR\1.HOÀN THIỆN\AI ghép\Đã ghép"

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

def get_all_random_video_groups(video_list, group_size=6):
    import random
    random.shuffle(video_list)
    groups = []
    for i in range(0, len(video_list), group_size):
        group = video_list[i:i+group_size]
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

import os

def read_used_source_videos(log_path: str):
    used_files = []
    if not os.path.exists(log_path):
        return used_files
    
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or ":" not in line:
                continue
            parts = line.split(":", 1)
            if len(parts) < 2:
                continue
            content = parts[1].strip()

            if "+ BGM:" in content:
                content = content.split("+ BGM:")[0].strip()
            #split by comma
            inputs = [p.strip() for p in content.split(",") if p.strip()]
            used_files.extend(inputs)
    
    return used_files

def read_log_info(log_path: str):
    used_inputs = set()
    done_count = 0
    if not os.path.exists(log_path):
        return used_inputs, done_count

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or ":" not in line:
                continue
            done_count += 1
            # bỏ phần "xxx.mp4:"
            content = line.split(":", 1)[1]
            if "+ BGM:" in content:
                content = content.split("+ BGM:")[0]
            # tách file input
            inputs = [p.strip() for p in content.split(",") if p.strip()]
            used_inputs.update(inputs)
    return used_inputs, done_count



