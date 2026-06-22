CREATE TABLE [OwnerEntity] (
  [id] integer PRIMARY KEY,
  [owner_name] nvarchar(255),
  [inn] nvarchar(255) UNIQUE,
  [owner_id] integer,
  [ultimate_owner_id] integer,
  [ownership_percentage] decimal
)
GO

CREATE TABLE [Address] (
  [id] integer PRIMARY KEY,
  [country] nvarchar(255),
  [region] nvarchar(255),
  [city] nvarchar(255),
  [street] nvarchar(255),
  [house] nvarchar(255),
  [title] nvarchar(255),
  [fias_code] nvarchar(255)
)
GO

CREATE TABLE [Category] (
  [id] integer PRIMARY KEY,
  [object_level] integer,
  [category_name] nvarchar(255)
)
GO

CREATE TABLE [Object] (
  [id] integer PRIMARY KEY,
  [object_name] nvarchar(255),
  [object_short_name] nvarchar(255),
  [object_old_name] nvarchar(255),
  [object_law_name] nvarchar(255),
  [hierarchy_level] integer,
  [object_class] nvarchar(255),
  [category] integer,
  [start_date] date,
  [is_reconstructed] bool,
  [capacity] nvarchar(255),
  [status] nvarchar(255) NOT NULL CHECK ([status] IN ('active', 'in_project', 'reconstruction', 'stopped')),
  [parent_object_id] integer,
  [address_id] integer,
  [owner_entity_id] integer
)
GO

CREATE TABLE [AutomatedSystem] (
  [id] integer PRIMARY KEY,
  [autosystem_name] nvarchar(255),
  [autosystem__short_name] nvarchar(255),
  [system_class] integer,
  [vendor_id] integer,
  [vendor_product_id] integer,
  [version] nvarchar(255),
  [modules] json,
  [interfaces] json,
  [system_status] nvarchar(255) NOT NULL CHECK ([system_status] IN ('active', 'inactive', 'maintenance', 'upgrade')),
  [installation_date] date,
  [notes] text
)
GO

CREATE TABLE [AutomationClass] (
  [id] integer PRIMARY KEY,
  [level] integer,
  [system_class] nvarchar(255),
  [description] text
)
GO

CREATE TABLE [ObjectSystem] (
  [id] integer PRIMARY KEY,
  [object_id] integer,
  [system_id] integer,
  [status] nvarchar(255) NOT NULL CHECK ([status] IN ('planned', 'in_progress', 'completed', 'partial')),
  [implementation_date] date,
  [integrator_id] integer,
  [implementer_id] integer,
  [notes] text
)
GO

CREATE TABLE [ObjectCharacteristic] (
  [id] integer PRIMARY KEY,
  [object_id] integer,
  [characteristic_name] nvarchar(255),
  [code] nvarchar(255),
  [unit] nvarchar(255),
  [description] text,
  [is_required] boolean
)
GO

CREATE TABLE [ObjectCharacteristicValue] (
  [id] integer PRIMARY KEY,
  [characteristic_id] integer,
  [value] double,
  [measurement_date] date,
  [notes] text
)
GO

CREATE TABLE [AutomationRequirement] (
  [id] integer PRIMARY KEY,
  [automation] nvarchar(255),
  [requirement] text,
  [is_mandatory] boolean,
  [regulation] nvarchar(255)
)
GO

CREATE TABLE [Participant] (
  [id] integer PRIMARY KEY,
  [participant_name] nvarchar(255),
  [inn] nvarchar(255) UNIQUE,
  [participant_type] nvarchar(255) NOT NULL CHECK ([participant_type] IN ('vendor', 'engineering', 'full_cycle', 'supplier')),
  [is_partner] boolean,
  [registration_date] date,
  [website] nvarchar(255),
  [kam_name] nvarchar(255),
  [kam_phone] nvarchar(255),
  [contact_person] nvarchar(255),
  [contact_phone] nvarchar(255),
  [presentation_url] nvarchar(255),
  [profile] text,
  [industries] json,
  [contacts] json,
  [financial_data] json
)
GO

