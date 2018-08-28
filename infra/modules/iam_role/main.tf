data "aws_kms_alias" "ssm" {
  name = "alias/aws/ssm"
}

resource "aws_iam_role" "role" {
  name = "${var.project}-${terraform.workspace}-role"

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
  name = "${var.project}-${terraform.workspace}-input-stream-policy"
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
  name = "${var.project}-${terraform.workspace}-error-stream-policy"
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

resource "aws_iam_role_policy" "invalid_stream" {
  name = "${var.project}-${terraform.workspace}-invalid-stream-policy"
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
        "${var.invalid_stream_arn}"
      ]
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "dynamodb" {
  name = "${var.project}-${terraform.workspace}-dynamodb"
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
  name   = "${var.project}-${terraform.workspace}-upload-buckets"
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

resource "aws_iam_role_policy" "jisc-repository-bucket" {
  name   = "${var.project}-${terraform.workspace}-jisc-repository-bucket"
  role   = "${aws_iam_role.role.id}"
  policy = "${data.aws_iam_policy_document.jisc_repository_bucket_policy.json}"
}

data "aws_iam_policy_document" "jisc_repository_bucket_policy" {
  statement {
    effect = "Allow"

    actions = ["s3:Get*"]

    resources = [
      "${var.jisc_repository_bucket_arn}",
      "${var.jisc_repository_bucket_arn}/*",
    ]
  }
}

resource "aws_iam_role_policy" "cloudwatch" {
  name = "${var.project}-${terraform.workspace}-cloudwatch"
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
  name = "${var.project}-${terraform.workspace}-objects"
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

resource "aws_iam_role_policy" "ssm" {
  name = "${var.project}-${terraform.workspace}-ssm"
  role = "${aws_iam_role.role.id}"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter"
            ],
            "Resource": [
              "arn:aws:ssm:::parameterpreservica-adaptor*${terraform.workspace}*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
              "kms:Decrypt"
            ],
            "Resource": [
                "${data.aws_kms_alias.ssm.arn}"
            ]
        }
    ]
}
EOF
}

resource "aws_iam_role_policy" "pure" {
  name = "${var.project}-${terraform.workspace}-pure"
  role = "${aws_iam_role.role.id}"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::pure-adaptor-*/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListObjects"
            ],
            "Resource": [
                "arn:aws:s3:::pure-adaptor-*"
            ]
        }
    ]
}
EOF
}
