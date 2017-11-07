provider "aws" {
  region = "${var.aws_region}"
}

terraform {
  backend "s3" {
    bucket = "rdss-preservicaservice-terraform-state"
    key    = "preservicaservice.tfstate"
    region = "eu-west-2"
  }
}

####################
# SSH Key Pair
####################

data "template_file" "public_key" {
  template = "${file("public-keys/preservicaservice-${terraform.env}.pub")}"
}

resource "aws_key_pair" "auth" {
  key_name   = "${var.project}-${terraform.env}"
  public_key = "${data.template_file.public_key.rendered}"

  lifecycle {
    create_before_destroy = true
  }
}

####################
# S3 Objects
####################

data "template_file" "awslogs_agent_bastion_config" {
  template = "${file("./s3-objects/config-objects/bastion/awslogs-agent-config.conftemplate")}"

  vars {
    instance_type         = "bastion"
    terraform_environment = "${terraform.env}"
  }
}

resource "aws_s3_bucket_object" "config_objects_awslogs_agent_bastion_config" {
  bucket  = "${var.objects_bucket}"
  key     = "application/config/${terraform.env}/bastion/awslogs-agent-config.conf"
  content = "${data.template_file.awslogs_agent_bastion_config.rendered}"
  etag    = "${md5(data.template_file.awslogs_agent_bastion_config.rendered)}"
}

data "template_file" "awslogs_agent_node_config" {
  template = "${file("./s3-objects/config-objects/node/awslogs-agent-config.conftemplate")}"

  vars {
    instance_type         = "node"
    terraform_environment = "${terraform.env}"
  }
}

resource "aws_s3_bucket_object" "config_objects_awslogs_agent_node_config" {
  bucket  = "${var.objects_bucket}"
  key     = "application/config/${terraform.env}/node/awslogs-agent-config.conf"
  content = "${data.template_file.awslogs_agent_node_config.rendered}"
  etag    = "${md5(data.template_file.awslogs_agent_node_config.rendered)}"
}

####################
# VPC
####################

module "vpc" {
  source               = "./modules/vpc"
  enable_dns_support   = true
  enable_dns_hostnames = true
  availability_zones   = "${var.availability_zones}"
  project              = "${var.project}"
  service              = "${var.service}"
  cost_centre          = "${var.cost_centre}"
  owner                = "${var.owner}"
}

####################
# Bastion Server
####################

module "bastion" {
  source             = "./modules/bastion"
  key_name           = "${aws_key_pair.auth.key_name}"
  bastion_sg         = "${module.security_groups.bastion-sg}"
  public_subnet      = "${module.vpc.igw_subnet_id}"
  objects_bucket_arn = "arn:aws:s3:::${var.objects_bucket}"
  project            = "${var.project}"
  service            = "${var.service}"
  cost_centre        = "${var.cost_centre}"
  owner              = "${var.owner}"
  aws_region         = "${var.aws_region}"
}

####################
# Security Groups
####################

module "security_groups" {
  source               = "./modules/security_groups"
  access_ip_whitelist  = "${var.access_ip_whitelist}"
  private_subnets_cidr = "${module.vpc.private_subnets_cidr}"
  vpc                  = "${module.vpc.vpc_id}"
  project              = "${var.project}"
  service              = "${var.service}"
  cost_centre          = "${var.cost_centre}"
  owner                = "${var.owner}"
}

####################
# IAM
####################

module "iam_role" {
  source              = "./modules/iam_role"
  input_stream_arn    = "${data.aws_kinesis_stream.input_stream.arn}"
  error_stream_arn    = "arn:aws:kinesis:*:*:stream/${var.error_stream_name}_${terraform.env}"
  upload_buckets_arns = "${formatlist("arn:aws:s3:::preservica-%s-api-%s-autoupload", var.upload_buckets_ids, terraform.env)}"
  objects_bucket_arn  = "arn:aws:s3:::${var.objects_bucket}"
  dynamodb_arn        = "*"
  project             = "${var.project}"
}

####################
# Auto Scaling Group
####################

module "autoscaling" {
  source              = "./modules/autoscaling"
  key_name            = "${aws_key_pair.auth.key_name}"
  ami                 = "${var.instance_ami}"
  type                = "${var.instance_type}"
  security_groups     = ["${module.security_groups.app-sg}"]
  availability_zones  = "${var.availability_zones}"
  systemd_unit        = "${var.systemd_unit}"
  vpc_zone_identifier = ["${module.vpc.private_subnet_ids}"]
  role_name           = "${module.iam_role.role_name}"
  min_size            = "${var.autoscaling_min_size}"
  max_size            = "${var.autoscaling_max_size}"
  desired_capacity    = "${var.autoscaling_desired_capacity}"
  env_file_path       = "${var.autoscaling_env_file_path}"
  project             = "${var.project}"
  service             = "${var.service}"
  cost_centre         = "${var.cost_centre}"
  owner               = "${var.owner}"
}

