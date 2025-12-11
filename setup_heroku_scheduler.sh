#!/bin/bash
# Heroku Scheduler Auto Clock-Out Setup Script

echo "🚀 Setting up Heroku Scheduler for Auto Clock-Out System"

# 1. Add Heroku Scheduler add-on
echo "📦 Adding Heroku Scheduler add-on..."
heroku addons:create scheduler:standard

# 2. Verify add-on installation
echo "✅ Verifying scheduler installation..."
heroku addons | grep scheduler

# 3. Open scheduler dashboard for manual job configuration
echo "🌐 Opening Heroku Scheduler dashboard..."
echo "Configure the following job:"
echo ""
echo "┌─────────────────────────────────────────────────────────┐"
echo "│ HEROKU SCHEDULER JOB CONFIGURATION                     │"
echo "├─────────────────────────────────────────────────────────┤"
echo "│ Command: python manage.py auto_clock_out_excessive      │"
echo "│ Frequency: Every 30 minutes                            │"
echo "│ Dyno Size: Standard-1X                                 │"
echo "│ Next Due: <will auto-calculate>                        │"
echo "└─────────────────────────────────────────────────────────┘"
echo ""

# Open the dashboard
heroku addons:open scheduler

echo "✅ Heroku Scheduler setup complete!"
echo ""
echo "📋 NEXT STEPS:"
echo "1. Configure the job in the opened dashboard"
echo "2. Test with: heroku run python manage.py auto_clock_out_excessive --dry-run"
echo "3. Monitor logs: heroku logs --tail --app your-app-name"
echo ""
echo "🔔 PUSHER NOTIFICATIONS:"
echo "Real-time notifications are automatically sent via:"
echo "• hotel-{slug}.attendance (clock status updates)"  
echo "• hotel-{slug}.staff-{id}-notifications (personal alerts)"