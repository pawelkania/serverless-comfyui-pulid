NODES = [
    "https://github.com/ltdrdata/ComfyUI-Manager",
    "https://github.com/lldacing/ComfyUI_PuLID_Flux_ll",
    "https://github.com/2frames/ComfyUI-AQnodes",
    "https://github.com/ltdrdata/ComfyUI-Impact-Pack",
    "https://github.com/ltdrdata/ComfyUI-Impact-Subpack",
    "https://github.com/city96/ComfyUI_ExtraModels",
    "https://github.com/cubiq/ComfyUI_essentials",
    "https://github.com/BadCafeCode/masquerade-nodes-comfyui",
    "https://github.com/Fannovel16/comfyui_controlnet_aux",
    "https://github.com/WASasquatch/was-node-suite-comfyui",
    "https://github.com/pythongosssss/ComfyUI-Custom-Scripts",
]


def download_nodes():
    import subprocess
    import os

    for url in NODES:
        name = url.split("/")[-1]
        print(name)
        command = f"cd /root/custom_nodes && git clone {url}"

        try:
            subprocess.run(command, shell=True, check=True)
            print(f"Repository {url} cloned successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e.stderr}")

        pip_command = None
        if os.path.isfile(f"/root/custom_nodes/{name}/requirements.txt"):
            print("Installing custom node requirements...")
            pip_command = f"pip install -r /root/custom_nodes/{name}/requirements.txt"
        try:
            if pip_command:
                subprocess.run(pip_command, shell=True, check=True)
            if os.path.isfile(f"/root/custom_nodes/{name}/install.py"):
                process = subprocess.Popen(
                    ["python", f"./custom_nodes/{name}/install.py"]
                )
                process.wait()
                retcode = process.returncode

                if retcode != 0:
                    raise RuntimeError(
                        f"{name} install.py exited unexpectedly with code {retcode}"
                    )

            print(f"Requirements for {url} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error installing requirements: {e.stderr}")