####################
# Flow Logs
####################

module "flowlogs" {
  source      = "./modules/flowlogs"
  vpc_id      = "${module.vpc.vpc_id}"
  project     = "${var.project}"
  service     = "${var.service}"
  cost_centre = "${var.cost_centre}"
  owner       = "${var.owner}"
}

####################
# CloudWatch
####################

resource "aws_iam_user" "cloudwatch_kinesis_user" {
  name = "preservicaservice-${terraform.env}-cloudwatch-kinesis-user"
}

resource "aws_iam_access_key" "cloudwatch_kinesis_user_access_key" {
  user = "${aws_iam_user.cloudwatch_kinesis_user.name}"
}

resource "aws_iam_user_policy_attachment" "cloudwatch_kinesis_user_role_policy_attachment_cloudwatch" {
  user       = "${aws_iam_user.cloudwatch_kinesis_user.name}"
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchFullAccess"
}

resource "aws_iam_user_policy_attachment" "cloudwatch_kinesis_user_role_policy_attachment_dynamo" {
  user       = "${aws_iam_user.cloudwatch_kinesis_user.name}"
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

resource "aws_iam_user_policy_attachment" "cloudwatch_kinesis_user_role_policy_attachment_kinesis" {
  user       = "${aws_iam_user.cloudwatch_kinesis_user.name}"
  policy_arn = "arn:aws:iam::aws:policy/AmazonKinesisReadOnlyAccess"
}

resource "aws_iam_role" "cloudwatch_kinesis_role" {
  name = "preservicaservice-${terraform.env}-cloudwatch-kinesis-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": {
    "Effect": "Allow",
    "Principal": {
      "Service": "logs.${var.aws_region}.amazonaws.com"
    },
    "Action": "sts:AssumeRole"
  }
}
EOF
}

resource "aws_iam_role_policy" "cloudwatch_kinesis_policy" {
  name = "preservicaservice-${terraform.env}-cloudwatch-kinesis-policy"
  role = "${aws_iam_role.cloudwatch_kinesis_role.id}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "kinesis:PutRecord",
      "Resource": [
        "${module.cloudwatch_flowlogs_stream.arn}",
        "${module.cloudwatch_audit_stream.arn}",
        "${module.cloudwatch_cron_stream.arn}",
        "${module.cloudwatch_dmesg_stream.arn}",
        "${module.cloudwatch_messages_stream.arn}",
        "${module.cloudwatch_secure_stream.arn}",
        "${module.cloudwatch_debug_stream.arn}",
        "${module.cloudwatch_auth_stream.arn}",
        "${module.cloudwatch_dpkg_stream.arn}",
        "${module.cloudwatch_kern_stream.arn}",
        "${module.cloudwatch_syslog_stream.arn}"
      ]
    },
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "${aws_iam_role.cloudwatch_kinesis_role.arn}"
    }
  ]
}
EOF
}

resource "aws_cloudwatch_log_subscription_filter" "cloudwatch_flowlogs" {
  name            = "subscription_filter_preservicaservice_flowlogs_${terraform.env}"
  role_arn        = "${aws_iam_role.cloudwatch_kinesis_role.arn}"
  log_group_name  = "${module.flowlogs.log_group_name}"
  filter_pattern  = ""
  destination_arn = "${module.cloudwatch_flowlogs_stream.arn}"

  depends_on = ["aws_iam_role_policy.cloudwatch_kinesis_policy"]
}

resource "aws_cloudwatch_log_subscription_filter" "cloudwatch_audit" {
  name            = "subscription_filter_preservicaservice_audit_${terraform.env}"
  role_arn        = "${aws_iam_role.cloudwatch_kinesis_role.arn}"
  log_group_name  = "preservicaservice-${terraform.env}-/var/log/audit/audit.log"
  filter_pattern  = ""
  destination_arn = "${module.cloudwatch_audit_stream.arn}"

  depends_on = ["aws_iam_role_policy.cloudwatch_kinesis_policy"]
}

resource "aws_cloudwatch_log_subscription_filter" "cloudwatch_cron" {
  name           = "subscription_filter_preservicaservice_cron_${terraform.env}"
  role_arn       = "${aws_iam_role.cloudwatch_kinesis_role.arn}"
  log_group_name = "preservicaservice-${terraform.env}-/var/log/cron"
  filter_pattern = ""

  destination_arn = "${module.cloudwatch_cron_stream.arn}"

  depends_on = ["aws_iam_role_policy.cloudwatch_kinesis_policy"]
}

