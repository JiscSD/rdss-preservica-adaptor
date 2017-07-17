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

variable "name" {}

variable "shard_count" {
  description = "Stream shards number."
  default     = 1
}

variable "shard_level_metricsc" {
  description = "Metrics to tract on shards."
  type        = "list"

  default = [
    "IncomingBytes",
    "OutgoingBytes",
  ]
}

variable "retention_period" {
  description = "How many hours to keep date in stream, maximum is 168"
  default     = 24
}
