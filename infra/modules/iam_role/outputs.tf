output "role_id" {
  value = "${aws_iam_role.role.id}"
}

output "role_arn" {
  value = "${aws_iam_role.role.arn}"
}

output "role_name" {
  value = "${aws_iam_role.role.name}"
}
