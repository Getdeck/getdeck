from enum import Enum


class ProviderType(Enum):
    K3D = "k3d"
    KUBECTLCTX = "KubectlCtx"
    KIND = "kind"
    BEIBOOT = "beiboot"
