variable "name" {
  description = "The name of the subscription filter to create."
}

variable "role_arn" {
  description = "The ARN of the role for the subscription filter."
}

variable "log_group_name" {
  description = "The name of the log group that the subscription filter reads from."
}

variable "destination_arn" {
  description = "The ARN of the destination for the subscription filter."
}
