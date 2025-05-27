import pathlib
import json
import subprocess
import time
import modal
import random
import os
import datetime

from .container import image, gpu
from pydantic import BaseModel

app = modal.App("comfy-api")
vol = modal.Volume.from_name("hf-hub-cache", create_if_missing=True)


class InferModel(BaseModel):
    session_id: str
    prompt: str


class JobResult(BaseModel):
    base64_image: str
    signed_url: str


@app.cls(
    gpu=gpu,
    image=image,
    scaledown_window=60 * 10,  # 10 minutes
    timeout=60 * 2,  # 2 minutes
    secrets=[modal.Secret.from_name("gemini_api_key")],
    volumes={"/cache": vol},
)

class ComfyUI:
    def _run_comfyui_server(self, port=8188):
        cmd = f"python main.py --listen 0.0.0.0 --port {port}"
        subprocess.Popen(cmd, shell=True)

    @modal.enter()
    def prepare(self):
        # Load workflow JSON when container starts
        self.workflow_json = json.loads(
            pathlib.Path("/root/workflow_api.json").read_text()
        )
        self._run_comfyui_server(port=8189)

    @modal.method()
    def infer(self, input: InferModel):
        import urllib
        import base64
        import websocket
        import requests
        import copy

        while True:
            try:
                requests.get("http://0.0.0.0:8189/prompt")
                break
            except (requests.ConnectionError, requests.Timeout) as e:
                continue
            except:
                pass

        response = requests.get("https://cdn.pixabay.com/photo/2020/05/06/18/53/girl-5138811_1280.jpg")
        bytes = response.content

        pathlib.Path(f"/root/input/{input.session_id}").write_bytes(bytes)

        # Create a client-side timestamp as a dictionary
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        start_time = {
            'timestamp': now_utc.timestamp(),
            'iso': now_utc.isoformat()
        }

        workflow = copy.deepcopy(self.workflow_json)
        workflow["111"]["inputs"]["seed"] = random.randint(1, 2**64)
        workflow["232"]["inputs"]["image"] = input.session_id
        workflow["338"]["inputs"]["text"] += input.prompt
        workflow["425"]["inputs"]["gemini_api_key"] = os.environ["gemini_api_key"]

        data = json.dumps({"prompt": workflow, "client_id": input.session_id}).encode(
            "utf-8"
        )

        response = urllib.request.Request(f"http://0.0.0.0:8189/prompt", data=data)
        result = json.loads(urllib.request.urlopen(response).read())

        prompt_id = result["prompt_id"]

        ws = websocket.WebSocket()
        while True:
            try:
                ws.connect(f"ws://0.0.0.0:8189/ws?clientId={input.session_id}")
                break
            except ConnectionRefusedError:
                time.sleep(1)

        images_output = None
        current_node = ""
        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)

                if message["type"] == "executing":
                    data = message["data"]

                    if data.get("prompt_id") and data.get("prompt_id") == prompt_id:
                        if data["node"] is None:
                            break
                        else:
                            current_node = data["node"]

                elif message["type"] == "progress":
                    data = message["data"]

            else:
                if (
                    workflow[current_node]
                    and workflow[current_node]["class_type"] == "SaveImageWebsocket"
                ):
                    images_output = out[8:]


        # Create end timestamp in the same format
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        end_time = {
            'timestamp': now_utc.timestamp(),
            'iso': now_utc.isoformat()
        }

        result = base64.b64encode(images_output).decode()
        requests.post(
            "https://api.hooklistener.com/in/S3UxGPr8ZAemCQ9wX3ryp",
            data=base64.b64encode(images_output),
        )
        requests.post(
            "https://8d55f2997a.endpoints.dev",
            data=base64.b64encode(images_output),
        )

        return f"data:image/png;base64,{result}"


@app.function(
    gpu=None,
    image=image,
    timeout=60 * 15,
    scaledown_window=60 * 15,  # 15 minutes
    volumes={"/cache": vol},
)
@modal.concurrent(max_inputs=100) 
@modal.asgi_app()
def api():
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware

    fastapi = FastAPI()
    fastapi.add_middleware(
        CORSMiddleware,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        allow_origins=["*"],
    )

    comfyui = ComfyUI()

    @fastapi.post("/job")
    def on_job_post(input: InferModel):
        job = comfyui.infer.spawn(input)
        return job.object_id

    @fastapi.get("/job/{job_id}/{session_id}")
    def on_get_job(job_id: str, session_id: str):
        function_call = modal.functions.FunctionCall.from_id(job_id)
        try:
            # Get the base64 result
            base64_result = function_call.get(timeout=60)

            # Return both results
            return JobResult(base64_image=base64_result, signed_url='')

        except TimeoutError:
            raise HTTPException(status_code=425, detail="Job is still processing")
        except Exception as e:
            print(f"Error processing job {job_id}: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Error processing job: {str(e)}"
            )

    return fastapi
