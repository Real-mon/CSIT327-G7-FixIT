# accounts/management/commands/import_faqs.py
from django.core.management.base import BaseCommand
from accounts.models import FAQCategory, FAQItem 
import html

class Command(BaseCommand):
    help = 'Import FAQ data from HTML to database'
    
    def handle(self, *args, **options):
        # Define FAQ data matching your HTML structure
        faq_data = [
            {
                'category': 'Account Information',
                'slug': 'account-info',
                'icon': 'fa-user-circle',
                'faqs': [
                    {
                        'question': 'How do I create an account?',
                        'short_question': 'Create Account',
                        'answer': """To create an account:
1. Click on the "Sign Up" button on the homepage
2. Select your user type (User or Technician)
3. Fill in your email, username, and password
4. Click "Create Account"
5. You'll be automatically logged in after successful registration""",
                        'short_answer': 'Click Sign Up, choose user type, fill details, and create account.',
                        'keywords': 'signup, register, create account, new user',
                        'order': 1,
                    },
                    {
                        'question': 'How do I reset my password?',
                        'short_question': 'Reset Password',
                        'answer': """To reset your password:
1. Go to the login page
2. Click on "Forgot Password?"
3. Enter your registered email address
4. Follow the instructions sent to your email
5. Create a new password and confirm it""",
                        'short_answer': 'Use Forgot Password on login page, follow email instructions.',
                        'keywords': 'password reset, forgot password, change password',
                        'order': 2,
                    },
                    {
                        'question': 'How do I update my profile information?',
                        'short_question': 'Update Profile',
                        'answer': """To update your profile:
1. Log in to your account
2. Click on "Update Profile" in the navigation menu
3. Edit your personal information (name, email, phone, address, etc.)
4. Upload a profile picture if desired (max 5MB)
5. Click "Save Changes" to update your profile""",
                        'short_answer': 'Go to Update Profile, edit info, upload picture, save changes.',
                        'keywords': 'profile, update profile, edit profile, profile picture',
                        'order': 3,
                    },
                    {
                        'question': 'What\'s the difference between User and Technician accounts?',
                        'short_question': 'User vs Technician',
                        'answer': """User Account:
• Create support tickets for technical issues
• Message technicians for help
• Track ticket history
• Chat with FixIT Assistant bot

Technician Account:
• Receive and respond to support tickets
• Communicate with users seeking help
• Manage service requests
• Listed in technician directory""",
                        'short_answer': 'Users request help, technicians provide help.',
                        'keywords': 'user account, technician account, roles, account types',
                        'order': 4,
                    },
                    {
                        'question': 'How do I delete my account?',
                        'short_question': 'Delete Account',
                        'answer': """To delete your account, please contact our support team:
• Email: support@fixit.com
• Create a support ticket requesting account deletion
• Message a technician through the platform""",
                        'short_answer': 'Contact support team via email, ticket, or message.',
                        'keywords': 'delete account, remove account, account deletion',
                        'order': 5,
                    },
                    {
                        'question': 'Can I change my account type from User to Technician?',
                        'short_question': 'Change Account Type',
                        'answer': """Yes, you can request to change your account type:
1. Contact our support team through a support ticket
2. Provide relevant qualifications or experience (for Technician accounts)
3. Wait for approval from the admin team
4. Your account type will be updated upon approval""",
                        'short_answer': 'Contact support with qualifications to change account type.',
                        'keywords': 'change account type, become technician, switch account',
                        'order': 6,
                    },
                    {
                        'question': 'How do I manage notification settings?',
                        'short_question': 'Notification Settings',
                        'answer': """To manage your notification preferences:
1. Go to your Dashboard
2. Click on "Settings" in the sidebar or navigation
3. Toggle Email Notifications and SMS Notifications as desired
4. Changes are saved automatically

You can receive notifications for:
• New messages from technicians
• Ticket status updates
• Account security alerts""",
                        'short_answer': 'Go to Settings to toggle email and SMS notifications.',
                        'keywords': 'notifications, settings, email notifications, sms notifications',
                        'order': 7,
                    },
                ]
            },
            {
                'category': 'Tickets & Support',
                'slug': 'tickets-support',
                'icon': 'fa-ticket-alt',
                'faqs': [
                    {
                        'question': 'How do I create a support ticket?',
                        'short_question': 'Create Support Ticket',
                        'answer': """To create a support ticket:
1. Go to your Dashboard
2. Click on "Create Ticket" button (or find it in the sidebar)
3. Fill in the ticket details:
   • Title: Brief description of your issue
   • Description: Detailed explanation
   • Category: Hardware, Software, Network, or Other
   • Priority: Low, Medium, High, or Critical
4. Click "Submit Ticket"
5. You'll receive a ticket number for tracking""",
                        'short_answer': 'Go to Create Ticket, fill details, and submit.',
                        'keywords': 'ticket, support, create ticket, help request',
                        'order': 1,
                    },
                    {
                        'question': 'How can I track my ticket status?',
                        'short_question': 'Track Ticket Status',
                        'answer': """You can track your tickets in multiple ways:
1. Go to "My Tickets" in the sidebar menu
2. View all your tickets with their current status:
   • Open: Ticket has been submitted and waiting for technician assignment
   • Pending: Technician is working on your issue
   • Solved: Issue has been resolved
3. Click on any ticket to view details and updates
4. Check your email for notifications (if enabled in Settings)""",
                        'short_answer': 'Check My Tickets page or email notifications.',
                        'keywords': 'track ticket, ticket status, check progress',
                        'order': 2,
                    },
                    {
                        'question': 'What ticket priorities should I choose?',
                        'short_question': 'Ticket Priorities',
                        'answer': """Choose the appropriate priority level:

🟢 Low Priority
Minor issues, questions, or feature requests. Not affecting daily work.
Example: "How do I change my profile picture?"

🟡 Medium Priority
Issues affecting productivity but have workarounds.
Example: "Printer not working, can use another one"

🟠 High Priority
Service degradation affecting multiple users or critical functions.
Example: "Internet connection very slow for entire office"

🔴 Critical Priority
Complete service outage or data loss. Immediate attention needed.
Example: "Server down, cannot access any files" """,
                        'short_answer': 'Choose based on impact: Low, Medium, High, or Critical.',
                        'keywords': 'priority, ticket priority, urgency, importance',
                        'order': 3,
                    },
                    {
                        'question': 'How long does it take to get a response?',
                        'short_question': 'Response Time',
                        'answer': """Response times vary based on ticket priority:
• Critical: Within 1 hour
• High: Within 4 hours
• Medium: Within 24 hours
• Low: Within 48 hours

These are target response times. Actual resolution may take longer depending on issue complexity.""",
                        'short_answer': 'Critical: 1h, High: 4h, Medium: 24h, Low: 48h.',
                        'keywords': 'response time, wait time, ticket response',
                        'order': 4,
                    },
                    {
                        'question': 'Can I cancel or close a ticket?',
                        'short_question': 'Cancel Ticket',
                        'answer': """Yes, you can manage your tickets:
1. Go to "My Tickets" page
2. Click on the ticket you want to close
3. Look for the "Close Ticket" or "Mark as Resolved" button
4. Confirm your action

You can also reopen a closed ticket if the issue persists.""",
                        'short_answer': 'Yes, use Close Ticket button on My Tickets page.',
                        'keywords': 'cancel ticket, close ticket, mark resolved',
                        'order': 5,
                    },
                    {
                        'question': 'What information should I include in my ticket?',
                        'short_question': 'Ticket Information',
                        'answer': """For faster resolution, include:
• Clear description: What exactly is the problem?
• When it started: Date and time the issue began
• Steps to reproduce: What actions lead to the problem?
• Error messages: Any error codes or messages you see
• Device info: Computer model, operating system, browser (if relevant)
• What you've tried: Any troubleshooting steps you've already attempted
• Impact: How is this affecting your work?

The more details you provide, the faster we can solve your issue!""",
                        'short_answer': 'Include description, steps, errors, device info, and impact.',
                        'keywords': 'ticket details, information, troubleshooting steps',
                        'order': 6,
                    },
                ]
            },
            {
                'category': 'Messaging',
                'slug': 'messaging',
                'icon': 'fa-comments',
                'faqs': [
                    {
                        'question': 'How do I message a technician?',
                        'short_question': 'Message Technician',
                        'answer': """To start a conversation with a technician:
1. Go to "Messages" in the sidebar
2. Browse the "Technician Directory" to find available technicians
3. Click on a technician's profile
4. Click "Start Conversation" or "Message" button
5. Type your message and hit send

Technicians will receive notifications and respond as soon as they're available.""",
                        'short_answer': 'Use Messages page or Technician Directory to start chat.',
                        'keywords': 'message, chat, contact technician, conversation',
                        'order': 1,
                    },
                    {
                        'question': 'What is the FixIT Assistant bot?',
                        'short_question': 'FixIT Assistant',
                        'answer': """FixIT Assistant is an automated chatbot that helps with common technical issues:
• Available 24/7: Get instant help anytime
• Common Issues: Solutions for internet, computer performance, printer problems, etc.
• Quick Answers: FAQs and troubleshooting guides
• No Wait Time: Immediate responses for basic questions

If the bot can't solve your issue, it will recommend creating a ticket or contacting a technician.""",
                        'short_answer': 'AI chatbot for instant help with common tech issues.',
                        'keywords': 'bot, assistant, chatbot, ai help',
                        'order': 2,
                    },
                    {
                        'question': 'How do I start a chat with the FixIT Assistant?',
                        'short_question': 'Start Bot Chat',
                        'answer': """To chat with the FixIT Assistant bot:
1. Navigate to "Messages" from your dashboard
2. Click on "Start Bot Chat" or "Chat with FixIT Assistant" button
3. A new chat window will open with a welcome message
4. Type your question or describe your issue
5. The bot will provide instant troubleshooting steps

You can also use the "Common Issues" dropdown for quick solutions to popular problems.""",
                        'short_answer': 'Click Start Bot Chat in Messages page.',
                        'keywords': 'start bot chat, chat with bot, assistant chat',
                        'order': 3,
                    },
                    {
                        'question': 'Can I view my message history?',
                        'short_question': 'Message History',
                        'answer': """Yes, all your conversations are saved:
1. Go to the "Messages" page
2. You'll see a list of all your conversations on the left side
3. Click on any conversation to view the full message history
4. Both technician chats and bot conversations are saved
5. Scroll up to see older messages

Message history helps you reference previous solutions and maintain conversation context.""",
                        'short_answer': 'Yes, all conversations are saved in Messages page.',
                        'keywords': 'message history, chat history, conversation history',
                        'order': 4,
                    },
                    {
                        'question': 'How do I know if a technician has read my message?',
                        'short_question': 'Message Status',
                        'answer': """Message status indicators:
• Sent: Message has been delivered to the system
• Read: Technician has opened and viewed your message
• Typing: Technician is currently typing a response

You can also check:
• Notification settings to receive alerts for new messages
• Last active time of the technician
• Response time estimates in the conversation""",
                        'short_answer': 'Check message status indicators: Sent, Read, Typing.',
                        'keywords': 'message status, read receipt, message delivery',
                        'order': 5,
                    },
                    {
                        'question': 'Can I attach files or screenshots in messages?',
                        'short_question': 'Attach Files',
                        'answer': """Currently, file attachments in direct messages are not supported. However, you can:
• Create a ticket: Tickets support file uploads and screenshots
• Share links: Upload files to cloud storage and share the link in messages
• Describe the issue: Provide detailed text descriptions and error messages

For issues requiring screenshots or files, we recommend creating a support ticket instead.""",
                        'short_answer': 'Not in messages; use tickets for file attachments.',
                        'keywords': 'attachments, files, screenshots, upload',
                        'order': 6,
                    },
                ]
            },
            {
                'category': 'Technical Issues',
                'slug': 'technical',
                'icon': 'fa-tools',
                'faqs': [
                    {
                        'question': 'My computer is running very slow, what should I do?',
                        'short_question': 'Slow Computer',
                        'answer': """Quick fixes to try:
1. Restart your computer: This clears temporary files and refreshes system resources
2. Close unused programs: Open Task Manager (Ctrl+Shift+Esc) and close unnecessary applications
3. Check disk space: Ensure you have at least 15% free space on your C: drive
4. Run antivirus scan: Malware can significantly slow down your computer
5. Update Windows: Install pending updates that may improve performance
6. Disable startup programs: Prevent unnecessary apps from launching at startup

If the problem persists, create a ticket or chat with FixIT Assistant for more advanced solutions.""",
                        'short_answer': 'Restart, close programs, check disk space, scan for malware.',
                        'keywords': 'slow computer, performance, lag, speed',
                        'order': 1,
                    },
                    {
                        'question': 'I can\'t connect to the internet, how do I fix this?',
                        'short_question': 'No Internet',
                        'answer': """Troubleshooting steps:
1. Check physical connections: Ensure Ethernet cable is plugged in or WiFi is turned on
2. Restart your router: Unplug for 30 seconds, then plug back in
3. Restart your computer: Simple but often effective
4. Run Windows Network Diagnostics: Right-click network icon → Troubleshoot problems
5. Forget and reconnect to WiFi: Remove the network and add it again with the password
6. Update network drivers: Device Manager → Network Adapters → Update driver
7. Check with other devices: Verify if other devices can connect (helps identify if it's router or computer issue)

If none of these work, contact your ISP or create a high-priority ticket.""",
                        'short_answer': 'Check connections, restart router/computer, update drivers.',
                        'keywords': 'internet, wifi, connection, network',
                        'order': 2,
                    },
                    {
                        'question': 'My printer won\'t print, what should I check?',
                        'short_question': 'Printer Issues',
                        'answer': """Common printer issues and solutions:
1. Basic checks:
   • Is the printer powered on?
   • Is there paper in the tray?
   • Are ink/toner levels sufficient?
   • Are there any error lights blinking?
2. Check connections: Verify USB cable or network connection is secure
3. Set as default printer: Settings → Devices → Printers & scanners
4. Clear print queue: Cancel all pending print jobs and try again
5. Restart printer and computer: Power cycle both devices
6. Update printer drivers: Download latest drivers from manufacturer's website
7. Run printer troubleshooter: Windows Settings → Update & Security → Troubleshoot""",
                        'short_answer': 'Check power, paper, ink, connections, and drivers.',
                        'keywords': 'printer, printing, printer not working',
                        'order': 3,
                    },
                    {
                        'question': 'I\'m getting a "Blue Screen of Death" (BSOD), what does this mean?',
                        'short_question': 'Blue Screen',
                        'answer': """A Blue Screen of Death indicates a critical system error. Here's what to do:

Immediate Actions:
• Note the error code (e.g., "STOP: 0x0000007B")
• Take a photo of the screen if possible
• Restart your computer

Troubleshooting Steps:
• Boot in Safe Mode (F8 during startup)
• Check for recent software/driver installations and uninstall them
• Run Windows Memory Diagnostic tool
• Check for Windows updates
• Scan for malware

Important: If BSOD occurs frequently, create a CRITICAL priority ticket immediately. This could indicate hardware failure.""",
                        'short_answer': 'Note error code, restart, boot in Safe Mode, check for issues.',
                        'keywords': 'blue screen, bsod, crash, error',
                        'order': 4,
                    },
                    {
                        'question': 'How do I backup my important files?',
                        'short_question': 'Backup Files',
                        'answer': """Backup methods:
1. External Hard Drive:
   • Connect external drive to your computer
   • Copy important folders (Documents, Pictures, etc.)
   • Most reliable for large amounts of data
2. Cloud Storage:
   • Use services like Google Drive, OneDrive, or Dropbox
   • Automatic syncing keeps files up-to-date
   • Access files from anywhere
3. Windows Backup:
   • Settings → Update & Security → Backup
   • Turn on "File History" for automatic backups
   • Schedule regular system image backups

Best Practice: Follow the 3-2-1 rule: 3 copies of data, 2 different media types, 1 offsite backup.""",
                        'short_answer': 'Use external drive, cloud storage, or Windows Backup.',
                        'keywords': 'backup, files, data backup, cloud storage',
                        'order': 5,
                    },
                    {
                        'question': 'What should I do if I suspect my computer has a virus?',
                        'short_question': 'Virus/Malware',
                        'answer': """Signs of malware infection:
• Computer running unusually slow
• Pop-ups appearing frequently
• Programs opening/closing automatically
• Browser homepage changed without your permission
• Antivirus software disabled

Immediate actions:
1. Disconnect from internet: Prevents malware from spreading or communicating
2. Boot in Safe Mode: Restart and press F8 repeatedly
3. Run full antivirus scan: Use Windows Defender or your installed antivirus
4. Use Malwarebytes: Free tool for additional scanning
5. Delete suspicious programs: Control Panel → Uninstall a program
6. Change passwords: After cleaning, change all important passwords from a clean device

If you can't remove the virus yourself, create a HIGH priority ticket immediately!""",
                        'short_answer': 'Disconnect internet, boot in Safe Mode, run antivirus scan.',
                        'keywords': 'virus, malware, antivirus, security',
                        'order': 6,
                    },
                ]
            },
        ]
        
        for category_data in faq_data:
            category, created = FAQCategory.objects.update_or_create(
                slug=category_data['slug'],
                defaults={
                    'name': category_data['category'],
                    'icon': category_data['icon'],
                    'order': faq_data.index(category_data)  # Maintain order
                }
            )
            
            self.stdout.write(f"{'Created' if created else 'Updated'} category: {category.name}")
            
            for faq in category_data['faqs']:
                faq_item, created = FAQItem.objects.update_or_create(
                    category=category,
                    question=faq['question'],
                    defaults={
                        'short_question': faq['short_question'],
                        'answer': faq['answer'],
                        'short_answer': faq['short_answer'],
                        'keywords': faq['keywords'],
                        'order': faq['order'],
                        'is_active': True,
                        'show_in_dashboard': True,
                        'show_in_bot_buttons': True,
                    }
                )
                self.stdout.write(f"  - {'Created' if created else 'Updated'}: {faq['question']}")
        
        self.stdout.write(self.style.SUCCESS('Successfully imported all FAQ data!'))