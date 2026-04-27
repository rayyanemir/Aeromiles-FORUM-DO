DROP SCHEMA IF EXISTS AEROMILES CASCADE;
CREATE SCHEMA AEROMILES;

SET search_path TO AEROMILES;

CREATE TABLE TIER (
    id_tier VARCHAR(10) PRIMARY KEY,
    nama VARCHAR(50) NOT NULL,
    minimal_frekuensi_terbang INT NOT NULL,
    minimal_tier_miles INT NOT NULL
);

CREATE TABLE PENGGUNA (
    email VARCHAR(100) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    salutation VARCHAR(10) NOT NULL CHECK (salutation IN ('Mr.', 'Mrs.', 'Ms.', 'Dr.')),
    first_mid_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    country_code VARCHAR(5) NOT NULL,
    mobile_number VARCHAR(20) NOT NULL,
    tanggal_lahir DATE NOT NULL,
    kewarganegaraan VARCHAR(50) NOT NULL
);

CREATE TABLE MEMBER (
    email VARCHAR(100) PRIMARY KEY REFERENCES PENGGUNA(email) ON DELETE CASCADE,
    nomor_member VARCHAR(20) NOT NULL UNIQUE, 
    tanggal_bergabung DATE NOT NULL DEFAULT CURRENT_DATE,
    id_tier VARCHAR(10) NOT NULL REFERENCES TIER(id_tier),
    award_miles INT DEFAULT 0,
    total_miles INT DEFAULT 0
);

CREATE TABLE PENYEDIA (
    id SERIAL PRIMARY KEY
);

CREATE TABLE MASKAPAI (
    kode_maskapai VARCHAR(10) PRIMARY KEY,
    nama_maskapai VARCHAR(100) NOT NULL,
    id_penyedia INT NOT NULL UNIQUE REFERENCES PENYEDIA(id) ON DELETE CASCADE
);

CREATE TABLE STAF (
    email VARCHAR(100) PRIMARY KEY REFERENCES PENGGUNA(email) ON DELETE CASCADE,
    id_staf VARCHAR(20) NOT NULL UNIQUE,
    kode_maskapai VARCHAR(10) NOT NULL REFERENCES MASKAPAI(kode_maskapai)
);

CREATE TABLE MITRA (
    email_mitra VARCHAR(100) PRIMARY KEY,
    id_penyedia INT NOT NULL UNIQUE REFERENCES PENYEDIA(id) ON DELETE CASCADE,
    nama_mitra VARCHAR(100) NOT NULL,
    tanggal_kerja_sama DATE NOT NULL
);

CREATE TABLE IDENTITAS (
    nomor VARCHAR(50) PRIMARY KEY,
    email_member VARCHAR(100) NOT NULL REFERENCES MEMBER(email) ON DELETE CASCADE,
    tanggal_habis DATE NOT NULL,
    tanggal_terbit DATE NOT NULL,
    negara_penerbit VARCHAR(50) NOT NULL,
    jenis VARCHAR(30) NOT NULL CHECK (jenis IN ('Paspor', 'KTP', 'SIM'))
);

CREATE TABLE AWARD_MILES_PACKAGE (
    id VARCHAR(20) PRIMARY KEY,
    harga_paket DECIMAL(15,2) NOT NULL,
    jumlah_award_miles INT NOT NULL
);

CREATE TABLE MEMBER_AWARD_MILES_PACKAGE (
    id_award_miles_package VARCHAR(20) REFERENCES AWARD_MILES_PACKAGE(id),
    email_member VARCHAR(100) REFERENCES MEMBER(email) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_award_miles_package, email_member, timestamp)
);


CREATE TABLE BANDARA (
    iata_code CHAR(3) PRIMARY KEY,
    nama VARCHAR(100) NOT NULL,
    kota VARCHAR(100) NOT NULL,
    negara VARCHAR(100) NOT NULL
);


CREATE TABLE CLAIM_MISSING_MILES (
    id SERIAL PRIMARY KEY,
    email_member VARCHAR(100) NOT NULL REFERENCES MEMBER(email) ON DELETE CASCADE,
    email_staf VARCHAR(100) REFERENCES STAF(email),
    maskapai VARCHAR(10) NOT NULL REFERENCES MASKAPAI(kode_maskapai),
    bandara_asal CHAR(3) NOT NULL REFERENCES BANDARA(iata_code),
    bandara_tujuan CHAR(3) NOT NULL REFERENCES BANDARA(iata_code),
    tanggal_penerbangan DATE NOT NULL,
    flight_number VARCHAR(10) NOT NULL,
    nomor_tiket VARCHAR(20) NOT NULL,
    kelas_kabin VARCHAR(20) NOT NULL CHECK (kelas_kabin IN ('Economy', 'Business', 'First')),
    pnr VARCHAR(10) NOT NULL,
    status_penerimaan VARCHAR(20) NOT NULL DEFAULT 'Menunggu' CHECK (status_penerimaan IN ('Menunggu', 'Disetujui', 'Ditolak')),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_claim UNIQUE (email_member, flight_number, tanggal_penerbangan, nomor_tiket)
);

