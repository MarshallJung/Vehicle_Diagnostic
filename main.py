# main.py

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
# Import our new client function and the schemas it uses
from llm_client import (
    get_diagnostic_from_llm, 
    get_image_diagnostic_from_llm, 
    get_vehicle_info_from_image,
    get_vehicle_info_from_text
)
from schemas import (
    ConversationTurnRequest, 
    DiagnosticReportResponse, 
    ErrorResponse, 
    Vehicle,
    VehicleTextRequest
)

app = FastAPI(
    title="Vehicle Diagnostic Assistant API",
    version="1.0.0"
)

@app.get("/health")
def read_health():
    """Health check endpoint."""
    return {"status": "ok", "message": "API is running!"}

# CORS middleware configuration
origins = [
    "http://localhost",
    "http://localhost:8001", # The origin for our frontend server
    "http://127.0.0.1:8001" # Also add the IP address for good measure
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Allow these specific origins to make requests
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)



@app.post(
    "/diagnose/conversation",
    # Define what success and error responses look like for the docs
    responses={
        200: {"model": DiagnosticReportResponse},
        500: {"model": ErrorResponse}
    }
)
def diagnose_from_conversation(request: ConversationTurnRequest) -> DiagnosticReportResponse:
    """
    Receives conversation history, calls the LLM for a diagnosis,
    and returns the structured report.
    """
    # 1. Call our new function with the data from the request
    llm_result = get_diagnostic_from_llm(request.vehicle, request.history)

    # 2. Check if the LLM client returned an error
    if "error" in llm_result:
        raise HTTPException(
            status_code=500, 
            detail=llm_result["error"]
        )

    # 3. Validate the LLM's output against our Pydantic model.
    # This is a critical safety check! If the LLM's JSON doesn't match
    # our schema, this will raise an error, protecting our mobile client.
    try:
        validated_report = DiagnosticReportResponse(**llm_result)
        return validated_report
    except Exception as e:
        print(f"Failed to validate LLM response: {e}")
        raise HTTPException(
            status_code=500,
            detail="Diagnostic assistant returned a malformed report. Please try again."
        )

# 2. Image diagnosis endpoint
@app.post(
    "/diagnose/image",
    responses={
        200: {"model": DiagnosticReportResponse},
        500: {"model": ErrorResponse}
    }
)
async def diagnose_from_image(
    # FastAPI handles file uploads and form data differently from JSON bodies
    make: str = Form(...),
    model: str = Form(...),
    year: int = Form(...),
    prompt: str = Form(...),
    file: UploadFile = File(...)
) -> DiagnosticReportResponse:
    """
    Receives vehicle info, a text prompt, and an image file.
    Calls the multimodal LLM for a diagnosis and returns a structured report.
    """
    # 1. Read the image data from the uploaded file
    image_bytes = await file.read()
    
    # 2. Structure the vehicle data
    vehicle = Vehicle(make=make, model=model, year=year)

    # 3. Call our new image-aware LLM client function
    llm_result = get_image_diagnostic_from_llm(
        vehicle=vehicle,
        user_prompt=prompt,
        image_bytes=image_bytes
    )

    # 4. Handle errors and validate the response (same logic as before)
    if "error" in llm_result:
        raise HTTPException(
            status_code=500, 
            detail=llm_result["error"]
        )

    try:
        validated_report = DiagnosticReportResponse(**llm_result)
        return validated_report
    except Exception as e:
        print(f"Failed to validate LLM response: {e}")
        raise HTTPException(
            status_code=500,
            detail="Diagnostic assistant returned a malformed report. Please try again."
        )
    
# VIN identification endpoint
@app.post(
    "/vehicle/identify-from-image",
    # This endpoint will return our Vehicle schema on success
    responses={
        200: {"model": Vehicle},
        500: {"model": ErrorResponse}
    }
)
async def identify_vehicle_from_image(file: UploadFile = File(...)) -> Vehicle:
    """
    Receives an image of a vehicle's VIN sticker, uses the LLM to perform
    OCR and decode the VIN, and returns the vehicle's Make, Model, and Year.
    """
    # 1. Read the image data
    image_bytes = await file.read()

    # 2. Call our new LLM client function
    llm_result = get_vehicle_info_from_image(image_bytes)

    # 3. Handle errors
    if "error" in llm_result:
        raise HTTPException(
            status_code=500,
            detail=llm_result["error"]
        )

    # 4. Validate the result against our Vehicle schema and return it
    try:
        validated_vehicle = Vehicle(**llm_result)
        return validated_vehicle
    except Exception as e:
        print(f"Failed to validate vehicle response: {e}")
        raise HTTPException(
            status_code=500,
            detail="The assistant returned malformed vehicle data."
        )
    
@app.post(
    "/vehicle/identify-from-text",
    responses={
        200: {"model": Vehicle},
        500: {"model": ErrorResponse}
    }
)
def identify_vehicle_from_text(request: VehicleTextRequest) -> Vehicle:
    """
    Receives free-form text from a user, uses the LLM to parse it,
    and returns the vehicle's Make, Model, and Year.
    """
    llm_result = get_vehicle_info_from_text(request.query)

    if "error" in llm_result:
        raise HTTPException(status_code=500, detail=llm_result["error"])

    try:
        validated_vehicle = Vehicle(**llm_result)
        return validated_vehicle
    except Exception as e:
        print(f"Failed to validate vehicle response: {e}")
        raise HTTPException(status_code=500, detail="The assistant returned malformed vehicle data.")