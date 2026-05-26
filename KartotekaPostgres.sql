CREATE TYPE "object_category" AS ENUM (
  'main',
  'aux',
  'infra',
  'prep',
  'storage'
);

CREATE TYPE "object_status" AS ENUM (
  'active',
  'in_project',
  'reconstruction',
  'stopped'
);

CREATE TYPE "system_status" AS ENUM (
  'active',
  'inactive',
  'maintenance',
  'upgrade'
);

CREATE TYPE "auto_status" AS ENUM (
  'planned',
  'in_progress',
  'completed',
  'partial'
);

CREATE TYPE "participant_type" AS ENUM (
  'vendor',
  'engineering',
  'full_cycle',
  'supplier'
);

CREATE TYPE "product_type" AS ENUM (
  'software',
  'hardware',
  'service'
);

CREATE TABLE "OwnerEntity" (
  "id" integer PRIMARY KEY,
  "owner_name" varchar,
  "inn" varchar UNIQUE,
  "owner_id" integer,
  "ultimate_owner_id" integer,
  "ownership_percentage" decimal
);

CREATE TABLE "Address" (
  "id" integer PRIMARY KEY,
  "country" varchar,
  "region" varchar,
  "city" varchar,
  "street" varchar,
  "house" varchar,
  "title" varchar,
  "fias_code" varchar
);

CREATE TABLE "Object" (
  "id" integer PRIMARY KEY,
  "object_name" varchar,
  "object_short_name" varchar,
  "object_old_name" varchar,
  "object_law_name" varchar,
  "hierarchy_level" integer,
  "technology_info" varchar,
  "category" object_category,
  "start_date" date,
  "is_reconstructed" bool,
  "capacity" varchar,
  "status" object_status,
  "parent_object_id" integer,
  "address_id" integer,
  "owner_entity_id" integer
);

CREATE TABLE "AutomatedSystem" (
  "id" integer PRIMARY KEY,
  "autosystem_name" varchar,
  "autosystem__short_name" varchar,
  "system_class" integer,
  "vendor_id" integer,
  "vendor_product_id" integer,
  "version" varchar,
  "modules" json,
  "interfaces" json,
  "system_status" system_status,
  "installation_date" date,
  "notes" text
);

CREATE TABLE "AutomationClass" (
  "id" integer PRIMARY KEY,
  "level" integer,
  "system_class" varchar,
  "description" text
);

CREATE TABLE "ObjectSystem" (
  "id" integer PRIMARY KEY,
  "object_id" integer,
  "system_id" integer,
  "status" auto_status,
  "implementation_date" date,
  "integrator_id" integer,
  "implementer_id" integer,
  "notes" text
);

CREATE TABLE "ObjectCharacteristic" (
  "id" integer PRIMARY KEY,
  "object_id" integer,
  "characteristic_name" varchar,
  "code" varchar,
  "unit" varchar,
  "description" text,
  "is_required" boolean
);

CREATE TABLE "ObjectCharacteristicValue" (
  "id" integer PRIMARY KEY,
  "characteristic_id" integer,
  "value" double,
  "measurement_date" date,
  "notes" text
);

CREATE TABLE "ClassAutomationRequirement" (
  "id" integer PRIMARY KEY,
  "level_code" varchar,
  "requirement" text,
  "is_mandatory" boolean,
  "regulation" varchar
);

CREATE TABLE "Participant" (
  "id" integer PRIMARY KEY,
  "participant_name" varchar,
  "inn" varchar UNIQUE,
  "participant_type" participant_type,
  "is_partner" boolean,
  "registration_date" date,
  "website" varchar,
  "kam_name" varchar,
  "kam_phone" varchar,
  "contact_person" varchar,
  "contact_phone" varchar,
  "presentation_url" varchar,
  "profile" text,
  "industries" json,
  "contacts" json,
  "financial_data" json
);

CREATE TABLE "VendorProduct" (
  "id" integer PRIMARY KEY,
  "product_name" varchar,
  "vendor_id" integer,
  "product_type" product_type,
  "article" varchar UNIQUE,
  "description" text,
  "version" varchar,
  "technical_specs" json,
  "system_types" json,
  "industries" json,
  "release_year" date,
  "end_of_support" date,
  "is_active" boolean
);

COMMENT ON COLUMN "OwnerEntity"."owner_name" IS 'Название юр. лица';

COMMENT ON COLUMN "OwnerEntity"."inn" IS 'ИНН';

