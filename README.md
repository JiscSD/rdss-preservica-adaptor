# rdss-preservica-adaptor
Adaptor service for publishing to Preservica.

Note that the Preservica Adaptor will attempt to read from a Kinesis Stream created by the Message Broker component. Therefore, the Message Broker MUST be deployed to the target environment BEFORE this component.

## Service Information
Preservica DOI records are created/updated/removed based upon the [message payloads](https://github.com/JiscRDSS/rdss-message-api-docs/tree/master/messages/metadata) published to the input kinesis stream. Records are uploaded to/removed from the UoJ Preservica autoupload S3 bucket.

### Service Application Code
Python3.6. Uses the [AWS Kinesis Client Python Library](https://github.com/awslabs/amazon-kinesis-client-python).

#### Flow
1. Listens for Create/Update/Delete messages from the `shared_services_input_$ENVIRONMENT` kinesis stream using the [Java KCL daemon](https://github.com/awslabs/amazon-kinesis-client)
2. Downloads files referenced in payload message and generates a zip bundle
3. Uploads the zip bundle to the autoupload Preservica bucket for the organisation specified in the message payload - there is a map for `organisationID` to S3 bucket location for each organisation, see [`config/prod.py`](config/prod.py) for an example.

#### Message Filtering
The application ignores all requests which don't originate from organisations specified in the `organisationID` - S3 bucket map.

#### Create/Update/Delete behaviour
##### Create
Uploads zip to S3 bucket.
##### Update
Replaces existing object in S3 bucket.
##### Delete
Deletes existing object in S3 bucket.

#### Metatdata
A metadata file in dublin core format is created for each file listed in the message payload. The metatdata filename uses the same s3 object key name as its s3 object key (`{}.metadata.xml`). The metadata content is a single node listing the file name.

##### Metadata Example
Example create payload:
```JavaScript
{
  "messageHeader": {},
  "messageBody": {
    "objectFile": [{
      "fileName": "bar",
      "fileStorageLocation": "s3://somebucket/foo/bar.txt"
    }]
  }
}
```

Contents of `bar.txt.metadata.xml` file generated:
```XML
<oai_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
	<dc:fileName>bar</dc:fileName>
</oai_dc:dc>
```

#### Logging
Logs are written to the local syslog service and follow the format specified in [Message API docs logging section](https://github.com/JiscRDSS/rdss-message-api-docs/#logging).

#### Errors
Errors are published to the `message_error_$ENVIRONMENT` kinesis stream. Error handling adheres to the guidelines outlined in the [Message API docs](https://github.com/JiscRDSS/rdss-message-api-docs/#error-queues).

-----------------------------------------------------------
### Service Infrastructure
Fully baked AMI deployed into an Autoscaling Group using Ansible, Packer & Terraform.

#### Configuration
Application uses 12 Factor configuration. Selects appropriate configuration file based upon `$ENVIRONMENT` value set at deploy time.

#### Supported Environments
- `dev`
- `uat`
- `prod`

#### SSH Access to EC2 Instances

The application is deployed into a private subnet. A bastion box is not a requirement at this stage. If you need to SSH into the ec2 instance while testing change the value of `$LAUNCH_IN_PUBLIC_SUBNET` in your environment when running `deploy`.

#### Updating Base AMI Image
Choose the hvm-ssd image type from the [ubuntu AMI search page](https://cloud-images.ubuntu.com/locator/ec2/.)

-----------------------------------------------------------

## Deployment

Requires Terraform and Packer to be installed.

### Setup

Set required variables in environment.
```
cp .env.example .env
# edit .env
. .env
```

### All-in-one command to bake AMI and deploy stack.

```
./bin/deploy
```

### Bake AMI

Install packer.
```
./bin/buildami
```

### Deploy Stack

Install terraform.
```
./bin/deployterraform
```

-----------------------------------------------------------

## Tests

### Application Tests
```
make env
make deps
make test
make lint
```

### Kitchen Tests

Requires vagrant to be installed.

##### Install kitchen and dependencies
```
bundle install
```

### Run Tests
```
kitchen test
```
