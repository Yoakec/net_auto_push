from pydantic import BaseModel
from typing import Optional, List


class Device(BaseModel):
    ip: str
    type: str
    username: str
    password: str
    protocol: str = "ssh"
    port: int = 22
    area: str = ""
    encode: str = "utf-8"


class DeviceResponse(BaseModel):
    ip: str
    type: str
    username: str
    protocol: str
    port: int
    area: str
    encode: str


class ExecuteRequest(BaseModel):
    device_ips: List[str]
    commands: List[str]
    max_concurrent: int = 5


class SnippetItem(BaseModel):
    command: str
    category: str = ""
