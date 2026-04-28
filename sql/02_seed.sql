INSERT INTO blood_types (name, description) VALUES
('O-', 'Donador universal de glóbulos rojos'),
('O+', 'Tipo O positivo'),
('A-', 'Tipo A negativo'),
('A+', 'Tipo A positivo'),
('B-', 'Tipo B negativo'),
('B+', 'Tipo B positivo'),
('AB-', 'Tipo AB negativo'),
('AB+', 'Receptor universal de glóbulos rojos')
ON CONFLICT (name) DO NOTHING;

INSERT INTO categories (name, type, description) VALUES
('Soluciones intravenosas', 'INSUMO', 'Solución salina, glucosada y otros líquidos intravenosos'),
('Material de curación', 'INSUMO', 'Gasas, vendas, apósitos, guantes y material estéril'),
('Medicamentos generales', 'INSUMO', 'Medicamentos no controlados publicados por proveedores'),
('Equipo médico básico', 'INSUMO', 'Oxímetros, termómetros, baumanómetros y equipo auxiliar'),
('Sangre total', 'SANGRE', 'Disponibilidad o solicitud de sangre total'),
('Plaquetas', 'SANGRE', 'Disponibilidad o solicitud de plaquetas')
ON CONFLICT (name) DO NOTHING;

-- Nota: los passwords reales se generan desde la API. Estos hashes son solamente para pruebas directas.
-- password: lifelink123
INSERT INTO users (username, email, password_hash, full_name, phone, role) VALUES
('hospital_norte', 'hospital.norte@lifelink.test', '$2b$12$Yv48T7.ZHXvy9b8HE0xSvearXWMNP4Niixg0k5DwccyzFzddLP2Wi', 'Hospital General Norte', '5550001000', 'PROVIDER'),
('cruz_roja_cdmx', 'cruzroja.cdmx@lifelink.test', '$2b$12$Yv48T7.ZHXvy9b8HE0xSvearXWMNP4Niixg0k5DwccyzFzddLP2Wi', 'Cruz Roja CDMX', '5550002000', 'RECEIVER'),
('juan_donor', 'juan.donor@lifelink.test', '$2b$12$Yv48T7.ZHXvy9b8HE0xSvearXWMNP4Niixg0k5DwccyzFzddLP2Wi', 'Juan Pérez Donador', '5550003000', 'DONOR')
ON CONFLICT (username) DO NOTHING;

INSERT INTO profiles (user_id, organization_name, organization_type, description, address, latitude, longitude)
SELECT id, 'Hospital General Norte', 'Hospital', 'Proveedor de insumos médicos', 'Av. Salud 123, CDMX', 19.43260000, -99.13320000
FROM users WHERE username = 'hospital_norte'
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO profiles (user_id, organization_name, organization_type, description, address, latitude, longitude)
SELECT id, 'Cruz Roja CDMX', 'Cruz Roja', 'Receptor estratégico de insumos y sangre', 'Centro, CDMX', 19.43500000, -99.14000000
FROM users WHERE username = 'cruz_roja_cdmx'
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO donors (user_id, blood_type_id, date_of_birth, gender, is_available)
SELECT u.id, bt.id, '1995-05-10', 'MASCULINO', TRUE
FROM users u, blood_types bt
WHERE u.username = 'juan_donor' AND bt.name = 'O+'
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO inventory (provider_id, category_id, name, description, quantity, unit, expiration_date, latitude, longitude, urgency_level, status)
SELECT u.id, c.id, 'Solución salina 0.9%', 'Bolsas de solución salina de 1000 ml', 80, 'bolsas', '2027-01-31', 19.43260000, -99.13320000, 'MEDIA', 'DISPONIBLE'
FROM users u, categories c
WHERE u.username = 'hospital_norte' AND c.name = 'Soluciones intravenosas';

INSERT INTO inventory (provider_id, category_id, name, description, quantity, unit, expiration_date, latitude, longitude, urgency_level, status)
SELECT u.id, c.id, 'Gasas estériles', 'Paquetes de gasas estériles', 150, 'paquetes', '2028-06-30', 19.43260000, -99.13320000, 'BAJA', 'DISPONIBLE'
FROM users u, categories c
WHERE u.username = 'hospital_norte' AND c.name = 'Material de curación';
