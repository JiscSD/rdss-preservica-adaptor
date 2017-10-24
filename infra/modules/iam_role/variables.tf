variable "project" {
  description = "The name of the project to which the IAM Role belongs."
}

variable "input_stream_arn" {
  description = "Input stream ARN."
}

variable "error_stream_arn" {
  description = "Error stream ARN."
}

variable "upload_buckets_arns" {
  description = "Upload bucket ARN."
  type        = "list"
  default     = []
}

variable "objects_bucket_arn" {
  description = "Object bucket ARN."
}

variable "dynamodb_arn" {
  description = "Dynamodb to keep kinesis stream read ARN."
  default     = "*"
}
