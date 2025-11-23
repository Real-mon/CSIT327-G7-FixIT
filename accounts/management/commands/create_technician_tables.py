from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Create technician tables manually'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Create TechnicianSpecialty table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts_technicianspecialty (
                    id BIGSERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    icon_class VARCHAR(50)
                )
            """)
            self.stdout.write("Created accounts_technicianspecialty table")

            # Create Technician table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts_technician (
                    id BIGSERIAL PRIMARY KEY,
                    bio TEXT,
                    is_available BOOLEAN DEFAULT true,
                    average_rating DOUBLE PRECISION DEFAULT 4.0,
                    review_count INTEGER DEFAULT 0,
                    experience_years INTEGER DEFAULT 0,
                    average_response_time DOUBLE PRECISION DEFAULT 2.0,
                    hourly_rate NUMERIC(8,2),
                    certification VARCHAR(200),
                    languages VARCHAR(200),
                    working_hours_start TIME DEFAULT '09:00',
                    working_hours_end TIME DEFAULT '17:00',
                    accepts_emergency_calls BOOLEAN DEFAULT false,
                    completed_tickets INTEGER DEFAULT 0,
                    success_rate DOUBLE PRECISION DEFAULT 95.0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    user_profile_id INTEGER NOT NULL REFERENCES accounts_userprofile(id) DEFERRABLE INITIALLY DEFERRED
                )
            """)
            self.stdout.write("Created accounts_technician table")

            # Create the many-to-many table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts_technician_specialties (
                    id BIGSERIAL PRIMARY KEY,
                    technician_id BIGINT NOT NULL REFERENCES accounts_technician(id) DEFERRABLE INITIALLY DEFERRED,
                    technicianspecialty_id BIGINT NOT NULL REFERENCES accounts_technicianspecialty(id) DEFERRABLE INITIALLY DEFERRED
                )
            """)
            self.stdout.write("Created accounts_technician_specialties table")

            # Create TechnicianReview table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts_technicianreview (
                    id BIGSERIAL PRIMARY KEY,
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    comment TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    technician_id BIGINT NOT NULL REFERENCES accounts_technician(id) DEFERRABLE INITIALLY DEFERRED,
                    user_id INTEGER NOT NULL REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED,
                    UNIQUE(technician_id, user_id)
                )
            """)
            self.stdout.write("Created accounts_technicianreview table")

            # Create AssistanceRequest table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts_assistancerequest (
                    id BIGSERIAL PRIMARY KEY,
                    title VARCHAR(200) NOT NULL,
                    description TEXT NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    priority VARCHAR(20) DEFAULT 'medium',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    technician_id BIGINT NOT NULL REFERENCES accounts_technician(id) DEFERRABLE INITIALLY DEFERRED,
                    user_id INTEGER NOT NULL REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED
                )
            """)
            self.stdout.write("Created accounts_assistancerequest table")

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS accounts_technician_user_profile_id ON accounts_technician(user_profile_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS accounts_technicianreview_technician_id ON accounts_technicianreview(technician_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS accounts_technicianreview_user_id ON accounts_technicianreview(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS accounts_assistancerequest_technician_id ON accounts_assistancerequest(technician_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS accounts_assistancerequest_user_id ON accounts_assistancerequest(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS accounts_technician_specialties_technician_id ON accounts_technician_specialties(technician_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS accounts_technician_specialties_specialty_id ON accounts_technician_specialties(technicianspecialty_id)")
            
            self.stdout.write("Created all indexes")

        self.stdout.write(self.style.SUCCESS('Successfully created all technician tables!'))