CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `peer_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `role` INT DEFAULT 0,
  `warns` INT DEFAULT 0,
  `is_banned` TINYINT(1) DEFAULT 0,
  UNIQUE KEY `user_chat_unique` (`peer_id`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `warns_history` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `peer_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `reason` VARCHAR(255) DEFAULT 'Без причины',
  `given_by` BIGINT NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
