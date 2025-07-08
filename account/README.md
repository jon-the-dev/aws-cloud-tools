# Account Tools - MIGRATED TO V2

## Migration Notice

The account tools have been migrated to the new unified AWS Cloud Utilities v2 package.

### Original Scripts → New Commands

| Original Script | New Command | Status |
|----------------|-------------|---------|
| `aws_get_acct_info.py` | `aws-cloud-utilities account contact-info` | ✅ MIGRATED |
| `detect_control_tower.py` | `aws-cloud-utilities account detect-control-tower` | ✅ MIGRATED |

### New Enhanced Commands

```bash
# Get account contact information (migrated functionality)
aws-cloud-utilities account contact-info

# Detect Control Tower/Landing Zone (migrated with improvements)
aws-cloud-utilities account detect-control-tower
aws-cloud-utilities account detect-control-tower --verbose

# Additional account utilities (new in v2)
aws-cloud-utilities account info
aws-cloud-utilities account regions
aws-cloud-utilities account validate
aws-cloud-utilities account limits
```

### Installation

```bash
cd v2
./install_dev.sh
```

### Benefits of Migration

1. **Unified Interface**: Single command instead of multiple scripts
2. **Enhanced Functionality**: Better error handling, parallel processing
3. **Rich Output**: Tables, colors, multiple output formats
4. **Modern CLI**: Consistent patterns, help system, configuration management

For more details, see:
- `v2/README.md` - Full v2 documentation
- `v2/MIGRATED_COMMANDS.md` - Migration reference guide
- `Plan.md` - Complete migration plan