CREATE TABLE TRANSFER (
    email_member_1 VARCHAR(100) REFERENCES MEMBER(email) ON DELETE CASCADE,
    email_member_2 VARCHAR(100) REFERENCES MEMBER(email) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    jumlah INT NOT NULL CHECK (jumlah > 0),
    catatan VARCHAR(255),
    PRIMARY KEY (email_member_1, email_member_2, timestamp),
    CONSTRAINT cannot_transfer_to_self CHECK (email_member_1 <> email_member_2)
);

CREATE TABLE HADIAH (
    kode_hadiah VARCHAR(20) PRIMARY KEY,
    nama VARCHAR(100) NOT NULL,
    miles INT NOT NULL,
    deskripsi TEXT,
    valid_start_date DATE NOT NULL,
    program_end DATE NOT NULL,
    id_penyedia INT NOT NULL REFERENCES PENYEDIA(id) ON DELETE CASCADE
);

CREATE TABLE REDEEM (
    email_member VARCHAR(100) REFERENCES MEMBER(email) ON DELETE CASCADE,
    kode_hadiah VARCHAR(20) REFERENCES HADIAH(kode_hadiah),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (email_member, kode_hadiah, timestamp)
);

INSERT INTO TIER (id_tier, nama, minimal_frekuensi_terbang, minimal_tier_miles) VALUES 
('T01', 'Blue', 0, 0),
('T02', 'Silver', 10, 25000),
('T03', 'Gold', 30, 50000),
('T04', 'Platinum', 60, 100000);

INSERT INTO PENYEDIA (id) VALUES 
(1), (2), (3), (4), (5), (6), (7), (8), (9), (10);


INSERT INTO MASKAPAI (kode_maskapai, nama_maskapai, id_penyedia) VALUES 
('GA', 'Garuda Indonesia', 1),
('SQ', 'Singapore Airlines', 2),
('EK', 'Emirates', 3),
('QR', 'Qatar Airways', 4),
('CX', 'Cathay Pacific', 5);

INSERT INTO AWARD_MILES_PACKAGE (id, harga_paket, jumlah_award_miles) VALUES 
('AMP-001', 150000.00, 1000),
('AMP-002', 400000.00, 3000),
('AMP-003', 600000.00, 5000),
('AMP-004', 1100000.00, 10000),
('AMP-005', 2000000.00, 20000);

