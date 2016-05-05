from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from lego.app.content.tests import ContentTestMixin
from lego.app.events.exceptions import NoAvailablePools
from lego.app.events.models import Event, Pool, Registration
from lego.app.events.views import EventViewSet
from lego.users.models import AbakusGroup, User


def get_dummy_users(n):
    users = []

    for i in range(n):
        first_name = last_name = username = email = str(i)
        user = User(username=username, first_name=first_name, last_name=last_name, email=email)
        user.save()
        users.append(user)

    return users


class EventTest(TestCase, ContentTestMixin):
    fixtures = ['initial_abakus_groups.yaml', 'initial_users.yaml',
                'test_users.yaml', 'test_events.yaml']

    model = Event
    ViewSet = EventViewSet


class EventMethodTest(TestCase):
    fixtures = ['initial_abakus_groups.yaml', 'test_users.yaml', 'test_events.yaml']

    def setUp(self):
        self.event = Event.objects.get(pk=1)

    def test_str(self):
        self.assertEqual(str(self.event), self.event.title)


class PoolMethodTest(TestCase):
    fixtures = ['initial_abakus_groups.yaml', 'test_users.yaml', 'test_events.yaml']

    def setUp(self):
        event = Event.objects.get(title='SINGLE_POOL')
        self.pool = event.pools.first()

    def test_str(self):
        self.assertEqual(str(self.pool), self.pool.name)


class RegistrationMethodTest(TestCase):
    fixtures = ['initial_abakus_groups.yaml', 'test_users.yaml', 'test_events.yaml']

    def setUp(self):
        event = Event.objects.get(title='TWO_POOLS')
        user = get_dummy_users(1)[0]
        AbakusGroup.objects.get(name='Abakus').add_user(user)
        self.registration = event.register(user=user)

    def test_str(self):
        d = {
            'user': self.registration.user,
            'pool': self.registration.pool,
        }

        self.assertEqual(str(self.registration), str(d))


class PoolCapacityTestCase(TestCase):
    fixtures = ['initial_abakus_groups.yaml', 'test_users.yaml', 'test_events.yaml']

    def create_pools(self, event, capacities_to_add, permission_groups):
        for capacity in capacities_to_add:
            pool = Pool.objects.create(
                name='Abakus', capacity=capacity, event=event,
                activation_date=(timezone.now() - timedelta(hours=24)))
            pool.permission_groups = permission_groups

    def test_capacity_with_single_pool(self):
        event = Event.objects.get(title='NO_POOLS_ABAKUS')
        capacities_to_add = [10]
        self.create_pools(event, capacities_to_add, [AbakusGroup.objects.get(name='Abakus')])
        self.assertEqual(sum(capacities_to_add), event.capacity)

    def test_capacity_with_multiple_pools(self):
        event = Event.objects.get(title='NO_POOLS_ABAKUS')
        capacities_to_add = [10, 20]
        self.create_pools(event, capacities_to_add, [AbakusGroup.objects.get(name='Abakus')])
        self.assertEqual(sum(capacities_to_add), event.capacity)


class RegisterSinglePoolTestCase(TestCase):
    fixtures = ['initial_abakus_groups.yaml', 'test_users.yaml', 'test_events.yaml']

    def test_can_register_single_pool(self):
        user = get_dummy_users(1)[0]
        event = Event.objects.get(title='SINGLE_POOL')
        pool = event.pools.first()
        AbakusGroup.objects.get(name='Abakus').add_user(user)

        event.register(user=user)
        self.assertEqual(pool.number_of_registrations, event.number_of_registrations)

    def test_can_register_to_single_open_pool(self):
        users = get_dummy_users(10)
        abakus_users = users[:6]
        webkom_users = users[6:]
        event = Event.objects.get(title='TWO_POOLS')
        pool_one = event.pools.get(name='Abakus')
        pool_two = event.pools.get(name='Webkom')

        for user in abakus_users:
            AbakusGroup.objects.get(name='Abakus').add_user(user)
        for user in webkom_users:
            AbakusGroup.objects.get(name='Webkom').add_user(user)

        for user in webkom_users:
            event.register(user=user)

        self.assertEqual(pool_one.number_of_registrations, 2)
        self.assertEqual(pool_two.number_of_registrations, 2)
        self.assertEqual(event.number_of_registrations, 4)

    def test_can_not_register_pre_activation(self):
        user = get_dummy_users(1)[0]
        event = Event.objects.get(title='NO_POOLS_ABAKUS')
        pool = Pool.objects.create(
            name='Abakus', capacity=1, event=event,
            activation_date=(timezone.now() + timedelta(hours=24)))
        permission_group = AbakusGroup.objects.get(name='Abakus')
        pool.permission_groups = [permission_group]
        permission_group.add_user(user)

        with self.assertRaises(NoAvailablePools):
            event.register(user=user)
        self.assertEqual(event.number_of_registrations, 0)
        self.assertEqual(event.waiting_pool_registrations.count(), 0)


