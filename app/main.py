from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy import select, cast, String, or_, func
from app.db.database import get_db
from app.models.module import UserLog
from app.models.schemas import UserLogCreate
from sqlalchemy.exc import IntegrityError
import ipaddress
import random
from ipaddress import IPv4Address

# from sqlalchemy import insert
# from database import get_db
# from models import UserLog

app = FastAPI()


# get user detais by ID
@app.get("/user_logs/{log_id}")
async def get_user_log(log_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserLog).where(UserLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="user not mapped")
    return log


# methord 1
@app.get("/users_ip/{partial_ip:path}")
async def get_user_ip(partial_ip: str, db: AsyncSession = Depends(get_db)):
    #  return (partial_ip)

    result = await db.execute(
        select(UserLog).where(
            or_(
                UserLog.ip_address.op("<<=")(func.safe_inet_cast(partial_ip)),
                func.host(UserLog.ip_address).ilike(f"%{partial_ip}%"),
            )
        )
    )
    logs = result.scalars().all()
    if not logs:
        raise HTTPException(status_code=404, detail="No matching IP addresses found")
    return logs


# methord 2
@app.get("/v2/users_ip/{partial_ip:path}")
async def get_user_ip_v2(partial_ip: str, db: AsyncSession = Depends(get_db)):

    if is_subnet(partial_ip):
        result = await db.execute(
            select(UserLog).where(
                UserLog.ip_address.op("<<=")(func.safe_inet_cast(partial_ip))
            )
        )
    else:
        result = await db.execute(
            select(UserLog).where(
                func.host(UserLog.ip_address).ilike(f"%{partial_ip}%")
            )
        )

    logs = result.scalars().all()
    if not logs:
        raise HTTPException(status_code=404, detail="No 2 matching IP addresses found")
    return logs


# fetches all the data in the db
@app.post("/create_user_log")
async def create_user_log(payload: UserLogCreate, db: AsyncSession = Depends(get_db)):
    new_entry = UserLog(
        user_id=payload.user_id,
        ip_address=str(payload.ip_address),
    )
    db.add(new_entry)

    try:
        await db.commit()
        await db.refresh(new_entry)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="This IP address already exists")

    return {
        "message": "Entry created successfully",
        "data": {
            "id": new_entry.id,
            "user_id": new_entry.user_id,
            "ip_address": new_entry.ip_address,
        },
    }


def is_subnet(ip_str: str) -> bool:
    try:
        # Check if it has a slash (e.g., "192.168.1.0/24")
        if "/" in ip_str:
            # strict=False allows treating "192.168.1.5/24" as a valid subnet
            ipaddress.ip_network(ip_str, strict=False)
            return True
        return False
    except ValueError:
        # Not a valid IP or subnet format at all
        return False


# @app.post("/seed/user_logs")
# async def seed_user_logs(count: int = 50000, db: AsyncSession = Depends(get_db)):
#     if count > 4_000_000_000:
#         raise HTTPException(
#             status_code=400, detail="Count exceeds available IPv4 space"
#         )

#     # Generate `count` unique random 32-bit ints, then convert to IPv4 strings.
#     # random.sample on a range is memory-efficient — doesn't materialize the whole range.
#     ip_ints = random.sample(range(1, 2**32 - 1), count)

#     records = [
#         {
#             "user_id": random.randint(
#                 1, 1000
#             ),  # assumes user_ids 1-1000 exist if FK is set
#             "ip_address": str(IPv4Address(ip_int)),
#         }
#         for ip_int in ip_ints
#     ]

#     # Bulk insert in batches to avoid one giant statement
#     batch_size = 5000
#     for i in range(0, len(records), batch_size):
#         batch = records[i : i + batch_size]
#         await db.execute(insert(UserLog), batch)
#         await db.commit()

#     return {"inserted": count}
