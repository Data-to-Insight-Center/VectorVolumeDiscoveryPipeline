# InsightX

*Steps to host LLM vision model on server*
1. Git clone this repo to the server
2. Navigate to the folder llm_vision_models
3. Run this command to install the required packages: pip install -r requirements.txt
4. Execute this command to run the script for hosting the models. We have 2 models: Llama 3.2 vision and Paligemma
   i. Llama 3.2 vision
     python -m uvicorn llama_3_2_vision_host_script.py:app --host 0.0.0.0 --port 8000 --reload

   ii. Paligemma
     python -m uvicorn paligemma_host_script.py:app --host 0.0.0.0 --port 8000 --reload
