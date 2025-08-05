# Step Functions Commands

Step Functions workflow management commands for state machine operations and execution monitoring.

## Commands

### `list`

List Step Functions state machines with status and details.

```bash
aws-cloud-utilities stepfunctions list
```

**Options:**
- `--region REGION` - AWS region to query (default: all regions)
- `--status STATUS` - Filter by state machine status (ACTIVE, DELETING)
- `--type TYPE` - Filter by state machine type (STANDARD, EXPRESS)
- `--include-definition` - Include state machine definition in output
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# List all state machines
aws-cloud-utilities stepfunctions list

# List state machines in specific region
aws-cloud-utilities stepfunctions list --region us-east-1

# List only active state machines
aws-cloud-utilities stepfunctions list --status ACTIVE

# List EXPRESS type state machines
aws-cloud-utilities stepfunctions list --type EXPRESS

# Include definitions and save to file
aws-cloud-utilities stepfunctions list --include-definition --output-file state-machines.json
```

### `describe`

Get detailed information about a specific state machine.

```bash
aws-cloud-utilities stepfunctions describe STATE_MACHINE_ARN
```

**Arguments:**
- `STATE_MACHINE_ARN` - ARN of the state machine to describe

**Options:**
- `--region REGION` - AWS region where state machine exists
- `--include-definition` - Include the state machine definition
- `--include-executions` - Include recent execution history
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# Basic state machine details
aws-cloud-utilities stepfunctions describe arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine

# Include definition and executions
aws-cloud-utilities stepfunctions describe arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine --include-definition --include-executions

# Save to file
aws-cloud-utilities stepfunctions describe arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine --output-file state-machine-details.json
```

### `execute`

Start execution of a state machine with optional input.

```bash
aws-cloud-utilities stepfunctions execute STATE_MACHINE_ARN
```

**Arguments:**
- `STATE_MACHINE_ARN` - ARN of the state machine to execute

**Options:**
- `--region REGION` - AWS region where state machine exists
- `--input INPUT` - JSON input for the execution
- `--input-file FILE` - File containing JSON input
- `--name NAME` - Name for the execution (auto-generated if not provided)
- `--wait` - Wait for execution to complete
- `--timeout SECONDS` - Timeout for waiting (default: 300)

**Examples:**
```bash
# Start execution with no input
aws-cloud-utilities stepfunctions execute arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine

# Start execution with JSON input
aws-cloud-utilities stepfunctions execute arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine --input '{"key": "value"}'

# Start execution with input from file
aws-cloud-utilities stepfunctions execute arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine --input-file input.json

# Start execution and wait for completion
aws-cloud-utilities stepfunctions execute arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine --wait --timeout 600

# Start execution with custom name
aws-cloud-utilities stepfunctions execute arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine --name MyExecution-$(date +%Y%m%d-%H%M%S)
```

### `list-executions`

List executions for a state machine with filtering options.

```bash
aws-cloud-utilities stepfunctions list-executions STATE_MACHINE_ARN
```

**Arguments:**
- `STATE_MACHINE_ARN` - ARN of the state machine

**Options:**
- `--region REGION` - AWS region where state machine exists
- `--status STATUS` - Filter by execution status (RUNNING, SUCCEEDED, FAILED, TIMED_OUT, ABORTED)
- `--max-results NUM` - Maximum number of executions to return
- `--start-time TIME` - Filter executions started after this time (ISO format)
- `--end-time TIME` - Filter executions started before this time (ISO format)
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# List all executions
aws-cloud-utilities stepfunctions list-executions arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine

# List only failed executions
aws-cloud-utilities stepfunctions list-executions arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine --status FAILED

# List recent executions
aws-cloud-utilities stepfunctions list-executions arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine --start-time 2024-01-01T00:00:00Z

# Limit results and save to file
aws-cloud-utilities stepfunctions list-executions arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine --max-results 50 --output-file executions.json
```

### `logs`

Get execution logs and history for a state machine execution.

```bash
aws-cloud-utilities stepfunctions logs EXECUTION_ARN
```

**Arguments:**
- `EXECUTION_ARN` - ARN of the execution to get logs for

**Options:**
- `--region REGION` - AWS region where execution exists
- `--include-input-output` - Include input and output data in logs
- `--max-events NUM` - Maximum number of events to return
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# Get execution logs
aws-cloud-utilities stepfunctions logs arn:aws:states:us-east-1:123456789012:execution:MyStateMachine:execution-name

# Include input/output data
aws-cloud-utilities stepfunctions logs arn:aws:states:us-east-1:123456789012:execution:MyStateMachine:execution-name --include-input-output

# Limit events and save to file
aws-cloud-utilities stepfunctions logs arn:aws:states:us-east-1:123456789012:execution:MyStateMachine:execution-name --max-events 100 --output-file execution-logs.json
```

## Global Options

All Step Functions commands support these global options:

- `--profile PROFILE` - AWS profile to use
- `--region REGION` - AWS region
- `--output FORMAT` - Output format (table, json, yaml, csv)
- `--verbose` - Enable verbose output
- `--debug` - Enable debug mode

## Examples

### State Machine Monitoring Workflow

```bash
#!/bin/bash
# Monitor Step Functions state machines

MONITORING_DIR="./stepfunctions-monitoring-$(date +%Y%m%d)"
mkdir -p $MONITORING_DIR

echo "=== State Machine Inventory ==="
aws-cloud-utilities stepfunctions list --include-definition --output-file $MONITORING_DIR/state-machines.json

echo "=== Failed Executions ==="
aws-cloud-utilities stepfunctions list --output json | \
jq -r '.[].stateMachineArn' | \
while read arn; do
    echo "Checking failed executions for: $arn"
    aws-cloud-utilities stepfunctions list-executions $arn --status FAILED --output-file $MONITORING_DIR/failed-$(basename $arn).json
done

echo "=== Monitoring Complete ==="
echo "Monitoring data saved to: $MONITORING_DIR"
```

