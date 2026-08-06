# Common Use Cases

Worked examples that chain several commands together. Every command here is checked against the CLI
in CI, so these scripts run as written.

## Onboarding an unfamiliar account

You have been handed credentials to an account nobody has documented. Establish what it is, what is in
it, and what it costs.

```bash
#!/usr/bin/env bash
set -euo pipefail

OUT="./onboarding-$(date +%Y%m%d)"
mkdir -p "$OUT"

# Who and where
aws-cloud-utilities account info
aws-cloud-utilities account validate
aws-cloud-utilities account contact-info
aws-cloud-utilities account detect-control-tower --verbose

# What support plan, and whether Trusted Advisor is available
aws-cloud-utilities support check-level

# What exists
aws-cloud-utilities inventory scan --output-dir "$OUT/inventory" --include-tags

# What it costs
aws-cloud-utilities costops cost-analysis --months 6 --output-file "$OUT/spend-by-service.csv"
aws-cloud-utilities costops cost-analysis --months 6 --group-by region --output-file "$OUT/spend-by-region.csv"
```

`account validate` matters more than it looks. Commands here degrade gracefully on missing
permissions, so a thin result may mean thin credentials rather than an empty account.

## Cost reduction pass

Ordered by how much money it usually finds per minute spent.

```bash
#!/usr/bin/env bash
set -euo pipefail

OUT="./cost-review-$(date +%Y%m%d)"
mkdir -p "$OUT"

# 1. Where the money goes
aws-cloud-utilities costops cost-analysis --months 12 --output-file "$OUT/annual-spend.csv"

# 2. EBS -- unattached volumes and gp2 that should be gp3
aws-cloud-utilities costops ebs-optimization --all-regions --include-cost-estimates \
    --output-file "$OUT/ebs.csv"

# 3. DynamoDB -- provisioned capacity nobody is using
aws-cloud-utilities dynamodb cost-analysis --output-file "$OUT/dynamodb.csv"

# 4. Log retention -- groups keeping data forever
aws-cloud-utilities logs list-groups --all-regions --include-size \
    --output-file "$OUT/log-groups.csv"

# 5. Drill into the top service from step 1
aws-cloud-utilities costops usage-metrics AmazonEC2 --months 6 --group-by instance_type \
    --output-file "$OUT/ec2-usage.csv"

# 6. Trusted Advisor, if the support plan allows it
aws-cloud-utilities support trusted-advisor cost-savings || \
    echo "Trusted Advisor needs Business or Enterprise support -- skipped"
```

Cost Explorer bills roughly $0.01 per request, so a loop over every service adds up. Start with the
grouped view and drill into the two or three services that dominate.

### Spot pricing for batch workloads

Two steps, in order:

```bash
aws-cloud-utilities costops spot-pricing --all-regions \
    --instance-types m5.xlarge,m5.2xlarge,c5.xlarge \
    --time-range 168 \
    --output-dir ./spot-data

aws-cloud-utilities costops spot-analysis ./spot-data --top-n 20 --estimate-period 30
```

`spot-pricing` collects; `spot-analysis` reads the directory it wrote and ranks the results.

## Security review

```bash
#!/usr/bin/env bash
set -euo pipefail

OUT="./security-$(date +%Y%m%d)"
mkdir -p "$OUT"

# Findings from WAF, GuardDuty, and Security Hub, past week
aws-cloud-utilities security metrics --time-range 168 --all-regions \
    --output-file "$OUT/findings.json"

# Config rules currently failing
aws-cloud-utilities awsconfig list-rules --all-regions --compliance-state NON_COMPLIANT \
    --output-file "$OUT/failing-rules.csv"
aws-cloud-utilities awsconfig compliance-checker --all-regions --show-details \
    --output-file "$OUT/compliance.json"

# Full IAM surface, on disk
aws-cloud-utilities iam audit --output-dir "$OUT/iam"
aws-cloud-utilities --output csv iam list-policies --only-attached > "$OUT/attached-policies.csv"

# S3 encryption across every bucket
aws-cloud-utilities s3 analyze-encryption --output-file "$OUT/s3-encryption.html"

# Certificates about to become someone's outage
aws-cloud-utilities --output csv security list-certificates --all-regions > "$OUT/certificates.csv"
```

Not every command has `--output-file`. Where it is missing, set the global `--output` format and
redirect, as above.

### Diffing IAM between reviews

The point of `iam audit` writing to disk is that you can compare runs:

```bash
aws-cloud-utilities iam audit --output-dir "./iam-$(date +%Y%m%d)"
diff -r ./iam-20260701 ./iam-20260801
```

Anything in that diff is a permission change nobody mentioned.

## Log cleanup

CloudWatch log groups with no retention policy keep data forever and bill for it monthly. This is
usually the cheapest recurring saving available.

```bash
#!/usr/bin/env bash
set -euo pipefail

# What is there, and how big
aws-cloud-utilities logs list-groups --all-regions --include-size --output-file log-groups.csv

# Preview retention changes, only touching groups set to 'Never'
aws-cloud-utilities logs set-retention /aws/lambda/my-function 30 --if-never --dry-run

# Apply
aws-cloud-utilities logs set-retention /aws/lambda/my-function 30 --if-never
```

`--if-never` skips groups that already have a policy, so it will not silently shorten retention
somebody chose deliberately.

### Pulling logs down for offline analysis

```bash
# Download, then compact into larger files
aws-cloud-utilities logs download /aws/lambda/my-function --days 30 --output-dir ./raw-logs
aws-cloud-utilities logs aggregate ./raw-logs --target-size 250 --prefix lambda --output-dir ./compact

# Or merge into one chronologically sorted file
aws-cloud-utilities logs combine ./raw-logs --output-file combined.log
```

