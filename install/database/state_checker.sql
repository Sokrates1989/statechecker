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

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `checked_websites`
--

CREATE TABLE `checked_websites` (
  `ID` bigint NOT NULL,
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `state` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `isDownMessageHasBeenSent` tinyint NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
-- Indizes für die Tabelle `checked_websites`
--
ALTER TABLE `checked_websites`
  ADD PRIMARY KEY (`ID`);

--
-- AUTO_INCREMENT für exportierte Tabellen
--

--
-- AUTO_INCREMENT für Tabelle `checked_backups`
--
ALTER TABLE `checked_backups`
  MODIFY `ID` bigint NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT für Tabelle `checked_tools`
--
ALTER TABLE `checked_tools`
  MODIFY `ID` bigint NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT für Tabelle `checked_websites`
--
ALTER TABLE `checked_websites`
  MODIFY `ID` bigint NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
