from __future__ import annotations

import torch
import io

from application.utils import t, get_device

from application.resources.base import DataType
from application.resources.datatypes import DeployedModel

from application.mongo.resources.mongo_base_configs import *
from .documents import *


@DataType.set_resource_type()
class MongoDeployedModel(DeployedModel):

    @staticmethod
    def config_type() -> t.Type[MongoResourceConfig]:
        return MongoDeployedModelConfig

    @classmethod
    def canonical_typename(cls) -> str:
        return DeployedModel.canonical_typename()

    def get_prediction(self, input_data, transform, mode='plain', **kwargs):
        model = self.get_model()
        if mode == 'plain':
            input_bytes: dict[str, io.BytesIO] = {inp.filename: inp.read() for inp in input_data}
            output_bytes: dict[str, int] = {}
            # input_bytes = [inp.read() for inp in input_data]
            tensors = [transform(item_bytes).unsqueeze(0) for item_bytes in input_bytes.values()]
            device = get_device()
            tensors = [tensor.to(device) for tensor in tensors]
            batch_tensor = torch.stack(tensors)
            batch_tensor = batch_tensor.to(device)
            model.eval()
            outputs: torch.Tensor = model(batch_tensor)
            _, y_hat = outputs.max(1)
            y_hat = y_hat.to('cpu').numpy().astype(int)
            i = 0
            for filename in input_bytes.keys():
                output_bytes[filename] = int(y_hat[i])
                i += 1
            return output_bytes
        elif mode == 'zip':
            return NotImplemented
        else:
            raise ValueError(f"Unknown file transfer mode '{mode}'")


    def __repr__(self):
        return f"{type(self).__name__} ({super().__repr__()})."

    def __str__(self):
        return self.__repr__()


__all__ = [
    'MongoDeployedModel',
]