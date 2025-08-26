Going to try and create an app that makes email.ing much more efficient

7/28/25: Finished building the authentication process in the 'authent' folder. It uses OAuth to verify access to user's google account and saves user's info under 'tokens' folder after the first time they log in. 
    Next Step: Create the database and populate it with metadata regarding the user's emails

8/6/25: Finished setting up the database and tested it using fake data. 
    Next Step: Incorporate the database with the Gmail API and populate it with user's info.

8/8/25: Working on setting up the login process using FastAPI.
        Fixed issue with Dockerfile and module imports
        Combined db.py and init_db.py into one file
        
    Bug: Seems to be a port already in use issue that throws a 500 error to the server.
    Next Step: Incorporate the database with the Gmail API and populate it with user's info.