variable "project" {
  default = "rdss-preservica-adaptor"
}

variable "service" {
  default = "RDSS"
}

variable "cost_centre" {
  default = "RDSS"
}

variable "owner" {
  default = "alan.mackenzie@digirati.com"
}

variable "aws_region" {
  default = "eu-west-2"
}

variable "account_id" {
  description = "AWS account to use."
}

####################
# S3 Objects
####################

variable "objects_bucket" {
  default = "rdss-preservicaservice-objects"
}

####################
# VPC
####################

variable "availability_zones" {
  description = "List of availability zones."
  type        = "list"

  default = [
    "eu-west-2a",
    "eu-west-2b",
  ]
}

####################
#  Auto Scaling Group
####################

variable "instance_ami" {
  description = "Instance AMI."
}

variable "instance_type" {
  description = "Instance type."
  default     = "t2.small"
}

####################
# S3 Upload Buckets
####################

variable "upload_buckets_ids" {
  description = "Upload bucket ARN."
  type        = "list"

  default = [
    44,
    1539,
    1288,
    280,
    799,
    747,
    89,
    854,
    476,
    471,
  ]
}

####################
# Autoscaling
####################

variable "autoscaling_min_size" {
  description = "Minimal size of instances in group."
  default     = 1
}

variable "autoscaling_max_size" {
  description = "Maximum size of instances in group."
  default     = 3
}

variable "autoscaling_desired_capacity" {
  description = "Desired capacity of instances in group."
  default     = 1
}

variable "autoscaling_env_file_path" {
  description = "Path to system environment file."
  default     = "/etc/preservicaservice.env"
}

####################
# Kinesis streams
####################

variable "invalid_stream_name" {
  description = "Invalid stream name."
  default     = "message_invalid"
}

variable "error_stream_name" {
  description = "Error stream name."
  default     = "message_error"
}

variable "kinesis_shard_count" {
  default = 1
}

variable "kinesis_retention_period" {
  default = 168
}

####################
# systemd
####################
variable "systemd_unit" {
  description = "SystemD unit name for application."
  default     = "preservicaservice"
}

####################
# IP Whitelist
####################

variable "access_ip_whitelist" {
  description = "IP whitelist for access to bastion server"
  type        = "list"

  default = [
    "62.254.125.26/32",  # Glasgow
    "46.102.195.182/32", # London
    "88.98.212.19/32",   # Mark Winterbottom
  ]
}

variable "uat_dev_uoj_workaround_bucket" {
  description = "Buckets to upload to for temp workaround until Preservica is available in UAT and DEV"
  default     = ["arn:aws:s3:::uk.ac.jisc.alpha.researchdata.s3.uoj.autoupload"]
}

variable "jisc_repository_bucket_arn" {
  description = "Jisc Repoository bucket ARN"
  default     = "arn:aws:s3:::repository-${terraform.workspace}-files"
}
