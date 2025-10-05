
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

- newer C++ version
- dfdf

Uvicorn
Option 1: Using the Python script
python run_uvicorn.py
Option 3: Direct Uvicorn command
uvicorn mysite.asgi:application --host 127.0.0.1 --port 8000 --reload

Uvicorn doesnt working with django debug toolbar

admin   1q2w

Ideas for site:
- changing password from user profile
- coworking pages (private or not)
- users making new polls