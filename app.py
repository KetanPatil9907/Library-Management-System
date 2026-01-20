from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =============================================================================
# MODELS (Many-to-Many Relationship)
# =============================================================================

# Association table for many-to-many relationship
book_author = db.Table('book_author',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('author_id', db.Integer, db.ForeignKey('author.id'), primary_key=True)
)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer)
    isbn = db.Column(db.String(20), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Many-to-many relationship with Author
    authors = db.relationship('Author', secondary=book_author, 
                            backref=db.backref('books', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'year': self.year,
            'isbn': self.isbn,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'authors': [author.simple_dict() for author in self.authors] if self.authors else []
        }
    
    def simple_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'year': self.year
        }

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    birth_year = db.Column(db.Integer)
    country = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'birth_year': self.birth_year,
            'country': self.country,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'books': [book.simple_dict() for book in self.books] if self.books else []
        }
    
    def simple_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'country': self.country
        }

# =============================================================================
# BOOK API ROUTES (5 endpoints)
# =============================================================================

# 1. GET all books
@app.route('/api/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    return jsonify({
        'success': True,
        'count': len(books),
        'books': [book.to_dict() for book in books]
    })

# 2. GET single book
@app.route('/api/books/<int:id>', methods=['GET'])
def get_book(id):
    book = Book.query.get(id)
    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404
    return jsonify({'success': True, 'book': book.to_dict()})

# 3. POST create new book
@app.route('/api/books', methods=['POST'])
def create_book():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    if not data.get('title'):
        return jsonify({'success': False, 'error': 'Title is required'}), 400
    
    # Check for duplicate ISBN
    if data.get('isbn'):
        existing = Book.query.filter_by(isbn=data['isbn']).first()
        if existing:
            return jsonify({'success': False, 'error': 'ISBN already exists'}), 400
    
    # Create book
    new_book = Book(
        title=data['title'],
        year=data.get('year'),
        isbn=data.get('isbn')
    )
    
    # Add authors if provided
    if data.get('author_ids'):
        for author_id in data['author_ids']:
            author = Author.query.get(author_id)
            if author:
                new_book.authors.append(author)
    
    db.session.add(new_book)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Book created successfully',
        'book': new_book.to_dict()
    }), 201

# 4. PUT update book
@app.route('/api/books/<int:id>', methods=['PUT'])
def update_book(id):
    book = Book.query.get(id)
    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    # Update fields
    if 'title' in data:
        book.title = data['title']
    if 'year' in data:
        book.year = data['year']
    if 'isbn' in data:
        book.isbn = data['isbn']
    
    # Update authors if provided
    if 'author_ids' in data:
        book.authors = []
        for author_id in data['author_ids']:
            author = Author.query.get(author_id)
            if author:
                book.authors.append(author)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Book updated successfully',
        'book': book.to_dict()
    })

# 5. DELETE book
@app.route('/api/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    book = Book.query.get(id)
    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404
    
    db.session.delete(book)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Book deleted successfully'
    })

# =============================================================================
# AUTHOR API ROUTES (5 endpoints)
# =============================================================================

# 6. GET all authors
@app.route('/api/authors', methods=['GET'])
def get_authors():
    authors = Author.query.all()
    return jsonify({
        'success': True,
        'count': len(authors),
        'authors': [author.to_dict() for author in authors]
    })

# 7. GET single author
@app.route('/api/authors/<int:id>', methods=['GET'])
def get_author(id):
    author = Author.query.get(id)
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404
    return jsonify({'success': True, 'author': author.to_dict()})

# 8. POST create new author
@app.route('/api/authors', methods=['POST'])
def create_author():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    if not data.get('name'):
        return jsonify({'success': False, 'error': 'Name is required'}), 400
    
    new_author = Author(
        name=data['name'],
        birth_year=data.get('birth_year'),
        country=data.get('country')
    )
    
    db.session.add(new_author)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Author created successfully',
        'author': new_author.to_dict()
    }), 201

# 9. PUT update author
@app.route('/api/authors/<int:id>', methods=['PUT'])
def update_author(id):
    author = Author.query.get(id)
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    # Update fields
    if 'name' in data:
        author.name = data['name']
    if 'birth_year' in data:
        author.birth_year = data['birth_year']
    if 'country' in data:
        author.country = data['country']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Author updated successfully',
        'author': author.to_dict()
    })

