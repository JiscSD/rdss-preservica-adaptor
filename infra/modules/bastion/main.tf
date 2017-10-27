resource "aws_instance" "bastion" {
  ami             = "ami-ed100689"
  instance_type   = "t2.micro"
  subnet_id       = "${var.public_subnet}"
  security_groups = ["${var.bastion_sg}"]
  key_name        = "${var.key_name}"

  user_data = <<EOF
#!/bin/bash

# Update all packages
yum clean all
yum -y upgrade

# Install NFS etc
yum -y install awslogs
service rpcbind restart

# Set up the AWS logs agent
mkdir -p /var/awslogs/state
sed -c -i "s/\(region *= *\).*/\1${var.aws_region}/" /etc/awslogs/awscli.conf
aws s3 cp s3://rdss-preservicaservice-objects/application/config/${terraform.env}/bastion/awslogs-agent-config.conf /etc/awslogs/awslogs.conf --region ${var.aws_region}
service awslogs start
chkconfig awslogs on
EOF

  tags {
    "Name"        = "${var.project}-${terraform.env}-bastion"
    "Environment" = "${terraform.env}"
    "Project"     = "${var.project}"
    "Service"     = "${var.service}"
    "CostCentre"  = "${var.cost_centre}"
    "Owner"       = "${var.owner}"
    "ManagedBy"   = "Terraform"
  }
}
