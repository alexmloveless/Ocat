#!/bin/bash
set -e

# Create necessary directories if they don't exist
mkdir -p /app/vector_stores/default
mkdir -p /home/ocat/.ocat

# If no config file exists, create a basic one
if [ ! -f /home/ocat/.ocat/config.yaml ]; then
    cat > /home/ocat/.ocat/config.yaml << EOF
# Ocat Configuration
llm:
  model: "${OCAT_MODEL:-gpt-4o-mini}"
  temperature: ${OCAT_TEMPERATURE:-1.0}
  max_tokens: ${OCAT_MAX_TOKENS:-4000}

vector_store:
  enabled: ${OCAT_VECTOR_STORE_ENABLED:-true}
  path: "${OCAT_VECTOR_STORE_PATH:-/app/vector_stores/default}"

logging:
  level: "${OCAT_LOG_LEVEL:-WARN}"

display:
  prompt_symbol: "🐱 > "
EOF
    echo "Created default configuration at /home/ocat/.ocat/config.yaml"
fi

# Execute the main command
exec "$@"
