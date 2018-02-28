# Throw Away Prototype

The aim of this is to ensure the following is supported by the new Preservica API

- [ ] Creation of new collection.
- [ ] Monitoring for workflow progress.
- [ ] Updating of metadata for records in Preservica.

## Running

```
docker build -t preservica-prototype . && \
docker run \
  --rm \
  --env BASE_URL=https://beta.preservica.com/ \
  --env TENANT=demo \
  --env USERNAME=alan.mackenzie@digirati.com \
  --env PASSWORD=_password_ \
  preservica-prototype python run.py
```
