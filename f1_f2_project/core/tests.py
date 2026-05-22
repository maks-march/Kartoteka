# core/tests_performance.py
from django.test import TestCase, TransactionTestCase
from django.db import connection, reset_queries
from django.urls import reverse
from time import time
import random
from datetime import date, timedelta

from .models import (
    Address, LegalEntity, ObjectClass, Object,
    AutomationLevel, Participant, VendorProduct, AutomatedSystem,
    ObjectAutomationLevel
)


class PerformanceTestBase(TransactionTestCase):
    """Базовый класс для тестов производительности"""

    def setUp(self):
        """Создаём большое количество тестовых данных"""
        self.create_large_dataset()

    def create_large_dataset(self, object_count=30, system_count=100):
        """Создание большого набора данных для тестов производительности"""
        print(f"\n  Создаём тестовые данные: {object_count} объектов, {system_count} систем...")

        # Адреса (3 шт)
        addresses = []
        for i in range(3):
            addr = Address.objects.create(
                country='Россия',
                region=f'Регион {i}',
                city=f'Город {i}',
                street=f'Улица {i}',
                house=str(i)
            )
            addresses.append(addr)

        # Юрлица (5 шт)
        legal_entities = []
        for i in range(5):
            le = LegalEntity.objects.create(
                name=f'Компания {i}',
                inn=f'{1000000000 + i}'
            )
            legal_entities.append(le)

        # Классы объектов (3 шт)
        object_classes = []
        parent = None
        for i in range(3):
            cls = ObjectClass.objects.create(
                name=f'Класс {i}',
                code=f'CLASS_{i:03d}',
                parent=parent
            )
            object_classes.append(cls)
            parent = cls

        # Уровни автоматизации
        levels = []
        for code in ['L1', 'L2', 'L3']:
            level = AutomationLevel.objects.create(
                code=code,
                name=f'Уровень {code}',
                description=f'Описание {code}',
                order=int(code[1:]) if code[1:].isdigit() else 0
            )
            levels.append(level)

        # Участники (10 шт)
        participants = []
        for i in range(10):
            p_type = random.choice(['VENDOR', 'ENGINEERING', 'FULL_CYCLE'])
            p = Participant.objects.create(
                name=f'Участник {i}',
                inn=f'{2000000000 + i}',
                participant_type=p_type,
                is_partner=random.choice([True, False]),
                industries=[f'Отрасль {random.randint(1, 3)}'],
                contacts={},
                financial_data=[]
            )
            participants.append(p)

        # Вендорские продукты (10 шт)
        products = []
        for i in range(10):
            vendor = random.choice(participants)
            prod = VendorProduct.objects.create(
                name=f'Продукт {i}',
                vendor=vendor,
                product_type=random.choice(['SOFTWARE', 'HARDWARE']),
                code=f'PROD-{i:04d}',
                description=f'Описание продукта {i}',
                version=f'{random.randint(1, 5)}.{random.randint(0, 9)}',
                is_active=random.choice([True, False])
            )
            products.append(prod)

        # Объекты
        self.objects = []
        for i in range(object_count):
            obj = Object.objects.create(
                name=f'Объект {i}',
                hierarchy_level=random.choice(['LEVEL_1', 'LEVEL_2', 'LEVEL_3']),
                object_class=random.choice(object_classes),
                technology=f'Технология {random.randint(1, 5)}',
                category=random.choice(['MAIN', 'AUX']),
                start_year=2000 + random.randint(0, 23),
                capacity=random.randint(100, 10000),
                status=random.choice(['ACTIVE', 'PROJECT']),
                parent=None if i == 0 else random.choice(self.objects[:i]) if i > 0 else None,
                address=random.choice(addresses),
                legal_entity=random.choice(legal_entities)
            )
            self.objects.append(obj)

        # Отслеживаем созданные пары (object, level)
        created_pairs = set()

        # Автоматизированные системы
        self.systems = []
        for i in range(system_count):
            obj = random.choice(self.objects)
            level = random.choice(levels)
            vendor = random.choice(participants)
            integrator = random.choice(participants) if random.random() > 0.3 else None
            product = random.choice(products) if random.random() > 0.4 else None

            system = AutomatedSystem.objects.create(
                name=f'Система {i}',
                system_class=random.choice(['DCS', 'SCADA', 'PLC']),
                object=obj,
                level=level,
                vendor=vendor,
                integrator=integrator,
                vendor_product=product,
                version=f'{random.randint(1, 5)}.{random.randint(0, 9)}',
                status=random.choice(['ACTIVE', 'INACTIVE']),
                installation_date=date(2010, 1, 1) + timedelta(days=random.randint(0, 5000))
            )
            self.systems.append(system)

            # Создаём ObjectAutomationLevel только если такой пары ещё нет
            pair_key = (obj.id, level.id)
            if pair_key not in created_pairs:
                ObjectAutomationLevel.objects.create(
                    object=obj,
                    level=level,
                    status=random.choice(['PLANNED', 'IN_PROGRESS', 'COMPLETED']),
                    implementation_year=random.randint(2010, 2025)
                )
                created_pairs.add(pair_key)

        print(f"  Создано {Object.objects.count()} объектов")
        print(f"  Создано {AutomatedSystem.objects.count()} систем")
        print(f"  Создано {ObjectAutomationLevel.objects.count()} связей (уникальных)")

    def measure_queries(self, func, *args, **kwargs):
        """Измеряет количество запросов и время выполнения"""
        reset_queries()
        start = time()
        result = func(*args, **kwargs)
        end = time()

        query_count = len(connection.queries)
        execution_time = (end - start) * 1000  # в миллисекундах

        return {
            'result': result,
            'query_count': query_count,
            'time_ms': round(execution_time, 2)
        }


