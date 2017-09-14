resource "aws_security_group" "access_to_bastion" {
  vpc_id = "${var.vpc}"

  ingress = {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = "${var.access_ip_whitelist}"
  }

  egress = {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags {
    Name        = "${var.project}-${terraform.env}-to-bastion-security-group"
    Environment = "${terraform.env}"
    Project     = "${var.project}"
    Owner       = "${var.owner}"
    CostCenter  = "${var.costcenter}"
    managed_by  = "terraform"
    service     = "${var.service}"
  }
}

resource "aws_security_group" "access_from_bastion" {
  vpc_id = "${var.vpc}"

  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = ["${aws_security_group.access_to_bastion.id}"]
  }

  tags {
    Name        = "${var.project}-${terraform.env}-from-bastion-security-group"
    Environment = "${terraform.env}"
    Project     = "${var.project}"
    Owner       = "${var.owner}"
    CostCenter  = "${var.costcenter}"
    managed_by  = "terraform"
    service     = "${var.service}"
  }
}

resource "aws_instance" "bastion" {
  ami             = "ami-ed100689"
  instance_type   = "t2.micro"
  subnet_id       = "${var.public_subnet}"
  security_groups = ["${aws_security_group.access_to_bastion.id}"]
  key_name        = "${var.key_name}"

  tags {
    Name        = "bastion-${var.project}-${terraform.env}"
    Environment = "${terraform.env}"
    Project     = "${var.project}"
    Owner       = "${var.owner}"
    CostCenter  = "${var.costcenter}"
    managed_by  = "terraform"
    service     = "${var.service}"
  }
}
