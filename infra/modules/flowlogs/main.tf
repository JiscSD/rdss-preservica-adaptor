resource "aws_flow_log" "flowlog" {
  log_group_name = "${aws_cloudwatch_log_group.flowlog_log_group.name}"
  iam_role_arn   = "${aws_iam_role.flowlog_role.arn}"
  vpc_id         = "${var.vpc_id}"
  traffic_type   = "ALL"
}

resource "aws_cloudwatch_log_group" "flowlog_log_group" {
  name = "preservicaservice-${terraform.workspace}-flowlogs"

  tags {
    "Name"        = "${var.project}-${terraform.workspace}-flowlogs"
    "Environment" = "${terraform.workspace}"
    "Project"     = "${var.project}"
    "Service"     = "${var.service}"
    "CostCentre"  = "${var.cost_centre}"
    "Owner"       = "${var.owner}"
    "ManagedBy"   = "Terraform"
  }
}

resource "aws_iam_role" "flowlog_role" {
  name = "${var.project}-${terraform.workspace}-flowlogs-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "vpc-flow-logs.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "flowlog_policy" {
  name = "${var.project}-${terraform.workspace}-flowlogs-policy"
  role = "${aws_iam_role.flowlog_role.id}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}
EOF
}