INSERT INTO BANDARA (iata_code, nama, kota, negara) VALUES 
('CGK', 'Soekarno-Hatta', 'Jakarta', 'Indonesia'),
('DPS', 'I Gusti Ngurah Rai', 'Bali', 'Indonesia'),
('SUB', 'Juanda', 'Surabaya', 'Indonesia'),
('KNO', 'Kualanamu', 'Medan', 'Indonesia'),
('SIN', 'Changi Airport', 'Singapore', 'Singapore'),
('HND', 'Haneda Airport', 'Tokyo', 'Japan'),
('NRT', 'Narita Airport', 'Tokyo', 'Japan'),
('ICN', 'Incheon Intl', 'Seoul', 'South Korea'),
('DXB', 'Dubai Intl', 'Dubai', 'UAE'),
('LHR', 'Heathrow Airport', 'London', 'UK'),
('JFK', 'John F. Kennedy', 'New York', 'USA'),
('SYD', 'Kingsford Smith', 'Sydney', 'Australia'),
('MEL', 'Melbourne Airport', 'Melbourne', 'Australia'),
('HKG', 'Hong Kong International Airport', 'Hong Kong', 'China'),
('KUL', 'Kuala Lumpur Intl', 'Kuala Lumpur', 'Malaysia'),
('BKK', 'Suvarnabhumi', 'Bangkok', 'Thailand');
INSERT INTO PENGGUNA (email, password, salutation, first_mid_name, last_name, country_code, mobile_number, tanggal_lahir, kewarganegaraan) VALUES
('andi.pratama@mail.com', 'password123', 'Mr.', 'Andi', 'Pratama', '+62', '8123456701', '1990-05-12', 'Indonesia'),
('budi.santoso@mail.com', 'password123', 'Mr.', 'Budi', 'Santoso', '+62', '8123456702', '1985-08-22', 'Indonesia'),
('citra.lestari@mail.com', 'password123', 'Ms.', 'Citra', 'Lestari', '+62', '8123456703', '1995-11-30', 'Indonesia'),
('dewi.sari@mail.com', 'password123', 'Mrs.', 'Dewi', 'Sari', '+62', '8123456704', '1992-02-14', 'Indonesia'),
('eko.wahyudi@mail.com', 'password123', 'Mr.', 'Eko', 'Wahyudi', '+62', '8123456705', '1988-07-07', 'Indonesia'),
('fajar.hidayat@mail.com', 'password123', 'Mr.', 'Fajar', 'Hidayat', '+62', '8123456706', '1993-09-18', 'Indonesia'),
('gina.putri@mail.com', 'password123', 'Ms.', 'Gina', 'Putri', '+62', '8123456707', '1997-04-25', 'Indonesia'),
('hendra.kusuma@mail.com', 'password123', 'Mr.', 'Hendra', 'Kusuma', '+62', '8123456708', '1980-12-01', 'Indonesia'),
('indah.permata@mail.com', 'password123', 'Mrs.', 'Indah', 'Permata', '+62', '8123456709', '1991-06-15', 'Indonesia'),
('joko.susilo@mail.com', 'password123', 'Mr.', 'Joko', 'Susilo', '+62', '8123456710', '1987-03-10', 'Indonesia'),
('kartika.sari@mail.com', 'password123', 'Ms.', 'Kartika', 'Sari', '+62', '8123456711', '1994-01-20', 'Indonesia'),
('lukman.hakim@mail.com', 'password123', 'Mr.', 'Lukman', 'Hakim', '+62', '8123456712', '1989-10-05', 'Indonesia'),
('maya.andini@mail.com', 'password123', 'Mrs.', 'Maya', 'Andini', '+62', '8123456713', '1992-12-25', 'Indonesia'),
('nanda.putra@mail.com', 'password123', 'Mr.', 'Nanda', 'Putra', '+62', '8123456714', '1996-08-14', 'Indonesia'),
('olivia.tan@mail.com', 'password123', 'Ms.', 'Olivia', 'Tan', '+62', '8123456715', '1995-05-05', 'Indonesia'),
('panji.asmara@mail.com', 'password123', 'Mr.', 'Panji', 'Asmara', '+62', '8123456716', '1990-09-09', 'Indonesia'),
('qori.asari@mail.com', 'password123', 'Ms.', 'Qori', 'Asari', '+62', '8123456717', '1993-07-17', 'Indonesia'),
('rizky.ramadhan@mail.com', 'password123', 'Mr.', 'Rizky', 'Ramadhan', '+62', '8123456718', '1994-04-10', 'Indonesia'),
('sandra.dewi@mail.com', 'password123', 'Mrs.', 'Sandra', 'Dewi', '+62', '8123456719', '1986-11-11', 'Indonesia'),
('taufik.hidayat@mail.com', 'password123', 'Mr.', 'Taufik', 'Hidayat', '+62', '8123456720', '1985-06-06', 'Indonesia'),
('umar.bin@mail.com', 'password123', 'Mr.', 'Umar', 'Bin', '+62', '8123456721', '1991-01-01', 'Indonesia'),
('vivi.andriani@mail.com', 'password123', 'Ms.', 'Vivi', 'Andriani', '+62', '8123456722', '1997-02-02', 'Indonesia'),
('wahyu.setiawan@mail.com', 'password123', 'Mr.', 'Wahyu', 'Setiawan', '+62', '8123456723', '1988-03-03', 'Indonesia'),
('xena.warrior@mail.com', 'password123', 'Ms.', 'Xena', 'Warrior', '+62', '8123456724', '1992-04-04', 'Indonesia'),
('yayan.ruhian@mail.com', 'password123', 'Mr.', 'Yayan', 'Ruhian', '+62', '8123456725', '1980-05-05', 'Indonesia'),
('zaskia.gotik@mail.com', 'password123', 'Mrs.', 'Zaskia', 'Gotik', '+62', '8123456726', '1990-06-06', 'Indonesia'),
('adi.hidayat@mail.com', 'password123', 'Mr.', 'Adi', 'Hidayat', '+62', '8123456727', '1984-07-07', 'Indonesia'),
('bella.safira@mail.com', 'password123', 'Ms.', 'Bella', 'Safira', '+62', '8123456728', '1985-08-08', 'Indonesia'),
('coki.pardede@mail.com', 'password123', 'Mr.', 'Coki', 'Pardede', '+62', '8123456729', '1986-09-09', 'Indonesia'),
('deddy.corbuzier@mail.com', 'password123', 'Mr.', 'Deddy', 'Corbuzier', '+62', '8123456730', '1987-12-12', 'Indonesia'),
('erik.tenhag@mail.com', 'password123', 'Mr.', 'Erik', 'Ten Hag', '+62', '8123456731', '1970-02-02', 'Netherlands'),
('fuji.anti@mail.com', 'password123', 'Ms.', 'Fuji', 'Anti', '+62', '8123456732', '2002-11-03', 'Indonesia'),
('gading.marten@mail.com', 'password123', 'Mr.', 'Gading', 'Marten', '+62', '8123456733', '1982-05-08', 'Indonesia'),
('hesti.purwadinata@mail.com', 'password123', 'Mrs.', 'Hesti', 'Purwadinata', '+62', '8123456734', '1983-06-15', 'Indonesia'),
('ismail.marzuki@mail.com', 'password123', 'Mr.', 'Ismail', 'Marzuki', '+62', '8123456735', '1914-05-11', 'Indonesia'),
('jefri.nichol@mail.com', 'password123', 'Mr.', 'Jefri', 'Nichol', '+62', '8123456736', '1999-01-15', 'Indonesia'),
('keanu.reeves@mail.com', 'password123', 'Mr.', 'Keanu', 'Reeves', '+1', '8123456737', '1964-09-02', 'Canada'),
('luna.maya@mail.com', 'password123', 'Ms.', 'Luna', 'Maya', '+62', '8123456738', '1983-08-26', 'Indonesia'),
('mamat.alkatiri@mail.com', 'password123', 'Mr.', 'Mamat', 'Alkatiri', '+62', '8123456739', '1992-06-24', 'Indonesia'),
('najwa.shihab@mail.com', 'password123', 'Ms.', 'Najwa', 'Shihab', '+62', '8123456740', '1977-09-16', 'Indonesia'),
('onadio.leonardo@mail.com', 'password123', 'Mr.', 'Onadio', 'Leonardo', '+62', '8123456741', '1990-01-04', 'Indonesia'),
('pevita.pearce@mail.com', 'password123', 'Ms.', 'Pevita', 'Pearce', '+62', '8123456742', '1992-10-06', 'Indonesia'),
('raditya.dika@mail.com', 'password123', 'Mr.', 'Raditya', 'Dika', '+62', '8123456743', '1984-12-28', 'Indonesia'),
('syahrini.cetar@mail.com', 'password123', 'Mrs.', 'Syahrini', 'Cetar', '+62', '8123456744', '1980-08-01', 'Indonesia'),
('tulus.merdu@mail.com', 'password123', 'Mr.', 'Tulus', 'Merdu', '+62', '8123456745', '1987-08-20', 'Indonesia'),
('uzumaki.naruto@mail.com', 'password123', 'Mr.', 'Naruto', 'Uzumaki', '+81', '8123456746', '1999-10-10', 'Japan'),
('vincent.rompies@mail.com', 'password123', 'Mr.', 'Vincent', 'Rompies', '+62', '8123456747', '1980-03-29', 'Indonesia'),
('wika.salim@mail.com', 'password123', 'Ms.', 'Wika', 'Salim', '+62', '8123456748', '1992-02-26', 'Indonesia'),
('young.lex@mail.com', 'password123', 'Mr.', 'Young', 'Lex', '+62', '8123456749', '1992-04-18', 'Indonesia'),
('ziva.magnolya@mail.com', 'password123', 'Ms.', 'Ziva', 'Magnolya', '+62', '8123456750', '2001-03-14', 'Indonesia'),
('staff.ga.1@aeromiles.com', 'staffpass', 'Mr.', 'Staf', 'Satu', '+62', '8999901', '1990-01-01', 'Indonesia'),
('staff.ga.2@aeromiles.com', 'staffpass', 'Ms.', 'Staf', 'Dua', '+62', '8999902', '1992-05-05', 'Indonesia'),
('staff.sq.1@aeromiles.com', 'staffpass', 'Mr.', 'Staf', 'Tiga', '+62', '8999903', '1988-10-10', 'Indonesia'),
('staff.sq.2@aeromiles.com', 'staffpass', 'Ms.', 'Staf', 'Empat', '+62', '8999904', '1995-12-12', 'Indonesia'),
('staff.ek.1@aeromiles.com', 'staffpass', 'Mr.', 'Staf', 'Lima', '+62', '8999905', '1985-03-03', 'Indonesia'),
('staff.ek.2@aeromiles.com', 'staffpass', 'Dr.', 'Staf', 'Enam', '+62', '8999906', '1980-08-08', 'Indonesia'),
('staff.qr.1@aeromiles.com', 'staffpass', 'Mr.', 'Staf', 'Tujuh', '+62', '8999907', '1993-07-07', 'Indonesia'),
('staff.qr.2@aeromiles.com', 'staffpass', 'Ms.', 'Staf', 'Delapan', '+62', '8999908', '1991-09-09', 'Indonesia'),
('staff.cx.1@aeromiles.com', 'staffpass', 'Mr.', 'Staf', 'Sembilan', '+62', '8999909', '1989-11-11', 'Indonesia'),
('staff.cx.2@aeromiles.com', 'staffpass', 'Mrs.', 'Staf', 'Sepuluh', '+62', '8999910', '1987-04-04', 'Indonesia');

