-- ============================================
-- SISTEMA DE GESTIÓN DE BIBLIOTECAS
-- Base de datos PostgreSQL
-- ============================================

-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TIPOS ENUMERADOS
-- ============================================

CREATE TYPE tipo_prestamo_enum AS ENUM ('sala', 'domicilio');
CREATE TYPE estado_prestamo_enum AS ENUM ('activo', 'devuelto', 'vencido', 'cancelado');
CREATE TYPE estado_reserva_enum AS ENUM ('pendiente', 'activa', 'cancelada', 'completada');
CREATE TYPE estado_ejemplar_enum AS ENUM ('disponible', 'prestado', 'en_sala', 'devuelto', 'mantenimiento', 'baja');
CREATE TYPE rol_usuario_enum AS ENUM ('usuario', 'admin', 'bibliotecario');

-- ============================================
-- TABLA: bibliotecas
-- ============================================
CREATE TABLE bibliotecas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    direccion VARCHAR(255),
    telefono VARCHAR(20),
    activo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bibliotecas_activo ON bibliotecas(activo);

-- ============================================
-- TABLA: usuarios
-- ============================================
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    rut VARCHAR(12) UNIQUE NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol rol_usuario_enum NOT NULL DEFAULT 'usuario',
    activo BOOLEAN NOT NULL DEFAULT false,
    foto_url VARCHAR(255),
    huella_hash VARCHAR(255),
    fecha_sancion_hasta TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_usuarios_rut ON usuarios(rut);
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_usuarios_activo ON usuarios(activo);
CREATE INDEX idx_usuarios_rol ON usuarios(rol);

