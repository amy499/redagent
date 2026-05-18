from dotenv import load_dotenv
load_dotenv()

from db.seed import seed_db

attacks, targets, settings = seed_db()
print("Database seeded successfully.")
print(f"  attacks:  {attacks}")
print(f"  targets:  {targets}")
print(f"  settings: {settings}")
