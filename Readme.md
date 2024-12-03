
# Before running the application

### GenAi Sandbox

**Dockerfile**: gen-ai-sandbox/src/chatbot_app/Dockerfile


Requires the following files to be manually created or added in the gen-ai-sandbox folder.

- Can be created based on the env.sample
> .env 

- The key-gen.json *(GCP's SA)* is already in the .gitignore and .dockerignore. 
- The key-gen.json is binded to the container in the docker compose
  
>  key-gen.json

**Compose Watch Behaviour**

 - **src/** will trigger a sync files and restart of the container
 - **requirements.txt** will trigger a rebuild of the container
 - **.env** will trigger a sync the file and restart the container

---------

### Web Backend

**Dockerfile**: web-backend/Dockerfile.env

Requires the following files to be manually created or added.

- Can be created based on the env.sample
> .env 

- The key.json *(GCP's SA)* is already in the .gitignore and .dockerignore. 
- The key.json is binded to the container in the docker compose
  
>  key.json

**Compose Watch Behaviour**

 - **src/** will trigger a sync files and restart of the container
 - **requirements.txt** will trigger a rebuild of the container
 - **.env** will trigger a sync the file and restart the container

---------

 ### Web Application

**Dockerfile**: web-app/Dockerfile.env

Requires the following file to be manually created or added.

- Can be created based on the env.sample
> .env 

**Compose Watch Behaviour**

 - **src/** will trigger a sync files
 - **package.json** will trigger a rebuild of the container
 - **.env** will trigger a sync the file and restart the container


# Running the application

### Default behavior

- docker compose -f docker-compose.yml watch // In order to run watch mode, the apps will refresh when something changes. Web app and web backend

- docker compose -f docker-compose.yml up // Get the apps running . Web app and web backend
  
- docker compose -f docker-compose.yml down // Shutdown the apps . Web app and web backend 
 

### Use flag profile = full to start the genai-sandbox as well.

- docker-compose --profile full watch