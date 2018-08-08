variable "path" {
  description = "Relative path to code file.  (e.g. 'hello.js')"
}
variable "requirements" {
  description = "Requirements txt file"
  default = ""
}
variable "build_dir" {
  description = "Requirements txt file"
  default = ".lambda_build"
}

data "external" "lambda_packager" {
  program = [ "${path.module}/packager.py" ]
  query = {
    path = "${var.path}"
    requirements = "${var.requirements}"
    build_dir = "${var.build_dir}"
  }
}

output "output_filename" { value = "${data.external.lambda_packager.result["output_filename"]}" }
