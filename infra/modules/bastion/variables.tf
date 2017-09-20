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

variable "public_subnet" {
  description = "Public subnet for the bastion."
}

variable "bastion_sg" {
  description = "Security group for the bastion."
}

variable "key_name" {
  description = "The name of the public key to access the bastion server"
}
