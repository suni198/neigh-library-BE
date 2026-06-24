"""Initial migration - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-06-20 19:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create members table
    op.create_table('members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('membership_date', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_members_id'), 'members', ['id'], unique=False)
    op.create_index(op.f('ix_members_email'), 'members', ['email'], unique=True)

    # Create books table
    op.create_table('books',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('isbn', sa.String(length=13), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=False),
        sa.Column('publisher', sa.String(length=255), nullable=True),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('genre', sa.String(length=100), nullable=True),
        sa.Column('total_copies', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('available_copies', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint('total_copies >= 0', name='check_total_copies'),
        sa.CheckConstraint('available_copies >= 0', name='check_available_copies'),
        sa.CheckConstraint('available_copies <= total_copies', name='check_available_lte_total'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_books_id'), 'books', ['id'], unique=False)
    op.create_index(op.f('ix_books_isbn'), 'books', ['isbn'], unique=True)
    op.create_index(op.f('ix_books_title'), 'books', ['title'], unique=False)
    op.create_index(op.f('ix_books_author'), 'books', ['author'], unique=False)

    # Create borrowings table
    op.create_table('borrowings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('borrowed_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('return_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fine_amount', sa.DECIMAL(precision=10, scale=2), server_default=sa.text('0.00'), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default=sa.text("'BORROWED'")),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint("status IN ('BORROWED', 'RETURNED', 'OVERDUE', 'LOST')", name='check_status'),
        sa.CheckConstraint('fine_amount >= 0', name='check_fine_amount'),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_borrowings_id'), 'borrowings', ['id'], unique=False)
    op.create_index(op.f('ix_borrowings_member_id'), 'borrowings', ['member_id'], unique=False)
    op.create_index(op.f('ix_borrowings_book_id'), 'borrowings', ['book_id'], unique=False)
    op.create_index(op.f('ix_borrowings_due_date'), 'borrowings', ['due_date'], unique=False)
    op.create_index(op.f('ix_borrowings_status'), 'borrowings', ['status'], unique=False)

    # Create triggers and functions (PostgreSQL specific)
    op.execute("""
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """)

    op.execute("""
    CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    op.execute("""
    CREATE TRIGGER update_members_updated_at BEFORE UPDATE ON members
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    op.execute("""
    CREATE TRIGGER update_books_updated_at BEFORE UPDATE ON books
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    op.execute("""
    CREATE TRIGGER update_borrowings_updated_at BEFORE UPDATE ON borrowings
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    # Create function to update book availability
    op.execute("""
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
    """)

    op.execute("""
    CREATE TRIGGER manage_book_availability BEFORE INSERT OR UPDATE ON borrowings
        FOR EACH ROW EXECUTE FUNCTION update_book_availability();
    """)

    # Insert sample data
    op.execute("""
    INSERT INTO users (username, email, hashed_password, full_name, is_superuser) VALUES
        ('admin', 'admin@library.com', '$2b$12$l.hBIffJoY83VLvSDZsmd.YRKmDYb9CDnUV4fgCUJfDbEYzk4seDC', 'Admin User', TRUE);
    """)

    op.execute("""
    INSERT INTO members (first_name, last_name, email, phone, address) VALUES
        ('John', 'Doe', 'john.doe@example.com', '555-0101', '123 Main St'),
        ('Jane', 'Smith', 'jane.smith@example.com', '555-0102', '456 Oak Ave'),
        ('Bob', 'Johnson', 'bob.johnson@example.com', '555-0103', '789 Pine Rd');
    """)

    op.execute("""
    INSERT INTO books (isbn, title, author, publisher, publication_year, genre, total_copies, available_copies, description) VALUES
        ('9780141439518', 'Pride and Prejudice', 'Jane Austen', 'Penguin Classics', 1813, 'Classic Fiction', 3, 3, 'A romantic novel of manners'),
        ('9780743273565', 'The Great Gatsby', 'F. Scott Fitzgerald', 'Scribner', 1925, 'Classic Fiction', 2, 2, 'A tale of the Jazz Age'),
        ('9780451524935', '1984', 'George Orwell', 'Signet Classic', 1949, 'Dystopian Fiction', 4, 4, 'A dystopian social science fiction'),
        ('9780062315007', 'The Alchemist', 'Paulo Coelho', 'HarperOne', 1988, 'Fiction', 2, 2, 'A philosophical novel'),
        ('9780140283334', 'One Hundred Years of Solitude', 'Gabriel García Márquez', 'Penguin Books', 1967, 'Magical Realism', 1, 1, 'A landmark novel of magical realism');
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS manage_book_availability ON borrowings;")
    op.execute("DROP TRIGGER IF EXISTS update_borrowings_updated_at ON borrowings;")
    op.execute("DROP TRIGGER IF EXISTS update_books_updated_at ON books;")
    op.execute("DROP TRIGGER IF EXISTS update_members_updated_at ON members;")
    op.execute("DROP TRIGGER IF EXISTS update_users_updated_at ON users;")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS update_book_availability();")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")

    # Drop tables
    op.drop_index(op.f('ix_borrowings_status'), table_name='borrowings')
    op.drop_index(op.f('ix_borrowings_due_date'), table_name='borrowings')
    op.drop_index(op.f('ix_borrowings_book_id'), table_name='borrowings')
    op.drop_index(op.f('ix_borrowings_member_id'), table_name='borrowings')
    op.drop_index(op.f('ix_borrowings_id'), table_name='borrowings')
    op.drop_table('borrowings')
    
    op.drop_index(op.f('ix_books_author'), table_name='books')
    op.drop_index(op.f('ix_books_title'), table_name='books')
    op.drop_index(op.f('ix_books_isbn'), table_name='books')
    op.drop_index(op.f('ix_books_id'), table_name='books')
    op.drop_table('books')
    
    op.drop_index(op.f('ix_members_email'), table_name='members')
    op.drop_index(op.f('ix_members_id'), table_name='members')
    op.drop_table('members')
    
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
