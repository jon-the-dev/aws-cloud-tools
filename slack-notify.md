# Slack Notification Script

A simple, robust script for sending notifications to Slack from CI/CD pipelines.

## Overview

`slack-notify.sh` is a bash script that sends messages to Slack channels via webhook URLs. It's designed to be used in CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins, etc.) to notify teams about build status, deployments, test results, and other important events.

**Note:** All messages automatically include `@jon` at the beginning to ensure notifications are seen.

## Prerequisites

- Bash shell
- `curl` command (usually pre-installed on most systems)
- A Slack webhook URL

## Setup

### 1. Create a Slack Webhook

1. Go to [Slack API: Incoming Webhooks](https://api.slack.com/messaging/webhooks)
2. Create a new app or select an existing one
3. Enable Incoming Webhooks
4. Create a webhook for your desired channel
5. Copy the webhook URL (it looks like: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX`)

### 2. Set Environment Variable

Set the `SLACK_WEBHOOK` environment variable:

```bash
export SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

For CI/CD systems, add this as a secret environment variable in your pipeline configuration.

## Usage

### Basic Usage

```bash
./slack-notify.sh "Your message here"
```

This will send a message that appears as: `@jon Your message here`

### With Options

```bash
./slack-notify.sh "Build completed successfully" \
    --emoji ":white_check_mark:" \
    --color "good" \
    --title "Build Status"
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--emoji` | Emoji to display | `:speech_balloon:` |
| `--username` | Bot username | `CI/CD Pipeline` |
| `--channel` | Override default channel | (none) |
| `--color` | Message color (good, warning, danger, or hex) | (none) |
| `--title` | Attachment title | (none) |
| `--help, -h` | Show help message | - |

### Color Values

- `good` - Green (for success)
- `warning` - Yellow (for warnings)
- `danger` - Red (for errors)
- Hex codes - Custom colors (e.g., `#439FE0`)

## Examples

### Success Notification

```bash
./slack-notify.sh "All tests passed! ✓" \
    --emoji ":white_check_mark:" \
    --color "good" \
    --title "Test Results"
```

### Failure Notification

```bash
./slack-notify.sh "Build failed on branch main" \
    --emoji ":x:" \
    --color "danger" \
    --title "Build Failed"
```

### Deployment Notification

```bash
./slack-notify.sh "Deployed to production successfully" \
    --emoji ":rocket:" \
    --color "good" \
    --username "Deployment Bot"
```

### Warning Notification

```bash
./slack-notify.sh "Code coverage below 80%" \
    --emoji ":warning:" \
    --color "warning" \
    --title "Coverage Report"
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Build and Notify

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run tests
        run: |
          # Your test commands here
          npm test

      - name: Notify success
        if: success()
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
        run: |
          ./slack-notify.sh "Build succeeded for ${{ github.ref }}" \
            --emoji ":white_check_mark:" \
            --color "good" \
            --title "Build Success"

      - name: Notify failure
        if: failure()
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
        run: |
          ./slack-notify.sh "Build failed for ${{ github.ref }}" \
            --emoji ":x:" \
            --color "danger" \
            --title "Build Failed"
```

### GitLab CI

```yaml
stages:
  - test
  - notify

test:
  stage: test
  script:
    - npm test

notify_success:
  stage: notify
  when: on_success
  script:
    - |
      ./slack-notify.sh "Pipeline succeeded for $CI_COMMIT_REF_NAME" \
        --emoji ":white_check_mark:" \
        --color "good" \
        --title "Pipeline Success"

notify_failure:
  stage: notify
  when: on_failure
  script:
    - |
      ./slack-notify.sh "Pipeline failed for $CI_COMMIT_REF_NAME" \
        --emoji ":x:" \
        --color "danger" \
        --title "Pipeline Failed"
```

### Jenkins

```groovy
pipeline {
    agent any

    environment {
        SLACK_WEBHOOK = credentials('slack-webhook')
    }

    stages {
        stage('Build') {
            steps {
                sh 'npm install'
                sh 'npm test'
            }
        }
    }

    post {
        success {
            sh '''
                ./slack-notify.sh "Build succeeded for ${GIT_BRANCH}" \
                    --emoji ":white_check_mark:" \
                    --color "good" \
                    --title "Build Success"
            '''
        }
        failure {
            sh '''
                ./slack-notify.sh "Build failed for ${GIT_BRANCH}" \
                    --emoji ":x:" \
                    --color "danger" \
                    --title "Build Failed"
            '''
        }
    }
}
```

### CircleCI

```yaml
version: 2.1

jobs:
  build:
    docker:
      - image: cimg/base:2024.01
    steps:
      - checkout
      - run:
          name: Run tests
          command: npm test
      - run:
          name: Notify Slack on success
          when: on_success
          command: |
            ./slack-notify.sh "Build succeeded for ${CIRCLE_BRANCH}" \
              --emoji ":white_check_mark:" \
              --color "good" \
              --title "Build Success"
      - run:
          name: Notify Slack on failure
          when: on_fail
          command: |
            ./slack-notify.sh "Build failed for ${CIRCLE_BRANCH}" \
              --emoji ":x:" \
              --color "danger" \
              --title "Build Failed"

workflows:
  build-and-notify:
    jobs:
      - build
```

## Advanced Usage

### Using with Environment Variables

```bash
# Set webhook URL
export SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Set message details
export BUILD_STATUS="success"
export BUILD_BRANCH="main"
export BUILD_NUMBER="123"

# Send notification
./slack-notify.sh "Build #${BUILD_NUMBER} on ${BUILD_BRANCH} - ${BUILD_STATUS}" \
    --emoji ":rocket:" \
    --color "good"
```

### Dynamic Messages

```bash
# Get build info
BUILD_TIME=$(date '+%Y-%m-%d %H:%M:%S')
COMMIT_SHA=$(git rev-parse --short HEAD)
COMMIT_MSG=$(git log -1 --pretty=%B)

# Send detailed notification
./slack-notify.sh "Build completed at ${BUILD_TIME}\nCommit: ${COMMIT_SHA}\n${COMMIT_MSG}" \
    --emoji ":package:" \
    --color "good" \
    --title "Build Complete"
```

### Conditional Notifications

```bash
#!/bin/bash

# Run tests
if npm test; then
    ./slack-notify.sh "All tests passed!" \
        --emoji ":white_check_mark:" \
        --color "good" \
        --title "Test Results"
else
    ./slack-notify.sh "Some tests failed!" \
        --emoji ":x:" \
        --color "danger" \
        --title "Test Results"
    exit 1
fi
```

## Troubleshooting

### SLACK_WEBHOOK not set

**Error:** `SLACK_WEBHOOK environment variable is not set`

**Solution:** Set the environment variable:
```bash
export SLACK_WEBHOOK="your-webhook-url"
```

### Permission denied

**Error:** `Permission denied`

**Solution:** Make the script executable:
```bash
chmod +x slack-notify.sh
```

### Message not appearing in Slack

1. Verify the webhook URL is correct
2. Check that the webhook is enabled in Slack
3. Verify your Slack app has permission to post to the channel
4. Check the HTTP response code for errors

### Special characters in message

If your message contains special characters or quotes, ensure they're properly escaped or use single quotes:

```bash
./slack-notify.sh 'Message with "quotes" and $special characters'
```

## Exit Codes

- `0` - Success
- `1` - Missing required parameters or environment variables
- `2` - Failed to send message to Slack

## Security Considerations

- **Never commit webhook URLs to version control**
- Store webhook URLs as secrets in your CI/CD system
- Use environment variables to pass sensitive data
- Rotate webhook URLs periodically
- Limit webhook permissions to specific channels

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This script is part of the AWS Cloud Utilities project and is licensed under the MIT License.