CREATE TABLE [VendorProduct] (
  [id] integer PRIMARY KEY,
  [product_name] nvarchar(255),
  [vendor_id] integer,
  [product_type] nvarchar(255) NOT NULL CHECK ([product_type] IN ('software', 'hardware', 'service')),
  [article] nvarchar(255) UNIQUE,
  [description] text,
  [version] nvarchar(255),
  [technical_specs] json,
  [system_types] json,
  [industries] json,
  [release_year] date,
  [end_of_support] date,
  [is_active] boolean
)
GO

CREATE TABLE [Project] (
  [id] integer PRIMARY KEY,
  [participant_id] integer NOT NULL,
  [vendor_product_id] integer,
  [object_id] integer NOT NULL,
  [name] varchar(200) NOT NULL,
  [year] integer NOT NULL,
  [successful] boolean NOT NULL DEFAULT (true),
  [description] text,
  [created_at] datetime NOT NULL,
  [updated_at] datetime NOT NULL
)
GO

CREATE TABLE [Certificate] (
  [id] integer PRIMARY KEY,
  [participant_id] integer NOT NULL,
  [vendor_product_id] integer,
  [name] varchar(200) NOT NULL,
  [certificate_type] varchar(20) NOT NULL,
  [issued_by] varchar(200) NOT NULL,
  [issued_date] date NOT NULL,
  [expiry_date] date,
  [file] nvarchar(255),
  [created_at] datetime NOT NULL,
  [updated_at] datetime NOT NULL
)
GO

CREATE TABLE [Review] (
  [id] integer PRIMARY KEY,
  [participant_id] integer NOT NULL,
  [text] text NOT NULL,
  [rating] integer NOT NULL,
  [date] date NOT NULL,
  [source] varchar(200),
  [created_at] datetime NOT NULL,
  [updated_at] datetime NOT NULL
)
GO

