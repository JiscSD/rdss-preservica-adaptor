provider "aws" {
  region = "${var.region}"
}

terraform {
  backend "s3" {
    bucket = "rdss-preservicaservice-terraform-state"
    key    = "preservicaservice.tfstate"
    region = "eu-west-2"
  }
}

module "vpc" {
  source               = "./modules/vpc"
  environment          = "${terraform.env}"
  enable_dns_support   = true
  enable_dns_hostnames = true
  availability_zones   = "${var.availability_zones}"
  project              = "${var.project}"
  owner                = "${var.owner}"
  costcenter           = "${var.costcenter}"
  service              = "${var.service}"
  access_ip_whitelist  = "${var.access_ip_whitelist}"
  bastion_ami          = "${var.bastion_ami}"
}

data "aws_kinesis_stream" "input_stream" {
  name = "shared_services_input_${terraform.env}"
}

module "iam_role" {
  source              = "./modules/iam_role"
  input_stream_arn    = "${data.aws_kinesis_stream.input_stream.arn}"
  error_stream_arn    = "arn:aws:kinesis:*:*:stream/${var.error_stream_name}_${terraform.env}"
  upload_buckets_arns = "${formatlist("arn:aws:s3:::preservica-%s-api-%s-autoupload", var.upload_buckets_ids, terraform.env)}"
  dynamodb_arn        = "*"
  environment         = "${terraform.env}"
  project             = "${var.project}"
}

module "autoscaling" {
  source             = "./modules/autoscaling"
  key_name           = "${var.key_name}"
  ami                = "${var.instance_ami}"
  type               = "${var.instance_type}"
  security_groups    = ["${module.vpc.security_group_all_id}"]
  availability_zones = "${var.availability_zones}"
  systemd_unit       = "${var.systemd_unit}"

  # https://github.com/hashicorp/terraform/issues/12453
  vpc_zone_identifier = ["${module.vpc.private_subnet_ids}"]
  role_name           = "${module.iam_role.role_name}"
  min_size            = "${var.autoscaling_min_size}"
  max_size            = "${var.autoscaling_max_size}"
  desired_capacity    = "${var.autoscaling_desired_capacity}"
  env_file_path       = "${var.autoscaling_env_file_path}"
  environment         = "${terraform.env}"
  project             = "${var.project}"
  owner               = "${var.owner}"
  costcenter          = "${var.costcenter}"
  service             = "${var.service}"
}
