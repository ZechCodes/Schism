from nubby import ConfigModel
from pydantic import BaseModel


class SchismConfigModel(BaseModel, ConfigModel):
    def to_dict(self):
        return self.model_dump()
