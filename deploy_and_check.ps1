# Deploy and check script for VPS
# Run this with: .\deploy_and_check.ps1

$commands = @"
cd ~/povaly-bot
git pull origin main
python3 -m py_compile src/bot/handlers/reaction_handler.py
python3 -m py_compile src/bot/handlers/command_handler.py
python3 -m py_compile src/data/models/issue.py
python3 -m py_compile src/data/repositories/task_repository.py
echo '=== Syntax check passed ==='
sudo systemctl restart telegram-bot
sleep 3
sudo systemctl status telegram-bot
echo '=== Checking error logs ==='
tail -50 ~/povaly-bot/data/logs/errors.log
"@

Write-Host "Copy and paste these commands into your SSH session:" -ForegroundColor Green
Write-Host ""
Write-Host $commands -ForegroundColor Yellow
Write-Host ""
Write-Host "Or run: ssh root@76.13.133.176" -ForegroundColor Cyan
