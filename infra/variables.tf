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

  type = "list"

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
  description = "SSh key to use for EC2 instance."
  default     = "preservica-service-test"
}

####################
# Autoscaling
####################
variable "launch_in_public_subnet" {
  description = "Launch ASG ec2 nodes into public subnet"
  default     = "true"
}

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