`aggregate` and `combine` work on local directories, not on CloudWatch. Download first.

## Disaster recovery snapshots

Infrastructure that was clicked together rather than committed to a repo has no source of truth.
These commands create one.

```bash
#!/usr/bin/env bash
set -euo pipefail

OUT="./dr-snapshot-$(date +%Y%m%d)"

# Every stack template, parameter set, and output, every region
aws-cloud-utilities cloudformation backup --output-dir "$OUT/cloudformation" --format yaml

# Everything else, including the CloudFormation backups
aws-cloud-utilities inventory download-all --output-dir "$OUT/inventory" \
    --include-cloudformation --include-tags

# IAM, separately, because it is the hardest to reconstruct
aws-cloud-utilities iam audit --output-dir "$OUT/iam" --format yaml
```

Run it on a schedule and keep the output in version control. The diff between two snapshots is a
change log you did not have to write.

## Setting up cost reporting from scratch

If the account has no Cost and Usage Report, most cost tooling has nothing to read.

```bash
# See the plan without creating anything
aws-cloud-utilities billing cur-setup --bucket my-cur-bucket --dry-run

# Create the bucket, policy, lifecycle rule, and report in one step
aws-cloud-utilities billing cur-setup --bucket my-cur-bucket \
    --time-unit HOURLY --retention-days 365

# Confirm it registered
aws-cloud-utilities billing cur-list
aws-cloud-utilities billing cur-details hourly-cur
```

CUR is a us-east-1 global service, and the first file can take up to 24 hours to land.

## Cleaning up an S3 bucket safely

```bash
# What is actually in there
aws-cloud-utilities s3 bucket-details my-bucket --include-all

# Preview version cleanup
aws-cloud-utilities s3 delete-versions my-bucket --dry-run

# Remove old versions under one prefix
aws-cloud-utilities s3 delete-versions my-bucket --prefix old/ --delete-all-versions --confirm
```

To retire a bucket entirely while keeping a copy:

```bash
aws-cloud-utilities s3 nuke-bucket my-bucket --dry-run
aws-cloud-utilities s3 nuke-bucket my-bucket --download-first --output-dir ./bucket-backup --confirm
```

`--download-first` is the only built-in undo. Neither command is recoverable without it.

## Turning on CloudFront logging fleet-wide

```bash
# What exists and whether logging is already on
aws-cloud-utilities cloudfront list-distributions --include-disabled --show-logging-status

# Preview -- this touches every distribution in the account
aws-cloud-utilities cloudfront update-logging --log-bucket my-cf-logs --dry-run

# Apply
aws-cloud-utilities cloudfront update-logging --log-bucket my-cf-logs --log-prefix cf-logs
```

Then compact the delivered logs once they start arriving:

```bash
aws-cloud-utilities s3 download my-cf-logs --prefix cf-logs/ --output-dir ./cf-raw
aws-cloud-utilities logs aggregate ./cf-raw --log-type cloudfront --target-size 500
```

CloudWatch alarms (`--setup-alarms`) are billable per alarm per month and require `--sns-topic`. They
are deliberately not part of the default logging change.

## Debugging a WAF block

Someone reports a legitimate request being rejected.

```bash
# Find the Web ACL -- scope matters
aws-cloud-utilities waf list
aws-cloud-utilities --region us-east-1 waf list --scope CLOUDFRONT

# Which rules are firing
aws-cloud-utilities waf stats --web-acl my-web-acl --hours 24

# Full report: config, per-rule counts, sampled requests
aws-cloud-utilities waf troubleshoot --web-acl my-web-acl --hours 24 --output-file waf-report.json
```

A Web ACL missing from `list` is almost always a scope mismatch. `REGIONAL` covers ALB, API Gateway,
AppSync, and Cognito; `CLOUDFRONT` covers distributions and only resolves from `us-east-1`.

Sampled requests cover a rolling three-hour window, so `--hours 24` gives aggregate metrics without
per-request samples beyond that window.

## Automating a scheduled report

```bash
#!/usr/bin/env bash
# Weekly account report. Add to cron or a scheduled CI job.
set -euo pipefail

OUT="./weekly-$(date +%Y%m%d)"
mkdir -p "$OUT"

aws-cloud-utilities --output json account info > "$OUT/account.json"
aws-cloud-utilities costops cost-analysis --months 1 --output-file "$OUT/spend.csv"
aws-cloud-utilities security metrics --time-range 168 --output-file "$OUT/security.json"
aws-cloud-utilities logs list-groups --include-size --output-file "$OUT/log-groups.csv"
aws-cloud-utilities s3 list-buckets --include-size --output-file "$OUT/buckets.csv"

echo "Report written to $OUT"
```

Global options such as `--output` go before the command name. Command-level `--output-file` goes
after, and picks its format from the extension.

## Working across several accounts

```bash
#!/usr/bin/env bash
set -euo pipefail

for profile in dev staging production; do
  echo "=== $profile ==="
  aws-cloud-utilities --profile "$profile" account info
  aws-cloud-utilities --profile "$profile" costops cost-analysis --months 1 \
      --output-file "spend-${profile}.csv"
done
```

Some commands are single-region only. Loop over regions with the global `--region` flag where there is
no `--all-regions` or `--regions` option:

```bash
for region in us-east-1 us-west-2 eu-west-1; do
  aws-cloud-utilities --region "$region" rds list-instances
done
```

## Related

- [Command Reference](../commands/index.md) - every command and option
- [Quick Start](../getting-started/quick-start.md) - the five-minute version
- [Configuration](../getting-started/configuration.md) - profiles, regions, and defaults