INSERT INTO MEMBER (email, nomor_member, tanggal_bergabung, id_tier, award_miles, total_miles) VALUES
('andi.pratama@mail.com', 'M0001', '2024-01-01', 'T01', 1500, 5000),
('budi.santoso@mail.com', 'M0002', '2024-01-02', 'T01', 2000, 6000),
('citra.lestari@mail.com', 'M0003', '2024-01-03', 'T01', 1200, 4500),
('dewi.sari@mail.com', 'M0004', '2024-01-04', 'T01', 3000, 8000),
('eko.wahyudi@mail.com', 'M0005', '2024-01-05', 'T01', 500, 2000),
('fajar.hidayat@mail.com', 'M0006', '2024-01-06', 'T01', 1800, 5500),
('gina.putri@mail.com', 'M0007', '2024-01-07', 'T01', 2500, 7000),
('hendra.kusuma@mail.com', 'M0008', '2024-01-08', 'T01', 4000, 10000),
('indah.permata@mail.com', 'M0009', '2024-01-09', 'T01', 1000, 3000),
('joko.susilo@mail.com', 'M0010', '2024-01-10', 'T01', 2200, 6500),
('kartika.sari@mail.com', 'M0011', '2024-01-11', 'T01', 1500, 4000),
('lukman.hakim@mail.com', 'M0012', '2024-01-12', 'T01', 3500, 9000),
('maya.andini@mail.com', 'M0013', '2024-01-13', 'T01', 2800, 7500),
('nanda.putra@mail.com', 'M0014', '2024-01-14', 'T01', 600, 2500),
('olivia.tan@mail.com', 'M0015', '2024-01-15', 'T01', 1900, 5800),
('panji.asmara@mail.com', 'M0016', '2024-01-16', 'T01', 2100, 6200),
('qori.asari@mail.com', 'M0017', '2024-01-17', 'T01', 1300, 4800),
('rizky.ramadhan@mail.com', 'M0018', '2024-01-18', 'T01', 3200, 8500),
('sandra.dewi@mail.com', 'M0019', '2024-01-19', 'T01', 4500, 11000),
('taufik.hidayat@mail.com', 'M0020', '2024-01-20', 'T01', 1100, 3500),
('umar.bin@mail.com', 'M0021', '2024-01-21', 'T01', 2400, 6800),
('vivi.andriani@mail.com', 'M0022', '2024-01-22', 'T01', 1700, 5200),
('wahyu.setiawan@mail.com', 'M0023', '2024-01-23', 'T01', 3800, 9500),
('xena.warrior@mail.com', 'M0024', '2024-01-24', 'T01', 2600, 7200),
('yayan.ruhian@mail.com', 'M0025', '2024-01-25', 'T01', 800, 2800),
('zaskia.gotik@mail.com', 'M0026', '2024-01-26', 'T01', 2000, 6000),
('adi.hidayat@mail.com', 'M0027', '2024-01-27', 'T01', 1400, 4200),
('bella.safira@mail.com', 'M0028', '2024-01-28', 'T01', 3100, 8200),
('coki.pardede@mail.com', 'M0029', '2024-01-29', 'T01', 2700, 7400),
('deddy.corbuzier@mail.com', 'M0030', '2024-01-30', 'T01', 5000, 12000),
('erik.tenhag@mail.com', 'M0031', '2024-01-31', 'T01', 900, 3200),
('fuji.anti@mail.com', 'M0032', '2024-02-01', 'T01', 2300, 6600),
('gading.marten@mail.com', 'M0033', '2024-02-02', 'T01', 1600, 5000),
('hesti.purwadinata@mail.com', 'M0034', '2024-02-03', 'T01', 3400, 8800),
('ismail.marzuki@mail.com', 'M0035', '2024-02-04', 'T01', 2900, 7800),
('jefri.nichol@mail.com', 'M0036', '2024-02-05', 'T01', 700, 2600),
('keanu.reeves@mail.com', 'M0037', '2024-02-06', 'T01', 5500, 15000),
('luna.maya@mail.com', 'M0038', '2024-02-07', 'T01', 2000, 6100),
('mamat.alkatiri@mail.com', 'M0039', '2024-02-08', 'T01', 1200, 4400),
('najwa.shihab@mail.com', 'M0040', '2024-02-09', 'T01', 4200, 10500),
('onadio.leonardo@mail.com', 'M0041', '2024-02-10', 'T01', 2400, 6900),
('pevita.pearce@mail.com', 'M0042', '2024-02-11', 'T01', 3600, 9200),
('raditya.dika@mail.com', 'M0043', '2024-02-12', 'T01', 1800, 5600),
('syahrini.cetar@mail.com', 'M0044', '2024-02-13', 'T01', 4800, 11500),
('tulus.merdu@mail.com', 'M0045', '2024-02-14', 'T01', 2100, 6300),
('uzumaki.naruto@mail.com', 'M0046', '2024-02-15', 'T01', 6000, 20000),
('vincent.rompies@mail.com', 'M0047', '2024-02-16', 'T01', 3300, 8600),
('wika.salim@mail.com', 'M0048', '2024-02-17', 'T01', 2500, 7100),
('young.lex@mail.com', 'M0049', '2024-02-18', 'T01', 1000, 3100),
('ziva.magnolya@mail.com', 'M0050', '2024-02-19', 'T01', 2200, 6400);

