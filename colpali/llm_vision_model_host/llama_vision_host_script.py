import litserve as ls
import transformers
from transformers import MllamaForConditionalGeneration, AutoProcessor
import requests
from PIL import Image
import torch
from huggingface_hub import HfFolder
import base64
from io import BytesIO

def login_to_hf(token):
    HfFolder.save_token(token)

class Llama3VisionAPI(ls.LitAPI):
    def setup(self, device):
        model_id = "meta-llama/Llama-3.2-11B-Vision-Instruct"

        self.model = MllamaForConditionalGeneration.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        self.processor = AutoProcessor.from_pretrained(model_id)

    def decode_request(self, request):
        return request["image_base64"], request["user_query"]


    def predict(self, image_base64, user_query):
        image_data = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_data))

        messages = [
            {"role": "user", "content": [
                {"type": "image"},
                {"type": "text", "text": user_query}
            ]}
        ]
        input_text = self.processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = self.processor(image, input_text, return_tensors="pt").to(self.model.device)

        self.output = self.model.generate(**inputs, max_new_tokens=30)

    def encode_response(self, output):
        return {"output": self.processor.decode(output[0])}


if __name__ == "__main__":
    # Hugging Face token
    HF_TOKEN = "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"
    
    # Log in to Hugging Face
    login_to_hf(HF_TOKEN)

    server = ls.LitServer(Llama3VisionAPI(), accelerator="auto", max_batch_size=1)
    server.run(port=8000)