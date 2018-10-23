variable "project" {
  description = "The name of the project to which the Kinesis Stream belongs."
}

variable "service" {
  description = "The name of the service to which the Kinesis Stream belongs."
}

variable "cost_centre" {
  description = "The name of the cost centre to which the Kinesis Stream belongs."
}

variable "owner" {
  description = "The owner of the Kinesis Stream."
}

variable "name" {
  description = "The name of the Kinesis Stream."
}

variable "shard_count" {
  description = "Stream shards number."
}

variable "retention_period" {
  description = "How many hours to keep date in stream, maximum is 168."
}