INSERT INTO STAF (email, id_staf, kode_maskapai) VALUES
('staff.ga.1@aeromiles.com', 'S0001', 'GA'),
('staff.ga.2@aeromiles.com', 'S0002', 'GA'),
('staff.sq.1@aeromiles.com', 'S0003', 'SQ'),
('staff.sq.2@aeromiles.com', 'S0004', 'SQ'),
('staff.ek.1@aeromiles.com', 'S0005', 'EK'),
('staff.ek.2@aeromiles.com', 'S0006', 'EK'),
('staff.qr.1@aeromiles.com', 'S0007', 'QR'),
('staff.qr.2@aeromiles.com', 'S0008', 'QR'),
('staff.cx.1@aeromiles.com', 'S0009', 'CX'),
('staff.cx.2@aeromiles.com', 'S0010', 'CX');

INSERT INTO MITRA (email_mitra, id_penyedia, nama_mitra, tanggal_kerja_sama) VALUES
('partnership@hotelindonesia.com', 6, 'Hotel Indonesia Group', '2023-01-10'),
('promo@traveloka.com', 7, 'Traveloka', '2023-03-15'),
('cs@avis-carrental.com', 8, 'Avis Car Rental', '2023-05-20'),
('info@starbucks.co.id', 9, 'Starbucks Indonesia', '2023-08-12'),
('admin@blibli.com', 10, 'Blibli', '2023-11-05');

