import pathlib
from typing import Dict
from modal import App, enter, method

from snake.comfy.image import image, gpu
from snake.comfy.workflow import run_python_workflow
from snake.comfy.utils import download_image

comfy = App(name="comfy")


@comfy.cls(image=image, gpu=gpu, container_idle_timeout=300)
class ComfyUI:

    @enter()
    def on_enter(self):
        from nodes import init_extra_nodes

        init_extra_nodes()

    @method()
    def run(self, item: Dict):
        download_image(url=item["url"], filename=item["filename"])

        result = run_python_workflow(item)
        saved_image = result["ui"]["images"][0]

        filename = saved_image["filename"]

        bytes = pathlib.Path(f"output/{filename}").read_bytes()
        return bytes


@comfy.local_entrypoint()
def main() -> None:
    values = {
        "filename": "2",
        "url": "https://firebasestorage.googleapis.com/v0/b/wesmile-admin-dev.appspot.com/o/transformed.png?alt=media&token=25d4e1a0-286d-4692-a48f-f3f78ce3f97d",
        "prompt": "long sleeves, short lengs, tall face, mcdonalds, hamburger, no pickes, fries",
    }
    bytes = ComfyUI().run.remote(values)
    with open("result.png", "wb") as f:
        f.write(bytes)
        f.close()
    return
