# CW Logs Scripts

## Scriopts

- `manage_logs.py` - list,download,set-retention,delete,list-exports,export Logs

## Extras

- `extras/combine_logs.py` - combine a directory of *.log into a single `.log` file.

----

## `manage_cw_logs.py` Usage

### List

```bash
usage: manage_cw_logs.py list [-h] [--region REGION] [--all-regions]
                              [--verbose]

options:
  -h, --help       show this help message and exit
  --region REGION  AWS region to use (default: us-east-1)
  --all-regions    List log groups from all available regions.
  --verbose        Enable verbose logging
```

### Download

```bash
usage: manage_cw_logs.py download [-h] [--days DAYS] [--region REGION]
                                  [--verbose]
                                  log_group

positional arguments:
  log_group        Name of the CloudWatch log group, or 'ALL' for all groups.

options:
  -h, --help       show this help message and exit
  --days DAYS      Number of days to look back for logs (default: 365)
  --region REGION  AWS region to use (default: us-east-1)
  --verbose        Enable verbose logging
```

### set-retention

```bash
usage: manage_cw_logs.py set-retention [-h] [--if-never] [--region REGION]
                                       [--verbose]
                                       log_group [retention]

positional arguments:
  log_group        Name of the CloudWatch log group.
  retention        Retention period in days (default: 30) if targeting log
                   groups with 'Never' retention.

options:
  -h, --help       show this help message and exit
  --if-never       Only set retention if current retention is 'Never'.
  --region REGION  AWS region to use (default: us-east-1)
  --verbose        Enable verbose logging
```

### delete

```bash
usage: manage_cw_logs.py delete [-h] [--region REGION] [--verbose] log_group

positional arguments:
  log_group        Name of the CloudWatch log group.

options:
  -h, --help       show this help message and exit
  --region REGION  AWS region to use (default: us-east-1)
  --verbose        Enable verbose logging
```

### list-exports

```bash
usage: manage_cw_logs.py list-exports [-h] [--pending] [--wait]
                                      [--region REGION] [--verbose]

options:
  -h, --help       show this help message and exit
  --pending        Show only pending (or running) export tasks.
  --wait           Wait and refresh status every 60 seconds if any tasks are
                   still running.
  --region REGION  AWS region to use (default: us-east-1)
  --verbose        Enable verbose logging
```

### export

```bash
usage: manage_cw_logs.py export [-h] [--start START] [--end END]
                                [--region REGION] [--verbose]
                                log_group

positional arguments:
  log_group        Name of the CloudWatch log group.

options:
  -h, --help       show this help message and exit
  --start START    Start time in epoch seconds. Defaults to 5 years ago.
  --end END        End time in epoch seconds. Defaults to now.
  --region REGION  AWS region to use (default: us-east-1)
  --verbose        Enable verbose logging
```
