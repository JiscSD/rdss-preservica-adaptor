# Throw Away Prototype

The aim of this is to ensure the following is supported by the new Preservica API

- [x] Creation of new collection.
- [x] Monitoring for workflow progress.
- [x] Updating of metadata for records in Preservica.

## Running

The workflow context must have already been created in the UI, in

    "Ingest"
      -> "Manage"
      -> Choose "Website Ingest (Full)"
      -> Click "Add"
      -> Fill in the dialog
      -> Click "Create"

The ID is then tricky to find, but you can inspect the page after creating and find it in the row that contains information about the newly-created context.

```
docker build -t preservica-prototype . && \
docker run -it \
  --rm \
  --env BASE_URL=https://beta.preservica.com/ \
  --env TENANT=demo \
  --env USERNAME=alan.mackenzie@digirati.com \
  --env PASSWORD=_password_ \
  --env WORKFLOW_CONTEXT_ID=184 \
  --env WORKFLOW_CONTEXT_NAME=testWebsiteIngest \
  preservica-prototype python run.py
```
