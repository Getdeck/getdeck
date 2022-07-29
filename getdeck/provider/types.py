from enum import Enum


class ProviderType(Enum):
    K3D = "k3d"
    KUBECTLCTX = "kubectlctx"
    KIND = "kind"
    BEIBOOT = "beiboot"
