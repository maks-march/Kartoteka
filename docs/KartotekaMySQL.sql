CREATE TABLE `OwnerEntity` (
  `id` integer PRIMARY KEY,
  `owner_name` varchar(255) COMMENT 'Название юр. лица',
  `inn` varchar(255) UNIQUE COMMENT 'ИНН',
  `owner_id` integer COMMENT 'Следующий в иерархии владелец',
  `ultimate_owner_id` integer COMMENT 'Корневой владелец.',
  `ownership_percentage` decimal COMMENT 'Доля владения'
);

CREATE TABLE `Address` (
  `id` integer PRIMARY KEY,
  `country` varchar(255),
  `region` varchar(255),
  `city` varchar(255),
  `street` varchar(255),
  `house` varchar(255) COMMENT 'Адрес производства (уровень 1)',
  `title` varchar(255) COMMENT 'Адрес установки (уровень 3)',
  `fias_code` varchar(255)
);

CREATE TABLE `Object` (
  `id` integer PRIMARY KEY,
  `object_name` varchar(255) COMMENT 'Полное название объекта',
  `object_short_name` varchar(255) COMMENT 'Короткое название объекта',
  `object_old_name` varchar(255) COMMENT 'Историческое название объекта',
  `object_law_name` varchar(255) COMMENT 'Юридическое название объекта',
  `hierarchy_level` integer COMMENT 'Уровень в иерархии: производство -> цех -> установка',
  `technology_info` varchar(255),
  `category` ENUM ('main', 'aux', 'infra', 'prep', 'storage') COMMENT 'Разделение на категории: основное, вспомогательное, инфраструктурное, подготовительное, склад',
  `start_date` date COMMENT 'Дата ввода в эксплуатацию.',
  `is_reconstructed` bool COMMENT 'Была ли реконструкция',
  `capacity` varchar(255) COMMENT 'Мощность / объем производства',
  `status` ENUM ('active', 'in_project', 'reconstruction', 'stopped') COMMENT 'Состояние объекта',
  `parent_object_id` integer COMMENT 'Родительский объект на уровень(или 2) выше в иерархии',
  `address_id` integer,
  `owner_entity_id` integer
);

CREATE TABLE `AutomatedSystem` (
  `id` integer PRIMARY KEY,
  `autosystem_name` varchar(255) COMMENT 'Полное название системы автоматизации',
  `autosystem__short_name` varchar(255) COMMENT 'Короткое название системы автоматизации',
  `system_class` integer COMMENT 'Тип системы (уровень и класс)',
  `vendor_id` integer COMMENT 'Поставщик системы',
  `vendor_product_id` integer COMMENT 'Продукт',
  `version` varchar(255) COMMENT 'Версия системы',
  `modules` json COMMENT 'Модули системы',
  `interfaces` json COMMENT 'Интерфейсы системы',
  `system_status` ENUM ('active', 'inactive', 'maintenance', 'upgrade') COMMENT 'Статус системы.',
  `installation_date` date COMMENT 'Дата получения системы.',
  `notes` text COMMENT 'Дополнительная информация'
);

CREATE TABLE `AutomationClass` (
  `id` integer PRIMARY KEY,
  `level` integer COMMENT 'Уровень автоматизации: L0 | L1 | L2 | L3 | L4',
  `system_class` varchar(255) COMMENT 'Класс системы',
  `description` text
);

CREATE TABLE `ObjectSystem` (
  `id` integer PRIMARY KEY,
  `object_id` integer,
  `system_id` integer,
  `status` ENUM ('planned', 'in_progress', 'completed', 'partial') COMMENT 'Статус ввода системы в эксплуатацию',
  `implementation_date` date COMMENT 'Дата ввода системы в эксплуатацию',
  `integrator_id` integer COMMENT 'Интегратор системы',
  `implementer_id` integer COMMENT 'Внедряющая компания',
  `notes` text COMMENT 'Дополнительные пояснения'
);

CREATE TABLE `ObjectCharacteristic` (
  `id` integer PRIMARY KEY,
  `object_id` integer,
  `characteristic_name` varchar(255) COMMENT 'Название характеристики',
  `code` varchar(255) COMMENT 'Код характеристики',
  `unit` varchar(255) COMMENT 'Единица измерения',
  `description` text COMMENT 'Описание',
  `is_required` boolean COMMENT 'Обяательная характеристика'
);

CREATE TABLE `ObjectCharacteristicValue` (
  `id` integer PRIMARY KEY,
  `characteristic_id` integer,
  `value` double COMMENT 'Значение',
  `measurement_date` date COMMENT 'Дата измерения',
  `notes` text COMMENT 'Дополнительная информация'
);