CREATE TABLE [TCOAnalysis] (
  [id] integer PRIMARY KEY,
  [participant_id] integer NOT NULL,
  [vendor_product_id] integer NOT NULL,
  [capex] decimal(15,2) NOT NULL,
  [opex_per_year] decimal(15,2) NOT NULL,
  [period_years] integer NOT NULL DEFAULT (5),
  [discount_rate] decimal(5,2) NOT NULL DEFAULT (10),
  [notes] text,
  [created_at] datetime NOT NULL,
  [updated_at] datetime NOT NULL
)
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Название юр. лица',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'OwnerEntity',
@level2type = N'Column', @level2name = 'owner_name';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'ИНН',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'OwnerEntity',
@level2type = N'Column', @level2name = 'inn';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Следующий в иерархии владелец',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'OwnerEntity',
@level2type = N'Column', @level2name = 'owner_id';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Корневой владелец.',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'OwnerEntity',
@level2type = N'Column', @level2name = 'ultimate_owner_id';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Доля владения',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'OwnerEntity',
@level2type = N'Column', @level2name = 'ownership_percentage';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Адрес производства (уровень 1)',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Address',
@level2type = N'Column', @level2name = 'house';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Адрес установки (уровень 3)',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Address',
@level2type = N'Column', @level2name = 'title';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Уровень объекта',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Category',
@level2type = N'Column', @level2name = 'object_level';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Значение категории',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Category',
@level2type = N'Column', @level2name = 'category_name';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Полное название объекта',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Object',
@level2type = N'Column', @level2name = 'object_name';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Короткое название объекта',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Object',
@level2type = N'Column', @level2name = 'object_short_name';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Историческое название объекта',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Object',
@level2type = N'Column', @level2name = 'object_old_name';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Юридическое название объекта',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Object',
@level2type = N'Column', @level2name = 'object_law_name';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Уровень в иерархии: производство -> цех -> установка',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Object',
@level2type = N'Column', @level2name = 'hierarchy_level';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Классификация объекта (завод, цех, очередь, установка)',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Object',
@level2type = N'Column', @level2name = 'object_class';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Разделение на категории: 1:отраслевые, 2:назначения, 3:технология',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Object',
@level2type = N'Column', @level2name = 'category';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дата ввода в эксплуатацию.',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Object',
@level2type = N'Column', @level2name = 'start_date';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Была ли реконструкция',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Object',
@level2type = N'Column', @level2name = 'is_reconstructed';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Мощность / объем производства',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Object',
@level2type = N'Column', @level2name = 'capacity';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Состояние объекта',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Object',
@level2type = N'Column', @level2name = 'status';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Родительский объект на уровень(или 2) выше в иерархии',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Object',
@level2type = N'Column', @level2name = 'parent_object_id';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Полное название системы автоматизации',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'AutomatedSystem',
@level2type = N'Column', @level2name = 'autosystem_name';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Короткое название системы автоматизации',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'AutomatedSystem',
@level2type = N'Column', @level2name = 'autosystem__short_name';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Тип системы (уровень и класс)',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'AutomatedSystem',
@level2type = N'Column', @level2name = 'system_class';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Поставщик системы',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'AutomatedSystem',
@level2type = N'Column', @level2name = 'vendor_id';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Продукт',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'AutomatedSystem',
@level2type = N'Column', @level2name = 'vendor_product_id';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Версия системы',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'AutomatedSystem',
@level2type = N'Column', @level2name = 'version';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Модули системы',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'AutomatedSystem',
@level2type = N'Column', @level2name = 'modules';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Интерфейсы системы',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'AutomatedSystem',
@level2type = N'Column', @level2name = 'interfaces';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Статус системы.',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'AutomatedSystem',
@level2type = N'Column', @level2name = 'system_status';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дата получения системы.',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'AutomatedSystem',
@level2type = N'Column', @level2name = 'installation_date';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дополнительная информация',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'AutomatedSystem',
@level2type = N'Column', @level2name = 'notes';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Уровень автоматизации: L0 | L1 | L2 | L3 | L4',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'AutomationClass',
@level2type = N'Column', @level2name = 'level';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Класс системы',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'AutomationClass',
@level2type = N'Column', @level2name = 'system_class';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Статус ввода системы в эксплуатацию',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'ObjectSystem',
@level2type = N'Column', @level2name = 'status';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дата ввода системы в эксплуатацию',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'ObjectSystem',
@level2type = N'Column', @level2name = 'implementation_date';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Интегратор системы',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'ObjectSystem',
@level2type = N'Column', @level2name = 'integrator_id';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Внедряющая компания',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'ObjectSystem',
@level2type = N'Column', @level2name = 'implementer_id';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дополнительные пояснения',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'ObjectSystem',
@level2type = N'Column', @level2name = 'notes';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Название характеристики',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'ObjectCharacteristic',
@level2type = N'Column', @level2name = 'characteristic_name';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Код характеристики',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'ObjectCharacteristic',
@level2type = N'Column', @level2name = 'code';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Единица измерения',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'ObjectCharacteristic',
@level2type = N'Column', @level2name = 'unit';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Описание',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'ObjectCharacteristic',
@level2type = N'Column', @level2name = 'description';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Обяательная характеристика',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'ObjectCharacteristic',
@level2type = N'Column', @level2name = 'is_required';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Значение',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'ObjectCharacteristicValue',
@level2type = N'Column', @level2name = 'value';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дата измерения',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'ObjectCharacteristicValue',
@level2type = N'Column', @level2name = 'measurement_date';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дополнительная информация',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'ObjectCharacteristicValue',
@level2type = N'Column', @level2name = 'notes';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Требование',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'AutomationRequirement',
@level2type = N'Column', @level2name = 'requirement';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Обязательность',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'AutomationRequirement',
@level2type = N'Column', @level2name = 'is_mandatory';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Нормативный документ',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'AutomationRequirement',
@level2type = N'Column', @level2name = 'regulation';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'ИНН',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Participant',
@level2type = N'Column', @level2name = 'inn';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Тип участника: вендор, инжиниринговая компания, вендо полного цикла, поставщик',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Participant',
@level2type = N'Column', @level2name = 'participant_type';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Является ли партнером',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Participant',
@level2type = N'Column', @level2name = 'is_partner';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дата регистрации',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Participant',
@level2type = N'Column', @level2name = 'registration_date';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Ссылка на сайт',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Participant',
@level2type = N'Column', @level2name = 'website';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Имя КАМ',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Participant',
@level2type = N'Column', @level2name = 'kam_name';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Номер КАМ',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Participant',
@level2type = N'Column', @level2name = 'kam_phone';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Контакт от ЦК ПА',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Participant',
@level2type = N'Column', @level2name = 'contact_person';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Телефон от ЦК ПА',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Participant',
@level2type = N'Column', @level2name = 'contact_phone';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Ссылка на презентацию',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Participant',
@level2type = N'Column', @level2name = 'presentation_url';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Профиль компании',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Participant',
@level2type = N'Column', @level2name = 'profile';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Отрасли применения',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Participant',
@level2type = N'Column', @level2name = 'industries';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Контактная информация',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Participant',
@level2type = N'Column', @level2name = 'contacts';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Финансовые показатели',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Participant',
@level2type = N'Column', @level2name = 'financial_data';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Название вендорского продукта',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'VendorProduct',
@level2type = N'Column', @level2name = 'product_name';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Вендор',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'VendorProduct',
@level2type = N'Column', @level2name = 'vendor_id';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Тип продукта',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'VendorProduct',
@level2type = N'Column', @level2name = 'product_type';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Артикул',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'VendorProduct',
@level2type = N'Column', @level2name = 'article';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Описание',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'VendorProduct',
@level2type = N'Column', @level2name = 'description';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Версия',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'VendorProduct',
@level2type = N'Column', @level2name = 'version';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Технические характеристики',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'VendorProduct',
@level2type = N'Column', @level2name = 'technical_specs';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Типы систем',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'VendorProduct',
@level2type = N'Column', @level2name = 'system_types';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Отрасли применения',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'VendorProduct',
@level2type = N'Column', @level2name = 'industries';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дата выпуска',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'VendorProduct',
@level2type = N'Column', @level2name = 'release_year';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Конец поддержки',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'VendorProduct',
@level2type = N'Column', @level2name = 'end_of_support';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Активен ли продукт',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'VendorProduct',
@level2type = N'Column', @level2name = 'is_active';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Участник',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Project',
@level2type = N'Column', @level2name = 'participant_id';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Вендорский продукт',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Project',
@level2type = N'Column', @level2name = 'vendor_product_id';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Объект внедрения',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Project',
@level2type = N'Column', @level2name = 'object_id';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Название проекта',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Project',
@level2type = N'Column', @level2name = 'name';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Год реализации',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Project',
@level2type = N'Column', @level2name = 'year';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Успешный пуск',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Project',
@level2type = N'Column', @level2name = 'successful';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Описание',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Project',
@level2type = N'Column', @level2name = 'description';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дата создания',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Project',
@level2type = N'Column', @level2name = 'created_at';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дата обновления',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Project',
@level2type = N'Column', @level2name = 'updated_at';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Участник',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Certificate',
@level2type = N'Column', @level2name = 'participant_id';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Вендорский продукт',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Certificate',
@level2type = N'Column', @level2name = 'vendor_product_id';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Название сертификата',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Certificate',
@level2type = N'Column', @level2name = 'name';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Тип сертификата: ISO / AUTHORIZED / SPECIALIST / OTHER',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Certificate',
@level2type = N'Column', @level2name = 'certificate_type';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Кем выдан',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Certificate',
@level2type = N'Column', @level2name = 'issued_by';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дата выдачи',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Certificate',
@level2type = N'Column', @level2name = 'issued_date';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Срок действия',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Certificate',
@level2type = N'Column', @level2name = 'expiry_date';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Файл сертификата',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Certificate',
@level2type = N'Column', @level2name = 'file';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дата создания',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Certificate',
@level2type = N'Column', @level2name = 'created_at';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дата обновления',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Certificate',
@level2type = N'Column', @level2name = 'updated_at';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Участник',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Review',
@level2type = N'Column', @level2name = 'participant_id';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Текст отзыва',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Review',
@level2type = N'Column', @level2name = 'text';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Оценка 1..5',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Review',
@level2type = N'Column', @level2name = 'rating';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дата отзыва',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Review',
@level2type = N'Column', @level2name = 'date';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Источник',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Review',
@level2type = N'Column', @level2name = 'source';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дата создания',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Review',
@level2type = N'Column', @level2name = 'created_at';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дата обновления',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'Review',
@level2type = N'Column', @level2name = 'updated_at';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Участник',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'TCOAnalysis',
@level2type = N'Column', @level2name = 'participant_id';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Вендорский продукт',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'TCOAnalysis',
@level2type = N'Column', @level2name = 'vendor_product_id';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'CAPEX (млн руб)',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'TCOAnalysis',
@level2type = N'Column', @level2name = 'capex';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'OPEX в год (млн руб)',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'TCOAnalysis',
@level2type = N'Column', @level2name = 'opex_per_year';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Период анализа (лет)',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'TCOAnalysis',
@level2type = N'Column', @level2name = 'period_years';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Ставка дисконтирования %',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'TCOAnalysis',
@level2type = N'Column', @level2name = 'discount_rate';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Примечания',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'TCOAnalysis',
@level2type = N'Column', @level2name = 'notes';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дата создания',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'TCOAnalysis',
@level2type = N'Column', @level2name = 'created_at';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Дата обновления',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'TCOAnalysis',
@level2type = N'Column', @level2name = 'updated_at';
GO

