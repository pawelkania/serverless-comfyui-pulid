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
    {
        "url": "https://github.com/WASasquatch/was-node-suite-comfyui",
        "requirements": "requirements.txt",
    },
    {
        "url": "https://github.com/sipherxyz/comfyui-art-venture",
        "requirements": "requirements.txt",
    },
    {
        "url": "https://github.com/kijai/ComfyUI-KJNodes",
        "requirements": "requirements.txt",
    },
    {
        "url": "https://github.com/storyicon/comfyui_segment_anything",
        "requirements": "requirements.txt",
    },
    {
        "url": "https://github.com/shadowcz007/comfyui-mixlab-nodes",
        "requirements": "requirements.txt",
    },
    {"url": "https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes"},
    {"url": "https://github.com/cubiq/ComfyUI_IPAdapter_plus"},
    {"url": "https://github.com/ltdrdata/ComfyUI-Manager"},
    {"url": "https://github.com/ltdrdata/ComfyUI-Impact-Pack"},
    {"url": "https://github.com/pythongosssss/ComfyUI-Custom-Scripts"},
    {"url": "https://github.com/twri/sdxl_prompt_styler"},
    {"url": "https://github.com/rgthree/rgthree-comfy"},
    {"url": "https://github.com/Acly/comfyui-inpaint-nodes"},
    {"url": "https://github.com/KoreTeknology/ComfyUI-Universal-Styler"},
]

import pathlib


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
            if name == "ComfyUI-Impact-Pack":
                process = subprocess.Popen(
                    ["python", "./custom_nodes/ComfyUI-Impact-Pack/install.py"]
                )
                process.wait()
                retcode = process.returncode

                if retcode != 0:
                    raise RuntimeError(
                        f"Impact Pack's install.py exited unexpectedly with code {retcode}"
                    )

            print(f"Requirements for {url} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error installing requirements: {e.stderr}")

