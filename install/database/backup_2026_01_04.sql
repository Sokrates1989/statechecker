-- statechecker demo backup
--
-- This file contains both schema + example data and can be used as
-- /docker-entrypoint-initdb.d/init.sql for bootstrapping an empty db_data.

CREATE DATABASE IF NOT EXISTS state_checker;
USE state_checker;

CREATE TABLE IF NOT EXISTS `checked_tools` (
  `ID` BIGINT NOT NULL AUTO_INCREMENT,
  `name` TEXT NOT NULL,
  `description` TEXT NOT NULL,
  `token` TEXT NOT NULL,
  `stateCheckFrequency_inMinutes` INT NOT NULL,
  `lastTimeToolWasUp` BIGINT NOT NULL,
  `toolIsDownMessageHasBeenSent` TINYINT NOT NULL DEFAULT '0',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `checked_backups` (
  `ID` BIGINT NOT NULL AUTO_INCREMENT,
  `name` TEXT NOT NULL,
  `description` TEXT NOT NULL,
  `token` TEXT NOT NULL,
  `stateCheckFrequency_inMinutes` INT NOT NULL,
  `mostRecentBackupFile_creationDate` BIGINT NOT NULL,
  `mostRecentBackupFile_hash` TEXT NOT NULL,
  `backupIsDownMessageHasBeenSent` TINYINT NOT NULL DEFAULT '0',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `checked_websites` (
  `ID` BIGINT NOT NULL AUTO_INCREMENT,
  `name` TEXT NOT NULL,
  `state` TEXT NOT NULL,
  `isDownMessageHasBeenSent` TINYINT NOT NULL DEFAULT '0',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



-- statechecker demo backup
--
-- This file contains both schema + example data and can be used as
-- /docker-entrypoint-initdb.d/init.sql for bootstrapping an empty db_data.

CREATE DATABASE IF NOT EXISTS state_checker;
USE state_checker;

CREATE TABLE IF NOT EXISTS `checked_tools` (
  `ID` BIGINT NOT NULL AUTO_INCREMENT,
  `name` TEXT NOT NULL,
  `description` TEXT NOT NULL,
  `token` TEXT NOT NULL,
  `stateCheckFrequency_inMinutes` INT NOT NULL,
  `lastTimeToolWasUp` BIGINT NOT NULL,
  `toolIsDownMessageHasBeenSent` TINYINT NOT NULL DEFAULT '0',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `checked_backups` (
  `ID` BIGINT NOT NULL AUTO_INCREMENT,
  `name` TEXT NOT NULL,
  `description` TEXT NOT NULL,
  `token` TEXT NOT NULL,
  `stateCheckFrequency_inMinutes` INT NOT NULL,
  `mostRecentBackupFile_creationDate` BIGINT NOT NULL,
  `mostRecentBackupFile_hash` TEXT NOT NULL,
  `backupIsDownMessageHasBeenSent` TINYINT NOT NULL DEFAULT '0',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `checked_websites` (
  `ID` BIGINT NOT NULL AUTO_INCREMENT,
  `name` TEXT NOT NULL,
  `state` TEXT NOT NULL,
  `isDownMessageHasBeenSent` TINYINT NOT NULL DEFAULT '0',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



--
-- Daten für Tabelle `checked_backups`
--
INSERT INTO `checked_backups` (`ID`, `name`, `description`, `token`, `stateCheckFrequency_inMinutes`, `mostRecentBackupFile_creationDate`, `mostRecentBackupFile_hash`, `backupIsDownMessageHasBeenSent`) VALUES
(1, 'Backup File Check - PriceTracker', '', 'bD8dZL8uaEVJWROwoBKvqKPPIZpP0x2aW9cyLAmrUDsXrbxcw94R3xvpeDBQsAbrUBe0erbZSGSkI1woB89XhnNUocgdMflgJxtK', 1500, 1738469706, 'd41d8cd98f00b204e9800998ecf8427e', 1),
(2, 'Price Tracker Backup - Google Drive', '', 'l4Vf2iW4jYrdD8vd6bB5KaFB2VHjJnli0rF2eUGIz76uYsGqnQWBz4wHHfl2D8j1cxab4e12ujGlNUybMtmLKREEJPh7Vvy30kUW', 1500, 1755844219, '343f116525f69112d71921b07b33cc0d', 0),
(3, 'RemindMeBot Backup - Google Drive', 'nameTheCountdown folder name', 'EHwS6eILPih05JHZElnQr33PzZgyz608eDvn9KsbenSqyu7TXenGGYvq0JRIpNfmAO6anTWj2EswwwmWGrBr04J7y1U7EtMpQ13r', 1500, 1755844241, 'fe04717ce510318f207d8aa63a79f330', 0),
(4, 'Backup File Check - RemindMeBot', 'NameTheCountDownBot - live', '4KAJX2i4jHWcdCX14Gk4ix4PMx3hMLJDHcsiMgSuqQK86FsZUBtpx1A7SXZNPmqbQm2iBnQNe3AiOO5VLFDCQQwik0bq42QiRi9U', 1500, 1738469810, 'd41d8cd98f00b204e9800998ecf8427e', 1),
(5, 'Updraft Plus Websites - Google Drive', 'backup directory of websites secured by updraft plus', 'EHwS6eILPih05JHZElnQr33PzZgyz608eDvn9KsbenSqyu7TXenGGYvq0JRIpNfmAO6anTWj2EswwwmWGrBr04J7y1U7EtMpQ13r', 1500, 1755840561, '88e53d865ff31fa6ab67614b64f7c6af', 0);


--
-- Daten für Tabelle `checked_tools`
--
INSERT INTO `checked_tools` (`ID`, `name`, `description`, `token`, `stateCheckFrequency_inMinutes`, `lastTimeToolWasUp`, `toolIsDownMessageHasBeenSent`) VALUES
(3, 'nameTheCountDown-checkSchedule-development', 'Reminder tool telegram bot checking the schedule of reminders and countdowns', 'awlpsvzmilvsryxefgzdcphkreiugiwmclbagbkxiwhneaienmvqokauukafaiehaoqjrkmbxmgrgedmasgkljktlkzjecgclktp', 60, 1669171404, 1),
(4, 'nameTheCountDown-botApi-development', 'Reminder tool telegram bot listening to commands', '5zWZNwQUARO3z38PLD56CxxbZvgmsCwDp9hYo4HrIRUcz1cmPZaYBnvxP16m57KXZlT3tzvc1I6A0AMEhvs5faSvIJ5hM5GGmcqe', 60, 1669171404, 1),
(5, 'nameTheCountDown-botApi-live', 'Reminder tool telegram bot listening to commands', 'bH9zxL6eg2HzjVkqvKkF05nQQh9UcsIEsuke1Veu7OjRNM2q2cwebXxZjH9ntkC90CbRU23gJQZbXeTj6vK1XOcngJ6k248Is8NC', 5, 1755913045, 0),
(6, 'nameTheCountDown-checkSchedule-live', 'Reminder tool telegram bot checking the schedule of reminders and countdowns', 'qIyr5CpVAwPvJpqcU4Oe1IOLMIEasyP2uTkCugB9LaYJ1eiJ6ZyVQbZnBanLGLxCdobN19cbniWy3Y8pciBYmrqZvWkWHCTTcQTH', 5, 1765126390, 0),
(7, 'pricetracker-botApi-development', 'PriceTracker telegram bot listening to commands', 'NAFWG97surzhAL2PIoUp8BeHYg4PBHXDx31DNssmzIkLBUXXRXMymOH9dgp0il2FsZiIkyLqYWVZz1L8SkTCOY9uQ6DLVMk3wP3A', 10, 1682195646, 1),
(8, 'pricetracker-botApi-live', 'PriceTracker telegram bot listening to commands', '98j6D793lcZt071oB2QcACPsCqRIvUDu2ri3kR2aNHfxEJ7ClQpHbJFpGAyHruroeAvnamMb4EDRHKRGaNnDqyhf7kQQW9up5cm6', 5, 1765126391, 0),
(9, 'Telegram Photo Bot', 'makes photo every 5 minutes of security cams and sends them via telegram', 'QoqBoQpl4uKAo7m9kvu7aXFu30L1lHYVutqzVKxoDMd5Hqqq9Suxb2TPGstwHmRpioeKK62Ab8DDvfgq9tJdpVfhQZUBMNWlydEo', 12, 1742651722, 1),
(10, 'qnap cronjob check', '', 'nzl0L16Mm520Tmbcf2iKziDjfy8PCdDqBq8eS5e2cZmEKcba09zVwLcbsjDITUTC4nIH3YhS9iWWxWnc8mMjbTMHAGiDo5dlJ8cT', 60, 1755912662, 0),
(11, 'ananda-tracker-botApi-development', 'Ananda Tracker telegram bot listening to commands', '7w!z%C&F)J@NcRfUjXn2r5u8x/A?D(G-KaPdSgVkYp3s6v9y$B&E)H@MbQeThWmZ', 10, 1704601929, 1),
(12, 'ananda-tracker-bot', 'Ananda Tracker telegram bot listening to commands', '7w!z%C&F)J@NcRfUjXn2r5u8x/A?D(G-KaPdSgVkYp3s6v9y$B&E)H@MbQeThWmZ', 10, 1765126454, 0),
(13, 'priceTracker-checkPrices-dev', 'PriceTracker scheduled price check service', 'dev', 5, 1765126131, 0);



--
-- Daten für Tabelle `checked_websites`
--
INSERT INTO `checked_websites` (
  `name`,
  `state`,
  `isDownMessageHasBeenSent`
) VALUES
  ('https://example.com', 'up', 0),
  ('https://example.org', 'up', 0);