ALTER TABLE [OwnerEntity] ADD FOREIGN KEY ([owner_id]) REFERENCES [OwnerEntity] ([id])
GO

ALTER TABLE [OwnerEntity] ADD FOREIGN KEY ([ultimate_owner_id]) REFERENCES [OwnerEntity] ([id])
GO

ALTER TABLE [Object] ADD FOREIGN KEY ([category]) REFERENCES [Category] ([id])
GO

ALTER TABLE [Object] ADD FOREIGN KEY ([parent_object_id]) REFERENCES [Object] ([id])
GO

ALTER TABLE [Object] ADD FOREIGN KEY ([address_id]) REFERENCES [Address] ([id])
GO

ALTER TABLE [Object] ADD FOREIGN KEY ([owner_entity_id]) REFERENCES [OwnerEntity] ([id])
GO

ALTER TABLE [AutomatedSystem] ADD FOREIGN KEY ([system_class]) REFERENCES [AutomationClass] ([id])
GO

ALTER TABLE [AutomatedSystem] ADD FOREIGN KEY ([vendor_id]) REFERENCES [Participant] ([id])
GO

ALTER TABLE [AutomatedSystem] ADD FOREIGN KEY ([vendor_product_id]) REFERENCES [VendorProduct] ([id])
GO

ALTER TABLE [ObjectSystem] ADD FOREIGN KEY ([object_id]) REFERENCES [Object] ([id])
GO

