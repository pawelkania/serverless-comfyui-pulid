import pathlib
import json
import subprocess
import modal
import random
import os
import uuid

from .firebase import FirebaseAdmin, ResourceNotFound
from .container import image, gpu

app = modal.App("comfy-api")


@app.cls(
    gpu=gpu,
    image=image,
    container_idle_timeout=60 * 15,  # 15 minutes
    timeout=60 * 60,  # 1 hour
    secrets=[modal.Secret.from_name("googlecloud-secret")],
    mounts=[
        modal.Mount.from_local_file(
            local_path=(pathlib.Path(__file__).parent / "workflow_api.json"),
            remote_path="/root/workflow_api.json",
        ),
    ],
)
class Comfy:
    def _run_comfyui_server(self, port=8188):
        cmd = f"python main.py --listen 0.0.0.0 --port {port}"
        subprocess.Popen(cmd, shell=True)

    @modal.enter()
    def prepare(self):
        self._run_comfyui_server(port=8189)

    @modal.asgi_app()
    def api(self):
        from fastapi import FastAPI, HTTPException, WebSocket
        from fastapi.middleware.cors import CORSMiddleware
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

        websocket_client_id = str(uuid.uuid4())

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

            data = json.dumps(
                {"prompt": workflow_data, "client_id": websocket_client_id}
            ).encode("utf-8")
            response = urllib.request.Request(f"http://0.0.0.0:8189/prompt", data=data)
            result = json.loads(urllib.request.urlopen(response).read())
            print(f"Queued workflow {result['prompt_id']}")

            return result["prompt_id"]

        @fastapi.websocket("/prompt")
        async def proxy_websocket(websocket: WebSocket):
            import websockets
            import asyncio

            await websocket.accept()

            try:
                async with websockets.connect(
                    f"ws://0.0.0.0:8189/ws?clientId={websocket_client_id}",
                    max_size=1048576 * 3,
                ) as target_ws:

                    async def receive_from_client():
                        try:
                            while True:
                                data = await websocket.receive_text()
                                await target_ws.send(data)
                        except Exception as e:
                            print(f"Client disconnected: {e}")
                            await target_ws.close()

                    async def send_to_client():
                        try:
                            while True:
                                out = await target_ws.recv()
                                if isinstance(out, str):
                                    data = json.loads(out)
                                    await websocket.send_json(data)
                                else:
                                    await websocket.send_bytes(out)
                        except Exception as e:
                            print(f"Server disconnected or error: {e}")
                            await websocket.close()

                    receive_task = asyncio.create_task(receive_from_client())
                    send_task = asyncio.create_task(send_to_client())

                    await asyncio.wait(
                        [receive_task, send_task], return_when=asyncio.FIRST_COMPLETED
                    )
            except Exception as e:
                await websocket.close()
                print(f"WebSocket connection error: {e}")

        return fastapi
