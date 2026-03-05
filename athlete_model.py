from pydantic import BaseModel, Field
from typing import List

# --- Modelo Pydantic ---
class SportInfo(BaseModel):
    sport_name: str = Field(..., description="Name of the sport")
    major_achievements: str = Field(..., description="Major achievements in this sport or 'Information not publicly available'")
    paralympic_participation: str = Field(..., description="Paralympic participation in this sport or 'Information not publicly available'")
    participation: str = Field(..., description="Other sports the athlete has participated in or 'Information not publicly available'")
    achievements: str = Field(..., description="Achievements in other sports or 'Information not publicly available'")
    guide: str = Field(..., description="Guide for this sport if applicable, else 'Information not publicly available'")
    performance_trends: str = Field(..., description="Performance trends in this sport or 'Information not publicly available'")
    preparation_style: str = Field(..., description="Training or preparation style specific to this sport or 'Information not publicly available'")
    personal_contextual_info: str = Field(..., description="Personal or contextual info relevant to this sport or 'Information not publicly available'")

class AthleteSummary(BaseModel):
    name_of_the_athlete: str = Field(..., description="Full name of the athlete")
    date_of_birth: str = Field(..., description="Date of birth in YYYY-MM-DD or 'Information not publicly available'")
    gender: str = Field(..., description="Gender of the athlete or 'Information not publicly available'")
    sport_under_study: str = Field(..., description="Sport under study")
    world_cup_rank: int | str = Field(..., description="Current Rank in Word Cup")
    world_cup_points: int | str = Field(..., description="Current Points in Word Cup")

    country: str = Field(..., description="Country of representation or 'Information not publicly available'")
    category: str = Field(..., description="Category in which the athlete participates (sitting/stand/vision)")
    paralympic_category_lw: str = Field(..., description="Category (LW) or 'Information not publicly available'")
    sports: List[SportInfo] = Field(..., description="List of sports the athlete participates in, with detailed info per sport")
    personal_data: str = Field(..., description="Any personal or contextual info, else 'Information not publicly available'")
    reference_urls: List[str] = Field(..., description="List of URLs used to write the article")
