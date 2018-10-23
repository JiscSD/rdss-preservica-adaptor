variable "project" {
  description = "The name of the project to which the Flow Logs belong."
}

variable "service" {
  description = "The name of the service to which the Flow Logs belongs."
}

variable "cost_centre" {
  description = "The name of the cost centre to which the Flow Logs belongs."
}

variable "owner" {
  description = "The owner of the Flow Logs."
}

variable "vpc_id" {
  description = "The ID of the VPC that the Flow Logs will monitor."
}
