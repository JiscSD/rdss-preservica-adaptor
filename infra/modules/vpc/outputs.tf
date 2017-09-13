output "vpc_id" {
  value = "${aws_vpc.vpc.id}"
}

output "private_subnet_ids" {
  value = ["${aws_subnet.private.*.id}"]
}

output "nat_subnet_ids" {
  value = ["${aws_subnet.nat.*.id}"]
}

output "igw_subnet_ids" {
  value = ["${aws_subnet.igw.*.id}"]
}

output "security_group_all_id" {
  value = "${aws_security_group.all.id}"
}
