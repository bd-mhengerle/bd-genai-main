
# Endpoints

## File Upload

1.  #### `GET  /files/listing`

- **request**:  Query strings expected:
  - limit: number
  - order_by: string of the format name:desc, name:asc
  - filters: Filters to apply, e.g., name:startswith:test_name
  - cursor: Cursor for pagination
    
- **What it does** : Lists files from the files collection in FS. In adds a new property called authenticatedURL which is a signed url to get that file from gcs. It has  TTL of 6 hours.

2.  #### `GET /files/signed`

- **request** : 
  - blob_name. The gcs uri to signed. Only valid buckets for this are: bd-drive-data, bd-gh-data-spot-sdk, bd-user-upload
 
- **What it does** : Signs an url.


## Chat

1.  #### `POST /chat`

- **request** : 

```json
{
  "name": "test name"
}
```
 
- **What it does** : Creates a new chat. It also creates a default knowledge base attached to this chat.

2.  #### `GET /chat/listing`

- **request**:  Query strings expected:
  - limit: number
  - order_by: string of the format name:desc, name:asc
  - filters: Filters to apply, e.g., name:startswith:test_name
  - cursor: Cursor for pagination 
 
- **What it does** : Listing of chats. It will always bring only the chats created by the user doing the request.

3.  #### `GET /chat/{id}`

- **request**: id of the chat in the params paths 
 
- **What it does** : It will bring an object chat from the chats collection

4.  #### `PUT /chat/{id}`

- **request**: id of the chat in the params paths  

```json
{
  "name": "test name updated"
}
```

- **What it does** : It updates a chat object

5.  #### `DELETE /chat/{id}`

- **request**: id of the chat in the params paths  
 
- **What it does** : Soft delete a chat object

6.  #### `POST /chat/{id}/favorite`

- **request**: id of the chat in the params paths   
 
- **What it does** : Set a chat as favorite or remove it as favorite

7.  #### `POST /chat/{id}/ask`

- **request**: id of the chat in the params paths   

```json
{
  "question": "What is Spot?",
  "knowledge_base_ids": ["QU0OXStyBLs4nQxx7TeE"],
  "model": "gemini-1.5-pro"
}
```

- **What it does** :  This proxies a question to the genai chatbot


## Knowledge Base


1.  #### `POST /kb`

- **request** : 

```json
{
  "name": "Test KB",
  "public": false,
}
```
 
- **What it does** : This creates a user defined knowledgebase.

2.  #### `GET /kb/{id}`

- **request**: id of the kb in the params paths   
 
- **What it does** : This will bring a KB object from the kb collection


3.  #### `PUT /kb/{id}`

- **request**: id of the kb in the params paths   

```json
{
  "name": "Test KB updated",
  "public": true,
}
```
 
- **What it does**: This will bring update KB object in the kb collection


4.  #### `POST /kb/{id}/add/files`

- **request**: id of the kb in the params paths   

```
// Formdata
    files: Binary
``` 
 
- **What it does** : This will upload the given files to GCS, create the metadata in the files collection, associate the files to the kb object and the will proxy the request to the genai to generate the embeddings for the files.


5.  #### `POST /kb/{id}/remove/files`

- **request** : id of the kb in the params paths  

```json
{
  "file_ids": ["QU0OXSty"],
}
```
 
- **What it does** : This will proxy a request to the genai to remove the embeddings from the vector database and then will be remove the file from gcs, from firestore and the association with the kb.


6.  #### `DELETE /kb/{id}`

- **request** : id of the kb in the params paths   
 
- **What it does** : Soft deletes a KB. ATM it doesnt delete the files from gcs, or the embeddings.


7.  #### `GET /kb/listing/predefined`

- **request**: Query strings expected:
  - limit: number
  - order_by: string of the format name:desc, name:asc
  - filters: Filters to apply, e.g., name:startswith:test_name
  - cursor: Cursor for pagination 
 
