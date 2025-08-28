



***main.py***
Tech used: **FastAPI**, **google_auth_oauthlib**, **Scarlette**

**Definitions**
------------
• **API** (Application Programming Interface) - Defined rules that dictates how different softwares communicate with eachother. It provides a layer of abstraction because you can access       
                                                different software and use its full functionality without knowing or caring what's under the hood. 

• **REST** (Representational State Transfer) - A client-server architecture that imposes conditions on how an API should work. Some principles of the REST architectural style are:
- **Uniform Interface** - Requests should identify resources, clients have enough info in the resources representation to modify or delete the resouce, clients receive info about how to process the       
                          representations further and about all other related resources they need to complete a task
- **Statelessness** - Communication method in which the server can complete any request indepent of all others
- **Layered System** - Client can connect with other authorized intermediaries between the client & server and it will still receive a response from the server
- **Cacheability** - Support caching which is the process of storing responses on the client or an intermediary to improve server response time

• **FastAPI** - A Python web framework that allows developers to build APIs in an efficient manner and develop RESTful APIs, which is an interface that allows two computer systems to exchange information 
                securely over the internet. 

**Reasoning**
----------
I decided to use FastAPI because I wanted to learn it, but it also comes with great benefits that support what I wanted to do. The first benefit is asynchronous support which allows my program to process large volumes of requests. It also has built-in security, more specifically, OAuth2 which is what's needed to communicate with the Google API. Its simplicity allows me to efficiently expand on its functionality.