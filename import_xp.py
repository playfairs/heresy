import json
from database import db_manager

# XP data
xp_data = {
    "785042666475225109": 718968,
    "757355424621133914": 460,
    "1255320442894290954": 4,
    "740990115761094697": 844,
    "944298361073315870": 125,
    "1252011606687350805": 32,
    "920464444558028811": 286,
    "1286708426252226742": 95,
    "1138502259106381984": 29,
    "938889096804319303": 0,
    "812606857742647298": 83,
    "1160236117363273738": 118,
    "767848573445341244": 5,
    "926665802957066291": 72,
    "1217425775309881364": 5,
    "989251076073086986": 30,
    "1280027736152346742": 20
}

def import_xp_data():
    """Import XP data into the database."""
    for user_id, xp in xp_data.items():
        try:
            # Calculate level based on XP
            level = db_manager.calculate_level(xp)
            
            # Get a database session
            session = db_manager.get_session()
            
            # Check if user already exists
            from database import UserXP
            existing_user = session.query(UserXP).filter_by(user_id=user_id).first()
            
            if existing_user:
                # Update existing user
                existing_user.xp = xp
                existing_user.level = level
            else:
                # Create new user
                new_user = UserXP(user_id=user_id, xp=xp, level=level)
                session.add(new_user)
            
            # Commit changes
            session.commit()
            print(f"Imported XP for user {user_id}: {xp} XP (Level {level})")
        
        except Exception as e:
            print(f"Error importing XP for user {user_id}: {e}")
            session.rollback()
        finally:
            session.close()

if __name__ == "__main__":
    import_xp_data()
