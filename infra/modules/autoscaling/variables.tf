variable "project" {
  description = "The name of the project to which the auto scaling group belongs."
}

variable "service" {
  description = "The name of the service to which the auto scaling group belongs."
}

variable "cost_centre" {
  description = "The name of the cost centre to which the auto scaling group belongs."
}

variable "owner" {
  description = "The owner of the auto scaling group."
}

variable "ami" {
  description = "Instance AMI."
}

variable "type" {
  description = "Instance type."
}

variable "key_name" {
  description = "SSH key to use for instance."
}

variable "security_groups" {
  description = "Security groups to attach on instance."
  type        = "list"
}

variable "availability_zones" {
  description = "Availability zones to lunch instances."
  type        = "list"
}

variable "vpc_zone_identifier" {
  description = "Subnets to lunch instances in."
  type        = "list"
}

variable "min_size" {
  description = "Minimal size of instances in group."
}

variable "max_size" {
  description = "Maximum size of instances in group."
}

variable "desired_capacity" {
  description = "Desired capacity of instances in group."
}

variable "health_check_type" {
  description = "Health check type."
  default     = "EC2"
}

variable "health_check_grace_period" {
  description = "Health check grace period in seconds."
  default     = 300
}

variable "force_delete" {
  description = "Force instance deletion."
  default     = true
}

variable "env_file_path" {
  description = "Path to system environment file."
}

variable "role_name" {
  description = "Autoscale profile role name."
}

variable "systemd_unit" {
  description = "SystemD unit name for application."
}
