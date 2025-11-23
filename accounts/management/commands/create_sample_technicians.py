from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile, Technician, TechnicianSpecialty

class Command(BaseCommand):
    help = 'Create sample technicians and specialties'

    def handle(self, *args, **options):
        # Create specialties
        specialties_data = [
            {'name': 'Hardware Repair', 'icon_class': 'fa-laptop'},
            {'name': 'Software Support', 'icon_class': 'fa-desktop'},
            {'name': 'Network Issues', 'icon_class': 'fa-wifi'},
            {'name': 'Mobile Devices', 'icon_class': 'fa-mobile-alt'},
            {'name': 'Data Recovery', 'icon_class': 'fa-hdd'},
        ]
        
        for spec_data in specialties_data:
            obj, created = TechnicianSpecialty.objects.get_or_create(
                name=spec_data['name'],
                defaults={'icon_class': spec_data['icon_class']}
            )
            self.stdout.write(f"{'Created' if created else 'Found'}: {spec_data['name']}")

        # Create sample technicians
        technicians_data = [
            {
                'username': 'john_technician',
                'first_name': 'John',
                'last_name': 'Smith',
                'email': 'john.tech@fixit.com',
                'bio': 'Experienced hardware and software technician with 5 years of experience.',
                'experience_years': 5,
                'rating': 4.5,
                'review_count': 42,
                'response_time': 1.2,
                'hourly_rate': 75.00,
                'certification': 'CompTIA A+ Certified',
                'languages': 'English, Spanish',
                'specialties': ['Hardware Repair', 'Software Support'],
            },
            {
                'username': 'maria_technician', 
                'first_name': 'Maria',
                'last_name': 'Johnson',
                'email': 'maria.tech@fixit.com',
                'bio': 'Network specialist with expertise in WiFi setup and server maintenance.',
                'experience_years': 8,
                'rating': 4.8,
                'review_count': 67,
                'response_time': 0.8,
                'hourly_rate': 85.00,
                'certification': 'Cisco CCNA',
                'languages': 'English, French',
                'is_available': False,
                'specialties': ['Network Issues'],
            },
            {
                'username': 'david_technician',
                'first_name': 'David',
                'last_name': 'Brown',
                'email': 'david.tech@fixit.com',
                'bio': 'Mobile device and data recovery specialist.',
                'experience_years': 4,
                'rating': 4.3,
                'review_count': 28,
                'response_time': 1.5,
                'hourly_rate': 65.00,
                'certification': 'Apple Certified Technician',
                'languages': 'English, German',
                'specialties': ['Mobile Devices', 'Data Recovery'],
            }
        ]

        for tech_data in technicians_data:
            # Create or get user
            user, created = User.objects.get_or_create(
                username=tech_data['username'],
                defaults={
                    'email': tech_data['email'],
                    'first_name': tech_data['first_name'],
                    'last_name': tech_data['last_name'],
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(f"Created user: {tech_data['username']}")

            # Create or get user profile and mark as technician
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.is_technician = True
            profile.save()

            # Create technician profile
            tech, created = Technician.objects.get_or_create(
                user_profile=profile,
                defaults={
                    'bio': tech_data['bio'],
                    'experience_years': tech_data['experience_years'],
                    'average_rating': tech_data['rating'],
                    'review_count': tech_data['review_count'],
                    'average_response_time': tech_data['response_time'],
                    'hourly_rate': tech_data['hourly_rate'],
                    'certification': tech_data['certification'],
                    'languages': tech_data['languages'],
                    'is_available': tech_data.get('is_available', True),
                }
            )

            # Add specialties
            for spec_name in tech_data['specialties']:
                specialty = TechnicianSpecialty.objects.get(name=spec_name)
                tech.specialties.add(specialty)

            self.stdout.write(f"Created technician: {tech_data['first_name']} {tech_data['last_name']}")

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(technicians_data)} technicians and {len(specialties_data)} specialties'
            )
        )