# schemas.py

# 1. Import necessary components from pydantic and typing
from pydantic import BaseModel
from typing import List, Literal # Literal is used for specific string values

# --- Reusable Sub-Models ---
# These are building blocks for our main models

class Vehicle(BaseModel):
    make: str
    model: str
    year: int

class Problem(BaseModel):
    name: str
    description: str

class Severity(BaseModel):
    level: Literal["CRITICAL", "CAUTION", "INFORMATION"] # Enforces these exact strings
    message: str

class EstimatedCost(BaseModel):
    range: str
    disclaimer: str

class HistoryTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


# --- Request Models (Client -> Backend) ---
# What we expect to receive from the mobile app

class ConversationTurnRequest(BaseModel):
    vehicle: Vehicle
    history: List[HistoryTurn]

class VehicleTextRequest(BaseModel):
    query: str

# --- Response Models (Backend -> Client) ---
# What our API will send back to the mobile app

class DiagnosticReportResponse(BaseModel):
    potential_problems: List[Problem]
    severity: Severity
    next_steps: List[str]
    estimated_cost: EstimatedCost
    disclaimers: List[str] # A list of optional disclaimers

class ErrorResponse(BaseModel):
    error: str