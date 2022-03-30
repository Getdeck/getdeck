from typing import List

from pydantic import BaseModel


class K8sSourceFile(BaseModel):
    name: str
    content: dict


class GeneratedDeck(BaseModel):
    files: List[K8sSourceFile]
