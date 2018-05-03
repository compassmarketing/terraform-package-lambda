# terraform-package-lambda

This is a terraform module which provides an external data source which does
all the work in packaging an AWS lambda.

It tries really hard to make packages [*repeatable*](#repeatability) (see below).

## Usage

```hcl
module "lambda-package" {
  source = "github.com/2uinc/terraform-package-lambda"
  path   = "lambdas"
  output_filename = "lambda_package.zip"
  /*
   * Optional zip file containing external dependencies.
   */
  deps_filename = "deps.zip"
}

resource "aws_lambda_function" "my_lambda" {
  /* ... */
  filename = "${module.lambda-package.output_filename}"
  source_code_hash = "${module.lambda-package.output_base64sha256}"
  /* ... */
}
```

## Repeatability

`terraform-package-lambda` tries really hard to make packages *repeatable* by
working around quirks in `pip` (compile times embedded in the `.pyc`
files).

This is a hard problem, as these tools were not designed to produce identical
results on every run.  There may be other places that encode compile times
or have randomness, for example in binary extensions.

If you find that Terraform wants to update the source every time you run
`terraform plan` or `terraform apply`, save two copies of the zip file with
different hashes, as `a.zip` and `b.zip` and do the following:

```sh
$ zipinfo -v a.zip > a.txt
$ zipinfo -v b.zip > b.txt
$ diff -u a.txt b.txt |less
```

This should give you an idea of which files are changing and how.  If file
contents are changing, you will see changed CRC-32 values in the diffs.
Otherwise you'll see changed permissions, modified times, or something.

Submit a bug report. Bonus: Submit a test case that demonstrates the failure.

## Developing

Run tests with `python -munittest discover`.

Every bug fix should have a corresponding test case which demonstrates the
problem.  Every new feature should be test-covered.
