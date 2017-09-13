resource "aws_vpc" "vpc" {
  cidr_block           = "${var.vpc_cidr}"
  enable_dns_support   = "${var.enable_dns_support}"
  enable_dns_hostnames = "${var.enable_dns_hostnames}"

  tags {
    Name        = "${var.project}-${terraform.env}-vpc"
    Environment = "${terraform.env}"
    Project     = "${var.project}"
    Owner       = "${var.owner}"
    CostCenter  = "${var.costcenter}"
    managed_by  = "terraform"
    service     = "${var.service}"
  }
}

####################
# Internet Gateway #
####################

resource "aws_internet_gateway" "igw" {
  vpc_id = "${aws_vpc.vpc.id}"

  tags {
    Name        = "${var.project}-${terraform.env}-igw"
    Environment = "${terraform.env}"
    Project     = "${var.project}"
    Owner       = "${var.owner}"
    CostCenter  = "${var.costcenter}"
    managed_by  = "terraform"
    service     = "${var.service}"
  }
}

resource "aws_subnet" "igw" {
  vpc_id                  = "${aws_vpc.vpc.id}"
  cidr_block              = "${var.igw_cidr}"
  map_public_ip_on_launch = true

  tags {
    Name        = "${var.project}-${terraform.env}-igw"
    Environment = "${terraform.env}"
    Project     = "${var.project}"
    Owner       = "${var.owner}"
    CostCenter  = "${var.costcenter}"
    managed_by  = "terraform"
    service     = "${var.service}"
  }
}

resource "aws_route_table" "igw" {
  vpc_id = "${aws_vpc.vpc.id}"

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = "${aws_internet_gateway.igw.id}"
  }

  tags {
    Name        = "${var.project}-${terraform.env}-igw"
    Environment = "${terraform.env}"
    Project     = "${var.project}"
    Owner       = "${var.owner}"
    CostCenter  = "${var.costcenter}"
    managed_by  = "terraform"
    service     = "${var.service}"
  }
}

resource "aws_route_table_association" "igw" {
  subnet_id      = "${aws_subnet.igw.id}"
  route_table_id = "${aws_route_table.igw.id}"
}

##################
# Private Subnet #
##################

resource "aws_subnet" "private" {
  vpc_id                  = "${aws_vpc.vpc.id}"
  count                   = "${length(var.private_subnets_cidr)}"
  cidr_block              = "${element(var.private_subnets_cidr, count.index)}"
  availability_zone       = "${element(var.availability_zones, count.index)}"
  map_public_ip_on_launch = false

  tags {
    Name        = "${var.project}-${terraform.env}-private-${count.index}"
    Environment = "${terraform.env}"
    Project     = "${var.project}"
    Owner       = "${var.owner}"
    CostCenter  = "${var.costcenter}"
    managed_by  = "terraform"
    service     = "${var.service}"
  }
}

resource "aws_route_table" "private" {
  vpc_id = "${aws_vpc.vpc.id}"

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = "${aws_nat_gateway.natgw.id}"
  }

  tags {
    Name        = "${var.project}-${terraform.env}-private"
    Environment = "${terraform.env}"
    Project     = "${var.project}"
    Owner       = "${var.owner}"
    CostCenter  = "${var.costcenter}"
    managed_by  = "terraform"
    service     = "${var.service}"
  }
}

resource "aws_route_table_association" "private" {
  count          = "${length(var.private_subnets_cidr)}"
  subnet_id      = "${element(aws_subnet.private.*.id, count.index)}"
  route_table_id = "${aws_route_table.private.id}"
}

#######
# NAT #
#######

resource "aws_subnet" "nat" {
  vpc_id                  = "${aws_vpc.vpc.id}"
  count                   = "${length(var.nat_cidr)}"
  cidr_block              = "${element(var.nat_cidr, count.index)}"
  availability_zone       = "${element(var.availability_zones, count.index)}"
  map_public_ip_on_launch = false

  tags {
    Name        = "${var.project}-${terraform.env}-nat-${count.index}"
    Environment = "${terraform.env}"
    Project     = "${var.project}"
    Owner       = "${var.owner}"
    CostCenter  = "${var.costcenter}"
    managed_by  = "terraform"
    service     = "${var.service}"
  }
}

resource "aws_route_table" "nat" {
  vpc_id = "${aws_vpc.vpc.id}"

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = "${aws_nat_gateway.natgw.id}"
  }

  tags {
    Name        = "${var.project}-${terraform.env}-nat"
    Environment = "${terraform.env}"
    Project     = "${var.project}"
    Owner       = "${var.owner}"
    CostCenter  = "${var.costcenter}"
    managed_by  = "terraform"
    service     = "${var.service}"
  }
}

resource "aws_route_table_association" "nat" {
  count          = "${length(var.nat_cidr)}"
  subnet_id      = "${element(aws_subnet.nat.*.id, count.index)}"
  route_table_id = "${aws_route_table.nat.id}"
}

resource "aws_eip" "nat" {
  vpc = true
}

resource "aws_nat_gateway" "natgw" {
  allocation_id = "${aws_eip.nat.id}"
  subnet_id     = "${aws_subnet.igw.id}"
}

########################
# "All" Security Group #
########################

resource "aws_security_group" "all" {
  name = "all"

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  vpc_id = "${aws_vpc.vpc.id}"

  tags {
    Name        = "${var.project}-${terraform.env}-security-group-all"
    Environment = "${terraform.env}"
    Project     = "${var.project}"
    Owner       = "${var.owner}"
    CostCenter  = "${var.costcenter}"
    managed_by  = "terraform"
    service     = "${var.service}"
  }
}
