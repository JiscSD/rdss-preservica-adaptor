resource "aws_cloudwatch_log_subscription_filter" "subscription_filter" {
  name            = "${var.name}"
  role_arn        = "${var.role_arn}"
  log_group_name  = "${var.log_group_name}"
  filter_pattern  = ""
  destination_arn = "${var.destination_arn}"
}
