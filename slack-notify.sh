#!/bin/bash

##############################################################################
# Slack Notification Script for CI/CD Pipelines
#
# This script sends messages to a Slack channel via a webhook URL.
# It can be used in CI/CD pipelines to send notifications about build status,
# deployment results, or any other important events.
#
# Usage:
#   ./slack-notify.sh "Your message here"
#   ./slack-notify.sh "Build completed successfully" --emoji ":white_check_mark:"
#   ./slack-notify.sh "Deployment failed" --emoji ":x:" --username "CI/CD Bot"
#
# Environment Variables:
#   SLACK_WEBHOOK (required): The Slack webhook URL
#
# Options:
#   --emoji        : Emoji to display (default: :speech_balloon:)
#   --username     : Username to display (default: CI/CD Pipeline)
#   --channel      : Override default channel (optional)
#   --color        : Message color (good, warning, danger, or hex code)
#   --title        : Title for the attachment (optional)
#   --help, -h     : Show this help message
#
# Exit Codes:
#   0 - Success
#   1 - Missing required parameters or environment variables
#   2 - Failed to send message to Slack
#
# Examples:
#   # Simple message
#   SLACK_WEBHOOK="https://hooks.slack.com/..." ./slack-notify.sh "Build completed"
#
#   # Success notification with emoji
#   ./slack-notify.sh "Tests passed!" --emoji ":white_check_mark:" --color "good"
#
#   # Error notification
#   ./slack-notify.sh "Build failed on branch main" --emoji ":x:" --color "danger"
#
##############################################################################

set -e

# Default values
EMOJI=":speech_balloon:"
USERNAME="CI/CD Pipeline"
CHANNEL=""
COLOR=""
TITLE=""
MESSAGE=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display help
show_help() {
    cat << EOF
Slack Notification Script for CI/CD Pipelines

Usage: $0 "message" [OPTIONS]

Options:
    --emoji EMOJI          Emoji to display (default: :speech_balloon:)
    --username USERNAME    Username to display (default: CI/CD Pipeline)
    --channel CHANNEL      Override default channel (optional)
    --color COLOR          Message color (good, warning, danger, or hex code)
    --title TITLE          Title for the attachment (optional)
    --help, -h            Show this help message

Environment Variables:
    SLACK_WEBHOOK         (required) The Slack webhook URL

Examples:
    # Simple message
    $0 "Build completed successfully"

    # Success notification
    $0 "Tests passed!" --emoji ":white_check_mark:" --color "good"

    # Error notification
    $0 "Build failed" --emoji ":x:" --color "danger" --title "Build Status"

Exit Codes:
    0 - Success
    1 - Missing required parameters or environment variables
    2 - Failed to send message to Slack
EOF
}

# Function to log messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --emoji)
            EMOJI="$2"
            shift 2
            ;;
        --username)
            USERNAME="$2"
            shift 2
            ;;
        --channel)
            CHANNEL="$2"
            shift 2
            ;;
        --color)
            COLOR="$2"
            shift 2
            ;;
        --title)
            TITLE="$2"
            shift 2
            ;;
        *)
            if [[ -z "$MESSAGE" ]]; then
                MESSAGE="$1"
            else
                log_error "Unknown option: $1"
                show_help
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate required parameters
if [[ -z "$SLACK_WEBHOOK" ]]; then
    log_error "SLACK_WEBHOOK environment variable is not set"
    echo ""
    echo "Please set the SLACK_WEBHOOK environment variable:"
    echo "  export SLACK_WEBHOOK='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'"
    echo ""
    exit 1
fi

if [[ -z "$MESSAGE" ]]; then
    log_error "Message is required"
    echo ""
    show_help
    exit 1
fi

# Build JSON payload
log_info "Preparing Slack message..."

# Start building the payload
PAYLOAD="{\"username\": \"$USERNAME\", \"icon_emoji\": \"$EMOJI\""

# Add channel if specified
if [[ -n "$CHANNEL" ]]; then
    PAYLOAD="$PAYLOAD, \"channel\": \"$CHANNEL\""
fi

# If color or title is specified, use attachments format
if [[ -n "$COLOR" ]] || [[ -n "$TITLE" ]]; then
    PAYLOAD="$PAYLOAD, \"attachments\": [{"

    if [[ -n "$COLOR" ]]; then
        PAYLOAD="$PAYLOAD\"color\": \"$COLOR\","
    fi

    if [[ -n "$TITLE" ]]; then
        # Escape the title
        TITLE_ESCAPED=$(echo "$TITLE" | sed 's/"/\\"/g' | sed "s/'/\\'/g")
        PAYLOAD="$PAYLOAD\"title\": \"$TITLE_ESCAPED\","
    fi

    # Escape the message for JSON
    MESSAGE_ESCAPED=$(echo "$MESSAGE" | sed 's/"/\\"/g' | sed "s/'/\\'/g")
    PAYLOAD="$PAYLOAD\"text\": \"$MESSAGE_ESCAPED\""

    PAYLOAD="$PAYLOAD}]"
else
    # Simple text format
    # Escape the message for JSON
    MESSAGE_ESCAPED=$(echo "$MESSAGE" | sed 's/"/\\"/g' | sed "s/'/\\'/g")
    PAYLOAD="$PAYLOAD, \"text\": \"$MESSAGE_ESCAPED\""
fi

PAYLOAD="$PAYLOAD}"

# Send message to Slack
log_info "Sending message to Slack..."

HTTP_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H 'Content-type: application/json' \
    --data "$PAYLOAD" \
    "$SLACK_WEBHOOK")

# Extract HTTP status code (last line)
HTTP_CODE=$(echo "$HTTP_RESPONSE" | tail -n1)

# Extract response body (all but last line)
RESPONSE_BODY=$(echo "$HTTP_RESPONSE" | sed '$d')

# Check response
if [[ "$HTTP_CODE" -eq 200 ]]; then
    log_info "Message sent successfully!"
    echo ""
    echo "Message: $MESSAGE"
    if [[ -n "$TITLE" ]]; then
        echo "Title: $TITLE"
    fi
    echo "Username: $USERNAME"
    echo "Emoji: $EMOJI"
    if [[ -n "$COLOR" ]]; then
        echo "Color: $COLOR"
    fi
    exit 0
else
    log_error "Failed to send message to Slack"
    echo "HTTP Status Code: $HTTP_CODE"
    echo "Response: $RESPONSE_BODY"
    exit 2
fi
