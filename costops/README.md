# CostOps Tools

## `aws_pricing.py`

This script will download the pricing files from AWS and save them in `${HOME}/data/AWS`.

### `aws_pricing.py` Prerequisites

- Python 3.x
- Boto3 library

### `aws_pricing.py` Usage

```shell
usage: aws_pricing.py [-h] [--data-dir DATA_DIR] [--workers WORKERS]

AWS Pricing Data

options:
  -h, --help           show this help message and exit
  --data-dir DATA_DIR  Data directory
  --workers WORKERS    Number of workers
```

## `gpu_spots.py`

This script finds the cheapest AWS GPU spot instance that meets specified resource criteria using the AWS SDK for Python (Boto3).

### `gpu_spots.py` Prerequisites

- Python 3.x
- Boto3 library

### Usage

Run the script with the desired options to find the cheapest GPU spot instance:

```shell
usage: gpu_spots.py [-h] [--us-only] [--eu-only] [--min-gpu-ram MIN_GPU_RAM] [--min-cores MIN_CORES] [--min-ram MIN_RAM]
                    [--save-data]

Find the cheapest AWS GPU spot instance for your workload.

options:
  -h, --help            show this help message and exit
  --us-only             Limit search to US regions
  --eu-only             Limit search to EU regions
  --min-gpu-ram MIN_GPU_RAM
                        Minimum total GPU RAM in GB
  --min-cores MIN_CORES
                        Minimum number of CPU cores
  --min-ram MIN_RAM     Minimum system RAM in GB
  --save-data           Save the results to JSON files locally
```

If the `--save-data option` is used, the results will be saved to `gpu_spot_region_results.json` and `gpu_spot_best_result.json`.

#### Logging

The script uses Python's `logging` module to log debug and error messages. By default, the logging level is set to `ERROR`. You can change the logging level by modifying the `logging.basicConfig(level=logging.ERROR)` line in the script.
