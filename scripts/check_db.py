
from app import app
from extensions import db
from models import User, UserProfile, UserDailyHabits, SimulationRun

with app.app_context():
    user_count = User.query.count()
    profile_count = UserProfile.query.count()
    habits_count = UserDailyHabits.query.count()
    sim_count = SimulationRun.query.count()
    
    print(f"Users: {user_count}")
    print(f"Profiles: {profile_count}")
    print(f"Habits: {habits_count}")
    print(f"Simulations: {sim_count}")

    if user_count == 0:
        print("Creating default user with ID 1...")
        user = User(id=1, email="test@example.com")
        db.session.add(user)
        db.session.commit()
        print("User 1 created.")
