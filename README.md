> **Warning**
> As per the [Salesforce Functions Retirement announcement](https://devcenter.heroku.com/articles/salesforce-functions-retirement), this repository is now archived.

# Sample Python Function

Install the Python function dependencies:
```sh
cd functions/python_watermark
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Start the local function container:
```sh
sf run function start
```

Retrieve a ContentDocument ID by running this SOQL query (tip: use the VSCode command):
```sql
SELECT PathOnClient, ContentDocumentId FROM ContentVersion WHERE IsLatest=true
```

Call the local function (make sure to replace the ContentDocument ID):
```sh
sf run function --function-url http://localhost:8080 --payload '{"docId": "069DK000001i2QBYAY"}'
```
