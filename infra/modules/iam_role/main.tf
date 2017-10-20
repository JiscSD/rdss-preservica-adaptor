resource "aws_iam_role" "role" {
  name = "${var.project}-${terraform.env}-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "input_stream" {
  name = "${var.project}-${terraform.env}-input-stream-policy"
  role = "${aws_iam_role.role.id}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kinesis:Get*",
        "kinesis:List*",
        "kinesis:Describe*"
      ],
      "Resource": [
        "${var.input_stream_arn}"
      ]
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "error_stream" {
  name = "${var.project}-${terraform.env}-error-stream-policy"
  role = "${aws_iam_role.role.id}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kinesis:Get*",
        "kinesis:List*",
        "kinesis:Describe*",
        "kinesis:Put*"
      ],
      "Resource": [
        "${var.error_stream_arn}"
      ]
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "dynamodb" {
  name = "${var.project}-${terraform.env}-dynamodb"
  role = "${aws_iam_role.role.id}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Stmt456",
      "Effect": "Allow",
      "Action": [
        "dynamodb:*"
      ],
      "Resource": [
        "${var.dynamodb_arn}"
      ]
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "upload" {
  name   = "${var.project}-${terraform.env}-upload-buckets"
  role   = "${aws_iam_role.role.id}"
  policy = "${data.aws_iam_policy_document.upload_buckets_policy.json}"
}

data "aws_iam_policy_document" "upload_buckets_policy" {
  statement {
    effect = "Allow"

    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation",
    ]

    resources = "${var.upload_buckets_arns}"
  }

  statement {
    effect = "Allow"

    actions = [
      "s3:Put*",
      "s3:Get*",
    ]

    resources = "${formatlist("%s/*", var.upload_buckets_arns)}"
  }
}

resource "aws_iam_role_policy" "cloudwatch" {
  name = "${var.project}-${terraform.env}-cloudwatch"
  role = "${aws_iam_role.role.id}"

  policy = <<EOF
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Effect":"Allow",
      "Action":[
        "cloudwatch:Put*"
      ],
      "Resource": ["*"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": [
        "arn:aws:logs:*:*:*"
      ]
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "objects" {
  name = "${var.project}-${terraform.env}-objects"
  role = "${aws_iam_role.role.id}"

  policy = <<EOF
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": [
        "${var.objects_bucket_arn}/*"
      ]
    }
  ]
}
EOF
}
