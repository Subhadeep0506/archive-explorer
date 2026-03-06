from enum import Enum


class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"


class DomainEnum(str, Enum):
    marketing = "Marketing"
    finance = "Finance"
    legal = "Legal"
    insurance = "Insurance"
    technology = "Technology"
    industrial = "Industrial"
    healthcare = "Healthcare"
    education = "Education"
    automobile = "Automobile"
    agriculture = "Agriculture"
    telecommunications = "Telecommunications"
    manufacturing = "Manufacturing"
    media = "Media"


class ReproducibilityEnum(str, Enum):
    reproducable = "Reproducible"
    reapplicable = "Reapplicable"


class EmergingTechEnum(str, Enum):
    machine_learning = "Machine Learning"
    deep_learning = "Deep Learning"
    computer_vision = "Computer Vision"
    nlp = "Natural Language Processing"
    llms = "LLMs"
    vlms = "VLMs"
    rag = "RAG"
    agentic_ai = "Agentic AI"
    multimodal_ai = "Multimodal AI"
    cloud_computing = "Cloud Computing"
    observability = "Observability"
    cybersecurity = "Cybersecurity"
    reinforcement_learning = "Reinforcement Learning"
    robotics = "Robotics"


class ServiceType(str, Enum):
    WEB_SEARCH = "web_search"
    WEB_SCRAPE = "web_scrape"
    LLM = "llm"
    EMBEDDING = "embedding"
    RERANK = "rerank"
    VECTOR_STORE = "vector_store"


class PaperSourceEnum(str, Enum):
    ARXIV = "arxiv"
    USER_UPLOAD = "user_upload"
    OTHER = "other"