CREATE TABLE `ClassAutomationRequirement` (
  `id` integer PRIMARY KEY,
  `level_code` varchar(255),
  `requirement` text COMMENT 'Требование',
  `is_mandatory` boolean COMMENT 'Обязательность',
  `regulation` varchar(255) COMMENT 'Нормативный документ'
);

CREATE TABLE `Participant` (
  `id` integer PRIMARY KEY,
  `participant_name` varchar(255),
  `inn` varchar(255) UNIQUE COMMENT 'ИНН',
  `participant_type` ENUM ('vendor', 'engineering', 'full_cycle', 'supplier') COMMENT 'Тип участника: вендор, инжиниринговая компания, вендо полного цикла, поставщик',
  `is_partner` boolean COMMENT 'Является ли партнером',
  `registration_date` date COMMENT 'Дата регистрации',
  `website` varchar(255) COMMENT 'Ссылка на сайт',
  `kam_name` varchar(255) COMMENT 'Имя КАМ',
  `kam_phone` varchar(255) COMMENT 'Номер КАМ',
  `contact_person` varchar(255) COMMENT 'Контакт от ЦК ПА',
  `contact_phone` varchar(255) COMMENT 'Телефон от ЦК ПА',
  `presentation_url` varchar(255) COMMENT 'Ссылка на презентацию',
  `profile` text COMMENT 'Профиль компании',
  `industries` json COMMENT 'Отрасли применения',
  `contacts` json COMMENT 'Контактная информация',
  `financial_data` json COMMENT 'Финансовые показатели'
);

CREATE TABLE `VendorProduct` (
  `id` integer PRIMARY KEY,
  `product_name` varchar(255) COMMENT 'Название вендорского продукта',
  `vendor_id` integer COMMENT 'Вендор',
  `product_type` ENUM ('software', 'hardware', 'service') COMMENT 'Тип продукта',
  `article` varchar(255) UNIQUE COMMENT 'Артикул',
  `description` text COMMENT 'Описание',
  `version` varchar(255) COMMENT 'Версия',
  `technical_specs` json COMMENT 'Технические характеристики',
  `system_types` json COMMENT 'Типы систем',
  `industries` json COMMENT 'Отрасли применения',
  `release_year` date COMMENT 'Дата выпуска',
  `end_of_support` date COMMENT 'Конец поддержки',
  `is_active` boolean COMMENT 'Активен ли продукт'
);

ALTER TABLE `OwnerEntity` ADD FOREIGN KEY (`owner_id`) REFERENCES `OwnerEntity` (`id`);

ALTER TABLE `OwnerEntity` ADD FOREIGN KEY (`ultimate_owner_id`) REFERENCES `OwnerEntity` (`id`);

ALTER TABLE `Object` ADD FOREIGN KEY (`parent_object_id`) REFERENCES `Object` (`id`);

ALTER TABLE `Object` ADD FOREIGN KEY (`address_id`) REFERENCES `Address` (`id`);

ALTER TABLE `Object` ADD FOREIGN KEY (`owner_entity_id`) REFERENCES `OwnerEntity` (`id`);

ALTER TABLE `AutomatedSystem` ADD FOREIGN KEY (`system_class`) REFERENCES `AutomationClass` (`id`);

ALTER TABLE `AutomatedSystem` ADD FOREIGN KEY (`vendor_id`) REFERENCES `Participant` (`id`);

ALTER TABLE `AutomatedSystem` ADD FOREIGN KEY (`vendor_product_id`) REFERENCES `VendorProduct` (`id`);

ALTER TABLE `ObjectSystem` ADD FOREIGN KEY (`object_id`) REFERENCES `Object` (`id`);

ALTER TABLE `ObjectSystem` ADD FOREIGN KEY (`system_id`) REFERENCES `AutomatedSystem` (`id`);

ALTER TABLE `ObjectSystem` ADD FOREIGN KEY (`integrator_id`) REFERENCES `Participant` (`id`);

ALTER TABLE `ObjectSystem` ADD FOREIGN KEY (`implementer_id`) REFERENCES `Participant` (`id`);

ALTER TABLE `ObjectCharacteristic` ADD FOREIGN KEY (`object_id`) REFERENCES `Object` (`id`);

ALTER TABLE `ObjectCharacteristicValue` ADD FOREIGN KEY (`characteristic_id`) REFERENCES `ObjectCharacteristic` (`id`);

ALTER TABLE `ClassAutomationRequirement` ADD FOREIGN KEY (`level_code`) REFERENCES `ObjectSystem` (`id`);

ALTER TABLE `VendorProduct` ADD FOREIGN KEY (`vendor_id`) REFERENCES `Participant` (`id`);
