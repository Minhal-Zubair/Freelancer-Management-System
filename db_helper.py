from app import app, db
from models import *

def verify_database_connection():
    """Test database connection and print table information"""
    with app.app_context():
        try:
            # Check if tables exist
            tables = db.engine.table_names()
            print(f"Tables found in database: {tables}")
            
            # Get all table data counts
            print("\nData counts in tables:")
            for table in tables:
                result = db.engine.execute(f"SELECT COUNT(*) FROM {table}")
                count = result.scalar()
                print(f"  {table}: {count} records")
                
            # Test a basic query
            print("\nTesting a basic query:")
            result = db.engine.execute("SELECT id, name, email FROM freelancer LIMIT 3")
            for row in result:
                print(f"  Freelancer: {row}")
                
            print("\nDatabase connection successful!")
            
        except Exception as e:
            print(f"Error connecting to database: {e}")

if __name__ == "__main__":
    verify_database_connection()