import pathlib
import json
import subprocess
import modal
import random
import os
import uuid
import time
import base64

from .firebase import FirebaseAdmin, ResourceNotFound
from .container import image, gpu

app = modal.App("comfy-api")

client_id = str(uuid.uuid4())
comfyui_server_address = "127.0.0.1:8189"


def connect_to_websocket():
    import websocket

    ws = websocket.WebSocket()
    while True:
        try:
            ws.connect(f"ws://0.0.0.0:8189/ws?clientId={client_id}")
            print("Connection established!")
            break
        except ConnectionRefusedError:
            print("Server still standing up...")
            time.sleep(1)
    return ws


def event_stream(workflow: dict, prompt_id: str):
    ws = connect_to_websocket()

    output_images = []
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

                if (
                    data.get("prompt_id")
                    and data.get("prompt_id") == prompt_id
                    and data["node"] == "11"
                ):
                    progress = data["value"] - data["max"]
                    yield f'data: {{"status": "pending", "progress": {progress}}}\n\n'
        else:
            if workflow.get(current_node):
                if workflow[current_node].get("class_type") == "SaveImageWebsocket":
                    output_images.append(
                        out[8:]
                    )  # parse out header of the image byte string

    if output_images:
        result = base64.b64encode(output_images[0]).decode()
        yield f'data: {{"status": "executed", "data": "{result}"}}\n\n'


@app.cls(
    gpu=gpu,
    image=image,
    mounts=[
        modal.Mount.from_local_file(
            local_path=(pathlib.Path(__file__).parent / "workflow_api.json"),
            remote_path="/root/workflow_api.json",
        ),
    ],
    secrets=[modal.Secret.from_name("googlecloud-secret")],
    container_idle_timeout=60 * 15,  # 15 minutes
    timeout=60 * 60,  # 1 hour
    allow_concurrent_inputs=10,
)
class ComfyUI:
    def _run_comfyui_server(self, port=8188):
        cmd = f"python main.py --listen --port {port}"
        subprocess.Popen(cmd, shell=True)

    @modal.enter()
    def prepare(self):
        self._run_comfyui_server(port=8189)

    @modal.web_server(8188, startup_timeout=300)
    def ui(self):
        self._run_comfyui_server()

    @modal.asgi_app()
    def server(self):
        from fastapi import FastAPI, HTTPException, Request
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import StreamingResponse
        from pydantic import BaseModel

        class PostPromptModel(BaseModel):
            session_id: str
            prompt: str

        fastapi = FastAPI()
        fastapi.add_middleware(
            CORSMiddleware,
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
            allow_origins=["*"],
        )

        admin = FirebaseAdmin(os.environ["SERVICE_ACCOUNT_JSON"])
        workflow_json = json.loads(
            (pathlib.Path(__file__).parent / "workflow_api.json").read_text()
        )

        # TODO: add authorization
        # @fastapi.middleware("http")
        # async def check_bearer_token(request: Request, call_next):
        #     authorization = request.headers.get("authorization")
        #     if not authorization or not authorization.startswith("Bearer "):
        #         raise HTTPException(status_code=401, detail="Bearer token required")

        #     token = authorization.split(" ")[1]
        #     if not admin.verify_token(token):
        #         raise HTTPException(status_code=401, detail="Invalid or expired token")

        #     return await call_next(request)

        @fastapi.get("/blob/{blob_name:path}")
        def get_presigned_url(blob_name: str):
            return admin.sign_blob_url(blob_name, minutes=30)

        @fastapi.post("/prompt")
        def post_prompt(body: PostPromptModel):
            import urllib
            import requests

            try:
                requests.get("http://0.0.0.0:8189/prompt")
            except (requests.ConnectionError, requests.Timeout) as e:
                raise HTTPException(status_code=425, detail="Server not reachable yet")
            except:
                pass

            try:
                bytes = admin.download_bytes(f"{body.session_id}/before")
                pathlib.Path(f"/root/input/{body.session_id}").write_bytes(bytes)
                print(f"{body.session_id}/before image successfully downloaded")
            except ResourceNotFound as e:
                print(f"Error downloading {body.session_id}/before image: {e}")
                return HTTPException(status_code=404, detail=ResourceNotFound.cause)

            workflow_data = workflow_json.copy()
            workflow_data["11"]["inputs"]["seed"] = random.randint(1, 2**64)
            workflow_data["1"]["inputs"]["image"] = body.session_id
            workflow_data["9"]["inputs"]["text"] += body.prompt

            data = json.dumps({"prompt": workflow_data, "client_id": client_id}).encode(
                "utf-8"
            )
            response = urllib.request.Request(f"http://0.0.0.0:8189/prompt", data=data)
            result = json.loads(urllib.request.urlopen(response).read())
            print(f"Queued workflow {result['prompt_id']}")

            return result["prompt_id"]

        @fastapi.get("/prompt/{prompt_id}")
        def get_prompt(prompt_id: str):
            return StreamingResponse(
                event_stream(workflow_json, prompt_id), media_type="text/event-stream"
            )

        return fastapi
