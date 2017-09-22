# rdss-preservica-adaptor
Adaptor service for publishing to Preservica.

Note that the Preservica Adaptor will attempt to read from a Kinesis Stream created by the Message Broker component. Therefore, the Message Broker MUST be deployed to the target environment BEFORE this component.

## Service Information
Preservica DOI records are created based upon the [message payloads](https://github.com/JiscRDSS/rdss-message-api-docs/tree/master/messages/metadata) published to the input kinesis stream.

### Service Application Code
Python3.6. Uses the [AWS Kinesis Client Python Library](https://github.com/awslabs/amazon-kinesis-client-python).

#### Flow
1. Listens for create messages from the `shared_services_input_$ENVIRONMENT` kinesis stream using the [Java KCL daemon](https://github.com/awslabs/amazon-kinesis-client)
2. Downloads files referenced in payload message and generates a zip bundle
3. Uploads the zip bundle to the appropriate bucket for the organisation which produced the files. A dictionary mapping organisation ID to to S3 bucket is present in the config file for each environment, see the [dev config](config/dev.py) for an example.

#### Create behaviour
Uploads zip to S3 bucket.
Update/Delete operations are not supported.

#### Metatdata

##### Root Metadata file
A metadata file is created and placed in the root of the package. The contents are the entire kinesis message converted into XML.

##### Metadata for individual Files in the payload
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

Contents of `bar.txt.metadata` file generated:
```XML
<oai_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
	<dc:fileName>bar</dc:fileName>
</oai_dc:dc>
```

#### Zip bundle contents

Example message written to input stream:

```
{
  "messageHeader": {
    "messageId": "ad6dee33-80ed-ae48-9cac-ed6f2250b017",
    "messageType": "MetadataCreate",
    "messageClass": "Command"
  },
  "messageBody": {
    "objectUuid": "e9bf8212-b2e8-ead2-c88f-809a21a8ce1b",
    "objectTitle": "Research about birds in the UK.",
    "objectFile": [
      {
        "fileUuid": "a3290140-18e1-506e-abec-61e31791e749",
        "fileStorageLocation": "s3://testdata.researchdata.alpha.jisc.ac.uk/unsorted/10.17863/CAM.679/data.zip",
        "fileStorageType": "s3",
        "fileName": "Label of this intellectual asset: 1"
      },
      {
        "fileUuid": "9c5f1f7f-39a7-93fc-0327-5ffaa81dee62",
        "fileStorageLocation": "s3://testdata.researchdata.alpha.jisc.ac.uk/unsorted/10.17863/CAM.679/readme.txt",
        "fileStorageType": "s3",
        "fileName": "Label of this intellectual asset: 2"
      }
    ]
  }
}
```

The following will be produced as the contents of the zip bundle:

```
10.17863
    └── 10.17863.metadata
    └── CAM.679
        ├── data.zip
        ├── data.zip.metadata
        ├── readme.txt
        └── readme.txt.metadata
```

#### [S3 metadata attributes](http://docs.aws.amazon.com/AmazonS3/latest/dev/UsingMetadata.html#object-metadata) set on the zip bundle uploaded to S3.

These are needed for Preservica to be able to ingest the package.

```
key               <messageId>
bucket            <name of S3 bucket that you upload zip to>
status            ready (hardcoded value)
name              <messageId>.zip
size              zip bundle file size
size_uncompressed file size of all files in zip (ie before compression)
createddate       `"fileDateCreated"` property of `ObjectFile` object
createdby         `"role"` property of `messageBody.objectOrganisationRole` object
```

#### Assumptions

- `createdby` S3 attribute of zip bundle - taken from `messageBody.ObjectPublisher[]` objects - `role` property. An assumption that all objects have the same value for `role` property. Current logic is to take the value from first object in the list.

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

-----------------------------------------------------------
## Jenkins

### Vagrant

1. Make sure config contains relevant to your box configuration
2. Setup vagrant box `vagrant up`
3. Run installation process by opening http://192.168.33.10:8080/
(or other configured address) and follow instructions
4. Set credentials  see below
5. Create pipeline job
6. Configure pipeline job - set Definition - select "Pipeline script from SCM" option
7. Set SCM branch to any which contains a Jenkinsfile in the root of the repository. Set polling interval to `H/2 * * * *`
8. install https://wiki.jenkins.io/display/JENKINS/CloudBees+AWS+Credentials+Plugin

### Setting up credentials

Follow this [guide](https://support.cloudbees.com/hc/en-us/articles/203802500-Injecting-Secrets-into-Jenkins-Build-Jobs) to add credentials to the Global domain.

1. add ssh key with id `git`
2. add aws key pair as "AWS Credentials" kind with id `jenkins_aws`
