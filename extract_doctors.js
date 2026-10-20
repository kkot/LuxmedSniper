const fs = require('fs');
const path = require('path');

// Read the doctors.json file
const doctorsData = JSON.parse(fs.readFileSync('doctors.json', 'utf8'));

// Extract firstName and lastName for each doctor
const doctorNames = doctorsData.doctors
    .filter(doctor => doctor.firstName && doctor.lastName) // Filter out entries without names
    .map(doctor => `${doctor.firstName} ${doctor.lastName}`);

// Write to a text file, each name on a new line
const outputContent = doctorNames.join('\n');
fs.writeFileSync('doctors_names.txt', outputContent, 'utf8');

console.log(`Extracted ${doctorNames.length} doctor names to doctors_names.txt`);
