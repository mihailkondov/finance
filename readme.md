# I. Commands to start working in virtual environment

    # 1 Create virtual environment -> plenty of guides online, look them up
        python -m venv /path/to/new/virtual/environment # create virtual environment
        Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope Process # This gives you 
        # permission to run scripts in the current powershell instance
        .venv\Scripts\activate # This runs the script to activate the virtual environment

    # 2 Set correct python path so you install packages on the right place (inside the virtual environment)
        # 
        # Windows + R
        # sysdm.cpl
        # OK
        # Advanced
        # Environment Variables
        # User Variables For <username>
        # New...
        # Variable Name: 
        # path
        # Variable Value:
        # /path/to/new/virtual/environment
        # The path given here should be abolute, not relative
        # that means it should start with C:/... or D:/... and not with ./ or ../ or similar
        # create second variable for the scripts:
        # write ; after the path of the variable you just created
        # then append /path/to/new/virtual/environment/Scripts
        # the final result looks like this
        # /path/to/new/virtual/environment;/path/to/new/virtual/environment/Scripts
        
# II. Install requirements

    # 1 Instead of Flask-Sessions I am using Flask-Sessions2 because Flask-Sessions throws an 
    # error when installing msgspec and I can't get past it
        pip install -r requirements.txt

# III. Run Flask:
    flask run