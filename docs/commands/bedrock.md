# Bedrock Commands

Amazon Bedrock management commands for foundation models, custom models, and AI/ML operations.

## Commands

### `list-models`

List Amazon Bedrock foundation models across regions.

```bash
aws-cloud-utilities bedrock list-models
```

**Options:**
- `--region REGION` - Specific region to list models from (default: all regions)
- `--output-file FILE` - Save results to file (supports .json, .csv, .yaml)
- `--model-type TYPE` - Type of models to list (foundation, custom, all) [default: foundation]
- `--provider PROVIDER` - Filter by model provider (e.g., amazon, anthropic, ai21, cohere)

**Examples:**
```bash
# List all foundation models
aws-cloud-utilities bedrock list-models

# List models from specific region
aws-cloud-utilities bedrock list-models --region us-east-1

# Filter by provider
aws-cloud-utilities bedrock list-models --provider anthropic

# Save to file
aws-cloud-utilities bedrock list-models --output-file bedrock-models.json
```

### `model-details`

Get detailed information about a specific Bedrock model.

```bash
aws-cloud-utilities bedrock model-details MODEL_ID
```

**Arguments:**
- `MODEL_ID` - The model identifier to get details for

**Options:**
- `--region REGION` - AWS region to query (default: current region)
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# Get model details
aws-cloud-utilities bedrock model-details anthropic.claude-v2

# Save details to file
aws-cloud-utilities bedrock model-details anthropic.claude-v2 --output-file claude-details.json
```

### `list-custom-models`

List custom models in your account.

```bash
aws-cloud-utilities bedrock list-custom-models
```

**Options:**
- `--region REGION` - Specific region to list models from (default: all regions)
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# List all custom models
aws-cloud-utilities bedrock list-custom-models

# List custom models in specific region
aws-cloud-utilities bedrock list-custom-models --region us-west-2
```

### `list-model-jobs`

List model customization jobs.

```bash
aws-cloud-utilities bedrock list-model-jobs
```

**Options:**
- `--region REGION` - Specific region to list jobs from (default: all regions)
- `--status STATUS` - Filter by job status (InProgress, Completed, Failed, Stopping, Stopped)
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# List all model jobs
aws-cloud-utilities bedrock list-model-jobs

# List only completed jobs
aws-cloud-utilities bedrock list-model-jobs --status Completed
```

### `regions`

List AWS regions where Bedrock is available.

```bash
aws-cloud-utilities bedrock regions
```

**Examples:**
```bash
# List Bedrock regions
aws-cloud-utilities bedrock regions
```

## Global Options

All bedrock commands support these global options:

- `--profile PROFILE` - AWS profile to use
- `--region REGION` - AWS region
- `--output FORMAT` - Output format (table, json, yaml, csv)
- `--verbose` - Enable verbose output
- `--debug` - Enable debug mode

## Examples

### Model Discovery Workflow

```bash
#!/bin/bash
# Discover available Bedrock models

echo "=== Available Regions ==="
aws-cloud-utilities bedrock regions

echo "=== Foundation Models ==="
aws-cloud-utilities bedrock list-models --output-file foundation-models.json

echo "=== Custom Models ==="
aws-cloud-utilities bedrock list-custom-models --output-file custom-models.json

echo "=== Model Jobs ==="
aws-cloud-utilities bedrock list-model-jobs --output-file model-jobs.json
```

### Provider-Specific Analysis

```bash
#!/bin/bash
# Analyze models by provider

for provider in amazon anthropic ai21 cohere; do
    echo "=== $provider Models ==="
    aws-cloud-utilities bedrock list-models --provider $provider --output-file ${provider}-models.json
done
```

## Common Use Cases

1. **Model Discovery**
   ```bash
   aws-cloud-utilities bedrock list-models --provider anthropic
   aws-cloud-utilities bedrock model-details anthropic.claude-v2
   ```

2. **Custom Model Management**
   ```bash
   aws-cloud-utilities bedrock list-custom-models
   aws-cloud-utilities bedrock list-model-jobs --status InProgress
   ```

3. **Regional Analysis**
   ```bash
   aws-cloud-utilities bedrock regions
   aws-cloud-utilities bedrock list-models --region us-east-1
   ```

4. **Comprehensive Audit**
   ```bash
   aws-cloud-utilities bedrock list-models --output-file all-models.json
   aws-cloud-utilities bedrock list-custom-models --output-file custom-models.json
   aws-cloud-utilities bedrock list-model-jobs --output-file model-jobs.json
   ```
