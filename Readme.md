# DOMjudge Cloudformation Generator
`dj_cfn_generator` creates cloudformation templates suited for running a DOMjudge cluster.

## Getting Started
`pip install dj_cfn_generator`

```
$ dj_cfn_generator --help
Usage: dj_cfn_generator [-v] [-f <file>]
       dj_cfn_generator [-v] -u [--bucket <s3bucket>]

Generate DOMjudge cluster cloudformation template on STDOUT.

Options:
  -u, --upload                  Upload template to Amazon S3
  --bucket <s3bucket>           Bucket to use for uploads[default: cloudcontest.org-cf-templates]
  -f <file>, --file <file>      Save template as <file>
  -v, --verbose                 Be verbose
  -h, --help                    Show this help message
```


## Developing
```
virtualenv venv
source venv/bin/activate
python setup.py develop
```