### Execution Analysis Script

```bash
#!/bin/bash
# Analyze specific state machine executions

STATE_MACHINE_ARN="arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine"
ANALYSIS_DIR="./execution-analysis-$(date +%Y%m%d)"

mkdir -p $ANALYSIS_DIR

echo "=== State Machine Details ==="
aws-cloud-utilities stepfunctions describe $STATE_MACHINE_ARN --include-definition --output-file $ANALYSIS_DIR/state-machine.json

echo "=== Recent Executions ==="
aws-cloud-utilities stepfunctions list-executions $STATE_MACHINE_ARN --max-results 100 --output-file $ANALYSIS_DIR/executions.json

echo "=== Failed Execution Analysis ==="
aws-cloud-utilities stepfunctions list-executions $STATE_MACHINE_ARN --status FAILED --output json | \
jq -r '.[].executionArn' | head -5 | \
while read exec_arn; do
    echo "Analyzing execution: $exec_arn"
    aws-cloud-utilities stepfunctions logs $exec_arn --include-input-output --output-file $ANALYSIS_DIR/logs-$(basename $exec_arn).json
done

echo "=== Analysis Complete ==="
echo "Analysis data saved to: $ANALYSIS_DIR"
```

### Batch Execution Script

```bash
#!/bin/bash
# Execute state machine with multiple inputs

STATE_MACHINE_ARN="arn:aws:states:us-east-1:123456789012:stateMachine:BatchProcessor"
INPUT_DIR="./batch-inputs"
RESULTS_DIR="./batch-results-$(date +%Y%m%d)"

mkdir -p $RESULTS_DIR

echo "=== Starting Batch Executions ==="

for input_file in $INPUT_DIR/*.json; do
    filename=$(basename $input_file .json)
    execution_name="batch-$filename-$(date +%Y%m%d-%H%M%S)"
    
    echo "Starting execution: $execution_name"
    aws-cloud-utilities stepfunctions execute $STATE_MACHINE_ARN \
        --input-file $input_file \
        --name $execution_name \
        --wait \
        --timeout 600 > $RESULTS_DIR/$execution_name.log
    
    echo "Execution $execution_name completed"
done

echo "=== Batch Executions Complete ==="
echo "Results saved to: $RESULTS_DIR"
```

### Health Check Script

```bash
#!/bin/bash
# Health check for Step Functions

echo "=== Step Functions Health Check ==="

# Check for active state machines
echo "Active State Machines:"
aws-cloud-utilities stepfunctions list --status ACTIVE --output table

# Check for running executions
echo -e "\n=== Running Executions ==="
aws-cloud-utilities stepfunctions list --output json | \
jq -r '.[].stateMachineArn' | \
while read arn; do
    running_count=$(aws-cloud-utilities stepfunctions list-executions $arn --status RUNNING --output json | jq '. | length')
    if [ $running_count -gt 0 ]; then
        echo "$arn: $running_count running executions"
    fi
done

# Check for recent failures
echo -e "\n=== Recent Failures ==="
aws-cloud-utilities stepfunctions list --output json | \
jq -r '.[].stateMachineArn' | \
while read arn; do
    failed_count=$(aws-cloud-utilities stepfunctions list-executions $arn --status FAILED --start-time $(date -d '1 hour ago' -Iseconds) --output json | jq '. | length')
    if [ $failed_count -gt 0 ]; then
        echo "$arn: $failed_count failures in last hour"
    fi
done

echo -e "\n=== Health Check Complete ==="
```

## Common Use Cases

1. **State Machine Management**
   ```bash
   aws-cloud-utilities stepfunctions list --include-definition
   aws-cloud-utilities stepfunctions describe arn:aws:states:region:account:stateMachine:name
   ```

2. **Execution Monitoring**
   ```bash
   aws-cloud-utilities stepfunctions list-executions arn:aws:states:region:account:stateMachine:name --status FAILED
   aws-cloud-utilities stepfunctions logs arn:aws:states:region:account:execution:name:id
   ```

3. **Automated Execution**
   ```bash
   aws-cloud-utilities stepfunctions execute arn:aws:states:region:account:stateMachine:name --input-file data.json --wait
   ```

4. **Troubleshooting**
   ```bash
   aws-cloud-utilities stepfunctions list-executions arn:aws:states:region:account:stateMachine:name --status FAILED
   aws-cloud-utilities stepfunctions logs arn:aws:states:region:account:execution:name:id --include-input-output
   ```

## Integration with Other Commands

Step Functions commands work well with other AWS Cloud Utilities:

```bash
# Combine with logs analysis
aws-cloud-utilities stepfunctions logs execution-arn --include-input-output
aws-cloud-utilities logs aggregate --log-group /aws/stepfunctions/MyStateMachine

# Combine with inventory
aws-cloud-utilities inventory resources --resource-type stepfunctions
aws-cloud-utilities stepfunctions list --include-definition
```

## Best Practices

- Use meaningful execution names for easier tracking
- Monitor failed executions regularly for operational issues
- Include input/output data in logs for debugging
- Set appropriate timeouts for long-running workflows
- Use JSON files for complex input data
- Implement proper error handling in state machine definitions
- Regular backup of state machine definitions
- Monitor execution costs for EXPRESS workflows
