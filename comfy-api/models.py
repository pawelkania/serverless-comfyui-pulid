import os
import pathlib
import subprocess
import modal

vol = modal.Volume.from_name("hf-hub-cache1", create_if_missing=True)


MODELS = [
    # FLUX Core Models - Using HF repo info where available
    {
        "repo_id": "Kijai/flux-fp8",
        "filename": "flux1-dev-fp8.safetensors",
        "directory": "/root/models/unet",
        "local_filename": "flux1-dev-fp8.safetensors",
    },
    {
        "repo_id": "Shakker-Labs/FLUX.1-dev-ControlNet-Union-Pro-2.0",
        "filename": "diffusion_pytorch_model.safetensors",
        "directory": "/root/models/controlnet",
        "local_filename": "FLUX.1-dev-ControlNet-Union-Pro-2.0-fp8.safetensors",
    },
    {
        "repo_id": "comfyanonymous/flux_text_encoders",
        "filename": "t5xxl_fp8_e4m3fn_scaled.safetensors",
        "directory": "/root/models/clip",
        "local_filename": "t5xxl_fp8_e4m3fn_scaled_flux.safetensors",
    },
    {
        "repo_id": "comfyanonymous/flux_text_encoders",
        "filename": "clip_l.safetensors",
        "directory": "/root/models/clip",
        "local_filename": "clip_l_flux.safetensors",
    },
    {
        "repo_id": "black-forest-labs/FLUX.1-dev",
        "filename": "ae.safetensors",
        "directory": "/root/models/vae",
        "local_filename": "ae.safetensors",
    },
    # PuLID Models
    {
        "repo_id": "guozinan/PuLID",
        "filename": "pulid_flux_v0.9.1.safetensors",
        "directory": "/root/models/pulid",
        "local_filename": "pulid_flux_v0.9.1.safetensors",
    },
    # Upscaling Models
    {
        "url": "https://huggingface.co/Phips/2xNomosUni_span_multijpg_ldl/resolve/main/2xNomosUni_span_multijpg_ldl.safetensors?download=true",
        "directory": "/root/models/upscale_models",
        "local_filename": "2xNomosUni_span_multijpg_ldl.safetensors",
    },
    {
        "url": "https://huggingface.co/Bingsu/adetailer/blob/main/face_yolov8m.pt",
        "directory": "/root/models/ultralytics/bbox",
        "local_filename": "face_yolov8m.pt",
    }
]


def hf_download():
    """Download models using huggingface_hub for faster downloads with hf_transfer support."""
    from huggingface_hub import hf_hub_download, login
    import httpx
    from tqdm import tqdm

    login(token=os.environ["HF_TOKEN"])

    for model in MODELS:
        directory = model["directory"]
        local_filename = model["local_filename"]

        # Create target directory
        target_dir = pathlib.Path(directory)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / local_filename

        # Remove existing file/symlink if it exists
        if target_path.exists() or target_path.is_symlink():
            print(f"Removing existing file/symlink: {target_path}")
            target_path.unlink()
        else:
            print(f"No existing file at: {target_path}")

        if "repo_id" in model:
            # Use HF Hub download for repo_id models
            repo_id = model["repo_id"]
            filename = model["filename"]

            print(f"Downloading {repo_id}/{filename}...")

            # Download the model to cache
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                cache_dir="/cache",
            )

                        # Resolve the actual file path (HF cache uses symlinks internally)
            actual_file_path = pathlib.Path(downloaded_path).resolve()
            
            
            print(f"Downloaded to: {downloaded_path}")
            print(f"Resolved to: {actual_file_path}")
            print(f"Creating symlink: {target_path} -> {actual_file_path}")
            
            # Create symlink to the actual file
            try:
                subprocess.run(
                    f"ln -s {actual_file_path} {target_path}",
                    shell=True,
                    check=True,
                )
                print(f"✓ Successfully created symlink: {target_path} -> {actual_file_path}")
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to create symlink: {e}")
                raise

        elif "url" in model:
            # Fallback to regular HTTP download for URL models
            url = model["url"]
            # Fix blob URLs to resolve URLs
            if "/blob/" in url:
                url = url.replace("/blob/", "/resolve/")

            print(f"Downloading {url}...")

            with httpx.stream("GET", url, follow_redirects=True) as stream:
                total = int(stream.headers.get("Content-Length", 0))
                with open(target_path, "wb") as f, tqdm(
                    total=total, unit_scale=True, unit_divisor=1024, unit="B"
                ) as progress:
                    num_bytes_downloaded = stream.num_bytes_downloaded
                    for data in stream.iter_bytes():
                        f.write(data)
                        progress.update(stream.num_bytes_downloaded - num_bytes_downloaded)
                        num_bytes_downloaded = stream.num_bytes_downloaded

            print(f"Downloaded {url} -> {target_path}")
        else:
            print(f"Warning: Model {model} has neither repo_id nor url, skipping...")


def download_checkpoints():
    """Legacy function - use hf_download() for better performance."""
    import httpx
    from tqdm import tqdm

    for model in MODELS:
        # For backward compatibility, construct URL from repo_id and filename
        if "repo_id" in model:
            url = f"https://huggingface.co/{model['repo_id']}/resolve/main/{model['filename']}"
        else:
            url = model["url"]
        
        local_filename = model["local_filename"] if "local_filename" in model else model["filename"]
        
        local_filepath = pathlib.Path(model["directory"], local_filename)
        local_filepath.parent.mkdir(parents=True, exist_ok=True)

        print(f"downloading {url} ...")
        with httpx.stream("GET", url, follow_redirects=True) as stream:
            total = int(stream.headers["Content-Length"])
            with open(local_filepath, "wb") as f, tqdm(
                total=total, unit_scale=True, unit_divisor=1024, unit="B"
            ) as progress:
                num_bytes_downloaded = stream.num_bytes_downloaded
                for data in stream.iter_bytes():
                    f.write(data)
                    progress.update(stream.num_bytes_downloaded - num_bytes_downloaded)
                    num_bytes_downloaded = stream.num_bytes_downloaded
