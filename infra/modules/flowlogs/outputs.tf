output "log_group_name" {
  value = "${aws_cloudwatch_log_group.flowlog_log_group.name}"
}
