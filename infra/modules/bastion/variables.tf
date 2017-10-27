variable "project" {
  description = "The name of the project to which the bastion server belongs."
}

variable "service" {
  description = "The name of the service to which the bastion server belongs."
}

variable "cost_centre" {
  description = "The name of the cost centre to which the bastion server belongs."
}

variable "owner" {
  description = "The owner of the bastion server."
}

variable "aws_region" {
  description = "The AWS region into which the bastion server will be deployed."
}

variable "public_subnet" {
  description = "Public subnet for the bastion server."
}

variable "bastion_sg" {
  description = "Security group for the bastion server."
}

variable "key_name" {
  description = "The name of the public key to access the bastion server."
}

variable "objects_bucket_arn" {
  description = "The ARN of the objects bucket."
}
