# Quick Start

Get from installed to useful in about five minutes.

## Install and verify

```bash
git clone https://github.com/jon-the-dev/aws-cloud-tools.git
cd aws-cloud-tools
pip install -e .
```

```bash
aws-cloud-utilities --version
aws-cloud-utilities info
```

`info` prints the resolved profile, region, and caller identity. If that looks wrong, everything after
it will be wrong too, so start here.

```bash
# Confirm which account and identity you are using
aws-cloud-utilities account info

# Check that credentials work and see which permissions resolve
aws-cloud-utilities account validate
```

Most commands degrade gracefully when permissions are missing rather than failing outright, so
`account validate` is worth running before you read an empty result as "nothing there."

## Global options come first

```bash
aws-cloud-utilities [GLOBAL OPTIONS] COMMAND [SUBCOMMAND] [ARGUMENTS] [OPTIONS]
```

`--profile`, `--region`, `--output`, `--verbose`, `--debug`, and `--config` go **before** the command
name. Everything else goes after.

```bash
# Correct
aws-cloud-utilities --profile production --output json s3 list-buckets
```

```bash
# Rejected -- --output is not an option of 's3 list-buckets'  (validate-docs: ignore)
aws-cloud-utilities s3 list-buckets --output json
```

## See what exists

```bash
aws-cloud-utilities inventory services      # services the scanner supports
aws-cloud-utilities account regions         # every region
aws-cloud-utilities s3 list-buckets         # buckets, with regions
aws-cloud-utilities iam list-roles          # IAM roles
aws-cloud-utilities logs list-groups        # CloudWatch log groups
```

A full account inventory writes to a directory rather than the terminal, because the output is far
larger than a screen:

```bash
aws-cloud-utilities inventory scan --output-dir ./inventory
```

Scope it while you are getting oriented:

```bash
aws-cloud-utilities inventory scan --services ec2,s3,rds --regions us-east-1,us-west-2
```

## Find cost savings

```bash
# Spend by service over the last three months
aws-cloud-utilities costops cost-analysis

# EBS volumes worth changing -- usually the fastest win
aws-cloud-utilities costops ebs-optimization --all-regions --include-cost-estimates

# DynamoDB tables with provisioned capacity they are not using
aws-cloud-utilities dynamodb cost-analysis --top 10
```

Spot pricing is a two-step flow: collect, then analyze.

```bash
aws-cloud-utilities costops spot-pricing --all-regions --output-dir ./spot-data
aws-cloud-utilities costops spot-analysis ./spot-data --top-n 10
```

## Check security posture

```bash
# Findings from WAF, GuardDuty, and Security Hub
aws-cloud-utilities security metrics

# Certificates, including expired ones
aws-cloud-utilities security list-certificates --all-regions

# Config rules currently reporting non-compliance
aws-cloud-utilities awsconfig list-rules --compliance-state NON_COMPLIANT

# Dump every role and customer-managed policy for offline review
aws-cloud-utilities iam audit --output-dir ./iam-audit

# Account-wide S3 encryption report
aws-cloud-utilities s3 analyze-encryption --output-file s3-encryption.html
```

## Work with logs

```bash
# Log groups, with storage size
aws-cloud-utilities logs list-groups --include-size

# Download the last 7 days for one group
aws-cloud-utilities logs download /aws/lambda/my-function

# Find groups keeping data forever, then fix them
aws-cloud-utilities logs set-retention /aws/lambda/my-function 30 --if-never --dry-run
aws-cloud-utilities logs set-retention /aws/lambda/my-function 30 --if-never
```

Log groups with no retention policy keep data indefinitely and bill for it. `--if-never` only touches
those, so it is safe to run broadly.

## Get output you can script against

```bash
# JSON to stdout, for piping
aws-cloud-utilities --output json s3 list-buckets

# Write to a file; the format follows the extension
aws-cloud-utilities s3 list-buckets --output-file buckets.csv
aws-cloud-utilities logs list-groups --output-file log-groups.json
```

`--output` controls what is printed. `--output-file` writes to disk. They are independent, and not
every command has the latter - `iam list-roles` and `security list-certificates`, for instance, only
print. Redirect those instead:

```bash
aws-cloud-utilities --output json iam list-roles > roles.json
```

## Before you run anything destructive

A handful of commands delete data. They are listed in the
[command reference](../commands/index.md#commands-that-write-or-delete). Where `--dry-run` exists, use
it first:

```bash
aws-cloud-utilities s3 nuke-bucket my-bucket --dry-run
aws-cloud-utilities s3 delete-versions my-bucket --dry-run
aws-cloud-utilities cloudfront update-logging --log-bucket my-logs --dry-run
```

## When something does not work

```bash
# Every level is self-documenting
aws-cloud-utilities --help
aws-cloud-utilities costops --help
aws-cloud-utilities costops ebs-optimization --help
```

```bash
# See what is actually happening
aws-cloud-utilities --verbose --debug account validate
```

If this documentation disagrees with `--help`, trust `--help` and please
[open an issue](https://github.com/jon-the-dev/aws-cloud-tools/issues).

## Next

- [Configuration](configuration.md) - profiles, regions, and the config file
- [Command Reference](../commands/index.md) - every command, with options
- [Common Use Cases](../examples/common-use-cases.md) - longer worked examples
- [Migration from v1](migration.md) - mapping old scripts to v2 commands
