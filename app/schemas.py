from pydantic import BaseModel, field_validator, ConfigDict
import re

class PlasticQuantities(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rigid_plastic: float
    flexible_plastic: float
    multilayer_plastic: float

    @field_validator("*")
    @classmethod
    def validate_non_negative(cls, value):
        if value < 0:
            raise ValueError("Quantity cannot be negative")
        return value

class SubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    producer_id: str
    month: str
    declared_quantities_kg: PlasticQuantities

    @field_validator("month")
    @classmethod
    def validate_month(cls, value):
        if not re.match(r"^\d{4}-\d{2}$", value):
            raise ValueError("Month must be in YYYY-MM format")
        return value

class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    question: str