# 10. DELETE author
@app.route('/api/authors/<int:id>', methods=['DELETE'])
def delete_author(id):
    author = Author.query.get(id)
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404
    
    db.session.delete(author)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Author deleted successfully'
    })

# =============================================================================
# SEARCH API ENDPOINT
# =============================================================================

@app.route('/api/search', methods=['GET'])
def search_all():
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query is required'
        }), 400
    
    # Search for books by title
    books_by_title = Book.query.filter(Book.title.ilike(f'%{query}%')).all()
    
    # Search for authors by name
    authors_by_name = Author.query.filter(Author.name.ilike(f'%{query}%')).all()
    
    # Search for books by author name
    books_by_author_name = []
    if authors_by_name:
        for author in authors_by_name:
            books_by_author_name.extend(author.books)
    
    # Remove duplicates
    all_books = list(set(books_by_title + books_by_author_name))
    
    # Search for authors by book title
    authors_by_book_title = []
    if books_by_title:
        for book in books_by_title:
            authors_by_book_title.extend(book.authors)
    
    # Remove duplicates
    all_authors = list(set(authors_by_name + authors_by_book_title))
    
    return jsonify({
        'success': True,
        'query': query,
        'books': [book.to_dict() for book in all_books],
        'authors': [author.to_dict() for author in all_authors],
        'book_count': len(all_books),
        'author_count': len(all_authors)
    })

