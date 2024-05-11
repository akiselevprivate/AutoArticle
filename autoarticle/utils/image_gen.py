from replicate import Client
from settings.settings import settings
from settings.logger import logger
from settings import prompts
from PIL import Image


client = Client(api_token=settings.REPLICATE_API_TOKEN)


def generate_image(image_description: str):
    prompt = prompts.IMAGE_GENERATION.replace(r"{image_description}", image_description)
    for _ in range(3):
        try:
            output = client.run(
                settings.IMAGE_MODEL,
                input={
                    "width": settings.IMAGE_WIDTH,
                    "height": settings.IMAGE_HEIGHT,
                    "prompt": prompt,
                    "refine": "expert_ensemble_refiner",
                    "scheduler": "K_EULER_ANCESTRAL",
                    "lora_scale": 0.6,
                    "num_outputs": 1,
                    "guidance_scale": 7.5,
                    "apply_watermark": False,
                    "high_noise_frac": 0.8,
                    "negative_prompt": settings.IMAGE_NEGATIVE_PROMPT,
                    "prompt_strength": 0.8,
                    "num_inference_steps": settings.IMAGE_INFERENCE_STEPS,
                    "disable_safety_checker": True,
                },
            )
            return output[0]
        except Exception as e:
            logger.error(f"Image generation error: {repr(e)}")

    raise Exception("Too many retries of image generation")


def generate_upscale(image_url: str):
    output = client.run(
        "nightmareai/real-esrgan:42fed1c4974146d4d2414e2be2c5277c7fcf05fcc3a73abf41610695738c1d7b",
        input={
            "image": image_url,
            "scale": settings.UPSCALE_STEPS,
            "face_enhance": False,
        },
    )
    return output


def compress_convert_image(image_path: str, save_path: str):
    image = Image.open(image_path)
    image.save(save_path, "webp", optimize=True, quality=90)
