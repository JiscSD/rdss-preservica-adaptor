resource "aws_instance" "bastion" {
  ami                  = "ami-ed100689"
  instance_type        = "t2.nano"
  subnet_id            = "${var.public_subnet}"
  security_groups      = ["${var.bastion_sg}"]
  key_name             = "${var.key_name}"
  iam_instance_profile = "${aws_iam_instance_profile.profile.id}"

  user_data = <<EOF
#!/bin/bash

# Update all packages
yum clean all
yum -y upgrade

# Install awslogs
yum -y install awslogs
service rpcbind restart

# Set up the AWS logs agent
mkdir -p /var/awslogs/state
sed -c -i "s/\(region *= *\).*/\1${var.aws_region}/" /etc/awslogs/awscli.conf
aws s3 cp s3://rdss-preservicaservice-objects/application/config/${terraform.workspace}/bastion/awslogs-agent-config.conf /etc/awslogs/awslogs.conf --region ${var.aws_region}
service awslogs start
chkconfig awslogs on
EOF

  tags {
    "Name"        = "${var.project}-${terraform.workspace}-bastion"
    "Environment" = "${terraform.workspace}"
    "Project"     = "${var.project}"
    "Service"     = "${var.service}"
    "CostCentre"  = "${var.cost_centre}"
    "Owner"       = "${var.owner}"
    "ManagedBy"   = "Terraform"
  }
}

resource "aws_iam_role" "role" {
  name = "${var.project}-${terraform.workspace}-bastion-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "cloudwatch" {
  name = "${var.project}-${terraform.workspace}-bastion-cloudwatch"
  role = "${aws_iam_role.role.id}"

  policy = <<EOF
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Effect":"Allow",
      "Action":[
        "cloudwatch:Put*"
      ],
      "Resource": ["*"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": [
        "arn:aws:logs:*:*:*"
      ]
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "objects" {
  name = "${var.project}-${terraform.workspace}-bastion-objects"
  role = "${aws_iam_role.role.id}"

  policy = <<EOF
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": [
        "${var.objects_bucket_arn}/*"
      ]
    }
  ]
}
EOF
}

resource "aws_iam_instance_profile" "profile" {
  name = "${var.project}-${terraform.workspace}-bastion-profile"
  role = "${aws_iam_role.role.name}"
}
