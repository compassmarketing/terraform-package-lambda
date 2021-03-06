variable "path" {
  description = "Relative path to code file.  (e.g. 'hello.js')"
}
variable "requirements" {
  description = "Requirements txt file"
  default = ""
}
variable "build_dir" {
  description = "Requirements txt file"
  default = "/tmp"
}

data "external" "lambda_packager" {
  program = [ "${path.module}/packager.py" ]
  query = {
    path = "${var.path}"
    build_dir = "${var.build_dir}"
    requirements = "${var.requirements}"
  }
}

output "output_filename" { value = "${data.external.lambda_packager.result["output_filename"]}" }
