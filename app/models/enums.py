from enum import Enum


class Round(str, Enum):
    JEOPARDY = "Jeopardy!"
    DOUBLE_JEOPARDY = "Double Jeopardy!"
    FINAL_JEOPARDY = "Final Jeopardy!"


class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"