import modal

image = (
    modal.Image.debian_slim()
    .pip_install("firebase_admin")
    .run_commands("pip install --upgrade fastapi")
)
