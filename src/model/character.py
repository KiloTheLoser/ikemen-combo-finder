from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from src.model.move import Move

class Character(BaseModel):
    name: str = Field(..., description="Character folder or internal name")
    character_path: Path = Field(..., description="Absolute or relative path to character directory")
    moves: List[Move] = Field(default_factory=list, description="List of recognized moves and commands")

    class Config:
        arbitrary_types_allowed = True