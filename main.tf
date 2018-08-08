variable "path" {
  description = "Relative path to code file.  (e.g. 'hello.js')"
}
variable "requirements" {
  description = "Requirements txt file"
  default = ""
}

data "external" "lambda_packager" {
  program = [ "${path.module}/packager.py" ]
  query = {
    path = "${var.path}"
    requirements = "${var.requirements}"
  }
}

output "output_filename" { value = "${data.external.lambda_packager.result["output_filename"]}" }
output "output_base64sha256" { value = "${data.external.lambda_packager.result["output_base64sha256"]}" }
