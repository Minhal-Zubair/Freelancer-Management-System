from app import app, db  # noqa: F401
import routes  # noqa: F401
if __name__ == "__main__":
    with app.app_context():
        # Print the tables to verify database connection
        try:
            tables = db.engine.table_names()
            print(f"Connected to database. Available tables: {tables}")
        except Exception as e:
            print(f"Database connection error: {e}")
    
    app.run(debug=True, host="0.0.0.0", port=5000)