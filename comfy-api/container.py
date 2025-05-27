from modal import Image
import pathlib

import modal

from .models import download_checkpoints, hf_download
from .nodes import download_nodes

commit_sha = "c9e1821a7b49bb58f18f114336bae911160ac69d"
gpu = "L40S"
# gpu = "h100"


vol = modal.Volume.from_name("hf-hub-cache", create_if_missing=True)

# Define the image with correct configuration
image = (
    Image.from_registry("nvidia/cuda:12.6.3-devel-ubuntu22.04", add_python="3.11")
    .apt_install("git", "git-lfs", "libgl1-mesa-glx", "libglib2.0-0", "unzip", "clang")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
    .run_commands(
        "cd /root && git init .",
        "cd /root && git remote add --fetch origin https://github.com/comfyanonymous/ComfyUI",
        f"cd /root && git checkout {commit_sha}",
    )
    .run_commands(
        "cd /root && pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu126",
        "cd /root && pip install -r requirements.txt",
        gpu=gpu,
    )
    .pip_install(
        "httpx",
        "requests",
        "tqdm",
        "gdown",
        "websocket-client",
        "firebase_admin",
        "pydantic",
        "huggingface_hub[hf_transfer]",
        "fastapi",
    )
    .run_function(
        hf_download,
        secrets=[modal.Secret.from_name("HF_TOKEN")],
        volumes={"/cache": vol},
    )
    .run_function(
        download_nodes,
        gpu=gpu,
        volumes={"/cache": vol},
    )
    .run_commands(
        "mkdir -p /root/models/insightface",
        "cd /root/models/insightface && gdown https://drive.google.com/uc?id=1qXsQJ8ZT42_xSmWIYy85IcidpiZudOCB -O buffalo_l.zip",
        "cd /root/models/insightface && unzip buffalo_l.zip -d models",
    )
    .add_local_file(
        local_path=str(pathlib.Path(__file__).parent / "workflow_api.json"),
        remote_path="/root/workflow_api.json",
    )
)
