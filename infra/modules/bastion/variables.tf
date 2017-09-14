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

variable "vpc" {
  description = "VPC the bastion is protecting."
}

variable "public_subnet" {
  description = "Public subnet for the bastion."
}

variable "access_ip_whitelist" {
  description = "IP whitelist for access to bastion server"
  type        = "list"
}

variable "key_name" {
  description = "The name of the public key to access the bastion server"
}