COMMENT ON COLUMN "OwnerEntity"."owner_id" IS 'Следующий в иерархии владелец';

COMMENT ON COLUMN "OwnerEntity"."ultimate_owner_id" IS 'Корневой владелец.';

COMMENT ON COLUMN "OwnerEntity"."ownership_percentage" IS 'Доля владения';

COMMENT ON COLUMN "Address"."house" IS 'Адрес производства (уровень 1)';

COMMENT ON COLUMN "Address"."title" IS 'Адрес установки (уровень 3)';

COMMENT ON COLUMN "Object"."object_name" IS 'Полное название объекта';

COMMENT ON COLUMN "Object"."object_short_name" IS 'Короткое название объекта';

COMMENT ON COLUMN "Object"."object_old_name" IS 'Историческое название объекта';

COMMENT ON COLUMN "Object"."object_law_name" IS 'Юридическое название объекта';

COMMENT ON COLUMN "Object"."hierarchy_level" IS 'Уровень в иерархии: производство -> цех -> установка';

COMMENT ON COLUMN "Object"."category" IS 'Разделение на категории: основное, вспомогательное, инфраструктурное, подготовительное, склад';

COMMENT ON COLUMN "Object"."start_date" IS 'Дата ввода в эксплуатацию.';

COMMENT ON COLUMN "Object"."is_reconstructed" IS 'Была ли реконструкция';

COMMENT ON COLUMN "Object"."capacity" IS 'Мощность / объем производства';

COMMENT ON COLUMN "Object"."status" IS 'Состояние объекта';

COMMENT ON COLUMN "Object"."parent_object_id" IS 'Родительский объект на уровень(или 2) выше в иерархии';

COMMENT ON COLUMN "AutomatedSystem"."autosystem_name" IS 'Полное название системы автоматизации';

COMMENT ON COLUMN "AutomatedSystem"."autosystem__short_name" IS 'Короткое название системы автоматизации';

COMMENT ON COLUMN "AutomatedSystem"."system_class" IS 'Тип системы (уровень и класс)';

COMMENT ON COLUMN "AutomatedSystem"."vendor_id" IS 'Поставщик системы';

COMMENT ON COLUMN "AutomatedSystem"."vendor_product_id" IS 'Продукт';

COMMENT ON COLUMN "AutomatedSystem"."version" IS 'Версия системы';

COMMENT ON COLUMN "AutomatedSystem"."modules" IS 'Модули системы';

COMMENT ON COLUMN "AutomatedSystem"."interfaces" IS 'Интерфейсы системы';

COMMENT ON COLUMN "AutomatedSystem"."system_status" IS 'Статус системы.';

COMMENT ON COLUMN "AutomatedSystem"."installation_date" IS 'Дата получения системы.';

COMMENT ON COLUMN "AutomatedSystem"."notes" IS 'Дополнительная информация';

COMMENT ON COLUMN "AutomationClass"."level" IS 'Уровень автоматизации: L0 | L1 | L2 | L3 | L4';

COMMENT ON COLUMN "AutomationClass"."system_class" IS 'Класс системы';

COMMENT ON COLUMN "ObjectSystem"."status" IS 'Статус ввода системы в эксплуатацию';

COMMENT ON COLUMN "ObjectSystem"."implementation_date" IS 'Дата ввода системы в эксплуатацию';

COMMENT ON COLUMN "ObjectSystem"."integrator_id" IS 'Интегратор системы';

COMMENT ON COLUMN "ObjectSystem"."implementer_id" IS 'Внедряющая компания';

COMMENT ON COLUMN "ObjectSystem"."notes" IS 'Дополнительные пояснения';

COMMENT ON COLUMN "ObjectCharacteristic"."characteristic_name" IS 'Название характеристики';

COMMENT ON COLUMN "ObjectCharacteristic"."code" IS 'Код характеристики';

COMMENT ON COLUMN "ObjectCharacteristic"."unit" IS 'Единица измерения';

COMMENT ON COLUMN "ObjectCharacteristic"."description" IS 'Описание';

COMMENT ON COLUMN "ObjectCharacteristic"."is_required" IS 'Обяательная характеристика';

COMMENT ON COLUMN "ObjectCharacteristicValue"."value" IS 'Значение';

COMMENT ON COLUMN "ObjectCharacteristicValue"."measurement_date" IS 'Дата измерения';

COMMENT ON COLUMN "ObjectCharacteristicValue"."notes" IS 'Дополнительная информация';

COMMENT ON COLUMN "ClassAutomationRequirement"."requirement" IS 'Требование';

