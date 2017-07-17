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
}

module "input_stream" {
  source      = "./modules/kinesis"
  name        = "${var.input_stream_prefix}${terraform.env}"
  environment = "${terraform.env}"
  project     = "${var.project}"
  owner       = "${var.owner}"
  costcenter  = "${var.costcenter}"
  service     = "${var.service}"
}

module "iam_role" {
  source            = "./modules/iam_role"
  input_stream_arn  = "${module.input_stream.stream_arn}"
  error_stream_arn  = "arn:aws:kinesis:*:*:stream/${var.error_stream_name}_${terraform.env}"
  upload_bucket_arn = "arn:aws:s3:::${var.upload_bucket}"
  dynamodb_arn      = "*"
  environment       = "${terraform.env}"
  project           = "${var.project}"
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
  vpc_zone_identifier         = ["${split(",", var.launch_in_public_subnet == "true" ? join(",", module.vpc.public_subnet_ids) : join(",", module.vpc.private_subnet_ids))}"]
  associate_public_ip_address = "${var.launch_in_public_subnet}"
  role_name                   = "${module.iam_role.role_name}"
  min_size                    = "${var.autoscaling_min_size}"
  max_size                    = "${var.autoscaling_max_size}"
  desired_capacity            = "${var.autoscaling_desired_capacity}"
  env_file_path               = "${var.autoscaling_env_file_path}"
  environment                 = "${terraform.env}"
  project                     = "${var.project}"
  owner                       = "${var.owner}"
  costcenter                  = "${var.costcenter}"
  service                     = "${var.service}"
}