resource "aws_cloudwatch_log_subscription_filter" "cloudwatch_dmesg" {
  name            = "subscription_filter_preservicaservice_dmesg_${terraform.env}"
  role_arn        = "${aws_iam_role.cloudwatch_kinesis_role.arn}"
  log_group_name  = "preservicaservice-${terraform.env}-/var/log/dmesg"
  filter_pattern  = ""
  destination_arn = "${module.cloudwatch_dmesg_stream.arn}"

  depends_on = ["aws_iam_role_policy.cloudwatch_kinesis_policy"]
}

resource "aws_cloudwatch_log_subscription_filter" "cloudwatch_messages" {
  name            = "subscription_filter_preservicaservice_messages_${terraform.env}"
  role_arn        = "${aws_iam_role.cloudwatch_kinesis_role.arn}"
  log_group_name  = "preservicaservice-${terraform.env}-/var/log/messages"
  filter_pattern  = ""
  destination_arn = "${module.cloudwatch_messages_stream.arn}"

  depends_on = ["aws_iam_role_policy.cloudwatch_kinesis_policy"]
}

resource "aws_cloudwatch_log_subscription_filter" "cloudwatch_secure" {
  name           = "subscription_filter_preservicaservice_secure_${terraform.env}"
  role_arn       = "${aws_iam_role.cloudwatch_kinesis_role.arn}"
  log_group_name = "preservicaservice-${terraform.env}-/var/log/secure"
  filter_pattern = ""

  destination_arn = "${module.cloudwatch_secure_stream.arn}"

  depends_on = ["aws_iam_role_policy.cloudwatch_kinesis_policy"]
}

resource "aws_cloudwatch_log_subscription_filter" "cloudwatch_debug" {
  name            = "subscription_filter_preservicaservice_debug_${terraform.env}"
  role_arn        = "${aws_iam_role.cloudwatch_kinesis_role.arn}"
  log_group_name  = "preservicaservice-${terraform.env}-/var/log/preservicaservice/debug.log"
  filter_pattern  = ""
  destination_arn = "${module.cloudwatch_debug_stream.arn}"

  depends_on = ["aws_iam_role_policy.cloudwatch_kinesis_policy"]
}

resource "aws_cloudwatch_log_subscription_filter" "cloudwatch_auth" {
  name            = "subscription_filter_preservicaservice_auth_${terraform.env}"
  role_arn        = "${aws_iam_role.cloudwatch_kinesis_role.arn}"
  log_group_name  = "preservicaservice-${terraform.env}-/var/log/auth.log"
  filter_pattern  = ""
  destination_arn = "${module.cloudwatch_auth_stream.arn}"

  depends_on = ["aws_iam_role_policy.cloudwatch_kinesis_policy"]
}

resource "aws_cloudwatch_log_subscription_filter" "cloudwatch_dpkg" {
  name            = "subscription_filter_preservicaservice_dpkg_${terraform.env}"
  role_arn        = "${aws_iam_role.cloudwatch_kinesis_role.arn}"
  log_group_name  = "preservicaservice-${terraform.env}-/var/log/dpkg.log"
  filter_pattern  = ""
  destination_arn = "${module.cloudwatch_dpkg_stream.arn}"

  depends_on = ["aws_iam_role_policy.cloudwatch_kinesis_policy"]
}

resource "aws_cloudwatch_log_subscription_filter" "cloudwatch_kern" {
  name            = "subscription_filter_preservicaservice_kern_${terraform.env}"
  role_arn        = "${aws_iam_role.cloudwatch_kinesis_role.arn}"
  log_group_name  = "preservicaservice-${terraform.env}-/var/log/kern.log"
  filter_pattern  = ""
  destination_arn = "${module.cloudwatch_kern_stream.arn}"

  depends_on = ["aws_iam_role_policy.cloudwatch_kinesis_policy"]
}

resource "aws_cloudwatch_log_subscription_filter" "cloudwatch_syslog" {
  name            = "subscription_filter_preservicaservice_syslog_${terraform.env}"
  role_arn        = "${aws_iam_role.cloudwatch_kinesis_role.arn}"
  log_group_name  = "preservicaservice-${terraform.env}-/var/log/syslog"
  filter_pattern  = ""
  destination_arn = "${module.cloudwatch_syslog_stream.arn}"

  depends_on = ["aws_iam_role_policy.cloudwatch_kinesis_policy"]
}

####################
# Kinesis Streams
####################

data "aws_kinesis_stream" "input_stream" {
  name = "shared_services_output_${terraform.env}"
}

