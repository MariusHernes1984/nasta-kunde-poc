-- Nasta AS Kunde PoC - Database Schema
-- Azure SQL Database

CREATE TABLE Customers (
    kundenummer INT PRIMARY KEY,
    navn NVARCHAR(200) NOT NULL,
    adresse NVARCHAR(300),
    epost NVARCHAR(200),
    telefonnummer NVARCHAR(20),
    org_nummer NVARCHAR(20) UNIQUE NOT NULL
);

CREATE TABLE Machines (
    id INT IDENTITY(1,1) PRIMARY KEY,
    kundenummer INT NOT NULL,
    device_id NVARCHAR(50) UNIQUE NOT NULL,
    maskin_navn NVARCHAR(200) NOT NULL,
    aarsmodell INT,
    chassisnummer NVARCHAR(100) UNIQUE NOT NULL,
    CONSTRAINT FK_Machines_Customers FOREIGN KEY (kundenummer) REFERENCES Customers(kundenummer)
);

CREATE TABLE Orders (
    id INT IDENTITY(1,1) PRIMARY KEY,
    kundenummer INT NOT NULL,
    ordrenummer NVARCHAR(50) UNIQUE NOT NULL,
    ordretype NVARCHAR(50) NOT NULL,          -- Service, Reparasjon, Garanti, Deler
    beskrivelse NVARCHAR(500),
    device_id NVARCHAR(50) NOT NULL,
    status NVARCHAR(50) NOT NULL,             -- Mottatt, Under behandling, Ferdig, Avsluttet
    opprettet_dato DATE NOT NULL,
    symptomer_feil NVARCHAR(500),
    CONSTRAINT FK_Orders_Customers FOREIGN KEY (kundenummer) REFERENCES Customers(kundenummer),
    CONSTRAINT FK_Orders_Machines FOREIGN KEY (device_id) REFERENCES Machines(device_id)
);

-- Indexes for common lookups
CREATE INDEX IX_Machines_Kundenummer ON Machines(kundenummer);
CREATE INDEX IX_Orders_Kundenummer ON Orders(kundenummer);
CREATE INDEX IX_Orders_DeviceId ON Orders(device_id);
CREATE INDEX IX_Orders_Status ON Orders(status);
CREATE INDEX IX_Customers_OrgNummer ON Customers(org_nummer);
