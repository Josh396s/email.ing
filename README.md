# Email.ing

Going to try and create an app that makes email.ing much more efficient

## Updates

### 7/28/25:

- Finished building the authentication process in the 'authent' folder. It uses OAuth to verify access to user's google account and saves user's info under 'tokens' folder after the first time they log in.

> Next Step: Create the database and populate it with metadata regarding the user's emails

### 8/6/25:

- Finished setting up the database and tested it using fake data.

> Next Step: Incorporate the database with the Gmail API and populate it with user's info.

### 8/8/25:

- Working on setting up the login process using FastAPI.
- Fixed issue with Dockerfile and module imports
- Combined db.py and init_db.py into one file

> Bug: Seems to be a port already in use issue that throws a 500 error to the server.
> Next Step: Incorporate the database with the Gmail API and populate it with user's info.

### 9/02/25:

- Google authorization is fully functioning, might need to update scopes in the future based on info needed, but baseline is working.
- Updated User() model in database to incorporate important tokens such as access and refresh.
- Incorporated schemas using pydantic to ensure data being provided to the database is accurate and follows guidelines.
- Created 'Encryption.py' to encrypt/decrypt sensitive info.
- Encrypted sensitive info for User() before sending to DB. Decryption of the data after pulled from the DB works as expected.
- Created 'documentation.md' to keep track of tech being used and document work being done. Its mostly for my understanding.
- Created 'resources.txt' to maintain resources used in this project

> Next Step: Create JWT for users. Develop FastAPI paths to populate other tables in the DB.

### 11/05/25:

- Implemented JWT tokens: encode, decode, and validation. Tested to ensure it fully worked
- Updated authorization and user creation paths in main.py

> Next Step: Start working on decryption and connecting secure tokens with Gmail API

### 2/10/26:

* Encryption/Decryption fully working
* Full workflow works(Signup->Tokens->Email_fetch->DB_population)
* Implemented DB version control using alembic

> Next Step: Utilize Celery/Redis to handle large volumes of emails

### 2/11/26:

* Implented Celery/Redis to handle large volumes of emails via /sync function

> Next Step: Start looking into the implementation of classifying emails and their summarization
