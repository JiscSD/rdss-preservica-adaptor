resource "aws_instance" "bastion" {
  ami             = "ami-ed100689"
  instance_type   = "t2.micro"
  subnet_id       = "${var.public_subnet}"
  security_groups = ["${var.bastion_sg}"]
  key_name        = "${var.key_name}"

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
