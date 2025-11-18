
****Virtual environment****

        To create a virtual environment, decide upon a directory where you want to place it, and run the venv module as a script with the directory path:
python -m venv tutorial-env

    То асtivate on Windows, run:
tutorial-env\Scripts\activate

    To deactivate a virtual environment, type in terminal:

deactivate


<!-- ****Requirements**** -->

    Creating requirements.txt

pip freeze > requirements.txt
<!--  -->
    Installing dependensies

pip install -r requirements.txt


***To Do:***
- admin functioning for leetcode app
- check reset password via email functionality
- static files attach to amvera data storage
- newer C++ version (check that 17 using)
- Linux


Uvicorn
Option 1: Using the Python script
python run_uvicorn.py
Option 3: Direct Uvicorn command
uvicorn mysite.asgi:application --host 127.0.0.1 --port 8000 --reload

Uvicorn doesnt working with django debug toolbar

admin   1q2w
Millyvolt   1q2w3e4r

PowerShell policy fix when .ps1 doesnt running
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

***Ideas for site:***
- russian version of site
- coworking pages (private or not)
- users making new polls


Workout
    resume session
    session end not so scary



Implementation complete
1. Added PostgreSQL driver
Added psycopg2-binary==2.9.9 to requirements.txt
2. Updated database configuration
Modified mysite/settings.py to support PostgreSQL via environment variables
Supports DATABASE_URL connection string (common in cloud platforms)
Also supports individual variables: DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
Automatically falls back to SQLite for local development when no PostgreSQL variables are set
Handles both postgres:// and postgresql:// URL formats
3. Cache configuration
No changes needed — database cache works with PostgreSQL
Cache invalidation code remains the same
4. Created migration guide
Created POSTGRESQL_MIGRATION.md with:
Step-by-step setup instructions for Amvera
Environment variable configuration
Data migration steps (if needed)
Troubleshooting tips
How it works
Local development:
No DATABASE_URL → Uses SQLite (as before)
No changes needed for local work
Production (Amvera):
Set DATABASE_URL → Automatically uses PostgreSQL
Solves "database is locked" errors
Better performance and concurrency
Next steps for deployment
Add PostgreSQL service in Amvera dashboard
Set DATABASE_URL environment variable in Amvera project settings
Deploy the application
Run migrations: python manage.py migrate
Create cache table: python manage.py createcachetable
The application will automatically detect and use PostgreSQL in production while keeping SQLite for local development.