class QueryCountTests(PerformanceTestBase):
    """Тесты на количество SQL запросов"""

    def test_object_list_query_count(self):
        """Тест количества запросов на странице списка объектов"""
        client = self.client

        with self.assertNumQueries(6):
            response = client.get(reverse('object_list'))

        self.assertEqual(response.status_code, 200)

    def test_object_detail_query_count(self):
        """Тест количества запросов на детальной странице объекта"""
        client = self.client
        if not self.objects:
            self.skipTest("Нет объектов для теста")
        obj_id = self.objects[0].id

        with self.assertNumQueries(29):
            response = client.get(reverse('object_detail', args=[obj_id]))

        self.assertEqual(response.status_code, 200)

    def test_participant_detail_query_count(self):
        """Тест количества запросов на детальной странице участника"""
        client = self.client
        participant = Participant.objects.first()
        if not participant:
            self.skipTest("Нет участников для теста")

        with self.assertNumQueries(52):
            response = client.get(reverse('participant_detail', args=[participant.id]))

        self.assertEqual(response.status_code, 200)

    def test_graph_view_query_count(self):
        """Тест количества запросов на странице графа"""
        client = self.client

        with self.assertNumQueries(3):
            response = client.get(reverse('graph'))

        self.assertEqual(response.status_code, 200)


class PerformanceBenchmarkTests(PerformanceTestBase):
    """Тесты производительности (время выполнения)"""

    def test_object_list_response_time(self):
        """Тест времени ответа списка объектов"""
        client = self.client

        metrics = self.measure_queries(lambda: client.get(reverse('object_list')))

        print(f"\n⏱️  object_list: {metrics['time_ms']}ms, {metrics['query_count']} запросов")

        self.assertLess(metrics['time_ms'], 500)
        self.assertEqual(metrics['query_count'], 6)

    def test_object_detail_response_time(self):
        """Тест времени ответа детальной страницы объекта"""
        client = self.client
        if not self.objects:
            self.skipTest("Нет объектов для теста")
        obj_id = self.objects[random.randint(0, len(self.objects) - 1)].id

        metrics = self.measure_queries(lambda: client.get(reverse('object_detail', args=[obj_id])))

        print(f"⏱️  object_detail: {metrics['time_ms']}ms, {metrics['query_count']} запросов")

        self.assertLess(metrics['time_ms'], 800)
        self.assertEqual(metrics['query_count'], 29)

    def test_graph_response_time(self):
        """Тест времени ответа страницы графа"""
        client = self.client

        metrics = self.measure_queries(lambda: client.get(reverse('graph')))

        print(f"⏱️  graph: {metrics['time_ms']}ms, {metrics['query_count']} запросов")

        self.assertLess(metrics['time_ms'], 1500)
        self.assertEqual(metrics['query_count'], 3)


class LoadTest(TransactionTestCase):
    """Тест под нагрузкой"""
    def setUp(self):
        """Создаём минимальные тестовые данные"""
        self.address = Address.objects.create(
            country='Россия',
            region='Тест',
            city='Тест',
            street='Тест',
            house='1'
        )

        self.legal_entity = LegalEntity.objects.create(
            name='Тест',
            inn='1234567890'
        )

        self.object_class = ObjectClass.objects.create(
            name='Тест',
            code='TEST'
        )

        self.object = Object.objects.create(
            name='Тест',
            hierarchy_level='LEVEL_1',
            object_class=self.object_class,
            technology='Тест',
            category='MAIN',
            start_year=2020,
            capacity=100,
            status='ACTIVE',
            address=self.address,
            legal_entity=self.legal_entity
        )

        self.level = AutomationLevel.objects.create(
            code='L1',
            name='Тест',
            description='Тест',
            order=1
        )

        self.participant = Participant.objects.create(
            name='Тест',
            inn='0987654321',
            participant_type='VENDOR'
        )

        self.system = AutomatedSystem.objects.create(
            name='Тест',
            system_class='DCS',
            object=self.object,
            level=self.level,
            vendor=self.participant,
            status='ACTIVE'
        )

    def test_concurrent_requests(self):
        """Имитация конкурентных запросов"""
        import threading
        from django.test import Client

        results = []

        def make_request(url_name, args=None):
            client = Client()
            try:
                if args:
                    response = client.get(reverse(url_name, args=args))
                else:
                    response = client.get(reverse(url_name))
                results.append({
                    'url': url_name,
                    'status': response.status_code,
                    'success': response.status_code == 200
                })
            except Exception as e:
                results.append({
                    'url': url_name,
                    'error': str(e),
                    'success': False
                })

        # Список URL для тестирования
        urls_to_test = [
            ('overview', None),
            ('object_list', None),
            ('object_detail', [self.object.id]),
            ('participant_detail', [self.participant.id]),
            ('graph', None),
        ]

        # Создаём потоки
        threads = []
        for i in range(5):
            url_name, args = random.choice(urls_to_test)
            thread = threading.Thread(target=make_request, args=(url_name, args))
            threads.append(thread)
            thread.start()

        # Ждём завершения
        for thread in threads:
            thread.join()

        # Проверяем результаты
        success_count = sum(1 for r in results if r.get('success', False))
        fail_count = len(results) - success_count

        print(f"\n Результаты нагрузочного теста:")
        print(f"   Всего запросов: {len(results)}")
        print(f"   Успешно: {success_count}")
        print(f"   Ошибок: {fail_count}")

        self.assertEqual(fail_count, 0, f"Были ошибки: {fail_count}")