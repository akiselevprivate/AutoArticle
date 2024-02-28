from replicate import Client
from settings.settings import settings
from settings import prompts

client = Client(api_token=settings.REPLICATE_API_TOKEN)


def generate_image(image_description: str):
    prompt = prompts.IMAGE_GENERATION.replace(r"{image_description}", image_description)
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
        },
    )
    return output[0]
