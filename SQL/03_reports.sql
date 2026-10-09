-- Step 3: clinic summary reports.
-- Who was vaccinated, with what, and where (inner join on the clinic id).
SELECT v.patient_name, v.vaccine_type, c.name AS clinic_name
FROM vaccinations v
INNER JOIN clinics c ON v.clinic_id = c.id
ORDER BY v.id;

-- How many vaccinations each clinic has given.
SELECT c.name AS clinic_name, COUNT(v.id) AS vaccination_count
FROM vaccinations v
INNER JOIN clinics c ON v.clinic_id = c.id
GROUP BY c.id, c.name
ORDER BY c.id;