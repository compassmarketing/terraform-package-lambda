variable "path" {
  description = "Relative path to code file.  (e.g. 'hello.js')"
}
variable "deps_filename" {
  description = "Pre-packeged external dependencies in a zip file"
  default = ""
}

variable "output_filename" {
  description = "Name of zip file into which lambda functions and external deps (if present) will be combined"
  default = "lambda_package.zip"
}

data "external" "lambda_packager" {
  program = [ "${path.module}/packager.py" ]
  query = {
    path = "${var.path}"
    output_filename = "${var.output_filename}"
    deps_filename = "${var.deps_filename}"
  }
}

output "path" { value = "${data.external.lambda_packager.result.path}" }
output "output_filename" { value = "${data.external.lambda_packager.result.output_filename}" }
output "output_base64sha256" { value = "${data.external.lambda_packager.result.output_base64sha256}" }