class RegisterMultiplePoolTestCase(TestCase):
    fixtures = ['initial_abakus_groups.yaml', 'test_users.yaml', 'test_events.yaml']

    def test_registration_picks_correct_pool(self):
        event = Event.objects.get(title='TWO_POOLS')
        pool_one = event.pools.get(name='Abakus')
        pool_two = event.pools.get(name='Webkom')

        users = get_dummy_users(5)
        abakus_users = users[:3]
        webkom_users = users[3:]

        for user in abakus_users:
            AbakusGroup.objects.get(name='Abakus').add_user(user)
        for user in webkom_users:
            AbakusGroup.objects.get(name='Webkom').add_user(user)

        for user in users:
            event.register(user)

        self.assertEqual(pool_one.number_of_registrations, 3)
        self.assertEqual(pool_two.number_of_registrations, 2)

    def test_can_register_pre_merge(self):
        event = Event.objects.get(title='TWO_POOLS')
        pool_one = event.pools.get(name='Abakus')
        pool_two = event.pools.get(name='Webkom')

        users = get_dummy_users(5)
        abakus_users = users[:3]
        webkom_users = users[3:]

        for user in abakus_users:
            AbakusGroup.objects.get(name='Abakus').add_user(user)
        for user in webkom_users:
            AbakusGroup.objects.get(name='Webkom').add_user(user)

        for user in users:
            event.register(user)

        self.assertEqual(pool_one.number_of_registrations, 3)
        self.assertEqual(pool_two.number_of_registrations, 2)
        self.assertEqual(event.number_of_registrations, 5)

    def test_can_register_post_merge(self):
        event = Event.objects.get(title='TWO_POOLS')
        event.merge_time = timezone.now() - timedelta(hours=12)
        pool_one = event.pools.get(name='Abakus')
        pool_two = event.pools.get(name='Webkom')

        users = get_dummy_users(5)
        abakus_users = users[:4]
        webkom_users = users[4:]

        for user in abakus_users:
            AbakusGroup.objects.get(name='Abakus').add_user(user)
        for user in webkom_users:
            AbakusGroup.objects.get(name='Webkom').add_user(user)

        for user in users:
            event.register(user)

        self.assertEqual(pool_one.number_of_registrations, 4)
        self.assertEqual(pool_two.number_of_registrations, 1)
        self.assertEqual(event.number_of_registrations, 5)

    def test_no_duplicate_registrations(self):
        user = get_dummy_users(1)[0]
        event = Event.objects.get(title='TWO_POOLS')

        AbakusGroup.objects.get(name='Webkom').add_user(user)
        event.register(user=user)

        with self.assertRaises(NoAvailablePools):
            event.register(user=user)

        self.assertEqual(event.number_of_registrations, 1)

    def test_can_only_register_with_correct_permission_group(self):
        event = Event.objects.get(title='NO_POOLS_ABAKUS')
        event.merge_time = timezone.now() - timedelta(hours=12)
        permission_groups_one = [AbakusGroup.objects.get(name='Abakus')]
        permission_groups_two = [AbakusGroup.objects.get(name='Webkom')]
        pool = Pool.objects.create(
            name='Webkom', capacity=1, event=event,
            activation_date=(timezone.now() - timedelta(hours=24)))
        pool.permission_groups = permission_groups_two

        user = get_dummy_users(1)[0]
        permission_groups_one[0].add_user(user)

        with self.assertRaises(NoAvailablePools):
            event.register(user=user)

        self.assertEqual(pool.number_of_registrations, 0)

    def test_waiting_list_if_full(self):
        event = Event.objects.get(title='SINGLE_POOL')
        pool = event.pools.first()
        users = get_dummy_users(pool.capacity + 1)

        for user in users:
            AbakusGroup.objects.get(name='Abakus').add_user(user)
            event.register(user=user)

        self.assertEqual(event.waiting_pool_registrations.count(), 1)
        self.assertEqual(pool.number_of_registrations, pool.capacity)
        self.assertEqual(event.number_of_registrations, pool.number_of_registrations)

    def test_number_of_waiting_registrations(self):
        event = Event.objects.get(title='TWO_POOLS')
        pool = event.pools.get(name='Abakus')
        people_to_place_in_waiting_list = 3
        users = get_dummy_users(pool.capacity + 3)

        for user in users:
            AbakusGroup.objects.get(name='Abakus').add_user(user)
            event.register(user=user)

        self.assertEqual(event.waiting_pool_registrations.count(),
                         people_to_place_in_waiting_list)

    def test_placed_in_waiting_list_post_merge(self):
        event = Event.objects.get(title='TWO_POOLS')
        event.merge_time = timezone.now() - timedelta(hours=12)
        users = get_dummy_users(event.capacity + 1)

        for user in users:
            AbakusGroup.objects.get(name='Abakus').add_user(user)
            event.register(user=user)

        self.assertEqual(event.waiting_pool_registrations.count(), 1)

    def test_popping_from_waiting_list_pre_merge(self):
        event = Event.objects.get(title='NO_POOLS_WEBKOM')
        permission_groups = [AbakusGroup.objects.get(name='Webkom')]
        pool = Pool.objects.create(
            name='Webkom', capacity=0, event=event,
            activation_date=(timezone.now() - timedelta(hours=24)))
        pool.permission_groups = permission_groups
        users = get_dummy_users(pool.capacity + 10)

        for user in users:
            permission_groups[0].add_user(user)
            event.register(user=user)

        prev = event.pop_from_waiting_pool()
        for top in event.waiting_pool_registrations:
            self.assertLessEqual(prev.registration_date, top.registration_date)
            prev = top

    def test_popping_from_waiting_list_post_merge(self):
        event = Event.objects.get(title='TWO_POOLS')
        users = get_dummy_users(10)

        for user in users:
            AbakusGroup.objects.get(name='Webkom').add_user(user)
            event.register(user=user)

        prev = event.pop_from_waiting_pool()
        for registration in event.waiting_pool_registrations:
            self.assertLessEqual(prev.registration_date, registration.registration_date)
            prev = registration


