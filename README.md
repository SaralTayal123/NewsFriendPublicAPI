# NewsFriendAPI
Heroku API for NewsFriend

This is the Public Facing code for the NewsFriend API. More Details on NewsFriend is available here:https://github.com/SaralTayal123/NewsFriend

This is a duplicate repo for the original API. The original API has the Azure sentiment key stored in the repo. I can't use a gitignore for the private key files since Heroku needs them for its deployment. Hence the duplicate repo without the appropriate key files.

To restore full functionality, simply create a new file with the following format
`FileName: 'azureKey.py`
The contents of this file will be as follows
```
key = "<Enter Your key here, keep the quotes>"
endpoint = "https://<Your endpoint name>.cognitiveservices.azure.com/"
```

- api docs: https://newsfriend.herokuapp.com/docs 
- test: https://newsfriend.herokuapp.com/ping/https:%7C%7Cwww.bbc.com%7Cnews%7Cworld-europe-53832981
