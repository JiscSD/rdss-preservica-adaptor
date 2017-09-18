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

variable "enable_dns_support" {
  description = "To use private DNS within the VPC."
  default     = true
}

variable "enable_dns_hostnames" {
  description = "To use private hostname within the VPC."
  default     = true
}

variable "vpc_cidr" {
  description = "CIDR for VPC."
  default     = "10.0.0.0/16"
}

variable "private_subnets_cidr" {
  description = "CIDR for private subnets."

  type = "list"

  default = [
    "10.0.3.0/24",
    "10.0.4.0/24",
  ]
}

variable "nat_cidr" {
  description = "CIDR for NAT subnets."

  type = "list"

  default = [
    "10.0.5.0/24",
    "10.0.6.0/24",
  ]
}

variable "igw_cidr" {
  description = "CIDR to have access to IGW."
  default     = "10.0.8.0/24"
}

variable "availability_zones" {
  description = "Availability Zones for Subnets. Indexes must match `subnets_cidr`"
  type        = "list"
}
