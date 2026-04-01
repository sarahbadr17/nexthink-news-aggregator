from enum import Enum


class ArticleCategory(str, Enum):
    """Predefined categories for classifying articles."""
    CYBER = "Cybersecurity"
    AI = "Artificial Intelligence & Emerging Tech"
    SW = "Software & Development"
    HW = "Hardware & Devices"
    TECH_BSN = "Tech Industry & Business"
    OTHER = "Other"