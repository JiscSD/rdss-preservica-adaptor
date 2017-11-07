resource "aws_security_group" "bastion-sg" {
  vpc_id = "${var.vpc}"

  ingress = {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = "${var.access_ip_whitelist}"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags {
    "Name"        = "${var.project}-${terraform.env}-bastion-sg"
    "Environment" = "${terraform.env}"
    "Project"     = "${var.project}"
    "Service"     = "${var.service}"
    "CostCentre"  = "${var.cost_centre}"
    "Owner"       = "${var.owner}"
    "ManagedBy"   = "Terraform"
  }
}

resource "aws_security_group" "app-sg" {
  vpc_id = "${var.vpc}"

  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = ["${aws_security_group.bastion-sg.id}"]
  }

  egress = {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags {
    "Name"        = "${var.project}-${terraform.env}-app-sg"
    "Environment" = "${terraform.env}"
    "Project"     = "${var.project}"
    "Service"     = "${var.service}"
    "CostCentre"  = "${var.cost_centre}"
    "Owner"       = "${var.owner}"
    "ManagedBy"   = "Terraform"
  }
}
