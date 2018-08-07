variable "path" {
  description = "Relative path to code file.  (e.g. 'hello.js')"
}
variable "requirements" {
  description = "Requirements txt file"
}
variable "lambda_build_dir" {
  default = ".lambda_build"
}

resource "null_resource" "lambda_exporter" {

  provisioner "local-exec" "local-build" {
    command = "rm -rf ${var.lambda_build_dir} && mkdir -p ${var.lambda_build_dir}/packages && pip install -r ${var.requirements} -t ${var.lambda_build_dir}/packages"
  }

  triggers {
    requirements = "${md5(file(var.requirements))}"
  }
}

locals {
  null_resource_id = "${join(",",null_resource.lambda_exporter.*.id)}"
  archive_zip_file = "${var.lambda_build_dir}/${local.null_resource_id}-deps.zip"
}

data "null_data_source" "wait_for_lambda_exporter" {
  inputs = {
    resource_id = "${local.null_resource_id}"
    source_dir = "${var.lambda_build_dir}/packages"
  }
}

data "archive_file" "lambda_exporter" {
  output_path = "${local.archive_zip_file}"
  source_dir  = "${data.null_data_source.wait_for_lambda_exporter.outputs["source_dir"]}"
  type        = "zip"
}

data "external" "lambda_packager" {
  program = [ "${path.module}/packager.py" ]
  query = {
    path = "${var.path}"
    output_filename = "${var.lambda_build_dir}/lambda.zip"
    deps_filename = "${data.archive_file.lambda_exporter.output_path}"
  }
}

output "path" { value = "${data.external.lambda_packager.result["path"]}" }
output "output_filename" { value = "${data.external.lambda_packager.result["output_filename"]}" }
output "output_base64sha256" { value = "${data.external.lambda_packager.result["output_base64sha256"]}" }
