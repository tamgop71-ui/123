-- База данных для бота модерации бесед VK (8 уровней доступа + Супер-Админ)

CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `peer_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `role` INT DEFAULT 0 COMMENT '0-Участник, 1..7 - уровни админок',
  `is_super` TINYINT(1) DEFAULT 0 COMMENT '1 - Супер-доступ (Владелец бота)',
  `warns` INT DEFAULT 0,
  `mute_until` TIMESTAMP NULL DEFAULT NULL,
  `is_banned` TINYINT(1) DEFAULT 0,
  `nickname` VARCHAR(64) DEFAULT NULL,
  `experience` INT DEFAULT 0,
  `reputation` INT DEFAULT 0,
  `daily_bonus_last` TIMESTAMP NULL DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `user_chat_unique` (`peer_id`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `chats` (
  `peer_id` BIGINT PRIMARY KEY,
  `title` VARCHAR(255) DEFAULT 'Беседа',
  `owner_id` BIGINT DEFAULT NULL,
  `silent_mode` TINYINT(1) DEFAULT 0,
  `custom_cmd_access` JSON DEFAULT NULL,
  `filter_words` JSON DEFAULT NULL,
  `ignored_users` JSON DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `groups` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `owner_id` BIGINT NOT NULL,
  `group_name` VARCHAR(128) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `async_chats` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `owner_id` BIGINT NOT NULL,
  `peer_id` BIGINT NOT NULL,
  `async_group_id` INT DEFAULT NULL,
  UNIQUE KEY `peer_async_unique` (`peer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `warns_history` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `peer_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `reason` VARCHAR(255) DEFAULT 'Без причины',
  `given_by` BIGINT NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
