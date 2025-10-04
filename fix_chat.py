#!/usr/bin/env python3
"""Script to fix the chat.py routing issue."""

import os
import shutil

# Read the original file
with open('/home/alex/apps/ocat/src/ocat/chat.py', 'r') as f:
    content = f.read()

# Make the necessary replacements
# 1. Add routing_marker variable
content = content.replace(
    '        # Check if this is a productivity request\n        if (',
    '        # Check if this is a productivity request\n        routing_marker = self.config.productivity.routing_marker\n        if ('
)

# 2. Update the method call to pass routing_marker
content = content.replace(
    'and self.productivity_integration.should_use_productivity_agent(user_input)',
    'and self.productivity_integration.should_use_productivity_agent(user_input, routing_marker)'
)

# 3. Add marker stripping logic
content = content.replace(
    '                # Process with productivity agent\n                productivity_response = (\n                    await self.productivity_integration.process_productivity_request(\n                        user_input, self\n                    )\n                )',
    '                # Strip the routing marker from the input before processing\n                productivity_input = user_input.strip()\n                if productivity_input.startswith(routing_marker):\n                    productivity_input = productivity_input[len(routing_marker):].strip()\n\n                # Process with productivity agent\n                productivity_response = (\n                    await self.productivity_integration.process_productivity_request(\n                        productivity_input, self\n                    )\n                )'
)

# Backup original and write fixed version
shutil.copy('/home/alex/apps/ocat/src/ocat/chat.py', '/home/alex/apps/ocat/src/ocat/chat.py.backup')
with open('/home/alex/apps/ocat/src/ocat/chat.py.fixed', 'w') as f:
    f.write(content)

print("Fixed version created as chat.py.fixed")
print("Original backed up as chat.py.backup")
print("You'll need to replace the original with sudo or change permissions")
