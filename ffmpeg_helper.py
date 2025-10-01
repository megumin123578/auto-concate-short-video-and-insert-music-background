import subprocess
from concurrent.futures import ThreadPoolExecutor
from google.oauth2.service_account import Credentials
import shutil
import pathlib
import os

def normalize_video(
    input_path,
    output_path,
    width=1080,
    height=1920,
    fps=60,
    use_nvenc=True,
    cq=23,               # NVENC dùng -cq; x264 dùng -crf
    v_bitrate="12M",
    a_bitrate="160k",
    nvenc_preset="p4",   
):
    # Path chuẩn/Unicode OK
    in_p  = pathlib.Path(input_path)
    out_p = pathlib.Path(output_path)
    if not in_p.exists():
        raise FileNotFoundError(f"Input không tồn tại: {in_p}")

    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg không có trong PATH")

    # Chọn NVENC nếu có đủ điều kiện
    use_nv = bool(use_nvenc and has_encoder("h264_nvenc"))
    
    if use_nv and not nvenc_supports_preset(nvenc_preset):
        
        nvenc_preset = "medium"

    vf = f"fps={fps},scale={width}:{height}:flags=lanczos"

    if use_nv:
        video_args = [
            "-c:v", "h264_nvenc",
            "-profile:v", "main",
            "-rc", "vbr",
            "-cq", str(int(cq)),
            "-b:v", v_bitrate,
            "-maxrate", v_bitrate,
            "-bufsize", "24M",
            "-preset", nvenc_preset,     # p1..p7 nếu hỗ trợ, else 'medium'
        ]
    else:
        video_args = [
            "-c:v", "libx264",
            "-preset", "medium",
            "-profile:v", "main",
            "-level", "4.2",
            "-crf", str(int(cq) if isinstance(cq, int) else 20),
            "-maxrate", v_bitrate,
            "-bufsize", "16M",
        ]

    cmd = [
        "ffmpeg", "-y",
        "-fflags", "+genpts",
        "-i", str(in_p),
        "-vf", vf,
        *video_args,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-ar", "48000",
        "-b:a", a_bitrate,
        str(out_p)
    ]

    try:
        run_ffmpeg(cmd)
    except subprocess.CalledProcessError:
        
        if use_nv:
            print("⚠ NVENC failed → fallback libx264")
            video_args = [
                "-c:v", "libx264",
                "-preset", "medium",
                "-profile:v", "main",
                "-level", "4.2",
                "-crf", str(int(cq) if isinstance(cq, int) else 20),
                "-maxrate", v_bitrate,
                "-bufsize", "16M",
            ]
            cmd2 = [
                "ffmpeg", "-y",
                "-fflags", "+genpts",
                "-i", str(in_p),
                "-vf", vf,
                *video_args,
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-c:a", "aac",
                "-ar", "48000",
                "-b:a", a_bitrate,
                str(out_p)
            ]
            run_ffmpeg(cmd2)
        else:
            raise



def concat_video(video_paths, output_path):
    list_file = "temp.txt"
    with open(list_file, 'w', encoding='utf-8') as f:
        for path in video_paths:
            abs_path = os.path.abspath(path).replace("\\", "/")
            f.write(f"file '{abs_path}'\n")

    command = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output_path
    ]
    subprocess.run(command, check=True)
    os.remove(list_file)


def auto_concat(input_videos, output_path):
    normalized_paths = []

    def normalize_and_collect(i, path):
        fixed = f"normalized_{i}.mp4"
        normalize_video(path, fixed)
        return fixed

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(normalize_and_collect, i, path) for i, path in enumerate(input_videos)]
        for future in futures:
            normalized_paths.append(future.result())

    concat_video(normalized_paths, output_path)

    for path in normalized_paths:
        os.remove(path)

    print("Ghép video hoàn tất:", output_path)



def run_ffmpeg(cmd: list):
    try:
        p = subprocess.run(cmd, check=True, text=True,
                           capture_output=True, encoding="utf-8", errors="ignore")
        return p
    except subprocess.CalledProcessError as e:
        print("FFmpeg FAILED")
        print("CMD:", " ".join(cmd))
        print("STDERR:\n", e.stderr)  # <-- xem lỗi thật ở đây
        raise

def has_encoder(name="h264_nvenc"):
    try:
        out = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"],
                             capture_output=True, text=True, encoding="utf-8", errors="ignore").stdout.lower()
        return name.lower() in out
    except Exception:
        return False

def nvenc_supports_preset(preset: str) -> bool:
    try:
        out = subprocess.run(["ffmpeg", "-h", "encoder=h264_nvenc"],
                             capture_output=True, text=True, encoding="utf-8", errors="ignore").stdout.lower()
        return f"preset    {preset}".lower() in out or f"-preset {preset}".lower() in out
    except Exception:
        return False
