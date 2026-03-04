-- Database: contract_analyzer
-- Schema for Authentication and Contract Analysis

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contracts table
CREATE TABLE IF NOT EXISTS contracts (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Clauses table
CREATE TABLE IF NOT EXISTS clauses (
    id SERIAL PRIMARY KEY,
    contract_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    clause_type VARCHAR(100),
    segment_index INTEGER NOT NULL,
    FOREIGN KEY (contract_id) REFERENCES contracts (id) ON DELETE CASCADE
);

-- Risk flags table
CREATE TABLE IF NOT EXISTS risk_flags (
    id SERIAL PRIMARY KEY,
    clause_id INTEGER NOT NULL,
    category VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    confidence FLOAT NOT NULL,
    description TEXT NOT NULL,
    FOREIGN KEY (clause_id) REFERENCES clauses (id) ON DELETE CASCADE
);
