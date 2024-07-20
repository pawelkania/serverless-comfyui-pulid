import pathlib
from typing import Any, Mapping, Sequence, Union


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


def get_value_at_index(obj: Union[Sequence, Mapping], index: int) -> Any:
    try:
        return obj[index]
    except KeyError:
        return obj["result"][index]


def download_image(url: str, filename: str, save_path="input/"):
    import requests

    try:
        response = requests.get(url)
        response.raise_for_status()
        pathlib.Path(save_path + filename).write_bytes(response.content)
        print(f"{url} image successfully downloaded")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url} image: {e}")
