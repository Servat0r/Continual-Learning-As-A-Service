# Common utils that for imports order require to be defined here.
from __future__ import annotations
from application.utils import get_average_metric, TDesc
from application.resources.datatypes import StandardMetricSet


MNAMES_ORDER: list[str] = [
    'accuracy',
    'loss',
    'forgetting',

    'timing',
    'ram_usage',
    'cpu_usage',
    'disk_usage',
    'gpu_usage',

    'bwt',
    'forward_transfer',
    'MAC',
]


def mnames_order_filter(names: list[str]) -> list[str]:
    mnames_list = MNAMES_ORDER
    canonical: list[str | None] = len(mnames_list) * [None]
    extras: list[str] = []

    for i in range(len(names)):
        name = names[i]
        try:
            idx = mnames_list.index(name)
            canonical[idx] = name
        except ValueError:
            extras.append(name)

    result: list[str] = []
    for i in range(len(canonical)):
        name = canonical[i]
        if name is not None:
            result.append(name)
    result += extras
    return result


# noinspection PyUnusedLocal
def mnames_translations(gpu_id: int = 0, **kwargs):
    return {
        'accuracy': {
            'minibatch': 'Top1_Acc_MB',
            'epoch': 'Top1_Acc_Epoch',
            'experience': 'Top1_Acc_Exp',
            'stream': 'Top1_Acc_Stream',
        },
        'loss': {
            'minibatch': "Loss_MB",
            'epoch': "Loss_Epoch",
            'experience': "Loss_Exp",
            'stream': "Loss_Stream",
        },
        'forgetting': {
            'experience': "ExperienceForgetting",
            'stream': "StreamForgetting",
        },

        'timing': {
            'minibatch': "Time_MB",
            'epoch': "Time_Epoch",
            'experience': "Time_Exp",
            'stream': "Time_Stream",
        },
        'ram_usage': {
            'minibatch': "MaxRAMUsage_MB",
            'epoch': "MaxRAMUsage_Epoch",
            'experience': "MaxRAMUsage_Exp",
            'stream': "MaxRAMUsage_Stream",
        },
        'cpu_usage': {
            'minibatch': "CPUUsage_MB",
            'epoch': "CPUUsage_Epoch",
            'experience': "CPUUsage_Exp",
            'stream': "CPUUsage_Stream",
        },
        'disk_usage': {
            'minibatch': "DiskUsage_MB",
            'epoch': "DiskUsage_Epoch",
            'experience': "DiskUsage_Exp",
            'stream': "DiskUsage_Stream",
        },
        'gpu_usage': {
            'minibatch': f"MaxGPU{gpu_id}Usage_MB",
            'epoch': f"MaxGPU{gpu_id}Usage_Epoch",
            'experience': f"MaxGPU{gpu_id}Usage_Experience",
            'stream': f"MaxGPU{gpu_id}Usage_Stream",
        },

        'bwt': {
            'experience': "ExperienceBWT",
            'stream': "StreamBWT",
        },
        'forward_transfer': {
            'experience': "ExperienceForwardTransfer",
            'stream': "StreamForwardTransfer",
        },
        'MAC': {
            'minibatch': "MAC_MB",
            'epoch': "MAC_Epoch",
            'experience': "MAC_Exp",
        },
    }


__all__ = [
    'MNAMES_ORDER',
    'mnames_order_filter',
    'mnames_translations',
]