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

data "template_file" "public_key" {
  template = "${file("public-keys/${var.project}-${terraform.env}.pub")}"
}

resource "aws_key_pair" "auth" {
  key_name   = "${var.project}-${terraform.env}"
  public_key = "${data.template_file.public_key.rendered}"

  lifecycle {
    create_before_destroy = true
  }
}

data "template_file" "awslogs_agent_config" {
  template = "${file("./s3-objects/config-objects/awslogs-agent-config.conftemplate")}"

  vars {
    terraform_environment = "${terraform.env}"
  }
}

resource "aws_s3_bucket_object" "config_objects_awslogs_agent_config" {
  bucket  = "${var.objects_bucket}"
  key     = "application/config/${terraform.env}/awslogs-agent-config.conf"
  content = "${data.template_file.awslogs_agent_config.rendered}"
  etag    = "${md5(data.template_file.awslogs_agent_config.rendered)}"
}

module "vpc" {
  source               = "./modules/vpc"
  environment          = "${terraform.env}"
  enable_dns_support   = true
  enable_dns_hostnames = true
  availability_zones   = "${var.availability_zones}"
  project              = "${var.project}"
  service              = "${var.service}"
  cost_centre          = "${var.cost_centre}"
  owner                = "${var.owner}"
}

module "bastion" {
  source        = "./modules/bastion"
  environment   = "${terraform.env}"
  key_name      = "${aws_key_pair.auth.key_name}"
  bastion_sg    = "${module.security_groups.bastion-sg}"
  public_subnet = "${module.vpc.igw_subnet_id}"
  project       = "${var.project}"
  service       = "${var.service}"
  cost_centre   = "${var.cost_centre}"
  owner         = "${var.owner}"
}

module "security_groups" {
  source               = "./modules/security_groups"
  environment          = "${terraform.env}"
  access_ip_whitelist  = "${var.access_ip_whitelist}"
  private_subnets_cidr = "${module.vpc.private_subnets_cidr}"
  vpc                  = "${module.vpc.vpc_id}"
  project              = "${var.project}"
  service              = "${var.service}"
  cost_centre          = "${var.cost_centre}"
  owner                = "${var.owner}"
}

data "aws_kinesis_stream" "input_stream" {
  name = "shared_services_output_${terraform.env}"
}

module "iam_role" {
  source              = "./modules/iam_role"
  input_stream_arn    = "${data.aws_kinesis_stream.input_stream.arn}"
  error_stream_arn    = "arn:aws:kinesis:*:*:stream/${var.error_stream_name}_${terraform.env}"
  upload_buckets_arns = "${formatlist("arn:aws:s3:::preservica-%s-api-%s-autoupload", var.upload_buckets_ids, terraform.env)}"
  objects_bucket_arn  = "arn:aws:s3:::${var.objects_bucket}"
  dynamodb_arn        = "*"
  environment         = "${terraform.env}"
  project             = "${var.project}"
}

module "autoscaling" {
  source             = "./modules/autoscaling"
  key_name           = "${aws_key_pair.auth.key_name}"
  ami                = "${var.instance_ami}"
  type               = "${var.instance_type}"
  security_groups    = ["${module.security_groups.app-sg}"]
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
  service             = "${var.service}"
  cost_centre         = "${var.cost_centre}"
  owner               = "${var.owner}"
}
