# llm_client.py

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import io

# Schemas are needed to type hint and structure our function's inputs
from schemas import Vehicle, HistoryTurn

# Load environment variables from our .env file
load_dotenv()

# --- Configuration ---
# Configure the Google AI client with our API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# --- Constants ---
# Define the LLM model we want to use
MODEL_NAME = "gemini-2.5-flash" 

# This is our master prompt. It's the "brain" of our application.
SYSTEM_PROMPT = """
You are an expert vehicle diagnostic assistant for a mobile app.
Your user is a "Complete Novice" with no car knowledge.
Your tone must be helpful, reassuring, and use simple, easy-to-understand language.
You will reference the most current knowledge for the operating parameters, concepts, and basic systems of internal combustion vehicles.
You will think carefully about the symptoms of the user's reported vehicle issues and the potential interconnectedness of various systems in the vehicle.
For example: Lack of power could be a vehicle computer issuing limp mode due to a sensor failure, or it could be a transmission that is too low on fluid or is expereincing wear issues.

Your primary goal is to provide a diagnosis based on the user's description.
You MUST respond with a single, valid JSON object that strictly follows this format and NOTHING else:
{
  "potential_problems": [
    {"name": "string", "description": "string"}
  ],
  "severity": {
    "level": "CRITICAL" | "CAUTION" | "INFORMATION",
    "message": "string"
  },
  "next_steps": ["string"],
  "estimated_cost": {
    "range": "string",
    "disclaimer": "This is a rough estimate for reference only. Actual costs may vary."
  },
  "disclaimers": ["string"]
}

The user's vehicle information and the conversation history will be provided.
Analyze them and generate your JSON response. Do not add any text before or after the JSON object.
"""

# --- Client Function via Text ---
def get_diagnostic_from_llm(vehicle: Vehicle, history: list[HistoryTurn]) -> dict:
    """
    Sends the vehicle info and conversation history to the LLM and gets a structured
    JSON diagnosis back.
    """
    # 1. Instantiate the model
    model = genai.GenerativeModel(MODEL_NAME, system_instruction=SYSTEM_PROMPT)
    
    # 2. Format the user's conversation history into a single string for the prompt
    chat_history_str = "\n".join([f"{turn.role}: {turn.content}" for turn in history])
    user_prompt = f"""
    Vehicle: {vehicle.year} {vehicle.make} {vehicle.model}
    Conversation History:
    {chat_history_str}
    """
    
    # 3. Call the LLM
    print("--- Sending prompt to LLM ---")
    response = model.generate_content(user_prompt)
    print("--- Received response from LLM ---")
    
    # 4. Extract and parse the JSON response
    try:
        # The LLM response might have markdown ```json ... ``` around it
        raw_json = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw_json)
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error parsing LLM response: {e}")
        # If the LLM fails to return valid JSON, we return an error structure
        return {
            "error": "The diagnostic assistant failed to generate a valid response. Please try again."
        }
    
# --- Function for Image Diagnosis ---
def get_image_diagnostic_from_llm(vehicle: Vehicle, user_prompt: str, image_bytes: bytes) -> dict:
    """
    Sends vehicle info, a text prompt, and an image to the LLM and gets a structured
    JSON diagnosis back.
    """
    # 1. Instantiate the model. We can use the same system prompt to enforce JSON output.
    model = genai.GenerativeModel(MODEL_NAME, system_instruction=SYSTEM_PROMPT)

    # 2. Open the image from the raw bytes data
    image = Image.open(io.BytesIO(image_bytes))

    # 3. Construct the prompt. The library expects a list containing text and images.
    full_prompt = [
        f"Vehicle: {vehicle.year} {vehicle.make} {vehicle.model}\n",
        f"User's question: {user_prompt}\n\n",
        "Analyze the attached image and the user's question, then provide a full diagnostic report in the required JSON format.",
        image, # The PIL Image object
    ]

    # 4. Call the LLM
    print("--- Sending image and prompt to LLM ---")
    response = model.generate_content(full_prompt)
    print("--- Received response from LLM ---")

    # 5. Extract and parse the JSON response (same as our other function)
    try:
        raw_json = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw_json)
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error parsing LLM response: {e}")
        return {
            "error": "The diagnostic assistant failed to generate a valid response from the image."
        }
    
# --- Function for VIN Identification ---
def get_vehicle_info_from_image(image_bytes: bytes) -> dict:
    """
    Sends an image of a VIN sticker to the LLM and gets structured vehicle info back.
    """
    # 1. We don't need a complex system prompt here, just a direct instruction.
    vin_system_prompt = """
    You are a vehicle identification expert. Your task is to analyze the provided image,
    which contains a vehicle's information sticker.
    First, find the 17-character Vehicle Identification Number (VIN). It will be alphanumeric and in UPPER CASE
    Second, based on that VIN, determine the vehicle's Make, Model, and Year.
    You MUST respond with a single, valid JSON object that strictly follows this format and NOTHING else:
    {"make": "string", "model": "string", "year": integer}
    """
    model = genai.GenerativeModel(MODEL_NAME, system_instruction=vin_system_prompt)

    # 2. Open the image from the raw bytes data
    image = Image.open(io.BytesIO(image_bytes))

    # 3. Call the LLM with just the image. The system prompt has all the instructions.
    print("--- Sending VIN image to LLM ---")
    response = model.generate_content(image)
    print("--- Received VIN response from LLM ---")

    # 4. Extract and parse the JSON response
    try:
        raw_json = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw_json)
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error parsing LLM response for VIN: {e}")
        return {
            "error": "Could not identify the vehicle from the provided image. Please try again or enter manually."
        }
    
# --- Function for Text-Based Vehicle Identification ---
def get_vehicle_info_from_text(user_text: str) -> dict:
    """
    Sends free-form user text about their vehicle to the LLM and gets
    structured vehicle info back.
    """
    # This prompt is almost identical to the VIN prompt, just with a different input.
    text_system_prompt = """
    You are a vehicle identification expert. Your task is to analyze the provided text.
    Extract the vehicle's Make, Model, and Year from the text.
    You MUST respond with a single, valid JSON object that strictly follows this format and NOTHING else:
    {"make": "string", "model": "string", "year": integer}
    """
    model = genai.GenerativeModel(MODEL_NAME, system_instruction=text_system_prompt)

    print(f"--- Sending vehicle text to LLM: '{user_text}' ---")
    response = model.generate_content(user_text)
    print("--- Received vehicle text response from LLM ---")

    # The rest of this is identical to our other helper functions
    try:
        raw_json = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw_json)
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error parsing LLM response for text: {e}")
        return {
            "error": "Could not identify the vehicle from the provided text. Please try again."
        }