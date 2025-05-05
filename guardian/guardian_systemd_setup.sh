# 1. Create Guardian systemd service
cat <<EOF > /etc/systemd/system/guardian.service
[Unit]
Description=Guardian AI Loader
After=network.target

[Service]
ExecStart=/usr/bin/python3 /root/guardian_ai_loader.py
WorkingDirectory=/root
Restart=always
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 2. Reload systemd and enable Guardian
systemctl daemon-reexec
systemctl enable guardian.service
systemctl start guardian.service

# 3. Optional: Create a crontab entry to reassert Guardian every reboot (failsafe)
(crontab -l 2>/dev/null; echo "@reboot /usr/bin/python3 /root/guardian_ai_loader.py") | crontab -

# 4. Optional: Hook Guardian into Revenant or other scripts
# Example: Append Guardian call into ~/.bashrc or any shell profile for visibility
if ! grep -q "guardian_ai_loader.py" ~/.bashrc; then
  echo '/usr/bin/python3 /root/guardian_ai_loader.py' >> ~/.bashrc
fi

# 5. Optional: Wrap Guardian in a shell script for Watchtower hooks
cat <<EOF > /root/guardian_sync.sh
#!/bin/bash
/usr/bin/python3 /root/guardian_ai_loader.py
EOF
chmod +x /root/guardian_sync.sh