-- ============================================
-- TABLA: tokens_validacion
-- ============================================
CREATE TABLE tokens_validacion (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    token VARCHAR(100) UNIQUE NOT NULL,
    fecha_expiracion TIMESTAMP WITH TIME ZONE NOT NULL,
    usado BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tokens_validacion_token ON tokens_validacion(token);
CREATE INDEX idx_tokens_validacion_usuario ON tokens_validacion(usuario_id);
CREATE INDEX idx_tokens_validacion_expiracion ON tokens_validacion(fecha_expiracion) WHERE NOT usado;

-- ============================================
-- TABLA: documentos
-- ============================================
CREATE TABLE documentos (
    id SERIAL PRIMARY KEY,
    isbn VARCHAR(20) UNIQUE,
    tipo VARCHAR(50) NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    autor VARCHAR(255),
    editorial VARCHAR(255),
    existencias INTEGER NOT NULL DEFAULT 0,
    disponible(if existencias > 0) BOOLEAN NOT NULL DEFAULT true,
    anio INTEGER,
    edicion VARCHAR(50),
    categoria VARCHAR(100),
    tipo_medio VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documentos_tipo ON documentos(tipo);
CREATE INDEX idx_documentos_titulo ON documentos(titulo);
CREATE INDEX idx_documentos_autor ON documentos(autor);
CREATE INDEX idx_documentos_categoria ON documentos(categoria);

-- ============================================
-- TABLA: ejemplares
-- ============================================
CREATE TABLE ejemplares (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    estado estado_ejemplar_enum NOT NULL DEFAULT 'disponible',
    ubicacion VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ejemplares_codigo ON ejemplares(codigo);
CREATE INDEX idx_ejemplares_documento ON ejemplares(documento_id);
CREATE INDEX idx_ejemplares_estado ON ejemplares(estado);

-- ============================================
-- TABLA: historial_ejemplares
-- ============================================
CREATE TABLE historial_ejemplares (
    id SERIAL PRIMARY KEY,
    ejemplar_id INTEGER NOT NULL REFERENCES ejemplares(id) ON DELETE CASCADE,
    estado_anterior estado_ejemplar_enum,
    estado_nuevo estado_ejemplar_enum NOT NULL,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    motivo TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_historial_ejemplares_ejemplar ON historial_ejemplares(ejemplar_id);
CREATE INDEX idx_historial_ejemplares_fecha ON historial_ejemplares(created_at);

-- ============================================
-- TABLA: reservas
-- ============================================
CREATE TABLE reservas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    documento_id INTEGER NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    fecha_reserva DATE NOT NULL,
    estado estado_reserva_enum NOT NULL DEFAULT 'pendiente',
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    motivo_cancelacion VARCHAR(255)
);

CREATE INDEX idx_reservas_usuario ON reservas(usuario_id);
CREATE INDEX idx_reservas_documento ON reservas(documento_id);
CREATE INDEX idx_reservas_estado ON reservas(estado);
CREATE INDEX idx_reservas_fecha ON reservas(fecha_reserva);

-- ============================================
-- TABLA: prestamos
-- ============================================
CREATE TABLE prestamos (
    id SERIAL PRIMARY KEY,
    tipo_prestamo tipo_prestamo_enum NOT NULL,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    biblioteca_id INTEGER NOT NULL REFERENCES bibliotecas(id) ON DELETE RESTRICT,
    fecha_prestamo TIMESTAMP WITH TIME ZONE NOT NULL,
    hora_prestamo TIME NOT NULL,
    fecha_devolucion_estimada TIMESTAMP WITH TIME ZONE,
    hora_devolucion_estimada TIME,
    fecha_devolucion_real TIMESTAMP WITH TIME ZONE,
    hora_devolucion_real TIME,
    estado estado_prestamo_enum NOT NULL DEFAULT 'activo',
    notificado BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prestamos_usuario ON prestamos(usuario_id);
CREATE INDEX idx_prestamos_biblioteca ON prestamos(biblioteca_id);
CREATE INDEX idx_prestamos_estado ON prestamos(estado);
CREATE INDEX idx_prestamos_fecha_prestamo ON prestamos(fecha_prestamo);
CREATE INDEX idx_prestamos_fecha_devolucion ON prestamos(fecha_devolucion_estimada) WHERE estado = 'activo';

-- ============================================
-- TABLA: detalle_prestamo
-- ============================================
CREATE TABLE detalle_prestamo (
    id SERIAL PRIMARY KEY,
    prestamo_id INTEGER NOT NULL REFERENCES prestamos(id) ON DELETE CASCADE,
    ejemplar_id INTEGER NOT NULL REFERENCES ejemplares(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_detalle_prestamo_prestamo ON detalle_prestamo(prestamo_id);
CREATE INDEX idx_detalle_prestamo_ejemplar ON detalle_prestamo(ejemplar_id);

-- ============================================
-- TABLA: log_notificaciones
-- ============================================
CREATE TABLE log_notificaciones (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo VARCHAR(50) NOT NULL,
    asunto VARCHAR(255) NOT NULL,
    destinatario VARCHAR(120) NOT NULL,
    enviado_exitosamente BOOLEAN NOT NULL DEFAULT false,
    error_mensaje TEXT,
    fecha_envio TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_log_notificaciones_usuario ON log_notificaciones(usuario_id);
CREATE INDEX idx_log_notificaciones_tipo ON log_notificaciones(tipo);
CREATE INDEX idx_log_notificaciones_fecha ON log_notificaciones(fecha_envio);
CREATE INDEX idx_log_notificaciones_exitoso ON log_notificaciones(enviado_exitosamente);

-- ============================================
-- TRIGGERS PARA UPDATED_AT
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_bibliotecas_updated_at BEFORE UPDATE ON bibliotecas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_usuarios_updated_at BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documentos_updated_at BEFORE UPDATE ON documentos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ejemplares_updated_at BEFORE UPDATE ON ejemplares
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reservas_updated_at BEFORE UPDATE ON reservas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prestamos_updated_at BEFORE UPDATE ON prestamos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- TRIGGER PARA HISTORIAL DE EJEMPLARES
-- ============================================

CREATE OR REPLACE FUNCTION registrar_cambio_estado_ejemplar()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.estado IS DISTINCT FROM NEW.estado THEN
        INSERT INTO historial_ejemplares (ejemplar_id, estado_anterior, estado_nuevo)
        VALUES (NEW.id, OLD.estado, NEW.estado);
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_historial_ejemplar AFTER UPDATE ON ejemplares
    FOR EACH ROW EXECUTE FUNCTION registrar_cambio_estado_ejemplar();

-- ============================================
-- COMENTARIOS DE DOCUMENTACIÓN
-- ============================================

COMMENT ON TABLE usuarios IS 'Usuarios del sistema de bibliotecas';
COMMENT ON TABLE documentos IS 'Catálogo de documentos (libros, revistas, etc.)';
COMMENT ON TABLE ejemplares IS 'Copias físicas de cada documento';
COMMENT ON TABLE prestamos IS 'Registro de préstamos de documentos';
COMMENT ON TABLE reservas IS 'Reservas anticipadas de documentos';
COMMENT ON TABLE log_notificaciones IS 'Registro de todas las notificaciones enviadas';
COMMENT ON TABLE historial_ejemplares IS 'Auditoría de cambios de estado de ejemplares';

-- ============================================
-- DATOS INICIALES (OPCIONAL)
-- ============================================

-- Insertar biblioteca principal
INSERT INTO bibliotecas (nombre, direccion, telefono, activo) 
VALUES ('Biblioteca Central', 'Av. Principal 123', '+56912345678', true);

-- Insertar usuario administrador (cambiar password en producción)
INSERT INTO usuarios (rut, nombres, apellidos, email, password_hash, rol, activo)
VALUES ('11111111-1', 'Admin', 'Sistema', 'admin@biblioteca.cl', 
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYN8aKZxqsi', 
        'admin', true);