ALTER TABLE [ObjectSystem] ADD FOREIGN KEY ([system_id]) REFERENCES [AutomatedSystem] ([id])
GO

ALTER TABLE [ObjectSystem] ADD FOREIGN KEY ([integrator_id]) REFERENCES [Participant] ([id])
GO

ALTER TABLE [ObjectSystem] ADD FOREIGN KEY ([implementer_id]) REFERENCES [Participant] ([id])
GO

ALTER TABLE [ObjectCharacteristic] ADD FOREIGN KEY ([object_id]) REFERENCES [Object] ([id])
GO

ALTER TABLE [ObjectCharacteristicValue] ADD FOREIGN KEY ([characteristic_id]) REFERENCES [ObjectCharacteristic] ([id])
GO

ALTER TABLE [AutomationRequirement] ADD FOREIGN KEY ([automation]) REFERENCES [ObjectSystem] ([id])
GO

ALTER TABLE [VendorProduct] ADD FOREIGN KEY ([vendor_id]) REFERENCES [Participant] ([id])
GO

ALTER TABLE [Project] ADD FOREIGN KEY ([participant_id]) REFERENCES [Participant] ([id])
GO

ALTER TABLE [Project] ADD FOREIGN KEY ([vendor_product_id]) REFERENCES [VendorProduct] ([id])
GO

ALTER TABLE [Project] ADD FOREIGN KEY ([object_id]) REFERENCES [Object] ([id])
GO

ALTER TABLE [Certificate] ADD FOREIGN KEY ([participant_id]) REFERENCES [Participant] ([id])
GO

ALTER TABLE [Certificate] ADD FOREIGN KEY ([vendor_product_id]) REFERENCES [VendorProduct] ([id])
GO

ALTER TABLE [Review] ADD FOREIGN KEY ([participant_id]) REFERENCES [Participant] ([id])
GO

ALTER TABLE [TCOAnalysis] ADD FOREIGN KEY ([participant_id]) REFERENCES [Participant] ([id])
GO

ALTER TABLE [TCOAnalysis] ADD FOREIGN KEY ([vendor_product_id]) REFERENCES [VendorProduct] ([id])
GO
