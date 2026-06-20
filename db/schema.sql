-- Neighborhood Library Database Schema
-- Design Philosophy:
-- - Normalized to 3NF for data integrity
-- - Indexes on frequently queried columns
-- - Audit columns (created_at, updated_at) for tracking
-- - Soft deletes for data retention
-- - Constraints to enforce business rules

-- Users table: Authentication and authorization
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Members table: Library members who can borrow books
CREATE TABLE members (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    membership_date DATE NOT NULL DEFAULT CURRENT_DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Books table: Physical books in the library inventory
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    isbn VARCHAR(13) UNIQUE,
    title VARCHAR(500) NOT NULL,
    author VARCHAR(255) NOT NULL,
    publisher VARCHAR(255),
    publication_year INTEGER,
    genre VARCHAR(100),
    total_copies INTEGER NOT NULL DEFAULT 1 CHECK (total_copies >= 0),
    available_copies INTEGER NOT NULL DEFAULT 1 CHECK (available_copies >= 0),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_available_copies CHECK (available_copies <= total_copies)
);

-- Borrowing transactions: Track book checkouts and returns
CREATE TABLE borrowings (
    id SERIAL PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE RESTRICT,
    borrowed_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    return_date TIMESTAMP WITH TIME ZONE,
    fine_amount DECIMAL(10, 2) DEFAULT 0.00 CHECK (fine_amount >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'BORROWED' CHECK (status IN ('BORROWED', 'RETURNED', 'OVERDUE', 'LOST')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_return_date CHECK (return_date IS NULL OR return_date >= borrowed_date)
);

-- Indexes for performance optimization
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_members_email ON members(email);
CREATE INDEX idx_members_active ON members(is_active);
CREATE INDEX idx_books_isbn ON books(isbn);
CREATE INDEX idx_books_title ON books(title);
CREATE INDEX idx_books_author ON books(author);
CREATE INDEX idx_borrowings_member_id ON borrowings(member_id);
CREATE INDEX idx_borrowings_book_id ON borrowings(book_id);
CREATE INDEX idx_borrowings_status ON borrowings(status);
CREATE INDEX idx_borrowings_due_date ON borrowings(due_date);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to auto-update updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_members_updated_at BEFORE UPDATE ON members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_books_updated_at BEFORE UPDATE ON books
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_borrowings_updated_at BEFORE UPDATE ON borrowings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update book availability when borrowed
CREATE OR REPLACE FUNCTION update_book_availability()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.status = 'BORROWED' THEN
        UPDATE books SET available_copies = available_copies - 1
        WHERE id = NEW.book_id AND available_copies > 0;
        
        IF NOT FOUND THEN
            RAISE EXCEPTION 'No copies available for book_id %', NEW.book_id;
        END IF;
    ELSIF TG_OP = 'UPDATE' AND OLD.status = 'BORROWED' AND NEW.status = 'RETURNED' THEN
        UPDATE books SET available_copies = available_copies + 1
        WHERE id = NEW.book_id;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically manage book availability
CREATE TRIGGER manage_book_availability BEFORE INSERT OR UPDATE ON borrowings
    FOR EACH ROW EXECUTE FUNCTION update_book_availability();

-- Sample data for testing

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, hashed_password, full_name, is_superuser) VALUES
    ('admin', 'admin@library.com', '$2b$12$l.hBIffJoY83VLvSDZsmd.YRKmDYb9CDnUV4fgCUJfDbEYzk4seDC', 'Admin User', TRUE);

INSERT INTO members (first_name, last_name, email, phone, address) VALUES
    ('John', 'Doe', 'john.doe@example.com', '555-0101', '123 Main St'),
    ('Jane', 'Smith', 'jane.smith@example.com', '555-0102', '456 Oak Ave'),
    ('Bob', 'Johnson', 'bob.johnson@example.com', '555-0103', '789 Pine Rd');

INSERT INTO books (isbn, title, author, publisher, publication_year, genre, total_copies, available_copies, description) VALUES
    ('9780141439518', 'Pride and Prejudice', 'Jane Austen', 'Penguin Classics', 1813, 'Classic Fiction', 3, 3, 'A romantic novel of manners'),
    ('9780743273565', 'The Great Gatsby', 'F. Scott Fitzgerald', 'Scribner', 1925, 'Classic Fiction', 2, 2, 'A tale of the Jazz Age'),
    ('9780451524935', '1984', 'George Orwell', 'Signet Classic', 1949, 'Dystopian Fiction', 4, 4, 'A dystopian social science fiction'),
    ('9780062315007', 'The Alchemist', 'Paulo Coelho', 'HarperOne', 1988, 'Fiction', 2, 2, 'A philosophical novel'),
    ('9780140283334', 'One Hundred Years of Solitude', 'Gabriel García Márquez', 'Penguin Books', 1967, 'Magical Realism', 1, 1, 'A landmark novel of magical realism');
