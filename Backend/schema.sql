-- DukaTrack MySQL schema (generated from models.py). Create the database first:
-- CREATE DATABASE dukatrack CHARACTER SET utf8mb4;  USE dukatrack;

CREATE TABLE `Categories` (
	`CategoryID` INTEGER NOT NULL AUTO_INCREMENT, 
	`CategoryName` VARCHAR(60) NOT NULL, 
	PRIMARY KEY (`CategoryID`), 
	UNIQUE (`CategoryName`)
);

CREATE TABLE `Users` (
	`UserID` INTEGER NOT NULL AUTO_INCREMENT, 
	`FullName` VARCHAR(100) NOT NULL, 
	`Phone` VARCHAR(15), 
	`Username` VARCHAR(50) NOT NULL, 
	`PasswordHash` VARCHAR(255) NOT NULL, 
	`Role` ENUM('Owner','Attendant') NOT NULL, 
	`IsActive` BOOL NOT NULL, 
	`FailedAttempts` INTEGER NOT NULL, 
	`LockedUntil` DATETIME, 
	`CreatedAt` DATETIME NOT NULL, 
	PRIMARY KEY (`UserID`), 
	UNIQUE (`Username`)
);

CREATE TABLE `BackupLogs` (
	`BackupID` INTEGER NOT NULL AUTO_INCREMENT, 
	`UserID` INTEGER NOT NULL, 
	`FileName` VARCHAR(150), 
	`BackupDate` DATETIME NOT NULL, 
	`Status` ENUM('Success','Failed') NOT NULL, 
	PRIMARY KEY (`BackupID`), 
	FOREIGN KEY(`UserID`) REFERENCES `Users` (`UserID`)
);

CREATE TABLE `Products` (
	`ProductID` INTEGER NOT NULL AUTO_INCREMENT, 
	`CategoryID` INTEGER NOT NULL, 
	`ProductName` VARCHAR(100) NOT NULL, 
	`UnitPrice` NUMERIC(10, 2) NOT NULL, 
	`StockQty` INTEGER NOT NULL, 
	`ReorderLevel` INTEGER NOT NULL, 
	`IsActive` BOOL NOT NULL, 
	PRIMARY KEY (`ProductID`), 
	FOREIGN KEY(`CategoryID`) REFERENCES `Categories` (`CategoryID`)
);

CREATE TABLE `Sales` (
	`SaleID` INTEGER NOT NULL AUTO_INCREMENT, 
	`UserID` INTEGER NOT NULL, 
	`SaleDate` DATETIME NOT NULL, 
	`Status` ENUM('Completed','Cancelled') NOT NULL, 
	`TotalAmount` NUMERIC(10, 2) NOT NULL, 
	PRIMARY KEY (`SaleID`), 
	FOREIGN KEY(`UserID`) REFERENCES `Users` (`UserID`)
);

CREATE TABLE `Forecasts` (
	`ForecastID` INTEGER NOT NULL AUTO_INCREMENT, 
	`ProductID` INTEGER NOT NULL, 
	`UserID` INTEGER NOT NULL, 
	`PeriodStart` DATE NOT NULL, 
	`PeriodDays` INTEGER NOT NULL, 
	`PredictedQty` NUMERIC(10, 2) NOT NULL, 
	`GeneratedAt` DATETIME NOT NULL, 
	PRIMARY KEY (`ForecastID`), 
	FOREIGN KEY(`ProductID`) REFERENCES `Products` (`ProductID`), 
	FOREIGN KEY(`UserID`) REFERENCES `Users` (`UserID`)
);

CREATE TABLE `SaleItems` (
	`SaleItemID` INTEGER NOT NULL AUTO_INCREMENT, 
	`SaleID` INTEGER NOT NULL, 
	`ProductID` INTEGER NOT NULL, 
	`Quantity` INTEGER NOT NULL, 
	`UnitPrice` NUMERIC(10, 2) NOT NULL, 
	PRIMARY KEY (`SaleItemID`), 
	FOREIGN KEY(`SaleID`) REFERENCES `Sales` (`SaleID`), 
	FOREIGN KEY(`ProductID`) REFERENCES `Products` (`ProductID`)
);

CREATE TABLE `StockMovements` (
	`MovementID` INTEGER NOT NULL AUTO_INCREMENT, 
	`ProductID` INTEGER NOT NULL, 
	`UserID` INTEGER NOT NULL, 
	`SaleID` INTEGER, 
	`MovementType` ENUM('StockIn','StockOut','StockReturn') NOT NULL, 
	`Quantity` INTEGER NOT NULL, 
	`SupplierName` VARCHAR(100), 
	`MovementDate` DATETIME NOT NULL, 
	PRIMARY KEY (`MovementID`), 
	FOREIGN KEY(`ProductID`) REFERENCES `Products` (`ProductID`), 
	FOREIGN KEY(`UserID`) REFERENCES `Users` (`UserID`), 
	FOREIGN KEY(`SaleID`) REFERENCES `Sales` (`SaleID`)
);
