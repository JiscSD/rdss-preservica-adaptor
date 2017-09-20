variable "account_id" {
  description = "AWS account to use."
}

variable "project" {
  description = "Project name for tags and resource naming."
  default     = "preservicaservice"
}

variable "owner" {
  description = "Contact person responsible for the resource."
  default     = "alan.mackenzie@digirati.com"
}

variable "costcenter" {
  description = "Cost Center tag."
  default     = "RDSS"
}

variable "service" {
  description = "Service name for tags."
  default     = "rdss"
}

variable "region" {
  default = "eu-west-2"
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
#  EC2 instance
####################
variable "instance_ami" {
  description = "Instance AMI."
}

variable "instance_type" {
  description = "Instance type."
  default     = "t2.small"
}

variable "key_name" {
  description = "SSH key to use for EC2 instance."
  default     = "preservica-service-test"
}

####################
# upload buckets
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
variable "input_stream_prefix" {
  description = "Pattern to name input stream."
  default     = "rdss-preservica-adaptor-input-"
}

variable "error_stream_name" {
  description = "Error stream name."
  default     = "message_error"
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
    "88.98.209.19/32",   # Mark Winterbottom
  ]
}
