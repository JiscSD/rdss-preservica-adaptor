variable "project" {
  description = "The name of the project to which the security group belongs."
}

variable "service" {
  description = "The name of the service to which the security group belongs."
}

variable "cost_centre" {
  description = "The name of the cost centre to which the security group belongs."
}

variable "owner" {
  description = "The owner of the security group."
}

variable "private_subnets_cidr" {
  description = "CIDR for private subnets."
  type        = "list"
}

variable "vpc" {
  description = "VPC the bastion is protecting."
}

variable "access_ip_whitelist" {
  description = "IP whitelist for access to bastion server"
  type        = "list"
}