module "cloudwatch_flowlogs_stream" {
  source           = "./modules/kinesis"
  name             = "cloudwatch_preservicaservice_flowlogs_${terraform.env}"
  shard_count      = "${var.kinesis_shard_count}"
  retention_period = "${var.kinesis_retention_period}"
  project          = "${var.project}"
  service          = "${var.service}"
  cost_centre      = "${var.cost_centre}"
  owner            = "${var.owner}"
}

module "cloudwatch_audit_stream" {
  source           = "./modules/kinesis"
  name             = "cloudwatch_preservicaservice_audit_${terraform.env}"
  shard_count      = "${var.kinesis_shard_count}"
  retention_period = "${var.kinesis_retention_period}"
  project          = "${var.project}"
  service          = "${var.service}"
  cost_centre      = "${var.cost_centre}"
  owner            = "${var.owner}"
}

module "cloudwatch_cron_stream" {
  source           = "./modules/kinesis"
  name             = "cloudwatch_preservicaservice_cron_${terraform.env}"
  shard_count      = "${var.kinesis_shard_count}"
  retention_period = "${var.kinesis_retention_period}"
  project          = "${var.project}"
  service          = "${var.service}"
  cost_centre      = "${var.cost_centre}"
  owner            = "${var.owner}"
}

module "cloudwatch_dmesg_stream" {
  source           = "./modules/kinesis"
  name             = "cloudwatch_preservicaservice_dmesg_${terraform.env}"
  shard_count      = "${var.kinesis_shard_count}"
  retention_period = "${var.kinesis_retention_period}"
  project          = "${var.project}"
  service          = "${var.service}"
  cost_centre      = "${var.cost_centre}"
  owner            = "${var.owner}"
}

module "cloudwatch_messages_stream" {
  source           = "./modules/kinesis"
  name             = "cloudwatch_preservicaservice_messages_${terraform.env}"
  shard_count      = "${var.kinesis_shard_count}"
  retention_period = "${var.kinesis_retention_period}"
  project          = "${var.project}"
  service          = "${var.service}"
  cost_centre      = "${var.cost_centre}"
  owner            = "${var.owner}"
}

module "cloudwatch_secure_stream" {
  source           = "./modules/kinesis"
  name             = "cloudwatch_preservicaservice_secure_${terraform.env}"
  shard_count      = "${var.kinesis_shard_count}"
  retention_period = "${var.kinesis_retention_period}"
  project          = "${var.project}"
  service          = "${var.service}"
  cost_centre      = "${var.cost_centre}"
  owner            = "${var.owner}"
}

module "cloudwatch_debug_stream" {
  source           = "./modules/kinesis"
  name             = "cloudwatch_preservicaservice_debug_${terraform.env}"
  shard_count      = "${var.kinesis_shard_count}"
  retention_period = "${var.kinesis_retention_period}"
  project          = "${var.project}"
  service          = "${var.service}"
  cost_centre      = "${var.cost_centre}"
  owner            = "${var.owner}"
}

module "cloudwatch_auth_stream" {
  source           = "./modules/kinesis"
  name             = "cloudwatch_preservicaservice_auth_${terraform.env}"
  shard_count      = "${var.kinesis_shard_count}"
  retention_period = "${var.kinesis_retention_period}"
  project          = "${var.project}"
  service          = "${var.service}"
  cost_centre      = "${var.cost_centre}"
  owner            = "${var.owner}"
}

module "cloudwatch_dpkg_stream" {
  source           = "./modules/kinesis"
  name             = "cloudwatch_preservicaservice_dpkg_${terraform.env}"
  shard_count      = "${var.kinesis_shard_count}"
  retention_period = "${var.kinesis_retention_period}"
  project          = "${var.project}"
  service          = "${var.service}"
  cost_centre      = "${var.cost_centre}"
  owner            = "${var.owner}"
}

module "cloudwatch_kern_stream" {
  source           = "./modules/kinesis"
  name             = "cloudwatch_preservicaservice_kern_${terraform.env}"
  shard_count      = "${var.kinesis_shard_count}"
  retention_period = "${var.kinesis_retention_period}"
  project          = "${var.project}"
  service          = "${var.service}"
  cost_centre      = "${var.cost_centre}"
  owner            = "${var.owner}"
}

module "cloudwatch_syslog_stream" {
  source           = "./modules/kinesis"
  name             = "cloudwatch_preservicaservice_syslog_${terraform.env}"
  shard_count      = "${var.kinesis_shard_count}"
  retention_period = "${var.kinesis_retention_period}"
  project          = "${var.project}"
  service          = "${var.service}"
  cost_centre      = "${var.cost_centre}"
  owner            = "${var.owner}"
}