# =============================================================================
# HTML FRONTEND WITH JAVASCRIPT
# =============================================================================

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Library Management System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
            color: white;
            padding: 20px;
        }
        
        header h1 {
            font-size: 2.8rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        header p {
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 25px;
        }
        
        /* Search Section */
        .search-section {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .search-section h3 {
            color: white;
            margin-bottom: 15px;
            font-size: 1.4rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .search-box input {
            flex: 1;
            padding: 15px 20px;
            border: none;
            border-radius: 10px;
            font-size: 1.1rem;
            background: white;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .search-box input:focus {
            outline: none;
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .search-box button {
            padding: 15px 30px;
            background: linear-gradient(to right, #00b09b, #96c93d);
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1.1rem;
            font-weight: 600;
            transition: all 0.3s ease;
            white-space: nowrap;
        }
        
        .search-box button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0, 176, 155, 0.4);
        }
        
        .search-results {
            display: none;
            margin-top: 20px;
            animation: fadeIn 0.5s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.3);
        }
        
        .results-header h4 {
            color: white;
            font-size: 1.2rem;
        }
        
        .results-count {
            background: rgba(255, 255, 255, 0.2);
            padding: 5px 15px;
            border-radius: 20px;
            color: white;
            font-size: 0.9rem;
        }
        
        .results-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        @media (max-width: 768px) {
            .results-container {
                grid-template-columns: 1fr;
            }
        }
        
        .results-section {
            background: white;
            border-radius: 10px;
            padding: 20px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .results-section h5 {
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
            font-size: 1.1rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .clear-search {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            padding: 8px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }
        
        .clear-search:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        
        /* Main Content */
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }
        
        @media (max-width: 900px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
        }
        
        .section {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .section:hover {
            transform: translateY(-5px);
        }
        
        .section h2 {
            color: #333;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid #667eea;
            font-size: 1.8rem;
        }
        
        .controls {
            margin-bottom: 25px;
        }
        
        .btn-group {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        button {
            background: linear-gradient(to right, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        button.secondary {
            background: linear-gradient(to right, #f093fb, #f5576c);
        }
        
        .data-container {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            max-height: 500px;
            overflow-y: auto;
            margin-top: 20px;
        }
        
        .item {
            background: white;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            border-left: 4px solid #667eea;
        }
        
        .item:hover {
            border-left-color: #f5576c;
        }
        
        .item h3 {
            color: #333;
            margin-bottom: 8px;
        }
        
        .item p {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 5px;
        }
        
        .item .meta {
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #eee;
        }
        
        .badge {
            background: #e9ecef;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            color: #495057;
        }
        
        .badge.primary {
            background: #667eea;
            color: white;
        }
        
        .badge.secondary {
            background: #764ba2;
            color: white;
        }
        
        .badge.success {
            background: #00b09b;
            color: white;
        }
        
        .loading {
            text-align: center;
            color: #666;
            font-style: italic;
            padding: 20px;
        }
        
        .error {
            color: #dc3545;
            background: #f8d7da;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        
        .success {
            color: #28a745;
            background: #d4edda;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        
        footer {
            text-align: center;
            color: white;
            margin-top: 40px;
            padding: 20px;
            opacity: 0.8;
        }
        
        .form-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        
        .modal-content {
            background: white;
            padding: 40px;
            border-radius: 15px;
            width: 90%;
            max-width: 500px;
            max-height: 90vh;
            overflow-y: auto;
        }
        
        .modal-content h3 {
            margin-bottom: 25px;
            color: #333;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 600;
        }
        
        input, select, textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        
        input:focus, select:focus {
            border-color: #667eea;
            outline: none;
        }
        
        .close-btn {
            position: absolute;
            top: 15px;
            right: 15px;
            background: none;
            border: none;
            font-size: 1.5rem;
            color: #666;
            cursor: pointer;
        }
        
        .close-btn:hover {
            color: #333;
        }
        
        /* Search Results Items */
        .search-item {
            background: #f8f9fa;
            padding: 12px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 3px solid #00b09b;
        }
        
        .search-item h4 {
            color: #333;
            margin-bottom: 5px;
            font-size: 1rem;
        }
        
        .search-item p {
            color: #666;
            font-size: 0.85rem;
            margin-bottom: 3px;
        }
        
        .no-results {
            text-align: center;
            color: #666;
            font-style: italic;
            padding: 20px;
            background: white;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 Library Management System</h1>
            <p>Manage Books & Authors with REST API</p>
            
            <!-- Search Section -->
            <div class="search-section">
                <h3>🔍 Search Library</h3>
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Search books by title or authors by name...">
                    <button onclick="performSearch()">Search</button>
                </div>
                
                <!-- Search Results -->
                <div id="searchResults" class="search-results">
                    <div class="results-header">
                        <h4>Search Results for "<span id="searchQuery"></span>"</h4>
                        <div>
                            <span class="results-count" id="totalResults">0 results</span>
                            <button class="clear-search" onclick="clearSearch()" style="margin-left: 10px;">Clear Search</button>
                        </div>
                    </div>
                    
                    <div class="results-container">
                        <div class="results-section">
                            <h5>📚 Books (<span id="bookResultsCount">0</span>)</h5>
                            <div id="bookResults"></div>
                        </div>
                        
                        <div class="results-section">
                            <h5>✍️ Authors (<span id="authorResultsCount">0</span>)</h5>
                            <div id="authorResults"></div>
                        </div>
                    </div>
                </div>
            </div>
        </header>
        
        <div class="main-grid">
            <!-- Books Section -->
            <section class="section">
                <h2>📖 Books Management</h2>
                <div class="controls">
                    <div class="btn-group">
                        <button onclick="getAllBooks()">Get All Books</button>
                        <button onclick="showBookForm()">Add New Book</button>
                        <button onclick="getAllAuthors()" class="secondary">Load Authors First</button>
                    </div>
                </div>
                <div id="books-container" class="data-container">
                    <div class="loading">No books loaded. Click "Get All Books" to load.</div>
                </div>
            </section>
            
            <!-- Authors Section -->
            <section class="section">
                <h2>✍️ Authors Management</h2>
                <div class="controls">
                    <div class="btn-group">
                        <button onclick="getAllAuthors()">Get All Authors</button>
                        <button onclick="showAuthorForm()">Add New Author</button>
                    </div>
                </div>
                <div id="authors-container" class="data-container">
                    <div class="loading">No authors loaded. Click "Get All Authors" to load.</div>
                </div>
            </section>
        </div>
        
        <!-- Book Form Modal -->
        <div id="bookModal" class="form-modal">
            <div class="modal-content">
                <button class="close-btn" onclick="closeBookForm()">×</button>
                <h3 id="bookModalTitle">Add New Book</h3>
                <form id="bookForm" onsubmit="handleBookSubmit(event)">
                    <input type="hidden" id="bookId">
                    <div class="form-group">
                        <label for="bookTitle">Title *</label>
                        <input type="text" id="bookTitle" required>
                    </div>
                    <div class="form-group">
                        <label for="bookYear">Year</label>
                        <input type="number" id="bookYear">
                    </div>
                    <div class="form-group">
                        <label for="bookIsbn">ISBN</label>
                        <input type="text" id="bookIsbn">
                    </div>
                    <div class="form-group">
                        <label for="bookAuthors">Authors (Select Multiple)</label>
                        <select id="bookAuthors" multiple style="height: 120px;">
                            <option value="">Loading authors...</option>
                        </select>
                    </div>
                    <button type="submit" id="bookSubmitBtn">Save Book</button>
                </form>
            </div>
        </div>
        
        <!-- Author Form Modal -->
        <div id="authorModal" class="form-modal">
            <div class="modal-content">
                <button class="close-btn" onclick="closeAuthorForm()">×</button>
                <h3 id="authorModalTitle">Add New Author</h3>
                <form id="authorForm" onsubmit="handleAuthorSubmit(event)">
                    <input type="hidden" id="authorId">
                    <div class="form-group">
                        <label for="authorName">Name *</label>
                        <input type="text" id="authorName" required>
                    </div>
                    <div class="form-group">
                        <label for="authorBirthYear">Birth Year</label>
                        <input type="number" id="authorBirthYear">
                    </div>
                    <div class="form-group">
                        <label for="authorCountry">Country</label>
                        <input type="text" id="authorCountry">
                    </div>
                    <button type="submit" id="authorSubmitBtn">Save Author</button>
                </form>
            </div>
        </div>
        
        <footer>
            <p>Library Management System • 10 REST API Endpoints • Universal Search Feature</p>
            <p>Search books by title or authors by name. Results show both books and authors.</p>
        </footer>
    </div>
    
    <script>
        // API Base URL
        const API_BASE = window.location.origin;
        
        // Global state
        let allAuthors = [];
        let editingBookId = null;
        let editingAuthorId = null;
        
        // ============ SEARCH FUNCTIONS ============
        
        function performSearch() {
            const searchInput = document.getElementById('searchInput');
            const query = searchInput.value.trim();
            
            if (!query) {
                alert('Please enter a search term');
                return;
            }
            
            searchLibrary(query);
        }
        
        async function searchLibrary(query) {
            try {
                // Show loading state
                document.getElementById('searchResults').style.display = 'block';
                document.getElementById('searchQuery').textContent = query;
                document.getElementById('bookResults').innerHTML = '<div class="loading">Searching...</div>';
                document.getElementById('authorResults').innerHTML = '<div class="loading">Searching...</div>';
                
                const response = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                if (data.success) {
                    renderSearchResults(data);
                } else {
                    showSearchError(data.error || 'Search failed');
                }
            } catch (error) {
                showSearchError('Error performing search: ' + error.message);
            }
        }
        
        function renderSearchResults(data) {
            const { books, authors, book_count, author_count, query } = data;
            
            // Update counts
            document.getElementById('searchQuery').textContent = query;
            document.getElementById('bookResultsCount').textContent = book_count;
            document.getElementById('authorResultsCount').textContent = author_count;
            document.getElementById('totalResults').textContent = `${book_count + author_count} results`;
            
            // Render books
            const bookResults = document.getElementById('bookResults');
            if (book_count === 0) {
                bookResults.innerHTML = '<div class="no-results">No books found</div>';
            } else {
                let html = '';
                books.forEach(book => {
                    const authorNames = book.authors.map(a => a.name).join(', ') || 'No authors';
                    html += `
                        <div class="search-item">
                            <h4>${book.title}</h4>
                            <p>📅 Year: ${book.year || 'Unknown'}</p>
                            <p>📚 ISBN: ${book.isbn || 'No ISBN'}</p>
                            <p>✍️ Authors: ${authorNames}</p>
                            <div style="margin-top: 8px;">
                                <span class="badge">Book ID: ${book.id}</span>
                                <button onclick="viewBook(${book.id})" style="padding: 3px 8px; margin-left: 5px; font-size: 0.8rem;">View</button>
                            </div>
                        </div>
                    `;
                });
                bookResults.innerHTML = html;
            }
            
            // Render authors
            const authorResults = document.getElementById('authorResults');
            if (author_count === 0) {
                authorResults.innerHTML = '<div class="no-results">No authors found</div>';
            } else {
                let html = '';
                authors.forEach(author => {
                    const bookTitles = author.books ? author.books.map(b => b.title).join(', ') : 'No books';
                    html += `
                        <div class="search-item">
                            <h4>${author.name}</h4>
                            <p>🎂 Born: ${author.birth_year || 'Unknown'}</p>
                            <p>📍 Country: ${author.country || 'Unknown'}</p>
                            <p>📚 Books: ${author.books ? author.books.length : 0} book(s)</p>
                            <div style="margin-top: 8px;">
                                <span class="badge success">Author ID: ${author.id}</span>
                                <button onclick="viewAuthor(${author.id})" style="padding: 3px 8px; margin-left: 5px; font-size: 0.8rem;">View</button>
                            </div>
                        </div>
                    `;
                });
                authorResults.innerHTML = html;
            }
        }
        
        function showSearchError(message) {
            document.getElementById('bookResults').innerHTML = `<div class="error">${message}</div>`;
            document.getElementById('authorResults').innerHTML = `<div class="error">${message}</div>`;
        }
        
        function clearSearch() {
            document.getElementById('searchInput').value = '';
            document.getElementById('searchResults').style.display = 'none';
        }
        
        function viewBook(id) {
            getBook(id);
        }
        
        function viewAuthor(id) {
            getAuthor(id);
        }
        
        // Enable search on Enter key
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
        
        // ============ BOOK FUNCTIONS ============
        
        async function getAllBooks() {
            try {
                const response = await fetch(`${API_BASE}/api/books`);
                const data = await response.json();
                
                if (data.success) {
                    renderBooks(data.books);
                } else {
                    showError('books-container', 'Failed to load books');
                }
            } catch (error) {
                showError('books-container', 'Error loading books: ' + error.message);
            }
        }
        
        async function getBook(id) {
            try {
                const response = await fetch(`${API_BASE}/api/books/${id}`);
                const data = await response.json();
                
                if (data.success) {
                    // Show book details
                    alert(`Book Details:\\nTitle: ${data.book.title}\\nYear: ${data.book.year}\\nISBN: ${data.book.isbn}\\nAuthors: ${data.book.authors.map(a => a.name).join(', ')}`);
                }
            } catch (error) {
                alert('Error loading book: ' + error.message);
            }
        }
        
        async function deleteBook(id, title) {
            if (confirm(`Are you sure you want to delete "${title}"?`)) {
                try {
                    const response = await fetch(`${API_BASE}/api/books/${id}`, {
                        method: 'DELETE'
                    });
                    const data = await response.json();
                    
                    if (data.success) {
                        showMessage('books-container', 'Book deleted successfully', 'success');
                        getAllBooks(); // Refresh list
                    } else {
                        showError('books-container', data.error || 'Failed to delete book');
                    }
                } catch (error) {
                    showError('books-container', 'Error deleting book: ' + error.message);
                }
            }
        }
        
        function renderBooks(books) {
            const container = document.getElementById('books-container');
            
            if (books.length === 0) {
                container.innerHTML = '<div class="loading">No books found in the library.</div>';
                return;
            }
            
            let html = '';
            books.forEach(book => {
                const authorNames = book.authors.map(a => a.name).join(', ') || 'No authors';
                const bookYear = book.year ? book.year : 'Unknown year';
                
                html += `
                    <div class="item" data-id="${book.id}">
                        <h3>${book.title}</h3>
                        <p>📅 Published: ${bookYear}</p>
                        <p>📚 ISBN: ${book.isbn || 'No ISBN'}</p>
                        <p>✍️ Authors: ${authorNames}</p>
                        <div class="meta">
                            <div>
                                <span class="badge">ID: ${book.id}</span>
                                <span class="badge primary">${book.authors.length} author(s)</span>
                            </div>
                            <div>
                                <button onclick="editBook(${book.id})" style="padding: 5px 10px; margin-right: 5px;">Edit</button>
                                <button onclick="deleteBook(${book.id}, '${book.title.replace(/'/g, "\\\\'")}')" style="padding: 5px 10px; background: #f5576c;">Delete</button>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
        
        // ============ AUTHOR FUNCTIONS ============
        
        async function getAllAuthors() {
            try {
                const response = await fetch(`${API_BASE}/api/authors`);
                const data = await response.json();
                
                if (data.success) {
                    allAuthors = data.authors;
                    renderAuthors(data.authors);
                    
                    // Update book form author dropdown
                    updateAuthorDropdown();
                } else {
                    showError('authors-container', 'Failed to load authors');
                }
            } catch (error) {
                showError('authors-container', 'Error loading authors: ' + error.message);
            }
        }
        
        async function getAuthor(id) {
            try {
                const response = await fetch(`${API_BASE}/api/authors/${id}`);
                const data = await response.json();
                
                if (data.success) {
                    const author = data.author;
                    const bookTitles = author.books.map(b => b.title).join(', ') || 'No books';
                    
                    alert(`Author Details:\\nName: ${author.name}\\nBirth Year: ${author.birth_year || 'Unknown'}\\nCountry: ${author.country || 'Unknown'}\\nBooks: ${bookTitles}`);
                }
            } catch (error) {
                alert('Error loading author: ' + error.message);
            }
        }
        
        async function deleteAuthor(id, name) {
            if (confirm(`Are you sure you want to delete "${name}"?`)) {
                try {
                    const response = await fetch(`${API_BASE}/api/authors/${id}`, {
                        method: 'DELETE'
                    });
                    const data = await response.json();
                    
                    if (data.success) {
                        showMessage('authors-container', 'Author deleted successfully', 'success');
                        getAllAuthors(); // Refresh list
                        getAllBooks(); // Also refresh books since author relationship changed
                    } else {
                        showError('authors-container', data.error || 'Failed to delete author');
                    }
                } catch (error) {
                    showError('authors-container', 'Error deleting author: ' + error.message);
                }
            }
        }
        
        function renderAuthors(authors) {
            const container = document.getElementById('authors-container');
            
            if (authors.length === 0) {
                container.innerHTML = '<div class="loading">No authors found in the library.</div>';
                return;
            }
            
            let html = '';
            authors.forEach(author => {
                const bookCount = author.books ? author.books.length : 0;
                const birthYear = author.birth_year ? author.birth_year : 'Unknown';
                
                html += `
                    <div class="item" data-id="${author.id}">
                        <h3>${author.name}</h3>
                        <p>🎂 Born: ${birthYear}</p>
                        <p>📍 Country: ${author.country || 'Unknown'}</p>
                        <p>📚 Books: ${bookCount} book(s)</p>
                        <div class="meta">
                            <div>
                                <span class="badge">ID: ${author.id}</span>
                                <span class="badge secondary">${bookCount} book(s)</span>
                            </div>
                            <div>
                                <button onclick="editAuthor(${author.id})" style="padding: 5px 10px; margin-right: 5px;">Edit</button>
                                <button onclick="deleteAuthor(${author.id}, '${author.name.replace(/'/g, "\\\\'")}')" style="padding: 5px 10px; background: #f5576c;">Delete</button>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
        
        // ============ FORM HANDLING ============
        
        function updateAuthorDropdown() {
            const select = document.getElementById('bookAuthors');
            select.innerHTML = '';
            
            allAuthors.forEach(author => {
                const option = document.createElement('option');
                option.value = author.id;
                option.textContent = author.name;
                select.appendChild(option);
            });
        }
        
        function showBookForm(bookId = null) {
            editingBookId = bookId;
            const modal = document.getElementById('bookModal');
            const title = document.getElementById('bookModalTitle');
            const form = document.getElementById('bookForm');
            const submitBtn = document.getElementById('bookSubmitBtn');
            
            if (bookId) {
                title.textContent = 'Edit Book';
                submitBtn.textContent = 'Update Book';
                loadBookData(bookId);
            } else {
                title.textContent = 'Add New Book';
                submitBtn.textContent = 'Save Book';
                form.reset();
                document.getElementById('bookId').value = '';
            }
            
            modal.style.display = 'flex';
        }
        
        function closeBookForm() {
            document.getElementById('bookModal').style.display = 'none';
            editingBookId = null;
        }
        
        async function loadBookData(id) {
            try {
                const response = await fetch(`${API_BASE}/api/books/${id}`);
                const data = await response.json();
                
                if (data.success) {
                    const book = data.book;
                    document.getElementById('bookId').value = book.id;
                    document.getElementById('bookTitle').value = book.title;
                    document.getElementById('bookYear').value = book.year || '';
                    document.getElementById('bookIsbn').value = book.isbn || '';
                    
                    // Select authors
                    const authorSelect = document.getElementById('bookAuthors');
                    const authorIds = book.authors.map(a => a.id);
                    for (let option of authorSelect.options) {
                        option.selected = authorIds.includes(parseInt(option.value));
                    }
                }
            } catch (error) {
                showError('books-container', 'Error loading book data: ' + error.message);
                closeBookForm();
            }
        }
        
        async function handleBookSubmit(event) {
            event.preventDefault();
            
            const form = event.target;
            const bookId = document.getElementById('bookId').value;
            const title = document.getElementById('bookTitle').value;
            const year = document.getElementById('bookYear').value;
            const isbn = document.getElementById('bookIsbn').value;
            
            // Get selected author IDs
            const authorSelect = document.getElementById('bookAuthors');
            const selectedAuthorIds = Array.from(authorSelect.selectedOptions).map(opt => parseInt(opt.value));
            
            const bookData = {
                title: title,
                year: year ? parseInt(year) : null,
                isbn: isbn || null,
                author_ids: selectedAuthorIds
            };
            
            const method = bookId ? 'PUT' : 'POST';
            const url = bookId ? `${API_BASE}/api/books/${bookId}` : `${API_BASE}/api/books`;
            
            try {
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(bookData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('books-container', data.message, 'success');
                    closeBookForm();
                    getAllBooks(); // Refresh list
                } else {
                    showError('books-container', data.error || 'Failed to save book');
                }
            } catch (error) {
                showError('books-container', 'Error saving book: ' + error.message);
            }
        }
        
        function showAuthorForm(authorId = null) {
            editingAuthorId = authorId;
            const modal = document.getElementById('authorModal');
            const title = document.getElementById('authorModalTitle');
            const form = document.getElementById('authorForm');
            const submitBtn = document.getElementById('authorSubmitBtn');
            
            if (authorId) {
                title.textContent = 'Edit Author';
                submitBtn.textContent = 'Update Author';
                loadAuthorData(authorId);
            } else {
                title.textContent = 'Add New Author';
                submitBtn.textContent = 'Save Author';
                form.reset();
                document.getElementById('authorId').value = '';
            }
            
            modal.style.display = 'flex';
        }
        
        function closeAuthorForm() {
            document.getElementById('authorModal').style.display = 'none';
            editingAuthorId = null;
        }
        
        async function loadAuthorData(id) {
            try {
                const response = await fetch(`${API_BASE}/api/authors/${id}`);
                const data = await response.json();
                
                if (data.success) {
                    const author = data.author;
                    document.getElementById('authorId').value = author.id;
                    document.getElementById('authorName').value = author.name;
                    document.getElementById('authorBirthYear').value = author.birth_year || '';
                    document.getElementById('authorCountry').value = author.country || '';
                }
            } catch (error) {
                showError('authors-container', 'Error loading author data: ' + error.message);
                closeAuthorForm();
            }
        }
        
        async function handleAuthorSubmit(event) {
            event.preventDefault();
            
            const authorId = document.getElementById('authorId').value;
            const name = document.getElementById('authorName').value;
            const birthYear = document.getElementById('authorBirthYear').value;
            const country = document.getElementById('authorCountry').value;
            
            const authorData = {
                name: name,
                birth_year: birthYear ? parseInt(birthYear) : null,
                country: country || null
            };
            
            const method = authorId ? 'PUT' : 'POST';
            const url = authorId ? `${API_BASE}/api/authors/${authorId}` : `${API_BASE}/api/authors`;
            
            try {
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(authorData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('authors-container', data.message, 'success');
                    closeAuthorForm();
                    getAllAuthors(); // Refresh list
                    getAllBooks(); // Refresh books too in case of relationship changes
                } else {
                    showError('authors-container', data.error || 'Failed to save author');
                }
            } catch (error) {
                showError('authors-container', 'Error saving author: ' + error.message);
            }
        }
        
        // ============ EDIT FUNCTIONS ============
        
        async function editBook(id) {
            showBookForm(id);
        }
        
        async function editAuthor(id) {
            showAuthorForm(id);
        }
        
        // ============ HELPER FUNCTIONS ============
        
        function showError(containerId, message) {
            const container = document.getElementById(containerId);
            container.innerHTML = `<div class="error">${message}</div>`;
        }
        
        function showMessage(containerId, message, type = 'success') {
            const container = document.getElementById(containerId);
            const msgDiv = document.createElement('div');
            msgDiv.className = type;
            msgDiv.textContent = message;
            container.prepend(msgDiv);
            
            // Remove message after 5 seconds
            setTimeout(() => {
                if (msgDiv.parentNode === container) {
                    container.removeChild(msgDiv);
                }
            }, 5000);
        }
        
        // ============ INITIAL LOAD ============
        
        // Load authors first for the dropdown
        getAllAuthors();
        
        // Load books after a short delay
        setTimeout(() => {
            getAllBooks();
        }, 500);
    </script>
</body>
</html>
'''

# =============================================================================
# INITIALIZE DATABASE WITH SAMPLE DATA
# =============================================================================

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if we need to add sample data
        if Book.query.count() == 0 and Author.query.count() == 0:
            print("Creating sample data...")
            
            # Create sample authors
            authors = [
                Author(name='J.K. Rowling', birth_year=1965, country='United Kingdom'),
                Author(name='George Orwell', birth_year=1903, country='United Kingdom'),
                Author(name='Ernest Hemingway', birth_year=1899, country='United States'),
                Author(name='Agatha Christie', birth_year=1890, country='United Kingdom'),
                Author(name='Stephen King', birth_year=1947, country='United States'),
            ]
            
            for author in authors:
                db.session.add(author)
            
            db.session.commit()
            print(f"Created {len(authors)} sample authors")
            
            # Create sample books
            books = [
                Book(title='Harry Potter and the Philosopher\'s Stone', year=1997, isbn='978-0747532743'),
                Book(title='1984', year=1949, isbn='978-0451524935'),
                Book(title='Animal Farm', year=1945, isbn='978-0451526342'),
                Book(title='The Old Man and the Sea', year=1952, isbn='978-0684801223'),
                Book(title='Murder on the Orient Express', year=1934, isbn='978-0062693662'),
                Book(title='The Shining', year=1977, isbn='978-0307743657'),
            ]
            
            for book in books:
                db.session.add(book)
            
            db.session.commit()
            print(f"Created {len(books)} sample books")
            
            # Create relationships (many-to-many)
            # Get all authors and books
            all_authors = Author.query.all()
            all_books = Book.query.all()
            
            # Add authors to books
            all_books[0].authors = [all_authors[0]]  # Harry Potter -> J.K. Rowling
            all_books[1].authors = [all_authors[1]]  # 1984 -> George Orwell
            all_books[2].authors = [all_authors[1]]  # Animal Farm -> George Orwell
            all_books[3].authors = [all_authors[2]]  # Old Man and the Sea -> Hemingway
            all_books[4].authors = [all_authors[3]]  # Murder on the Orient Express -> Christie
            all_books[5].authors = [all_authors[4]]  # The Shining -> Stephen King
            
            # Add a book with multiple authors
            new_book = Book(
                title='Good Omens',
                year=1990,
                isbn='978-0060853983'
            )
            new_book.authors = [all_authors[3], all_authors[4]]  # Christie & King (just for demo)
            db.session.add(new_book)
            
            db.session.commit()
            print("Created book-author relationships")
            
            print("Sample data created successfully!")

# =============================================================================
# RUN APPLICATION
# =============================================================================

if __name__ == '__main__':
    init_db()
    print("\n🚀 Library Management System is running!")
    print("📚 Access the web interface at: http://localhost:5000")
    print("🔍 Search feature added - search for books by title or authors by name")
    print("\n📖 API Endpoints:")
    print("   GET    /api/books           - Get all books")
    print("   GET    /api/books/<id>      - Get single book")
    print("   POST   /api/books           - Create book")
    print("   PUT    /api/books/<id>      - Update book")
    print("   DELETE /api/books/<id>      - Delete book")
    print("   GET    /api/authors         - Get all authors")
    print("   GET    /api/authors/<id>    - Get single author")
    print("   POST   /api/authors         - Create author")
    print("   PUT    /api/authors/<id>    - Update author")
    print("   DELETE /api/authors/<id>    - Delete author")
    print("   GET    /api/search?q=<query> - Universal search")
    print("\nPress Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=5000)