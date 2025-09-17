from app.database import SessionLocal
from app.models.models import User

# Create a new DB session
db = SessionLocal()

# Delete all users
db.query(User).delete()
db.commit()

print("All users deleted.")
