-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Host: 10.5.0.10
-- Erstellungszeit: 07. Dez 2025 um 16:57
-- Server-Version: 9.4.0
-- PHP-Version: 8.3.26

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Datenbank: `state_checker`
--

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `checked_backups`
--

CREATE TABLE `checked_backups` (
  `ID` bigint NOT NULL,
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `token` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `stateCheckFrequency_inMinutes` int NOT NULL,
  `mostRecentBackupFile_creationDate` bigint NOT NULL,
  `mostRecentBackupFile_hash` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `backupIsDownMessageHasBeenSent` tinyint NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Daten für Tabelle `checked_backups`
--

INSERT INTO `checked_backups` (`ID`, `name`, `description`, `token`, `stateCheckFrequency_inMinutes`, `mostRecentBackupFile_creationDate`, `mostRecentBackupFile_hash`, `backupIsDownMessageHasBeenSent`) VALUES
(1, 'Backup File Check - PriceTracker', '', 'bD8dZL8uaEVJWROwoBKvqKPPIZpP0x2aW9cyLAmrUDsXrbxcw94R3xvpeDBQsAbrUBe0erbZSGSkI1woB89XhnNUocgdMflgJxtK', 1500, 1738469706, 'd41d8cd98f00b204e9800998ecf8427e', 1),
(2, 'Price Tracker Backup - Google Drive', '', 'l4Vf2iW4jYrdD8vd6bB5KaFB2VHjJnli0rF2eUGIz76uYsGqnQWBz4wHHfl2D8j1cxab4e12ujGlNUybMtmLKREEJPh7Vvy30kUW', 1500, 1755844219, '343f116525f69112d71921b07b33cc0d', 0),
(3, 'RemindMeBot Backup - Google Drive', 'nameTheCountdown folder name', 'EHwS6eILPih05JHZElnQr33PzZgyz608eDvn9KsbenSqyu7TXenGGYvq0JRIpNfmAO6anTWj2EswwwmWGrBr04J7y1U7EtMpQ13r', 1500, 1755844241, 'fe04717ce510318f207d8aa63a79f330', 0),
(4, 'Backup File Check - RemindMeBot', 'NameTheCountDownBot - live', '4KAJX2i4jHWcdCX14Gk4ix4PMx3hMLJDHcsiMgSuqQK86FsZUBtpx1A7SXZNPmqbQm2iBnQNe3AiOO5VLFDCQQwik0bq42QiRi9U', 1500, 1738469810, 'd41d8cd98f00b204e9800998ecf8427e', 1),
(5, 'Updraft Plus Websites - Google Drive', 'backup directory of websites secured by updraft plus', 'EHwS6eILPih05JHZElnQr33PzZgyz608eDvn9KsbenSqyu7TXenGGYvq0JRIpNfmAO6anTWj2EswwwmWGrBr04J7y1U7EtMpQ13r', 1500, 1755840561, '88e53d865ff31fa6ab67614b64f7c6af', 0);

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `checked_tools`
--

CREATE TABLE `checked_tools` (
  `ID` bigint NOT NULL,
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `token` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `stateCheckFrequency_inMinutes` int NOT NULL,
  `lastTimeToolWasUp` bigint NOT NULL,
  `toolIsDownMessageHasBeenSent` tinyint NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
-- Indizes der exportierten Tabellen
--

--
-- Indizes für die Tabelle `checked_backups`
--
ALTER TABLE `checked_backups`
  ADD PRIMARY KEY (`ID`);

--
-- Indizes für die Tabelle `checked_tools`
--
ALTER TABLE `checked_tools`
  ADD PRIMARY KEY (`ID`);

--
-- AUTO_INCREMENT für exportierte Tabellen
--

--
-- AUTO_INCREMENT für Tabelle `checked_backups`
--
ALTER TABLE `checked_backups`
  MODIFY `ID` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT für Tabelle `checked_tools`
--
ALTER TABLE `checked_tools`
  MODIFY `ID` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
