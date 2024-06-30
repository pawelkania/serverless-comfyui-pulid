import pathlib
import random
from typing import Any, Dict, Mapping, Sequence, Union


def get_value_at_index(obj: Union[Sequence, Mapping], index: int) -> Any:
    try:
        return obj[index]
    except KeyError:
        return obj["result"][index]


def download_image(url: str, filename: str, save_path="input/"):
    import requests

    try:
        response = requests.get(url)
        response.raise_for_status()
        pathlib.Path(save_path + filename).write_bytes(response.content)
        print(f"{url} image successfully downloaded")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url} image: {e}")


def run_python_workflow(item: Dict):
    import torch
    from nodes import (
        NODE_CLASS_MAPPINGS,
        EmptyLatentImage,
        LoadImage,
        VAEDecode,
        CheckpointLoaderSimple,
        KSampler,
        SaveImage,
        CLIPTextEncode,
    )

    result = None
    with torch.inference_mode():
        loadimage = LoadImage()
        loadimage_1 = loadimage.load_image(image=item["filename"])

        checkpointloadersimple = CheckpointLoaderSimple()
        checkpointloadersimple_5 = checkpointloadersimple.load_checkpoint(
            ckpt_name="dreamshaperXL_alpha2Xl10.safetensors"
        )

        cliptextencode = CLIPTextEncode()
        cliptextencode_9 = cliptextencode.encode(
            text="((Fully Clothed))" + item["prompt"],
            clip=get_value_at_index(checkpointloadersimple_5, 1),
        )

        cliptextencode_10 = cliptextencode.encode(
            text="(((NUDE, NAKED, Naked, NSFW))) drawing, cartoon, low quality, ugly,over-saturated, covered face, masked face, sunglasses, deformed, blurred background",
            clip=get_value_at_index(checkpointloadersimple_5, 1),
        )

        emptylatentimage = EmptyLatentImage()
        emptylatentimage_12 = emptylatentimage.generate(
            width=1024, height=1024, batch_size=1
        )

        midas_depthmappreprocessor = NODE_CLASS_MAPPINGS["MiDaS-DepthMapPreprocessor"]()
        openposepreprocessor = NODE_CLASS_MAPPINGS["OpenposePreprocessor"]()
        cr_multi_controlnet_stack = NODE_CLASS_MAPPINGS["CR Multi-ControlNet Stack"]()
        apply_controlnet_stack = NODE_CLASS_MAPPINGS["Apply ControlNet Stack"]()
        ksampler = KSampler()
        vaedecode = VAEDecode()
        reactorfaceswap = NODE_CLASS_MAPPINGS["ReActorFaceSwap"]()
        saveimage = SaveImage()

        midas_depthmappreprocessor_43 = midas_depthmappreprocessor.execute(
            a=6.28,
            bg_threshold=0.1,
            resolution=512,
            image=get_value_at_index(loadimage_1, 0),
        )
        openposepreprocessor_46 = openposepreprocessor.estimate_pose(
            detect_hand="enable",
            detect_body="enable",
            detect_face="enable",
            resolution=512,
            image=get_value_at_index(loadimage_1, 0),
        )
        cr_multi_controlnet_stack_45 = cr_multi_controlnet_stack.controlnet_stacker(
            switch_1="On",
            controlnet_1="control-lora-openposeXL2-rank256.safetensors",
            controlnet_strength_1=0.8,
            start_percent_1=0,
            end_percent_1=1,
            switch_2="On",
            controlnet_2="control-lora-depth-rank256.safetensors",
            controlnet_strength_2=0.6,
            start_percent_2=0,
            end_percent_2=1,
            switch_3="Off",
            controlnet_3="None",
            controlnet_strength_3=1,
            start_percent_3=0,
            end_percent_3=1,
            image_1=get_value_at_index(openposepreprocessor_46, 0),
            image_2=get_value_at_index(midas_depthmappreprocessor_43, 0),
        )
        apply_controlnet_stack_53 = apply_controlnet_stack.apply_cnet_stack(
            positive=get_value_at_index(cliptextencode_9, 0),
            negative=get_value_at_index(cliptextencode_10, 0),
            cnet_stack=get_value_at_index(cr_multi_controlnet_stack_45, 0),
        )
        ksampler_11 = ksampler.sample(
            seed=random.randint(1, 2**64),
            steps=22,
            cfg=7,
            sampler_name="dpm_2_ancestral",
            scheduler="normal",
            denoise=1,
            model=get_value_at_index(checkpointloadersimple_5, 0),
            positive=get_value_at_index(apply_controlnet_stack_53, 0),
            negative=get_value_at_index(apply_controlnet_stack_53, 1),
            latent_image=get_value_at_index(emptylatentimage_12, 0),
        )
        vaedecode_15 = vaedecode.decode(
            samples=get_value_at_index(ksampler_11, 0),
            vae=get_value_at_index(checkpointloadersimple_5, 2),
        )
        reactorfaceswap_21 = reactorfaceswap.execute(
            enabled=True,
            swap_model="inswapper_128.onnx",
            facedetection="YOLOv5l",
            face_restore_model="codeformer-v0.1.0.pth",
            face_restore_visibility=1,
            codeformer_weight=0.5,
            detect_gender_input="no",
            detect_gender_source="no",
            input_faces_index="0,1,2,3,4",
            source_faces_index="0,1,2,3,4",
            console_log_level=1,
            input_image=get_value_at_index(vaedecode_15, 0),
            source_image=get_value_at_index(loadimage_1, 0),
        )
        saveimage_16 = saveimage.save_images(
            filename_prefix="ComfyUI",
            images=get_value_at_index(reactorfaceswap_21, 0),
        )

        result = saveimage_16

    return result
