# Claude AI Assistant Instructions

This document provides guidelines for Claude AI when working on this repository.

## Repository Overview

This is the AWS Cloud Utilities repository - a unified command-line toolkit for AWS operations. It includes various tools for cost optimization, inventory management, security auditing, and more.

## Workflow Guidelines

### When Work is Completed

After completing a task (implementing features, fixing bugs, etc.), always notify via Slack:

1. **Send a Slack notification** using the `slack-notify.sh` script
2. Include a summary of what was completed
3. The script will automatically tag @jon in all messages

#### Success Notification Example

```bash
export SLACK_WEBHOOK="your-webhook-url"  # Usually set in CI/CD environment

./slack-notify.sh "Task completed: [brief description of work]

Changes made:
- [Change 1]
- [Change 2]
- [Change 3]

Branch: $(git branch --show-current)
Commit: $(git rev-parse --short HEAD)" \
    --emoji ":white_check_mark:" \
    --color "good" \
    --title "Development Complete"
```

#### Error/Blocker Notification Example

```bash
./slack-notify.sh "Task blocked: [description of blocker]

Issue: [What went wrong]
Next steps: [What needs to happen]

Branch: $(git branch --show-current)" \
    --emoji ":warning:" \
    --color "warning" \
    --title "Development Blocked"
```

### Notification Best Practices

- **Always notify when**:
  - A feature is complete and pushed
  - A bug fix is complete and pushed
  - Work is blocked and needs human intervention
  - A significant milestone is reached

- **Include in notifications**:
  - Summary of changes
  - Branch name
  - Commit SHA (short)
  - Any important notes or next steps

- **Use appropriate colors**:
  - `good` (green) - Success, completion
  - `warning` (yellow) - Blockers, needs attention
  - `danger` (red) - Errors, failures

### Git Workflow

1. Always work on feature branches (usually starting with `claude/`)
2. Commit with clear, descriptive messages
3. Push to the designated branch
4. Send Slack notification after pushing

### Code Standards

- Follow existing code style in the repository
- Add documentation for new scripts/features
- Update README.md when adding new functionality
- Include examples in documentation

## CI/CD Integration

The repository includes a `slack-notify.sh` script for Slack notifications:

- **Location**: `./slack-notify.sh`
- **Documentation**: `slack-notify.md`
- **Environment Variable Required**: `SLACK_WEBHOOK`

### Script Options

```bash
./slack-notify.sh "message" [OPTIONS]

Options:
  --emoji EMOJI          Emoji to display (default: :speech_balloon:)
  --username USERNAME    Username to display (default: CI/CD Pipeline)
  --color COLOR          Message color (good, warning, danger, or hex code)
  --title TITLE          Title for the attachment
  --channel CHANNEL      Override default channel
```

### Quick Reference

```bash
# Success
./slack-notify.sh "Work complete!" --emoji ":white_check_mark:" --color "good"

# Warning
./slack-notify.sh "Need attention" --emoji ":warning:" --color "warning"

# Error
./slack-notify.sh "Something failed" --emoji ":x:" --color "danger"
```

## Note on @jon Tagging

The slack-notify.sh script automatically includes @jon in all messages, so you don't need to manually add it. The mention is prepended to your message automatically.
