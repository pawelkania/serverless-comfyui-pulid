from modal import Image

from .models import download_checkpoints, download_upscaler
from .plugins import download_plugins
import pathlib

comfyui_commit_sha = "2a02546e2085487d34920e5b5c9b367918531f32"

image = (
    Image.from_registry("nvidia/cuda:12.1.1-devel-ubuntu22.04", add_python="3.11")
    .apt_install("git", "git-lfs", "libgl1-mesa-glx", "libglib2.0-0", "unzip", "clang")
    .run_commands(
        "cd /root && git init .",
        "cd /root && git remote add --fetch origin https://github.com/comfyanonymous/ComfyUI",
        f"cd /root && git checkout {comfyui_commit_sha}",
    )
    .run_commands(
        "cd /root && pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121",
        "cd /root && pip install -r requirements.txt",
        gpu="h100",
    )
    .pip_install(
        "httpx", "requests", "tqdm", "gdown", "huggingface_hub[cli]", "websocket-client"
    )
    .run_function(download_plugins, gpu="h100")
    .run_commands("pip install --upgrade fastapi")
    .run_function(download_checkpoints)
    .run_commands(
        "cd /root/models/controlnet && huggingface-cli download TencentARC/t2i-adapter-lineart-sdxl-1.0 --local-dir TencentARC/t2i-adapter-lineart-sdxl-1.0",
        "cd /root/models/controlnet && huggingface-cli download TencentARC/t2i-adapter-canny-sdxl-1.0 --local-dir TencentARC/t2i-adapter-canny-sdxl-1.0",
        "cd /root/models/controlnet && huggingface-cli download TencentARC/t2i-adapter-depth-zoe-sdxl-1.0 --local-dir TencentARC/t2i-adapter-depth-zoe-sdxl-1.0",
        "cd /root/models/controlnet && huggingface-cli download TencentARC/t2i-adapter-depth-midas-sdxl-1.0 --local-dir TencentARC/t2i-adapter-depth-midas-sdxl-1.0",
        "cd /root/models/controlnet && huggingface-cli download TencentARC/t2i-adapter-sketch-sdxl-1.0 --local-dir TencentARC/t2i-adapter-sketch-sdxl-1.0",
        "cd /root/models/controlnet && huggingface-cli download TencentARC/t2i-adapter-openpose-sdxl-1.0 --local-dir TencentARC/t2i-adapter-openpose-sdxl-1.0",
        "cd /root/models/controlnet && huggingface-cli download xinsir/controlnet-tile-sdxl-1.0 --local-dir controlnet-tile-sdxl-1.0",
        "cd /root/models/controlnet && huggingface-cli download xinsir/controlnet-canny-sdxl-1.0 --local-dir controlnet-canny-sdxl-1.0",
    )
    .run_commands(
        "cd /root/models/insightface && gdown https://drive.google.com/uc?id=1qXsQJ8ZT42_xSmWIYy85IcidpiZudOCB -O buffalo_l.zip",
        "cd /root/models/insightface && unzip buffalo_l.zip -d models",
    )
    .copy_local_file(
        pathlib.Path(__file__).parent.parent / "helpers.py", "/root/helpers.py"
    )
    .run_commands(
        "cd /root/custom_nodes && git clone https://github.com/ssitu/ComfyUI_UltimateSDUpscale --recursive"
    )
)
