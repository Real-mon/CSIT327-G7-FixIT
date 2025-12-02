# accounts/management/commands/sync_faq_bot.py
from django.core.management.base import BaseCommand
from accounts.models import FAQItem 

class Command(BaseCommand):
    help = 'Sync FAQ data between HTML and bot system'
    
    def handle(self, *args, **options):
        # Ensure all FAQ items have proper bot settings
        faqs = FAQItem.objects.all()
        
        updated = 0
        for faq in faqs:
            needs_update = False
            
            # Ensure keywords are set
            if not faq.keywords:
                # Generate keywords from question
                keywords = set()
                for word in faq.question.lower().split():
                    if len(word) > 3 and word not in ['what', 'how', 'why', 'when', 'where', 'which', 'that', 'this', 'with', 'from']:
                        keywords.add(word)
                faq.keywords = ','.join(list(keywords)[:10])
                needs_update = True
            
            # Ensure short_question is set
            if not faq.short_question or len(faq.short_question) > 50:
                faq.short_question = faq.question[:50] + '...' if len(faq.question) > 50 else faq.question
                needs_update = True
            
            # Ensure short_answer is set
            if not faq.short_answer:
                faq.short_answer = faq.answer[:100] + '...' if len(faq.answer) > 100 else faq.answer
                needs_update = True
            
            # Ensure bot_priority is set for popular questions
            if faq.order <= 3:  # Top questions in each category
                if faq.bot_priority < 5:
                    faq.bot_priority = 5
                    needs_update = True
            
            if needs_update:
                faq.save()
                updated += 1
        
        self.stdout.write(self.style.SUCCESS(f'Updated {updated} FAQ items for bot compatibility'))