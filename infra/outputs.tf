output "vpc_id" {
  value = "${module.vpc.vpc_id}"
}

output "input_stream_id" {
  value = "${module.input_stream.stream_id}"
}

output "input_stream_arn" {
  value = "${module.input_stream.stream_arn}"
}

output "autoscaling_group_id" {
  value = "${module.autoscaling.autoscaling_group_id}"
}

output "autoscaling_group_arn" {
  value = "${module.autoscaling.autoscaling_group_arn}"
}

output "autoscaling_group_vpc_zone_identifier" {
  value = "${module.autoscaling.autoscaling_group_vpc_zone_identifier}"
}

output "private_subnet_ids" {
  value = "${module.vpc.private_subnet_ids}"
}

output "public_subnet_ids" {
  value = "${module.vpc.public_subnet_ids}"
}
