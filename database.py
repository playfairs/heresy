import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, JSON, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create base class for declarative models
Base = declarative_base()

class UserXP(Base):
    __tablename__ = 'user_xp'
    
    user_id = Column(String, primary_key=True)
    xp = Column(Integer, default=0)
    level = Column(Integer, default=0)

class UserDino(Base):
    __tablename__ = 'user_dinos'
    
    user_id = Column(String, primary_key=True)
    dino_name = Column(String, default='Diplodoculus')
    dino_level = Column(Integer, default=0)

class UserBirthday(Base):
    __tablename__ = 'user_birthdays'
    
    user_id = Column(String, primary_key=True)
    birthday = Column(Date, nullable=False)

    def __repr__(self):
        return f"<UserBirthday(user_id={self.user_id}, birthday={self.birthday})>"

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'is_initialized'):
            self.initialize_database()
            self.is_initialized = True

    def initialize_database(self):
        # Try multiple connection strategies
        connection_strategies = [
            os.getenv('DATABASE_URL', 'postgresql://localhost/hersey_bot'),
            'postgresql://localhost/postgres',  # Fallback to default postgres DB
            'postgresql://localhost',  # Minimal connection string
        ]

        for db_url in connection_strategies:
            try:
                logger.info(f"Attempting to connect to database with URL: {db_url}")
                self.engine = create_engine(
                    db_url, 
                    echo=True,  # Log all SQL statements for debugging
                    pool_pre_ping=True,  # Test connection before using
                    pool_recycle=3600  # Recycle connections after 1 hour
                )
                
                # Create a scoped session factory
                self.session_factory = sessionmaker(bind=self.engine)
                self.Session = scoped_session(self.session_factory)

                # Create all tables
                Base.metadata.create_all(self.engine)
                logger.info("Database connection successful!")
                return
            except Exception as e:
                logger.warning(f"Connection failed with URL {db_url}: {e}")
        
        # If all connection strategies fail
        logger.error("Could not establish database connection. Please check your PostgreSQL setup.")
        sys.exit(1)

    def get_session(self):
        """Get a database session."""
        return self.Session()

    def add_xp(self, user_id, xp_amount):
        """Adds XP to a user."""
        session = self.get_session()
        try:
            user = session.query(UserXP).filter_by(user_id=str(user_id)).first()
            if not user:
                user = UserXP(user_id=str(user_id), xp=0)
                session.add(user)
            
            user.xp += xp_amount
            user.level = self.calculate_level(user.xp)
            session.commit()
            return user.xp, user.level
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding XP: {e}")
            raise
        finally:
            session.close()

    def get_xp(self, user_id):
        """Gets a user's XP."""
        session = self.get_session()
        try:
            user = session.query(UserXP).filter_by(user_id=str(user_id)).first()
            return user.xp if user else 0
        finally:
            session.close()

    def calculate_level(self, xp):
        """Calculates level based on XP."""
        level = 0
        while xp >= ((level + 1) ** 2) * 50:
            level += 1
        return level

    def add_dino(self, user_id, dino_name='Diplodoculus'):
        """Adds or updates a user's Diplodocus."""
        session = self.get_session()
        try:
            user_dino = session.query(UserDino).filter_by(user_id=str(user_id)).first()
            if not user_dino:
                user_dino = UserDino(user_id=str(user_id), dino_name=dino_name)
                session.add(user_dino)
            else:
                user_dino.dino_name = dino_name
            
            session.commit()
            return user_dino
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding dino: {e}")
            raise
        finally:
            session.close()

    def get_dino(self, user_id):
        """Gets a user's Diplodocus."""
        session = self.get_session()
        try:
            return session.query(UserDino).filter_by(user_id=str(user_id)).first()
        finally:
            session.close()

    def get_all_dinos(self):
        """Gets all Diplodocus."""
        session = self.get_session()
        try:
            return session.query(UserDino).all()
        finally:
            session.close()

    def set_birthday(self, user_id, birthday):
        """Set or update a user's birthday."""
        session = self.get_session()
        try:
            # Check if birthday already exists
            user_birthday = session.query(UserBirthday).filter_by(user_id=str(user_id)).first()
            
            if user_birthday:
                # Update existing birthday
                user_birthday.birthday = birthday
            else:
                # Create new birthday entry
                user_birthday = UserBirthday(user_id=str(user_id), birthday=birthday)
                session.add(user_birthday)
            
            session.commit()
            return user_birthday
        except Exception as e:
            session.rollback()
            logger.error(f"Error setting birthday: {e}")
            raise
        finally:
            session.close()

    def get_birthday(self, user_id):
        """Retrieve a user's birthday."""
        session = self.get_session()
        try:
            user_birthday = session.query(UserBirthday).filter_by(user_id=str(user_id)).first()
            return user_birthday.birthday if user_birthday else None
        finally:
            session.close()

    def get_all_birthdays(self):
        """Retrieve all user birthdays."""
        session = self.get_session()
        try:
            return session.query(UserBirthday).all()
        finally:
            session.close()

# Initialize the database manager
db_manager = DatabaseManager()
