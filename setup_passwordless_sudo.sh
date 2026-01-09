#!/bin/bash
#
# ONE-TIME SETUP FOR PASSWORDLESS SUDO ON RASPBERRY PI
#
# This script explains how to allow the 'procomm' user to restart the 
# 'phonesystem' service without a password.
#
# Run these commands directly on your Raspberry Pi via SSH.
#
# 🚨 SECURITY WARNING 🚨
# This is generally safe as it only allows a single, specific command to be
# run without a password. However, be aware of the security implications.

set -e

# The command we want to allow passwordless access to
COMMAND_TO_WHITELIST="/bin/systemctl restart phonesystem.service"
SUDOERS_FILE="/etc/sudoers.d/procomm-phonesystem"

echo "This is an INSTRUCTIONAL script. Do not run it directly."
echo "Connect to your Raspberry Pi using 'ssh procomm@100.100.196.210' and run the following commands:"
echo ""
echo "-------------------------------------------------------------------"
echo ""
echo "# 1. Create a new sudoers file for our custom rule:"
echo "sudo touch ${SUDOERS_FILE}"
echo ""
echo "# 2. Add the rule allowing the 'procomm' user to run the specific restart command:"
echo "echo 'procomm ALL=(ALL) NOPASSWD: ${COMMAND_TO_WHITELIST}' | sudo tee ${SUDOERS_FILE}"
echo ""
echo "# 3. Validate the syntax of the sudoers file (important!):"
echo "sudo visudo -c"
echo ""
echo "# 4. Secure the new sudoers file by setting correct permissions:"
echo "sudo chmod 0440 ${SUDOERS_FILE}"
echo ""
echo "-------------------------------------------------------------------"
echo ""
echo "Setup is complete. The ./update.sh script should now run without password prompts."

exit 1
