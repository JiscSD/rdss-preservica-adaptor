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
  preservica-prototype python run.py
```
