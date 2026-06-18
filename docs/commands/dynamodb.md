# DynamoDB Commands

The DynamoDB command group analyzes DynamoDB tables for provisioned capacity and estimated monthly cost, helping surface over-provisioned or idle tables.

## Commands

### `cost-analysis`

Scan DynamoDB tables and report capacity, size, and estimated monthly cost, with a summary of the most expensive tables and totals grouped by project prefix.

```bash
aws-cloud-utilities dynamodb cost-analysis [OPTIONS]
```

#### Options

- `--region REGION` - Single region to scan (default: all regions)
- `--all-regions` - Scan all regions (this is the default behavior)
- `--top N` - Number of top-expensive tables to show (default: 10)
- `--output-file FILE` - Save results to file (`.json`, `.yaml`, `.csv`)
- `--profile PROFILE` - AWS profile to use
- `--output FORMAT` - Output format (table, json, yaml, csv)

#### How cost is estimated

For **provisioned-throughput** tables the estimated monthly cost is:

```
(ReadCapacityUnits + WriteCapacityUnits) * $0.0072 * 24 * 30
```

This uses us-west-2 provisioned pricing. **On-demand** (`PAY_PER_REQUEST`) tables are listed but shown as `On-Demand`; their cost is usage-based and cannot be derived from table metadata, so they are excluded from the provisioned-cost totals.

#### What it reports

- Per-table: region, billing mode, RCU/WCU, item count, size, and estimated monthly cost (sorted by cost)
- Total provisioned RCU/WCU and estimated monthly cost
- Top-N most expensive tables
- "Empty but expensive" tables (zero items but a meaningful provisioned cost)
- Cost totals grouped by project prefix (the part of the table name before the first `-`)

#### Examples

```bash
# Analyze every region
aws-cloud-utilities dynamodb cost-analysis

# Analyze a single region
aws-cloud-utilities dynamodb cost-analysis --region us-east-1

# Show the top 5 and save a JSON report
aws-cloud-utilities dynamodb cost-analysis --top 5 --output-file dynamodb-cost.json
```
