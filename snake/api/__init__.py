import os
import modal
from base64 import b64encode

from snake.api.image import image
from snake.api.firebase import FirebaseAdmin

api = modal.App("api")


def yield_job_result(job_id: str):
    function_call = modal.functions.FunctionCall.from_id(job_id)
    bytes = function_call.get()
    base64_data = b64encode(bytes).decode("utf-8")
    yield f"data: {base64_data}\n\n"
    return


@api.function(image=image, secrets=[modal.Secret.from_name("googlecloud-secret")])
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI
    from fastapi.responses import StreamingResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel

    app = FastAPI()
    admin = FirebaseAdmin(os.environ["SERVICE_ACCOUNT_JSON"])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    class PostJob(BaseModel):
        session_id: str
        prompt: str | None

    @app.get("/blob/{blob_name:path}")
    def get_presigned_url(blob_name: str):
        return admin.sign_blob_url(blob_name, minutes=30)

    @app.post("/job")
    def post_job(body: PostJob):
        ComfyUI = modal.Cls.lookup("snake", "ComfyUI")
        comfyui = ComfyUI()

        url = admin.sign_blob_url(blob_name=f"{body.session_id}/before", minutes=5)
        data = {"filename": f"{body.session_id}", "url": url, "prompt": body.prompt}

        job = comfyui.run.spawn(data)
        return job.object_id

    @app.get("/job/{job_id}")
    def get_job_result(job_id: str):
        return StreamingResponse(
            yield_job_result(job_id), media_type="text/event-stream"
        )

    return app
