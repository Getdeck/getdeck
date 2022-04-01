from enum import Enum
from typing import Optional

from pydantic.main import BaseModel


class K8sProviderType(Enum):
    k3d = "k3d"
    kubectlctx = "KubectlCtx"


class K8sProviderData(BaseModel):
    id: str
    name: Optional[str] = None