INSERT INTO HADIAH (kode_hadiah, nama, miles, deskripsi, valid_start_date, program_end, id_penyedia) VALUES
('RWD-001', 'Voucher Hotel 500rb', 5000, 'Voucher menginap di HIG', '2024-01-01', '2025-12-31', 6),
('RWD-002', 'Free Coffee Starbucks', 1000, '1 Cup Grande', '2024-01-01', '2024-12-31', 9),
('RWD-003', 'Upgrade Bisnis GA', 15000, 'Upgrade kelas penerbangan', '2024-01-01', '2025-12-31', 1),
('RWD-004', 'Voucher Blibli 100rb', 2000, 'Belanja di Blibli', '2024-01-01', '2025-06-30', 10),
('RWD-005', 'Sewa Mobil 1 Hari', 8000, 'Layanan Avis', '2024-01-01', '2024-12-31', 8),
('RWD-006', 'Akses Lounge SQ', 4000, 'Akses SilverKris Lounge', '2024-01-01', '2025-12-31', 2),
('RWD-007', 'Kelebihan Bagasi 10kg', 6000, 'Rute Internasional EK', '2024-01-01', '2025-12-31', 3),
('RWD-008', 'Voucher Traveloka 200rb', 3500, 'Tiket Pesawat/Hotel', '2024-01-01', '2025-12-31', 7),
('RWD-009', 'Model Pesawat Diecast', 12000, 'Skala 1:200 GA', '2024-01-01', '2024-12-31', 1),
('RWD-010', 'Travel Kit QR', 5000, 'Amenity Kit Spesial', '2024-01-01', '2025-12-31', 4);

