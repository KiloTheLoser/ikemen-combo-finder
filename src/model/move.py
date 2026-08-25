from typing import Optional
from pydantic import BaseModel, Field

class Move(BaseModel):
    name: str = Field(..., description="Name of the command/move")
    command: str = Field(..., description="Input string sequence, e.g., ~D, DF, F, x")
    time: int = Field(default=15, description="Input buffer / execution time window")
    buffer_time: Optional[int] = Field(default=None, description="Optional buffer time")
    
    # New properties to map states and properties
    state_number: Optional[int] = Field(default=None, description="Associated state number triggered by this command")
    move_type: str = Field(default="unknown", description="Move type: normal, special, super, unknown")
    damage: Optional[int] = Field(default=None, description="Base damage if found")
    hitstun: Optional[int] = Field(default=None, description="Hitstun frames if found")
    notes: Optional[str] = Field(default=None, description="Additional context or remarks")