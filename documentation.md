# Backend

## **authent/Encryption.py**
Tech used: **Cryptography**
### <u> **Definitions** </u>

#### **Fernet**
> A symmetric encryption scheme (uses the same secret key for encrypt/decrypt) used for encrypting data.

### **Explanation**
Generated encryption keys and used them along with Fernet to encrypt data using the HS256 algorithm. I created an encryption file to ensure that sensitive data is kept secure in the DB.

---

## **db/database.py**
Tech used: **SQLAlchemy**
### <u> **Definitions** </u>

#### **SQLAlchemy**
>  Python library that offers SQL and ORM (Object relational mapping), allowing for interaction with relational databases through the use of Python objects

### **Explanation**
I used sqlalchemy because it allowed me to create a relational DB which can be found in another file. Here I only used it to connect to the DB and instantiate the tables if they weren't already created.  

---

## **db/models.py**
Tech used: **SQLAlchemy**
### <u> **Definitions** </u>

#### **SQLAlchemy**
>  Python library that offers SQL and ORM (Object relational mapping), allowing for interaction with relational databases through the use of Python objects

### **Explanation**
I used sqlalchemy because it allowed me to create a relational DB. I created tables, each having columns necessary to maintain imporant info used by the app. The User() table is the parent of all the other tables and contains info on the user upon signing up. The Email() table has information about emails, each of which need to map back to a single user in the User() table. The Attachment() table contains info about an attachment of an email that must map back to a single email in the Email() table. The Followup() table has info about following up on an email, of course this maps back to a single email.

---

## **db/schemas.py**
Tech used: **Pydantic**
### <u> **Definitions** </u>

#### **Pydantic**
>  Python library that is used for data validation

### **Explanation**
I used Pydantic to ensure all data being stored in the DB strictly follows the restrictions placed. I created different classes each having their own use cases when validating certain data. 

---

## **main.py**
Tech used: **FastAPI**, **OAuth**, **SQLAlchemy**, **Scarlette**
### <u> **Definitions** </u>

#### **API** (Application Programming Interface) 
> Defined rules that dictates how different softwares communicate with eachother. It provides a layer of abstraction because you can access different software and use its full functionality without knowing or caring what's under the hood. 

#### **REST** (Representational State Transfer)
> A client-server architecture that imposes conditions on how an API should work. Some principles of the REST architectural style are:
- **Uniform Interface** - Requests should identify resources, clients have enough info in the resources representation to modify or delete the resouce, clients receive info about how to process the representations further and about all other related resources they need to complete a task
- **Statelessness** - Communication method in which the server can complete any request indepent of all others
- **Layered System** - Client can connect with other authorized intermediaries between the client & server and it will still receive a response from the server
- **Cacheability** - Support caching which is the process of storing responses on the client or an intermediary to improve server response time

#### **FastAPI**
> A Python web framework that allows developers to build APIs in an efficient manner and develop RESTful APIs, which is an interface that allows two computer systems to exchange information securely over the internet. 

### **Oauth**
> A form of authorization that allows third party apps (such as myself) to access user's info on another service without sharing their username or password.

### **SQLAlchemy**
>  Python library that offers SQL and ORM (Object relational mapping), allowing for interaction with relational databases through the use of Python objects

### **Explanation**
I decided to use FastAPI because I wanted to learn it, but it also comes with great benefits that support what I wanted to do. The first benefit is asynchronous support which allows my program to process large volumes of requests. It also has built-in security, more specifically, OAuth2 which is what's needed to communicate with the Google API. Its simplicity allows me to efficiently expand on its functionality.