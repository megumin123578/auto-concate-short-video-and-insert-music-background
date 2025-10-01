from datetime import datetime
import os
import random

ROOT_DIR = r"\\192.168.1.92\Ổ Sever Mới\Định\Satisfy ASMR\SHORT AI\ASMR\Quay mới"
SAVE_FOLDER = r'\\192.168.1.92\Ổ Sever Mới\Định\Satisfy ASMR\SHORT AI\ASMR\1.HOÀN THIỆN\AI ghép'
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







