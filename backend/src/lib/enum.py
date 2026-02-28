from enum import Enum


class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"


class DomainEnum(str, Enum):
    marketing = "marketing"
    finance = "finance"
    legal = "legal"
    insurance = "insurance"
    technology = "technology"


class EmergingTechEnum(str, Enum):
    computer_vision = "computer_vision"
    nlp = "nlp"
    agentic_ai = "agentic_ai"
    rag = "rag"
    llms = "llms"
    vlms = "vlms"
    multimodal_ai = "multimodal_ai"
    cloud_computing = "cloud_computing"
    observability = "observability"
    cybersecurity = "cybersecurity"
    machine_learning = "machine_learning"
    deep_learning = "deep_learning"
    reinforcement_learning = "reinforcement_learning"
    robotics = "robotics"
