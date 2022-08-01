from typing import List

from pydantic import BaseModel


class K8sSourceFile(BaseModel):
    name: str
    namespace: str
    content: dict


class GeneratedDeck(BaseModel):
    name: str
    namespace: str
    files: List[K8sSourceFile]