INSERT INTO IDENTITAS (nomor, email_member, tanggal_habis, tanggal_terbit, negara_penerbit, jenis) VALUES
('IDN-001', 'andi.pratama@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'Paspor'),
('IDN-002', 'budi.santoso@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'KTP'),
('IDN-003', 'citra.lestari@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'SIM'),
('IDN-004', 'dewi.sari@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'Paspor'),
('IDN-005', 'eko.wahyudi@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'KTP'),
('IDN-006', 'fajar.hidayat@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'SIM'),
('IDN-007', 'gina.putri@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'Paspor'),
('IDN-008', 'hendra.kusuma@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'KTP'),
('IDN-009', 'indah.permata@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'SIM'),
('IDN-010', 'joko.susilo@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'Paspor'),
('IDN-011', 'kartika.sari@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'KTP'),
('IDN-012', 'lukman.hakim@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'SIM'),
('IDN-013', 'maya.andini@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'Paspor'),
('IDN-014', 'nanda.putra@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'KTP'),
('IDN-015', 'olivia.tan@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'SIM'),
('IDN-016', 'panji.asmara@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'Paspor'),
('IDN-017', 'qori.asari@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'KTP'),
('IDN-018', 'rizky.ramadhan@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'SIM'),
('IDN-019', 'sandra.dewi@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'Paspor'),
('IDN-020', 'taufik.hidayat@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'KTP'),
('IDN-021', 'umar.bin@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'SIM'),
('IDN-022', 'vivi.andriani@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'Paspor'),
('IDN-023', 'wahyu.setiawan@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'KTP'),
('IDN-024', 'xena.warrior@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'SIM'),
('IDN-025', 'yayan.ruhian@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'Paspor'),
('IDN-026', 'zaskia.gotik@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'KTP'),
('IDN-027', 'adi.hidayat@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'SIM'),
('IDN-028', 'bella.safira@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'Paspor'),
('IDN-029', 'coki.pardede@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'KTP'),
('IDN-030', 'deddy.corbuzier@mail.com', '2030-01-01', '2020-01-01', 'Indonesia', 'SIM');

INSERT INTO TRANSFER (email_member_1, email_member_2, timestamp, jumlah, catatan) VALUES
('andi.pratama@mail.com', 'budi.santoso@mail.com', CURRENT_TIMESTAMP, 500, 'Trf 1'),
('budi.santoso@mail.com', 'citra.lestari@mail.com', CURRENT_TIMESTAMP, 200, 'Trf 2'),
('citra.lestari@mail.com', 'dewi.sari@mail.com', CURRENT_TIMESTAMP, 300, 'Trf 3'),
('dewi.sari@mail.com', 'eko.wahyudi@mail.com', CURRENT_TIMESTAMP, 100, 'Trf 4'),
('eko.wahyudi@mail.com', 'fajar.hidayat@mail.com', CURRENT_TIMESTAMP, 400, 'Trf 5'),
('fajar.hidayat@mail.com', 'gina.putri@mail.com', CURRENT_TIMESTAMP, 150, 'Trf 6'),
('gina.putri@mail.com', 'hendra.kusuma@mail.com', CURRENT_TIMESTAMP, 250, 'Trf 7'),
('hendra.kusuma@mail.com', 'indah.permata@mail.com', CURRENT_TIMESTAMP, 500, 'Trf 8'),
('indah.permata@mail.com', 'joko.susilo@mail.com', CURRENT_TIMESTAMP, 100, 'Trf 9'),
('joko.susilo@mail.com', 'kartika.sari@mail.com', CURRENT_TIMESTAMP, 200, 'Trf 10'),
('kartika.sari@mail.com', 'lukman.hakim@mail.com', CURRENT_TIMESTAMP, 300, 'Trf 11'),
('lukman.hakim@mail.com', 'maya.andini@mail.com', CURRENT_TIMESTAMP, 400, 'Trf 12'),
('maya.andini@mail.com', 'nanda.putra@mail.com', CURRENT_TIMESTAMP, 100, 'Trf 13'),
('nanda.putra@mail.com', 'olivia.tan@mail.com', CURRENT_TIMESTAMP, 200, 'Trf 14'),
('olivia.tan@mail.com', 'panji.asmara@mail.com', CURRENT_TIMESTAMP, 300, 'Trf 15');

INSERT INTO REDEEM (email_member, kode_hadiah, timestamp) VALUES
('andi.pratama@mail.com', 'RWD-001', '2024-04-01 10:00:00'),
('budi.santoso@mail.com', 'RWD-002', '2024-04-01 11:00:00'),
('citra.lestari@mail.com', 'RWD-003', '2024-04-01 12:00:00'),
('dewi.sari@mail.com', 'RWD-004', '2024-04-01 13:00:00'),
('eko.wahyudi@mail.com', 'RWD-005', '2024-04-01 14:00:00'),
('fajar.hidayat@mail.com', 'RWD-006', '2024-04-01 15:00:00'),
('gina.putri@mail.com', 'RWD-007', '2024-04-01 16:00:00'),
('hendra.kusuma@mail.com', 'RWD-008', '2024-04-01 17:00:00'),
('indah.permata@mail.com', 'RWD-009', '2024-04-01 18:00:00'),
('joko.susilo@mail.com', 'RWD-010', '2024-04-01 19:00:00'),
('kartika.sari@mail.com', 'RWD-001', '2024-04-02 10:00:00'),
('lukman.hakim@mail.com', 'RWD-002', '2024-04-02 11:00:00'),
('maya.andini@mail.com', 'RWD-003', '2024-04-02 12:00:00'),
('nanda.putra@mail.com', 'RWD-004', '2024-04-02 13:00:00'),
('olivia.tan@mail.com', 'RWD-005', '2024-04-02 14:00:00'),
('panji.asmara@mail.com', 'RWD-006', '2024-04-02 15:00:00'),
('qori.asari@mail.com', 'RWD-007', '2024-04-02 16:00:00'),
('rizky.ramadhan@mail.com', 'RWD-008', '2024-04-02 17:00:00'),
('sandra.dewi@mail.com', 'RWD-009', '2024-04-02 18:00:00'),
('taufik.hidayat@mail.com', 'RWD-010', '2024-04-02 19:00:00');

INSERT INTO MEMBER_AWARD_MILES_PACKAGE (id_award_miles_package, email_member, timestamp) VALUES
('AMP-001', 'andi.pratama@mail.com', '2024-03-01 10:00:00'),
('AMP-002', 'budi.santoso@mail.com', '2024-03-02 10:00:00'),
('AMP-003', 'citra.lestari@mail.com', '2024-03-03 10:00:00'),
('AMP-004', 'dewi.sari@mail.com', '2024-03-04 10:00:00'),
('AMP-005', 'eko.wahyudi@mail.com', '2024-03-05 10:00:00'),
('AMP-001', 'fajar.hidayat@mail.com', '2024-03-06 10:00:00'),
('AMP-002', 'gina.putri@mail.com', '2024-03-07 10:00:00'),
('AMP-003', 'hendra.kusuma@mail.com', '2024-03-08 10:00:00'),
('AMP-004', 'indah.permata@mail.com', '2024-03-09 10:00:00'),
('AMP-005', 'joko.susilo@mail.com', '2024-03-10 10:00:00'),
('AMP-001', 'kartika.sari@mail.com', '2024-03-11 10:00:00'),
('AMP-002', 'lukman.hakim@mail.com', '2024-03-12 10:00:00'),
('AMP-003', 'maya.andini@mail.com', '2024-03-13 10:00:00'),
('AMP-004', 'nanda.putra@mail.com', '2024-03-14 10:00:00'),
('AMP-005', 'olivia.tan@mail.com', '2024-03-15 10:00:00'),
('AMP-001', 'panji.asmara@mail.com', '2024-03-16 10:00:00'),
('AMP-002', 'qori.asari@mail.com', '2024-03-17 10:00:00'),
('AMP-003', 'rizky.ramadhan@mail.com', '2024-03-18 10:00:00'),
('AMP-004', 'sandra.dewi@mail.com', '2024-03-19 10:00:00'),
('AMP-005', 'taufik.hidayat@mail.com', '2024-03-20 10:00:00');

INSERT INTO CLAIM_MISSING_MILES (email_member, email_staf, maskapai, bandara_asal, bandara_tujuan, tanggal_penerbangan, flight_number, nomor_tiket, kelas_kabin, pnr, status_penerimaan) VALUES
('andi.pratama@mail.com', 'staff.ga.1@aeromiles.com', 'GA', 'CGK', 'SIN', '2024-02-01', 'GA101', 'TKT001', 'Economy', 'PNR001', 'Disetujui'),
('budi.santoso@mail.com', NULL, 'SQ', 'SIN', 'HND', '2024-02-02', 'SQ202', 'TKT002', 'Business', 'PNR002', 'Menunggu'),
('citra.lestari@mail.com', 'staff.sq.1@aeromiles.com', 'SQ', 'SIN', 'CGK', '2024-02-03', 'SQ303', 'TKT003', 'Economy', 'PNR003', 'Ditolak'),
('dewi.sari@mail.com', 'staff.ek.1@aeromiles.com', 'EK', 'DXB', 'LHR', '2024-02-04', 'EK404', 'TKT004', 'First', 'PNR004', 'Disetujui'),
('eko.wahyudi@mail.com', NULL, 'GA', 'SUB', 'CGK', '2024-02-05', 'GA505', 'TKT005', 'Economy', 'PNR005', 'Menunggu'),
('fajar.hidayat@mail.com', 'staff.qr.1@aeromiles.com', 'QR', 'CGK', 'DXB', '2024-02-06', 'QR606', 'TKT006', 'Business', 'PNR006', 'Disetujui'),
('gina.putri@mail.com', NULL, 'CX', 'HKG', 'SIN', '2024-02-07', 'CX707', 'TKT007', 'Economy', 'PNR007', 'Menunggu'),
('hendra.kusuma@mail.com', 'staff.cx.1@aeromiles.com', 'CX', 'SIN', 'HKG', '2024-02-08', 'CX808', 'TKT008', 'Business', 'PNR008', 'Disetujui'),
('indah.permata@mail.com', NULL, 'GA', 'DPS', 'SIN', '2024-02-09', 'GA909', 'TKT009', 'Economy', 'PNR009', 'Menunggu'),
('joko.susilo@mail.com', 'staff.ga.2@aeromiles.com', 'GA', 'SIN', 'DPS', '2024-02-10', 'GA010', 'TKT010', 'Economy', 'PNR010', 'Ditolak'),
('kartika.sari@mail.com', 'staff.sq.2@aeromiles.com', 'SQ', 'HND', 'SIN', '2024-02-11', 'SQ111', 'TKT011', 'First', 'PNR011', 'Disetujui'),
('lukman.hakim@mail.com', NULL, 'EK', 'LHR', 'DXB', '2024-02-12', 'EK222', 'TKT012', 'Economy', 'PNR012', 'Menunggu'),
('maya.andini@mail.com', 'staff.ek.2@aeromiles.com', 'EK', 'DXB', 'CGK', '2024-02-13', 'EK333', 'TKT013', 'Business', 'PNR013', 'Disetujui'),
('nanda.putra@mail.com', NULL, 'QR', 'DXB', 'CGK', '2024-02-14', 'QR444', 'TKT014', 'Economy', 'PNR014', 'Menunggu'),
('olivia.tan@mail.com', 'staff.qr.2@aeromiles.com', 'QR', 'CGK', 'DXB', '2024-02-15', 'QR555', 'TKT015', 'Business', 'PNR015', 'Ditolak'),
('panji.asmara@mail.com', 'staff.cx.2@aeromiles.com', 'CX', 'CGK', 'HKG', '2024-02-16', 'CX666', 'TKT016', 'Economy', 'PNR016', 'Disetujui'),
('qori.asari@mail.com', NULL, 'GA', 'CGK', 'SUB', '2024-02-17', 'GA777', 'TKT017', 'Economy', 'PNR017', 'Menunggu'),
('rizky.ramadhan@mail.com', 'staff.ga.1@aeromiles.com', 'GA', 'SUB', 'DPS', '2024-02-18', 'GA888', 'TKT018', 'Economy', 'PNR018', 'Disetujui'),
('sandra.dewi@mail.com', NULL, 'SQ', 'CGK', 'SIN', '2024-02-19', 'SQ999', 'TKT019', 'Business', 'PNR019', 'Menunggu'),
('taufik.hidayat@mail.com', 'staff.sq.1@aeromiles.com', 'SQ', 'SIN', 'SYD', '2024-02-20', 'SQ020', 'TKT020', 'First', 'PNR020', 'Disetujui');
