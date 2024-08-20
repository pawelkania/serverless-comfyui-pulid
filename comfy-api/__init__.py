import pathlib
import json
import subprocess
import modal
import random

from typing import Dict

from .image import image

with image.imports():
    from helpers import connect_to_local_server, get_images


def download_image(url: str, filename: str, save_path="/root/input/"):
    import requests

    try:
        response = requests.get(url)
        response.raise_for_status()
        pathlib.Path(save_path + filename).write_bytes(response.content)
        print(f"{url} image successfully downloaded")

    except Exception as e:
        print(f"Error downloading {url} image: {e}")


app = modal.App("comfy-api")


@app.cls(
    gpu="h100",
    image=image,
    container_idle_timeout=5 * 60,
    mounts=[
        modal.Mount.from_local_file(
            local_path=(pathlib.Path(__file__).parent / "workflow_api.json"),
            remote_path="/root/workflow_api.json",
        ),
    ],
)
class ComfyUI:
    def _run_comfyui_server(self, port=8188):
        cmd = f"python main.py --listen --port {port}"
        subprocess.Popen(cmd, shell=True)

    @modal.web_server(8188, startup_timeout=300)
    def ui(self):
        self._run_comfyui_server()

    @modal.enter()
    def on_enter(self):
        self._run_comfyui_server(port=8189)

    @modal.method()
    def infer(self, item: Dict):
        import requests

        download_image(
            url=item["input_image_url"], filename=item["input_image_filename"]
        )

        workflow_data = json.loads(
            (pathlib.Path(__file__).parent / "workflow_api.json").read_text()
        )

        workflow_data["1"]["inputs"]["image"] = item["input_image_filename"]
        workflow_data["11"]["inputs"]["seed"] = random.randint(1, 2**64)
        workflow_data["9"]["inputs"]["text"] += item["prompt"]

        server_address = "127.0.0.1:8189"
        ws = connect_to_local_server(server_address)
        images = get_images(ws, workflow_data, server_address)

        files = {
            "file": (
                item["input_image_filename"] + "-after",
                images[0],
                "image/png",
            )
        }
        response = requests.post(
            "https://wesmile-photobooth.ew.r.appspot.com/image", files=files
        )
        return response.text


@app.function()
@modal.asgi_app()
def server():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    fastapi = FastAPI()
    fastapi.add_middleware(
        CORSMiddleware,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        allow_origins=["*"],
    )

    ComfyUI = modal.Cls.lookup("comfy-api", "ComfyUI")
    comfyui = ComfyUI()

    @fastapi.post("/")
    def on_post(item: Dict):
        job = comfyui.infer.spawn(item)
        return {"status": "started", "job_id": job.object_id}

    @fastapi.get("/{job_id}")
    def on_get_job(job_id: str):
        function_call = modal.functions.FunctionCall.from_id(job_id)
        try:
            result = function_call.get(timeout=60)
            return {"status": "completed", "job_id": job_id, "data": result}
        except TimeoutError:
            return {"status": "pending", "job_id": job_id}

    return fastapi
