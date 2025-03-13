from typing_extensions import Self
from pydantic import BaseModel, model_validator, Field, field_validator, ConfigDict
from typing import Literal, Union
import datetime
from enum import Enum

state_abbreviations = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", ""
]

class Sides(Enum):
    PLAINTIFF = "PLAINTIFF"
    DEFENDANT = "DEFENDANT"
    INTERPRETER = 'INTERPRETER'


class SideName(BaseModel):
    type_: Sides = Field(..., alias="type")
    name: str

    model_config = ConfigDict(
        populate_by_name=True,
    )


class SideAddress(SideName):
    address: list[str]
    city: str
    state: Literal[*state_abbreviations]
    zip_: str = Field(..., alias="zip")

    @field_validator('zip_', mode='after')  
    @classmethod
    def is_zip(cls, value: str) -> str:
        if len(value) != 5 or not value.isdigit():
            raise ValueError(f'{value} is not zip code')
        return value  

class FakeAttorney(BaseModel):
    address: Literal[['DO NOT USE']]

class DocketEntry(BaseModel):
    date: datetime.date
    text: str
    extra: str | None = None

class Event(BaseModel):
    room: str
    start: datetime.datetime
    end: datetime.datetime
    event: str
    judge: str
    result: str

class Disposition(BaseModel):
    code: str
    date: datetime.date | None = None
    judge: str
    status: Literal["CLOSED", "OPEN", "REOPEN (RO)"]
    status_date: datetime.date

    @model_validator(mode='after')
    def check_disposition(self) -> Self:
        if self.code != 'UNDISPOSED' and self.date is None:
            raise ValueError('Invalid Disposition')
        return self
    
class Case(BaseModel):
    case_number: str
    parties: list[Union[SideName, SideAddress]]
    docket: list[DocketEntry]
    attorneys: list[SideAddress | FakeAttorney]
    events: list[Event]
    dispositions: list[Disposition]