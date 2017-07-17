resource "aws_kinesis_stream" "stream" {
  name                = "${var.name}"
  shard_count         = "${var.shard_count}"
  retention_period    = "${var.retention_period}"
  shard_level_metrics = "${var.shard_level_metricsc}"

  tags {
    Name        = "${var.project}-${terraform.env}-stream-${var.name}"
    Environment = "${terraform.env}"
    Project     = "${var.project}"
    Owner       = "${var.owner}"
    CostCenter  = "${var.costcenter}"
    managed_by  = "terraform"
    service     = "${var.service}"
  }
}
