import asyncio
import random
import sys
from ipaddress import IPv4Address
from sqlalchemy import insert

# Updated to use your exact variable names from database.py
from app.db.database import AsyncSessionLocal, engine
from app.models.module import UserLog

# Configuration settings
TOTAL_RECORDS = 50_000
BATCH_SIZE = 5_000


async def seed_user_logs(count: int = TOTAL_RECORDS):
    if count > 4_000_000_000:
        print("Error: Count exceeds available IPv4 space.")
        return

    print(f"Generating {count} unique random IPv4 mappings...")
    ip_ints = random.sample(range(1, 2**32 - 1), count)

    print("Formatting payload dictionaries for database ingestion...")
    records = [
        {
            "user_id": random.randint(1, 1000),
            "ip_address": str(IPv4Address(ip_int)),
        }
        for ip_int in ip_ints
    ]

    print(f"Opening async transaction context...")
    # Used AsyncSessionLocal() to match your factory function
    async with AsyncSessionLocal() as session:
        try:
            for i in range(0, len(records), BATCH_SIZE):
                batch = records[i : i + BATCH_SIZE]

                # Execute optimized bulk insert
                await session.execute(insert(UserLog), batch)
                await session.commit()
                print(
                    f"Successfully committed batch {i // BATCH_SIZE + 1}: Records {i} to {i + len(batch)}"
                )

            print(
                f"\n🎉 Database seeding absolute success! {count} total rows inserted."
            )

        except Exception as e:
            await session.rollback()
            print(f"\n❌ Transaction error encountered: {e}")
            sys.exit(1)


async def main():
    await seed_user_logs()
    # Safely close down the engine pool connections when done
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
