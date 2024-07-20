from modal import Image
from snake.comfy.utils import download_checkpoints, download_plugins

## Define container image
MODELS = [
    {
        "url": "https://huggingface.co/Yabo/SDXL_LoRA/resolve/main/dreamshaperXL_alpha2Xl10.safetensors",
        "directory": "/root/models/checkpoints",
    },
    {
        "url": "https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/inswapper_128.onnx",
        "directory": "/root/models/insightface",
    },
    {
        "url": "https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/facerestore_models/codeformer-v0.1.0.pth",
        "directory": "/root/models/facerestore_models",
    },
    {
        "url": "https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/parsing_parsenet.pth",
        "directory": "/root/models/facedetection",
    },
    {
        "url": "https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/yolov5l-face.pth",
        "directory": "/root/models/facedetection",
    },
    {
        "url": "https://huggingface.co/stabilityai/control-lora/resolve/main/control-LoRAs-rank256/control-lora-depth-rank256.safetensors",
        "directory": "/root/models/controlnet",
    },
    {
        "url": "https://huggingface.co/thibaud/controlnet-openpose-sdxl-1.0/resolve/main/control-lora-openposeXL2-rank256.safetensors",
        "directory": "/root/models/controlnet",
    },
    {
        "url": "https://huggingface.co/lllyasviel/Annotators/resolve/main/dpt_hybrid-midas-501f0c75.pt",
        "directory": "/root/custom_nodes/comfyui_controlnet_aux/ckpts/lllyasviel/Annotators",
    },
    {
        "url": "https://huggingface.co/lllyasviel/Annotators/resolve/main/body_pose_model.pth",
        "directory": "/root/custom_nodes/comfyui_controlnet_aux/ckpts/lllyasviel/Annotators",
    },
    {
        "url": "https://huggingface.co/lllyasviel/Annotators/resolve/main/hand_pose_model.pth",
        "directory": "/root/custom_nodes/comfyui_controlnet_aux/ckpts/lllyasviel/Annotators",
    },
    {
        "url": "https://huggingface.co/lllyasviel/Annotators/resolve/main/facenet.pth",
        "directory": "/root/custom_nodes/comfyui_controlnet_aux/ckpts/lllyasviel/Annotators",
    },
]


# Add plugins to PLUGINS, a list of dictionaries with two keys:
# `url` for the github url and an optional `requirements` for the name of a requirements.txt to pip install (remove this key if there is none for the plugin).
PLUGINS = [
    {"url": "https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes"},
    {
        "url": "https://github.com/Gourieff/comfyui-reactor-node",
        "requirements": "requirements.txt",
    },
    {
        "url": "https://github.com/Fannovel16/comfyui_controlnet_aux",
        "requirements": "requirements.txt",
    },
    {
        "url": "https://github.com/jags111/efficiency-nodes-comfyui",
        "requirements": "requirements.txt",
    },
]

cuda_version = "12.4.0"
flavor = "devel"
os = "ubuntu22.04"
tag = f"{cuda_version}-{flavor}-{os}"
comfyui_commit_sha = "4ca9b9cc29fefaa899cba67d61a8252ae9f16c0d"

gpu = "h100"

image = (
    Image.from_registry(f"nvidia/cuda:{tag}", add_python="3.11")
    .apt_install("git", "libgl1-mesa-glx", "libglib2.0-0", "unzip", "clang")
    .run_commands(
        "cd /root && git init .",
        "cd /root && git remote add --fetch origin https://github.com/comfyanonymous/ComfyUI",
        f"cd /root && git checkout {comfyui_commit_sha}",
    )
    .run_commands(
        "cd /root && pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu124",
        "cd /root && pip install -r requirements.txt",
        gpu=gpu,
    )
    .pip_install(
        "httpx",
        "requests",
        "tqdm",
        "gdown",
    )
    .run_function(download_plugins, gpu=gpu)
    .run_function(download_checkpoints)
    .run_commands(
        "cd /root/models/insightface && gdown https://drive.google.com/uc?id=1qXsQJ8ZT42_xSmWIYy85IcidpiZudOCB -O buffalo_l.zip",
        "cd /root/models/insightface && unzip buffalo_l.zip -d models",
    )
)