class UnregisterTestCase(TestCase):
    fixtures = ['initial_abakus_groups.yaml', 'test_users.yaml', 'test_events.yaml']

    def test_unregistering_from_event(self):
        event = Event.objects.get(title='SINGLE_POOL')
        pool = event.pools.get(name='Abakus')
        user = get_dummy_users(1)[0]
        AbakusGroup.objects.get(name='Abakus').add_user(user)
        event.register(user)

        registrations_before = event.number_of_registrations
        pool_registrations_before = pool.number_of_registrations

        event.unregister(user)

        self.assertEqual(pool.number_of_registrations, pool_registrations_before - 1)
        self.assertEqual(event.number_of_registrations, registrations_before - 1)

    def test_register_after_unregister(self):
        event = Event.objects.get(title='SINGLE_POOL')
        user = get_dummy_users(1)[0]
        AbakusGroup.objects.get(name='Abakus').add_user(user)

        event.register(user)
        registrations_before = event.number_of_registrations

        event.unregister(user)
        self.assertEqual(event.number_of_registrations, registrations_before - 1)

        event.register(user)
        self.assertEqual(event.number_of_registrations, registrations_before)

    def test_unregistering_non_existing_user(self):
        event = Event.objects.get(title='SINGLE_POOL')
        user = get_dummy_users(1)[0]
        with self.assertRaises(Registration.DoesNotExist):
            event.unregister(user)

    def test_bump_single_pool(self):
        event = Event.objects.get(title='SINGLE_POOL')
        pool = event.pools.first()
        users = get_dummy_users(pool.capacity + 2)

        for user in users:
            AbakusGroup.objects.get(name='Abakus').add_user(user)
            event.register(user=user)

        waiting_list_before = event.waiting_pool_registrations.count()
        regs_before = event.number_of_registrations
        pool_before = pool.number_of_registrations

        event.bump(from_pool=pool)

        self.assertEqual(event.number_of_registrations, regs_before + 1)
        self.assertEqual(event.waiting_pool_registrations.count(), waiting_list_before - 1)
        self.assertEqual(event.waiting_pool_registrations.first().user, users[4])
        self.assertEqual(pool.number_of_registrations, pool_before + 1)

    def test_bumping_pre_merge(self):
        event = Event.objects.get(title='TWO_POOLS')
        pool = event.pools.first()
        users = get_dummy_users(pool.capacity + 10)

        for user in users:
            AbakusGroup.objects.get(name='Abakus').add_user(user)
            event.register(user=user)

        waiting_list_before = event.waiting_pool_registrations.count()
        event_size_before = event.number_of_registrations
        pool_size_before = pool.number_of_registrations

        user_to_unregister = event.registrations.first().user
        event.unregister(user_to_unregister)

        self.assertEqual(pool.number_of_registrations, pool_size_before)
        self.assertEqual(event.number_of_registrations, event_size_before)
        self.assertEqual(event.waiting_pool_registrations.count(), waiting_list_before - 1)
        self.assertLessEqual(event.number_of_registrations, event.capacity)

    def test_bumping_post_merge(self):
        event = Event.objects.get(title='TWO_POOLS')
        event.merge_time = timezone.now() - timedelta(hours=24)

        pool_one = event.pools.get(name='Abakus')
        pool_two = event.pools.get(name='Webkom')

        users = get_dummy_users(6)
        abakus_users = users[:5]
        webkom_users = users[5:]
        for user in abakus_users:
            AbakusGroup.objects.get(name='Abakus').add_user(user)
        for user in webkom_users:
            AbakusGroup.objects.get(name='Webkom').add_user(user)
            event.register(user=user)

        for user in abakus_users:
            event.register(user=user)

        waiting_list_before = event.waiting_pool_registrations.count()
        event_size_before = event.number_of_registrations
        pool_one_size_before = pool_one.number_of_registrations
        pool_two_size_before = pool_two.number_of_registrations

        user_to_unregister = event.registrations.first().user

        event.unregister(user_to_unregister)

        self.assertEqual(event.number_of_registrations, event_size_before)
        self.assertEqual(event.waiting_pool_registrations.count(), waiting_list_before - 1)
        self.assertEqual(pool_one.number_of_registrations, pool_one_size_before + 1)
        self.assertGreater(pool_one.number_of_registrations, pool_one.capacity)
        self.assertEqual(pool_two.number_of_registrations, pool_two_size_before - 1)
        self.assertLessEqual(event.number_of_registrations, event.capacity)

    def test_bumping_when_bumped_has_multiple_pools_available(self):
        event = Event.objects.get(title='TWO_POOLS')
        pool = event.pools.get(name='Webkom')
        users = get_dummy_users(6)

        pool_registrations_before = pool.number_of_registrations
        waiting_list_before = event.waiting_pool_registrations.count()
        number_of_registered_before = event.number_of_registrations

        for user in users:
            AbakusGroup.objects.get(name='Webkom').add_user(user)
            event.register(user=user)

        self.assertEqual(pool.number_of_registrations, pool_registrations_before + 2)
        self.assertEqual(event.waiting_pool_registrations.count(), waiting_list_before + 1)
        self.assertEqual(event.number_of_registrations, number_of_registered_before + 5)

        event.unregister(user=users[0])

        self.assertEqual(pool.number_of_registrations, pool_registrations_before + 2)
        self.assertEqual(event.waiting_pool_registrations.count(), waiting_list_before)
        self.assertEqual(event.number_of_registrations, number_of_registered_before + 5)

        event.unregister(user=users[1])

        self.assertEqual(event.number_of_registrations, number_of_registered_before + 4)

    def test_unregistration_date_is_set_at_unregistration(self):
        event = Event.objects.get(title='TWO_POOLS')
        user = get_dummy_users(1)[0]
        AbakusGroup.objects.get(name='Webkom').add_user(user)
        event.register(user=user)
        registration = event.registrations.first()

        self.assertIsNone(registration.unregistration_date)
        event.unregister(user=registration.user)
        registration = event.registrations.first()
        self.assertIsNotNone(registration.unregistration_date)

    def test_unregistering_from_waiting_list(self):
        event = Event.objects.get(title='TWO_POOLS')
        pool = event.pools.first()
        users = get_dummy_users(pool.capacity + 10)

        for user in users:
            AbakusGroup.objects.get(name='Abakus').add_user(user)
            event.register(user=user)

        event_size_before = event.number_of_registrations
        pool_size_before = pool.number_of_registrations
        waiting_list_before = event.waiting_pool_registrations.count()

        event.unregister(users[-1])

        self.assertEqual(event.number_of_registrations, event_size_before)
        self.assertEqual(pool.number_of_registrations, pool_size_before)
        self.assertEqual(event.waiting_pool_registrations.count(), waiting_list_before - 1)
        self.assertLessEqual(event.number_of_registrations, event.capacity)
