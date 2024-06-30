from modal import Image

import pathlib

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


def download_checkpoints():
    import httpx
    from tqdm import tqdm

    for model in MODELS:
        url = model["url"]
        local_filename = url.split("/")[-1]
        local_filepath = pathlib.Path(model["directory"], local_filename)
        local_filepath.parent.mkdir(parents=True, exist_ok=True)

        print(f"downloading {url} ...")
        with httpx.stream("GET", url, follow_redirects=True) as stream:
            total = int(stream.headers["Content-Length"])
            with open(local_filepath, "wb") as f, tqdm(
                total=total, unit_scale=True, unit_divisor=1024, unit="B"
            ) as progress:
                num_bytes_downloaded = stream.num_bytes_downloaded
                for data in stream.iter_bytes():
                    f.write(data)
                    progress.update(stream.num_bytes_downloaded - num_bytes_downloaded)
                    num_bytes_downloaded = stream.num_bytes_downloaded


# Add plugins to PLUGINS, a list of dictionaries with two keys:
# `url` for the github url and an optional `requirements` for the name of a requirements.txt to pip install (remove this key if there is none for the plugin).
PLUGINS = [
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
    {"url": "https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes"},
]


def download_plugins():
    import subprocess

    for plugin in PLUGINS:
        url = plugin["url"]
        name = url.split("/")[-1]
        command = f"cd /root/custom_nodes && git clone {url}"
        try:
            subprocess.run(command, shell=True, check=True)
            print(f"Repository {url} cloned successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e.stderr}")
        if plugin.get("requirements"):
            pip_command = f"cd /root/custom_nodes/{name} && pip install -r {plugin['requirements']}"
        try:
            subprocess.run(pip_command, shell=True, check=True)
            if name == "comfyui-reactor-node":
                process = subprocess.Popen(
                    ["python", "./custom_nodes/comfyui-reactor-node/install.py"]
                )
                process.wait()
                retcode = process.returncode

                if retcode != 0:
                    raise RuntimeError(
                        f"reactor's install.py exited unexpectedly with code {retcode}"
                    )

            print(f"Requirements for {url} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error installing requirements: {e.stderr}")


cuda_version = "12.1.1"
flavor = "devel"
os = "ubuntu22.04"
tag = f"{cuda_version}-{flavor}-{os}"
comfyui_commit_sha = "a88b0ebc2d2f933c94e42aa689c42e836eedaf3c"

gpu = "h100"

image = (
    Image.from_registry(f"nvidia/cuda:{tag}", add_python="3.10")
    .run_commands("gcc --version")
    .apt_install("git", "libgl1-mesa-glx", "libglib2.0-0", "unzip", "clang")
    # Here we place the latest ComfyUI repository code into /root.
    # Because /root is almost empty, but not entirely empty
    # as it contains this comfy_ui.py script, `git clone` won't work.
    # As a workaround we `init` inside the non-empty directory, then `checkout`.
    .run_commands(
        "cd /root && git init .",
        "cd /root && git remote add --fetch origin https://github.com/comfyanonymous/ComfyUI",
        f"cd /root && git checkout {comfyui_commit_sha}",
    )
    .run_commands(
        "cd /root && pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121",
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
