from pydantic import BaseModel, IPvAnyAddress


class UserLogCreate(BaseModel):
    user_id: int
    ip_address: str
