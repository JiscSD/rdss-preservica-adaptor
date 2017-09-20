output "bastion-sg" {
  value = "${aws_security_group.bastion-sg.id}"
}

output "app-sg" {
  value = "${aws_security_group.app-sg.id}"
}