- **What it does**: This will bring only the kbs that are defined by the system. Salesforce, gdrive and so on.


8.  #### `GET /kb/listing/user/public`

- **request**: Query strings expected:
  - limit: number
  - order_by: string of the format name:desc, name:asc
  - filters: Filters to apply, e.g., name:startswith:test_name
  - cursor: Cursor for pagination 
 
- **What it does**: This will bring only the kbs that other users are sharing.


9.  #### `GET /kb/listing/user/private`

- **request**: Query strings expected:
  - limit: number
  - order_by: string of the format name:desc, name:asc
  - filters: Filters to apply, e.g., name:startswith:test_name
  - cursor: Cursor for pagination 
 
- **What it does** : This will bring only the kbs a user owns.


## Reporting

1.  #### `GET /report/user-activity`

- **request**: Query strings expected:
  - limit: number
  - order_by: string of the format name:desc, name:asc
  - filters: Filters to apply, e.g., name:startswith:test_name
  - cursor: Cursor for pagination 
 
- **What it does** : It will list the user activity.  Its basically a general listing of all the interactions that user

2.  #### `GET /report/new-chats`

- **request**: Query strings expected:
  - limit: number
  - order_by: string of the format name:desc, name:asc
  - filters: Filters to apply, e.g., name:startswith:test_name
  - cursor: Cursor for pagination 
 
- **What it does** : This works for listing all the new entries for new chats created.

3.  #### `GET /report/msgs`

- **request**: Query strings expected:
  - limit: number
  - order_by: string of the format name:desc, name:asc
  - filters: Filters to apply, e.g., name:startswith:test_name
  - cursor: Cursor for pagination 
 
- **What it does**: This works for listing all the new entries for new messages created. All the interaction of the users questions.

4.  #### `GET /report/uploads`

- **request**: Query strings expected:
  - limit: number
  - order_by: string of the format name:desc, name:asc
  - filters: Filters to apply, e.g., name:startswith:test_name
  - cursor: Cursor for pagination  
 
- **What it does**: This works for listing all the new entries for new uploaded files. All the interaction of the user uploaded.

5.  #### `GET /report/resumed-chats`

- **request**: Query strings expected:
  - limit: number
  - order_by: string of the format name:desc, name:asc
  - filters: Filters to apply, e.g., name:startswith:test_name
  - cursor: Cursor for pagination 
 
- **What it does**: This works for listing all the new resumed chats. A chat is consider resumed if the user asked a question after 30 min.

6.  #### `GET /report/new-kbs`

- **request**: Query strings expected:
  - limit: number
  - order_by: string of the format name:desc, name:asc
  - filters: Filters to apply, e.g., name:startswith:test_name
  - cursor: Cursor for pagination 
 
- **What it does**: This works for listing all the new knowledgebase created.

7.  #### `GET /report/aggregation/count/new-chats`

- **request** : 
  - filters: Filters to apply, e.g., name:startswith:test_name
 
- **What it does** : It does aggregation of the new chats records. A total of new chats created.

8.  #### `GET /report/aggregation/count/msgs`

- **request** : 
  - filters: Filters to apply, e.g., name:startswith:test_name
 
- **What it does**: It does aggregation of the new messages records. A total of new messages created. 

9.  #### `GET /report/aggregation/count/uploads`

- **request** : 
  - filters: Filters to apply, e.g., name:startswith:test_name
 
- **What it does**: It does aggregation of the new file upload records. A total of new file upload created.

10.   #### `GET /report/aggregation/count/new-kbs`

- **request** : 
  - filters: Filters to apply, e.g., name:startswith:test_name
 
- **What it does**: It does aggregation of the new kb records. A total of new kb created.

11.   #### `GET /report/aggregation/count/resumed-chats`

- **request** : 
  - filters: Filters to apply, e.g., name:startswith:test_name
 
- **What it does**: It does aggregation of the resumed chats records. A total of resumed chats created.


