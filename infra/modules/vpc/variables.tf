variable "project" {
  description = "The name of the project to which the VPC belongs."
}

variable "service" {
  description = "The name of the service to which the VPC belongs."
}

variable "cost_centre" {
  description = "The name of the cost centre to which the VPC belongs."
}

variable "owner" {
  description = "The owner of the VPC."
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
