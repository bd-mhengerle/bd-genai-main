from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def get_user_info():
    try:
        service = build("people", "v1", credentials=creds)

        # Call the People API
        print("List 10 connection names")
        results = (
            service.people()
            .connections()
            .list(
                resourceName="people/me",
                pageSize=10,
                personFields="names,emailAddresses",
            )
            .execute()
        )
        connections = results.get("connections", [])

        for person in connections:
            names = person.get("names", [])
        if names:
            name = names[0].get("displayName")
            print(name)
    except HttpError as err:
        print(err)