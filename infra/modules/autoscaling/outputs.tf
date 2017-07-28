output "autoscaling_group_id" {
  value = "${aws_autoscaling_group.group.id}"
}

output "autoscaling_group_arn" {
  value = "${aws_autoscaling_group.group.arn}"
}

output "autoscaling_group_vpc_zone_identifier" {
  value = "${aws_autoscaling_group.group.vpc_zone_identifier}"
}
