import pathlib
from typing import Dict
from modal import App, enter, method

from .image import image, gpu
from .workflow import run_python_workflow, download_image

app = App(name="comfy-workflow-app")


# !TODO: Require as much CPU and RAM as ReActor would need to run faster
@app.cls(image=image, gpu=gpu, container_idle_timeout=300)
class ComfyUI:
    def prepare(self):
        from nodes import init_custom_nodes

        init_custom_nodes()

    @enter()
    def on_enter(self):
        self.prepare()

    @method()
    def warm_up(self):
        self.prepare()

    @method()
    def run(self, item: Dict):
        download_image(url=item["url"], filename=item["filename"])

        result = run_python_workflow(item)
        saved_image = result["ui"]["images"][0]

        filename = saved_image["filename"]

        bytes = pathlib.Path(f"output/{filename}").read_bytes()
        return bytes


@app.local_entrypoint()
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
