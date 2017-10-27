output "cloudwatch_kinesis_user_access_key_id" {
  value = "${aws_iam_access_key.cloudwatch_kinesis_user_access_key.id}"
}

output "cloudwatch_kinesis_user_secret_access_key" {
  value = "${aws_iam_access_key.cloudwatch_kinesis_user_access_key.secret}"
}
