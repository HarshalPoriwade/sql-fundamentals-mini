-- Step 1: build the vaccination drive database from nothing.
-- Safe to run again: the old tables are dropped first.
-- Drop the child table (vaccinations) before the parent table (clinics),
-- because vaccinations.clinic_id points at clinics.id.
DROP TABLE IF EXISTS vaccinations;
DROP TABLE IF EXISTS clinics;

CREATE TABLE clinics (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT NOT NULL
);

INSERT INTO clinics (id, name, location) VALUES (1, 'Downtown Center', 'Main St');
INSERT INTO clinics (id, name, location) VALUES (2, 'Westside Clinic', 'Oak Ave');

CREATE TABLE vaccinations (
    id INTEGER PRIMARY KEY,
    patient_name TEXT NOT NULL,
    patient_email TEXT NOT NULL,
    dose_number INTEGER NOT NULL,
    vaccine_type TEXT NOT NULL,
    vaccination_date TEXT NOT NULL,
    clinic_id INTEGER NOT NULL REFERENCES clinics (id)
);

INSERT INTO vaccinations (id, patient_name, patient_email, dose_number, vaccine_type, vaccination_date, clinic_id)
VALUES (1, 'Emma Wilson', 'emma@example.com', 1, 'Pfizer', '2025-01-10', 1);
INSERT INTO vaccinations (id, patient_name, patient_email, dose_number, vaccine_type, vaccination_date, clinic_id)
VALUES (2, 'Liam Brown', 'liam@example.com', 1, 'Moderna', '2025-01-11', 2);
INSERT INTO vaccinations (id, patient_name, patient_email, dose_number, vaccine_type, vaccination_date, clinic_id)
VALUES (3, 'Olivia Davis', 'olivia@example.com', 2, 'Pfizer', '2025-01-12', 1);