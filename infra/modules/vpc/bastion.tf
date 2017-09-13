resource "aws_security_group" "access_to_bastion" {
  vpc_id = "${aws_vpc.vpc.id}"

  ingress = {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = "${var.access_ip_whitelist}"
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
  vpc_id = "${aws_vpc.vpc.id}"

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

resource "aws_key_pair" "auth" {
  key_name   = "${var.project}-${terraform.env}"
  public_key = "${var.public_key}"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_instance" "bastion" {
  ami             = "ami-ed100689"
  instance_type   = "t2.micro"
  subnet_id       = "${aws_subnet.igw.id}"
  security_groups = ["${aws_security_group.access_to_bastion.id}"]
  key_name        = "${aws_key_pair.auth.id}"

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
