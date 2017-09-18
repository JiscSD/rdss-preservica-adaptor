resource "aws_instance" "bastion" {
  ami             = "ami-ed100689"
  instance_type   = "t2.micro"
  subnet_id       = "${var.public_subnet}"
  security_groups = ["${var.bastion_sg}"]
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
