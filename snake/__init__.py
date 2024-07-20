import modal

from .comfy import comfy
from .api import api

app = modal.App(name="snake")
app.include(comfy)
app.include(api)
