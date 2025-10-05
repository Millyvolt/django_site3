
****Virtual environment****

        To create a virtual environment, decide upon a directory where you want to place it, and run the venv module as a script with the directory path:
python -m venv tutorial-env

    То асtivate on Windows, run:
tutorial-env\Scripts\activate

    To deactivate a virtual environment, type in terminal:

deactivate


****Requirements****

    Creating requirements.txt

pip freeze > requirements.txt

    Installing dependensies

pip install -r requirements.txt


****To Do:****
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

Ideas for site:
- russian version of site
- coworking pages (private or not)
- users making new polls