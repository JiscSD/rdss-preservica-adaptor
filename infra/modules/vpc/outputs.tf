output "vpc_id" {
  value = "${aws_vpc.vpc.id}"
}

output "private_subnet_ids" {
  value = ["${aws_subnet.private.*.id}"]
}

output "private_subnet_cidr" {
  value = ["${var.private_subnets_cidr}"]
}

output "nat_subnet_ids" {
  value = ["${aws_subnet.nat.*.id}"]
}

output "igw_subnet_ids" {
  value = ["${aws_subnet.igw.*.id}"]
}

output "igw_subnet_id" {
  value = "${aws_subnet.igw.id}"
}
