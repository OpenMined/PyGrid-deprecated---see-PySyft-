import redis
import syft as sy

from typing import Union

from syft.serde import serialize, deserialize
from syft.generic.frameworks.types import FrameworkTensorType
from syft.generic.tensor import AbstractTensor
from syft.generic.object_storage import ObjectStorage

redis_db = None

def set_db_instance(database_url):
    global redis_db
    redis_db = redis.from_url(database_url)
    return redis_db

def get_db_instance():
    global redis_db
    return redis_db
