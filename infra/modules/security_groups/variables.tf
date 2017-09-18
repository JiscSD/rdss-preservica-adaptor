variable "project" {
  description = "Project name."
}

variable "owner" {
  description = "Project owner name."
}

variable "costcenter" {
  description = "Cost center name."
}

variable "service" {
  description = "Service name."
}

variable "environment" {
  description = "Environment we are working with."
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