COMMENT ON COLUMN "ClassAutomationRequirement"."is_mandatory" IS 'Обязательность';

COMMENT ON COLUMN "ClassAutomationRequirement"."regulation" IS 'Нормативный документ';

COMMENT ON COLUMN "Participant"."inn" IS 'ИНН';

COMMENT ON COLUMN "Participant"."participant_type" IS 'Тип участника: вендор, инжиниринговая компания, вендо полного цикла, поставщик';

COMMENT ON COLUMN "Participant"."is_partner" IS 'Является ли партнером';

COMMENT ON COLUMN "Participant"."registration_date" IS 'Дата регистрации';

COMMENT ON COLUMN "Participant"."website" IS 'Ссылка на сайт';

COMMENT ON COLUMN "Participant"."kam_name" IS 'Имя КАМ';

COMMENT ON COLUMN "Participant"."kam_phone" IS 'Номер КАМ';

COMMENT ON COLUMN "Participant"."contact_person" IS 'Контакт от ЦК ПА';

COMMENT ON COLUMN "Participant"."contact_phone" IS 'Телефон от ЦК ПА';

COMMENT ON COLUMN "Participant"."presentation_url" IS 'Ссылка на презентацию';

COMMENT ON COLUMN "Participant"."profile" IS 'Профиль компании';

COMMENT ON COLUMN "Participant"."industries" IS 'Отрасли применения';

COMMENT ON COLUMN "Participant"."contacts" IS 'Контактная информация';

COMMENT ON COLUMN "Participant"."financial_data" IS 'Финансовые показатели';

COMMENT ON COLUMN "VendorProduct"."product_name" IS 'Название вендорского продукта';

COMMENT ON COLUMN "VendorProduct"."vendor_id" IS 'Вендор';

COMMENT ON COLUMN "VendorProduct"."product_type" IS 'Тип продукта';

COMMENT ON COLUMN "VendorProduct"."article" IS 'Артикул';

COMMENT ON COLUMN "VendorProduct"."description" IS 'Описание';

COMMENT ON COLUMN "VendorProduct"."version" IS 'Версия';

COMMENT ON COLUMN "VendorProduct"."technical_specs" IS 'Технические характеристики';

COMMENT ON COLUMN "VendorProduct"."system_types" IS 'Типы систем';

COMMENT ON COLUMN "VendorProduct"."industries" IS 'Отрасли применения';

COMMENT ON COLUMN "VendorProduct"."release_year" IS 'Дата выпуска';

COMMENT ON COLUMN "VendorProduct"."end_of_support" IS 'Конец поддержки';

COMMENT ON COLUMN "VendorProduct"."is_active" IS 'Активен ли продукт';

ALTER TABLE "OwnerEntity" ADD FOREIGN KEY ("owner_id") REFERENCES "OwnerEntity" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "OwnerEntity" ADD FOREIGN KEY ("ultimate_owner_id") REFERENCES "OwnerEntity" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "Object" ADD FOREIGN KEY ("parent_object_id") REFERENCES "Object" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "Object" ADD FOREIGN KEY ("address_id") REFERENCES "Address" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "Object" ADD FOREIGN KEY ("owner_entity_id") REFERENCES "OwnerEntity" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "AutomatedSystem" ADD FOREIGN KEY ("system_class") REFERENCES "AutomationClass" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "AutomatedSystem" ADD FOREIGN KEY ("vendor_id") REFERENCES "Participant" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "AutomatedSystem" ADD FOREIGN KEY ("vendor_product_id") REFERENCES "VendorProduct" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "ObjectSystem" ADD FOREIGN KEY ("object_id") REFERENCES "Object" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "ObjectSystem" ADD FOREIGN KEY ("system_id") REFERENCES "AutomatedSystem" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "ObjectSystem" ADD FOREIGN KEY ("integrator_id") REFERENCES "Participant" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "ObjectSystem" ADD FOREIGN KEY ("implementer_id") REFERENCES "Participant" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "ObjectCharacteristic" ADD FOREIGN KEY ("object_id") REFERENCES "Object" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "ObjectCharacteristicValue" ADD FOREIGN KEY ("characteristic_id") REFERENCES "ObjectCharacteristic" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "ClassAutomationRequirement" ADD FOREIGN KEY ("level_code") REFERENCES "ObjectSystem" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "VendorProduct" ADD FOREIGN KEY ("vendor_id") REFERENCES "Participant" ("id") DEFERRABLE INITIALLY IMMEDIATE;
