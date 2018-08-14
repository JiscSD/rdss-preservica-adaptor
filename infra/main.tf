provider "aws" {
  region = "${var.aws_region}"
}

terraform {
  backend "s3" {
    bucket = "rdss-preservicaservice-terraform-state"
    key    = "preservicaservice.tfstate"
    region = "eu-west-2"
  }

  required_version = "0.10.8"
}

####################
# SSH Key Pair
####################

data "template_file" "public_key" {
  template = "${file("public-keys/preservicaservice-${terraform.workspace}.pub")}"
}

resource "aws_key_pair" "auth" {
  key_name   = "${var.project}-${terraform.workspace}"
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
    terraform_environment = "${terraform.workspace}"
  }
}

resource "aws_s3_bucket_object" "config_objects_awslogs_agent_bastion_config" {
  bucket  = "${var.objects_bucket}"
  key     = "application/config/${terraform.workspace}/bastion/awslogs-agent-config.conf"
  content = "${data.template_file.awslogs_agent_bastion_config.rendered}"
  etag    = "${md5(data.template_file.awslogs_agent_bastion_config.rendered)}"
}

data "template_file" "awslogs_agent_node_config" {
  template = "${file("./s3-objects/config-objects/node/awslogs-agent-config.conftemplate")}"

  vars {
    instance_type         = "node"
    terraform_environment = "${terraform.workspace}"
  }
}

resource "aws_s3_bucket_object" "config_objects_awslogs_agent_node_config" {
  bucket  = "${var.objects_bucket}"
  key     = "application/config/${terraform.workspace}/node/awslogs-agent-config.conf"
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
  source             = "./modules/iam_role"
  input_stream_arn   = "${data.aws_kinesis_stream.input_stream.arn}"
  invalid_stream_arn = "arn:aws:kinesis:*:*:stream/${var.invalid_stream_name}_${terraform.workspace}"
  error_stream_arn   = "arn:aws:kinesis:*:*:stream/${var.error_stream_name}_${terraform.workspace}"

  # upload_buckets_arns = "${formatlist("arn:aws:s3:::preservica-%s-api-%s-autoupload", var.upload_buckets_ids, terraform.workspace)}"

  # NOTE: The below is a temporary workaround until a `dev` and `uat` preservica
  # becomes available. Once that happens the bellow line can be removed and above
  # uncommented.
  upload_buckets_arns         = ["${split(",", terraform.workspace == "prod" ? join(",", formatlist("arn:aws:s3:::preservica-%s-api-%s-autoupload", var.upload_buckets_ids, terraform.workspace)) : join(",", var.uat_dev_uoj_workaround_bucket))}"]
  objects_bucket_arn          = "arn:aws:s3:::${var.objects_bucket}"
  jisc_repository_bucket_arn  = "${replace(var.jisc_repository_bucket_arn_template, "TERRAFORM-WORKSPACE", terraform.workspace)}"
  dynamodb_arn                = "*"
  project                     = "${var.project}"
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
# Kinesis Streams
####################

data "aws_kinesis_stream" "input_stream" {
  name = "shared_services_output_${terraform.workspace}"
}
