from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    cuisine: Mapped[str] = mapped_column(String(120), nullable=False, default="Unknown")
    prep_time: Mapped[str] = mapped_column(String(80), nullable=False, default="Unknown")
    cook_time: Mapped[str] = mapped_column(String(80), nullable=False, default="Unknown")
    total_time: Mapped[str] = mapped_column(String(80), nullable=False, default="Unknown")
    servings: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, default="easy")
    ingredients: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    instructions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    nutrition_estimate: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    substitutions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    shopping_list: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    related_recipes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
