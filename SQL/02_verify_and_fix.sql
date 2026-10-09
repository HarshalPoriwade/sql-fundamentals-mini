-- Step 2: check what was inserted, then correct the records.
-- Verify: all three patients should be listed.
SELECT * FROM vaccinations;

-- Liam was recorded as Moderna but actually received Pfizer.
UPDATE vaccinations SET vaccine_type = 'Pfizer' WHERE patient_name = 'Liam Brown';

-- Olivia's record was entered by mistake, so remove it.
DELETE FROM vaccinations WHERE patient_name = 'Olivia Davis';

-- Verify again: two patients left, both on Pfizer.
SELECT * FROM vaccinations;