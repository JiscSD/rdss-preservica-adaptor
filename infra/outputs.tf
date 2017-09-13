output "vpc_id" {
  value = "${module.vpc.vpc_id}"
}

output "input_stream_id" {
  value = "${data.aws_kinesis_stream.input_stream.id}"
}

output "input_stream_arn" {
  value = "${data.aws_kinesis_stream.input_stream.arn}"
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
