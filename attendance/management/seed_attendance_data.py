from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from attendance.models import Attendance
import random
from datetime import timedelta
import names

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate dummy data for testing the attendance system'

    def add_arguments(self, parser):
        parser.add_argument('--staff', type=int, default=5, help='Number of staff users to create')
        parser.add_argument('--community', type=int, default=20, help='Number of community users to create')
        parser.add_argument('--days', type=int, default=30, help='Number of days of attendance to generate')

    def handle(self, *args, **options):
        self.stdout.write('Starting dummy data generation...')

        # Create staff users
        staff_users = self._create_users(
            count=options['staff'],
            user_type='staff',
            prefix='staff'
        )

        # Create community users
        community_users = self._create_users(
            count=options['community'],
            user_type='community',
            prefix='community'
        )

        # Generate attendance records
        self._generate_attendance(
            users=staff_users + community_users,
            days=options['days']
        )

        self.stdout.write(self.style.SUCCESS('Successfully generated dummy data'))

    def _create_users(self, count, user_type, prefix):
        users = []
        for i in range(count):
            first_name = names.get_first_name()
            last_name = names.get_last_name()
            username = f"{prefix}_{first_name.lower()}_{i+1}"
            
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    password='testpass123',
                    email=f'{username}@example.com',
                    first_name=first_name,
                    last_name=last_name,
                    user_type=user_type,
                    phone_number=f'{"123" if user_type == "staff" else "987"}{i:05d}'
                )
                users.append(user)
                self.stdout.write(f'Created {user_type} user: {username}')
        
        return users

    def _generate_attendance(self, users, days):
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days-1)
        current_date = start_date

        while current_date <= end_date:
            # 70-90% attendance rate
            num_attendees = int(len(users) * random.uniform(0.7, 0.9))
            attendees = random.sample(users, num_attendees)

            for user in attendees:
                # Generate check-in time (8 AM - 10 AM)
                check_in_time = timezone.make_aware(
                    timezone.datetime.combine(
                        current_date,
                        timezone.datetime.min.time().replace(
                            hour=random.randint(8, 10),
                            minute=random.randint(0, 59)
                        )
                    )
                )

                # Generate check-out time (4 PM - 6 PM)
                check_out_time = timezone.make_aware(
                    timezone.datetime.combine(
                        current_date,
                        timezone.datetime.min.time().replace(
                            hour=random.randint(16, 18),
                            minute=random.randint(0, 59)
                        )
                    )
                )

                Attendance.objects.create(
                    user=user,
                    date=current_date,
                    check_in=check_in_time,
                    check_out=check_out_time
                )

            self.stdout.write(f'Created {num_attendees} attendance records for {current_date}')
            current_date += timedelta(days=1)