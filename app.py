"""
Elegant Events - Luxury Event Planning & Management Platform
Flask Application - Production Ready
Deployment: Render
Database: PostgreSQL (Supabase)
Storage: Supabase Storage
"""

import os
import uuid
import requests
from datetime import datetime
from functools import wraps
from flask import *
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.extras
import re

# ============================================================
# APPLICATION INITIALIZATION
# ============================================================

app = Flask(__name__)

# Environment Configuration
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():
    """Create and return a PostgreSQL database connection."""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return conn
    except psycopg2.OperationalError as e:
        print(f"Database connection error: {e}")
        return None

def close_db(conn, cursor=None):
    """Safely close database connection and cursor."""
    try:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    except Exception as e:
        print(f"Error closing connection: {e}")

# ============================================================
# IMAGE UPLOAD HELPER
# ============================================================

def upload_image(file, folder='services'):
    """Upload an image to Supabase Storage and return the public URL."""
    if not file or not file.filename:
        return None
    
    try:
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        filename = f"{folder}/{uuid.uuid4().hex}.{ext}"
        
        upload_url = f"{SUPABASE_URL}/storage/v1/object/images/{filename}"
        
        headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/octet-stream"
        }
        
        response = requests.post(upload_url, headers=headers, data=file.read())
        
        if response.status_code not in [200, 201]:
            print(f"Upload failed: {response.text}")
            return None
        
        image_url = f"{SUPABASE_URL}/storage/v1/object/public/images/{filename}"
        return image_url
    except Exception as e:
        print(f"Upload error: {e}")
        return None

# ============================================================
# AUTHENTICATION DECORATORS
# ============================================================

def admin_login_required(f):
    """Decorator to require admin login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please login to access the admin panel.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================
# CONTEXT PROCESSOR
# ============================================================

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# ============================================================
# PUBLIC ROUTES
# ============================================================

@app.route('/')
def index():
    """Homepage."""
    conn = get_db()
    if not conn:
        return render_template('index.html', 
                             featured_services=[],
                             featured_packages=[],
                             testimonials=[],
                             gallery=[])

    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM services WHERE status = 'active' AND featured = true ORDER BY created_at DESC LIMIT 4")
        featured_services = cursor.fetchall()
        
        cursor.execute("SELECT * FROM packages WHERE status = 'active' AND featured = true ORDER BY created_at DESC LIMIT 3")
        featured_packages = cursor.fetchall()
        
        cursor.execute("SELECT * FROM testimonials WHERE status = 'approved' AND is_featured = true ORDER BY created_at DESC LIMIT 4")
        testimonials = cursor.fetchall()
        
        cursor.execute("SELECT * FROM gallery WHERE status = 'active' ORDER BY display_order LIMIT 6")
        gallery = cursor.fetchall()
        
        close_db(conn, cursor)
        return render_template('index.html',
                             featured_services=featured_services,
                             featured_packages=featured_packages,
                             testimonials=testimonials,
                             gallery=gallery)
    except Exception as e:
        print(f"Index error: {e}")
        close_db(conn)
        return render_template('index.html', featured_services=[], featured_packages=[], testimonials=[], gallery=[])

@app.route('/about')
def about():
    """About page."""
    return render_template('about.html')

@app.route('/services')
def services():
    """Services listing page."""
    conn = get_db()
    if not conn:
        return render_template('services.html', services=[], categories=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM services WHERE status = 'active' ORDER BY category")
        categories = cursor.fetchall()
        
        services_by_category = {}
        for cat in categories:
            category_name = cat['category']
            cursor.execute("SELECT * FROM services WHERE status = 'active' AND category = %s ORDER BY name", (category_name,))
            services_by_category[category_name] = cursor.fetchall()
        
        close_db(conn, cursor)
        return render_template('services.html', services_by_category=services_by_category)
    except Exception as e:
        print(f"Services error: {e}")
        close_db(conn)
        return render_template('services.html', services_by_category={})

@app.route('/service/<slug>')
def service_detail(slug):
    """Single service page."""
    conn = get_db()
    if not conn:
        return render_template('service_detail.html', service=None, related_services=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM services WHERE slug = %s AND status = 'active'", (slug,))
        service = cursor.fetchone()
        
        if not service:
            close_db(conn, cursor)
            return render_template('service_detail.html', service=None, related_services=[])
        
        cursor.execute("SELECT * FROM services WHERE category = %s AND id != %s AND status = 'active' LIMIT 3", (service['category'], service['id']))
        related_services = cursor.fetchall()
        
        close_db(conn, cursor)
        return render_template('service_detail.html', service=service, related_services=related_services)
    except Exception as e:
        print(f"Service detail error: {e}")
        close_db(conn)
        return render_template('service_detail.html', service=None, related_services=[])

@app.route('/packages')
def packages():
    """Packages listing page."""
    conn = get_db()
    if not conn:
        return render_template('packages.html', packages=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM packages WHERE status = 'active' ORDER BY featured DESC, name")
        packages = cursor.fetchall()
        close_db(conn, cursor)
        return render_template('packages.html', packages=packages)
    except Exception as e:
        print(f"Packages error: {e}")
        close_db(conn)
        return render_template('packages.html', packages=[])

@app.route('/package/<slug>')
def package_detail(slug):
    """Single package page."""
    conn = get_db()
    if not conn:
        return render_template('package_detail.html', package=None, package_services=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM packages WHERE slug = %s AND status = 'active'", (slug,))
        package = cursor.fetchone()
        
        if not package:
            close_db(conn, cursor)
            return render_template('package_detail.html', package=None, package_services=[])
        
        cursor.execute("""
            SELECT s.* FROM services s
            JOIN package_services ps ON ps.service_id = s.id
            WHERE ps.package_id = %s AND s.status = 'active'
            ORDER BY ps.display_order
        """, (package['id'],))
        package_services = cursor.fetchall()
        
        close_db(conn, cursor)
        return render_template('package_detail.html', package=package, package_services=package_services)
    except Exception as e:
        print(f"Package detail error: {e}")
        close_db(conn)
        return render_template('package_detail.html', package=None, package_services=[])

@app.route('/gallery')
def gallery():
    """Gallery page."""
    conn = get_db()
    if not conn:
        return render_template('gallery.html', albums={})
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT album FROM gallery WHERE status = 'active' ORDER BY album")
        albums = cursor.fetchall()
        
        gallery_by_album = {}
        for album in albums:
            album_name = album['album']
            cursor.execute("SELECT * FROM gallery WHERE status = 'active' AND album = %s ORDER BY display_order", (album_name,))
            gallery_by_album[album_name] = cursor.fetchall()
        
        close_db(conn, cursor)
        return render_template('gallery.html', gallery_by_album=gallery_by_album)
    except Exception as e:
        print(f"Gallery error: {e}")
        close_db(conn)
        return render_template('gallery.html', albums={})

@app.route('/testimonials')
def testimonials():
    """Testimonials page."""
    conn = get_db()
    if not conn:
        return render_template('testimonials.html', testimonials=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM testimonials WHERE status = 'approved' ORDER BY is_featured DESC, created_at DESC")
        testimonials = cursor.fetchall()
        close_db(conn, cursor)
        return render_template('testimonials.html', testimonials=testimonials)
    except Exception as e:
        print(f"Testimonials error: {e}")
        close_db(conn)
        return render_template('testimonials.html', testimonials=[])

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page."""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        flash('Thank you for your message. We\'ll get back to you soon.', 'success')
        return redirect('/contact')
    return render_template('contact.html')

@app.route('/plan-event', methods=['GET', 'POST'])
def plan_event():
    conn = get_db()
    if not conn:
        return render_template('plan_event.html', services=[], packages=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, slug, price FROM services WHERE status = 'active' ORDER BY name")
        services = cursor.fetchall()
        cursor.execute("SELECT id, name, slug, price FROM packages WHERE status = 'active' ORDER BY name")
        packages = cursor.fetchall()
        close_db(conn, cursor)
        
        if request.method == 'POST':
            # Get contact info
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            
            # Get event info
            service_id = request.form.get('service_id')
            package_id = request.form.get('package_id')
            event_date = request.form.get('event_date')
            guest_count = request.form.get('guest_count')
            budget = request.form.get('budget')
            details = request.form.get('details', '').strip()
            
            # Validate required fields
            if not full_name or not email or not phone or not event_date or not guest_count or not details:
                flash('Please fill in all required fields.', 'danger')
                return render_template('plan_event.html', services=services, packages=packages)
            
            # Generate reference
            reference = "EE" + datetime.now().strftime("%Y%m%d%H%M%S")
            
            conn2 = get_db()
            if not conn2:
                flash('Database error. Please try again.', 'danger')
                return render_template('plan_event.html', services=services, packages=packages)
            
            try:
                cursor2 = conn2.cursor()
                cursor2.execute("""
                    INSERT INTO inquiries (
                        full_name, email, phone, service_id, package_id, 
                        event_date, guest_count, budget, details, status, reference
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (full_name, email, phone, service_id, package_id, event_date, 
                      guest_count, budget, details, 'pending', reference))
                inquiry_id = cursor2.fetchone()['id']
                conn2.commit()
                close_db(conn2, cursor2)
                flash('Inquiry submitted successfully!', 'success')
                return redirect(url_for('quote_summary', reference=reference))
            except Exception as e:
                print(f"Plan event error: {e}")
                close_db(conn2)
                flash('Error submitting inquiry. Please try again.', 'danger')
                return render_template('plan_event.html', services=services, packages=packages)
        
        return render_template('plan_event.html', services=services, packages=packages)
    except Exception as e:
        print(f"Plan event error: {e}")
        close_db(conn)
        return render_template('plan_event.html', services=[], packages=[])

@app.route('/quote-summary/<reference>')
def quote_summary(reference):
    conn = get_db()
    if not conn:
        flash('Database error.', 'danger')
        return render_template('quote_summary.html', inquiry=None)
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.*, s.name as service_name, p.name as package_name
            FROM inquiries i
            LEFT JOIN services s ON s.id = i.service_id
            LEFT JOIN packages p ON p.id = i.package_id
            WHERE i.reference = %s
        """, (reference,))
        inquiry = cursor.fetchone()
        close_db(conn, cursor)
        
        if not inquiry:
            flash('Inquiry not found.', 'warning')
            return render_template('quote_summary.html', inquiry=None)
        
        return render_template('quote_summary.html', inquiry=inquiry)
    except Exception as e:
        print(f"Quote summary error: {e}")
        close_db(conn)
        flash('Error loading inquiry.', 'danger')
        return render_template('quote_summary.html', inquiry=None)

@app.route('/inquiry-submitted')
def inquiry_submitted():
    """Inquiry submitted page."""
    return render_template('inquiry_submitted.html')

@app.route('/track-inquiry', methods=['GET'])
def track_inquiry():
    reference = request.args.get('reference', '').strip()
    
    if not reference:
        return render_template('track_inquiry.html', inquiry=None)
    
    conn = get_db()
    if not conn:
        flash('Database error.', 'danger')
        return render_template('track_inquiry.html', inquiry=None)
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.*, s.name as service_name, p.name as package_name
            FROM inquiries i
            LEFT JOIN services s ON s.id = i.service_id
            LEFT JOIN packages p ON p.id = i.package_id
            WHERE i.reference = %s
        """, (reference,))
        inquiry = cursor.fetchone()
        close_db(conn, cursor)
        
        if not inquiry:
            flash('No inquiry found with that reference number.', 'warning')
            return render_template('track_inquiry.html', inquiry=None)
        
        return render_template('track_inquiry.html', inquiry=inquiry)
    except Exception as e:
        print(f"Track inquiry error: {e}")
        close_db(conn)
        flash('Error tracking inquiry.', 'danger')
        return render_template('track_inquiry.html', inquiry=None)

@app.route('/faq')
def faq():
    """FAQ page."""
    return render_template('faq.html')

@app.route('/privacy-policy')
def privacy_policy():
    """Privacy Policy page."""
    return render_template('privacy_policy.html')

@app.route('/terms')
def terms():
    """Terms & Conditions page."""
    return render_template('terms.html')

@app.route('/sitemap.xml')
def sitemap():
    """Sitemap XML."""
    return send_from_directory(app.root_path, 'sitemap.xml')

@app.route('/robots.txt')
def robots():
    """Robots.txt."""
    return send_from_directory(app.root_path, 'robots.txt')

@app.route('/manifest.json')
def manifest():
    """Manifest.json."""
    return send_from_directory(app.root_path, 'manifest.json')

# ============================================================
# ADMIN AUTHENTICATION
# ============================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        if not conn:
            flash('Database error.', 'danger')
            return render_template('admin/login.html')
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admins WHERE username = %s AND status = 'active'", (username,))
            admin = cursor.fetchone()
            close_db(conn, cursor)
            
            if admin and check_password_hash(admin['password_hash'], password):
                session['admin_id'] = admin['id']
                session['admin_username'] = admin['username']
                session['admin_role'] = admin['role']
                flash(f'Welcome back, {admin["username"]}!', 'success')
                return redirect('/admin/dashboard')
            else:
                flash('Invalid username or password.', 'danger')
        except Exception as e:
            print(f"Admin login error: {e}")
            close_db(conn)
            flash('Login error.', 'danger')
        
        return render_template('admin/login.html')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect('/admin/login')

# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route('/admin/dashboard')
@admin_login_required
def admin_dashboard():
    conn = get_db()
    if not conn:
        return render_template('admin/dashboard.html', 
                             total_services=0, total_packages=0, 
                             total_inquiries=0, total_events=0,
                             recent_inquiries=[])

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM services")
        total_services = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM packages")
        total_packages = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM inquiries")
        total_inquiries = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM events")
        total_events = cursor.fetchone()['count']
        
        cursor.execute("SELECT * FROM inquiries ORDER BY created_at DESC LIMIT 5")
        recent_inquiries = cursor.fetchall()
        
        close_db(conn, cursor)
        return render_template('admin/dashboard.html',
                             total_services=total_services,
                             total_packages=total_packages,
                             total_inquiries=total_inquiries,
                             total_events=total_events,
                             recent_inquiries=recent_inquiries)
    except Exception as e:
        print(f"Dashboard error: {e}")
        close_db(conn)
        return render_template('admin/dashboard.html', 
                             total_services=0, total_packages=0, 
                             total_inquiries=0, total_events=0,
                             recent_inquiries=[])

# ============================================================
# ADMIN SERVICES
# ============================================================

@app.route('/admin/services')
@admin_login_required
def admin_services():
    conn = get_db()
    if not conn:
        return render_template('admin/services.html', services=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM services ORDER BY created_at DESC")
        services = cursor.fetchall()
        close_db(conn, cursor)
        return render_template('admin/services.html', services=services)
    except Exception as e:
        print(f"Admin services error: {e}")
        close_db(conn)
        return render_template('admin/services.html', services=[])

@app.route('/admin/services/add', methods=['GET', 'POST'])
@admin_login_required
def admin_service_add():
    if request.method == 'POST':
        name = request.form.get('name')
        
        if not name:
            flash('Name is required.', 'danger')
            return render_template('admin/service_form.html')
        
        # AUTO-GENERATE SLUG
        slug = name.lower()
        slug = slug.replace(' ', '-').replace('/', '-').replace('&', 'and')
        slug = re.sub(r'[^a-z0-9-]', '', slug)

        # Check if slug exists, make it unique if it does
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT slug FROM services WHERE slug = %s", (slug,))
        existing = cursor.fetchone()
        close_db(conn, cursor)
        
        if existing:
            slug = f"{slug}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        description = request.form.get('description')
        price = request.form.get('price')
        duration = request.form.get('duration')
        category = request.form.get('category')
        featured = request.form.get('featured') == 'on'
        status = request.form.get('status', 'active')
        
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                image_url = upload_image(file, 'services')
                if not image_url:
                    flash('Failed to upload image.', 'danger')
                    return render_template('admin/service_form.html')
        
        conn = get_db()
        if not conn:
            flash('Database error.', 'danger')
            return render_template('admin/service_form.html')
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO services (name, slug, description, price, duration, category, image, featured, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, slug, description, price, duration, category, image_url, featured, status))
            conn.commit()
            close_db(conn, cursor)
            flash('Service added successfully!', 'success')
            return redirect('/admin/services')
        except Exception as e:
            print(f"Add service error: {e}")
            close_db(conn)
            flash('Error adding service.', 'danger')
    
    return render_template('admin/service_form.html')

@app.route('/admin/services/edit/<int:service_id>', methods=['GET', 'POST'])
@admin_login_required
def admin_service_edit(service_id):
    conn = get_db()
    if not conn:
        flash('Database error.', 'danger')
        return redirect('/admin/services')
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM services WHERE id = %s", (service_id,))
        service = cursor.fetchone()
        
        if not service:
            flash('Service not found.', 'danger')
            close_db(conn, cursor)
            return redirect('/admin/services')
        
        if request.method == 'POST':
            name = request.form.get('name')
            slug = request.form.get('slug')
            description = request.form.get('description')
            price = request.form.get('price')
            duration = request.form.get('duration')
            category = request.form.get('category')
            featured = request.form.get('featured') == 'on'
            status = request.form.get('status', 'active')
            
            image_url = service['image']
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    image_url = upload_image(file, 'services')
                    if not image_url:
                        flash('Failed to upload image.', 'danger')
                        close_db(conn, cursor)
                        return render_template('admin/service_form.html', service=service)
            
            cursor.execute("""
                UPDATE services SET
                    name = %s, slug = %s, description = %s,
                    price = %s, duration = %s, category = %s,
                    image = %s, featured = %s, status = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (name, slug, description, price, duration, category, image_url, featured, status, service_id))
            conn.commit()
            close_db(conn, cursor)
            flash('Service updated!', 'success')
            return redirect('/admin/services')
        
        close_db(conn, cursor)
        return render_template('admin/service_form.html', service=service)
    except Exception as e:
        print(f"Edit service error: {e}")
        close_db(conn)
        flash('Error loading service.', 'danger')
        return redirect('/admin/services')

@app.route('/admin/services/delete/<int:service_id>')
@admin_login_required
def admin_service_delete(service_id):
    conn = get_db()
    if not conn:
        flash('Database error.', 'danger')
        return redirect('/admin/services')
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM services WHERE id = %s", (service_id,))
        conn.commit()
        close_db(conn, cursor)
        flash('Service deleted.', 'success')
    except Exception as e:
        print(f"Delete service error: {e}")
        close_db(conn)
        flash('Error deleting service.', 'danger')
    
    return redirect('/admin/services')

# ============================================================
# ADMIN PACKAGES (CRUD)
# ============================================================

@app.route('/admin/packages')
@admin_login_required
def admin_packages():
    conn = get_db()
    if not conn:
        return render_template('admin/packages.html', packages=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM packages ORDER BY created_at DESC")
        packages = cursor.fetchall()
        close_db(conn, cursor)
        return render_template('admin/packages.html', packages=packages)
    except Exception as e:
        print(f"Admin packages error: {e}")
        close_db(conn)
        return render_template('admin/packages.html', packages=[])

@app.route('/admin/packages/add', methods=['GET', 'POST'])
@admin_login_required
def admin_package_add():
    if request.method == 'POST':
        name = request.form.get('name')
        
        if not name:
            flash('Name is required.', 'danger')
            return render_template('admin/package_form.html')
        
        # AUTO-GENERATE SLUG FROM NAME
        slug = name.lower()
        slug = slug.replace(' ', '-').replace('/', '-').replace('&', 'and')
        slug = re.sub(r'[^a-z0-9-]', '', slug)

        # Check if slug exists, make it unique if it does
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT slug FROM packages WHERE slug = %s", (slug,))
        existing = cursor.fetchone()
        close_db(conn, cursor)
        
        if existing:
            slug = f"{slug}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # ✅ REMOVED the slug check since we auto-generate it
        description = request.form.get('description')
        price = request.form.get('price')
        duration = request.form.get('duration')
        featured = request.form.get('featured') == 'on'
        status = request.form.get('status', 'active')
        
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                image_url = upload_image(file, 'packages')
                if not image_url:
                    flash('Failed to upload image.', 'danger')
                    return render_template('admin/package_form.html')
        
        conn = get_db()
        if not conn:
            flash('Database error.', 'danger')
            return render_template('admin/package_form.html')
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO packages (name, slug, description, price, duration, image, featured, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, slug, description, price, duration, image_url, featured, status))
            conn.commit()
            close_db(conn, cursor)
            flash('Package added!', 'success')
            return redirect('/admin/packages')
        except Exception as e:
            print(f"Add package error: {e}")
            close_db(conn)
            flash('Error adding package.', 'danger')
    
    conn = get_db()
    services = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM services WHERE status = 'active' ORDER BY name")
        services = cursor.fetchall()
        close_db(conn, cursor)
    
    return render_template('admin/package_form.html', services=services)

@app.route('/admin/packages/edit/<int:package_id>', methods=['GET', 'POST'])
@admin_login_required
def admin_package_edit(package_id):
    conn = get_db()
    if not conn:
        flash('Database error.', 'danger')
        return redirect('/admin/packages')
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM packages WHERE id = %s", (package_id,))
        package = cursor.fetchone()
        
        if not package:
            flash('Package not found.', 'danger')
            close_db(conn, cursor)
            return redirect('/admin/packages')
        
        if request.method == 'POST':
            name = request.form.get('name')
            slug = request.form.get('slug')
            description = request.form.get('description')
            price = request.form.get('price')
            duration = request.form.get('duration')
            featured = request.form.get('featured') == 'on'
            status = request.form.get('status', 'active')
            
            image_url = package['image']
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    image_url = upload_image(file, 'packages')
                    if not image_url:
                        flash('Failed to upload image.', 'danger')
                        close_db(conn, cursor)
                        return render_template('admin/package_form.html', package=package, services=[])
            
            cursor.execute("""
                UPDATE packages SET
                    name = %s, slug = %s, description = %s,
                    price = %s, duration = %s,
                    image = %s, featured = %s, status = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (name, slug, description, price, duration, image_url, featured, status, package_id))
            conn.commit()
            
            # Update package_services
            if 'services' in request.form:
                cursor.execute("DELETE FROM package_services WHERE package_id = %s", (package_id,))
                services = request.form.getlist('services')
                for idx, service_id in enumerate(services):
                    cursor.execute("""
                        INSERT INTO package_services (package_id, service_id, display_order)
                        VALUES (%s, %s, %s)
                    """, (package_id, int(service_id), idx + 1))
                conn.commit()
            
            close_db(conn, cursor)
            flash('Package updated!', 'success')
            return redirect('/admin/packages')
        
        cursor.execute("SELECT id, name FROM services WHERE status = 'active' ORDER BY name")
        services = cursor.fetchall()
        
        cursor.execute("SELECT service_id FROM package_services WHERE package_id = %s ORDER BY display_order", (package_id,))
        selected_services = [row['service_id'] for row in cursor.fetchall()]
        
        close_db(conn, cursor)
        return render_template('admin/package_form.html', package=package, services=services, selected_services=selected_services)
    except Exception as e:
        print(f"Edit package error: {e}")
        close_db(conn)
        flash('Error loading package.', 'danger')
        return redirect('/admin/packages')

@app.route('/admin/packages/delete/<int:package_id>')
@admin_login_required
def admin_package_delete(package_id):
    conn = get_db()
    if not conn:
        flash('Database error.', 'danger')
        return redirect('/admin/packages')
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM packages WHERE id = %s", (package_id,))
        conn.commit()
        close_db(conn, cursor)
        flash('Package deleted.', 'success')
    except Exception as e:
        print(f"Delete package error: {e}")
        close_db(conn)
        flash('Error deleting package.', 'danger')
    
    return redirect('/admin/packages')

# ============================================================
# ADMIN INQUIRIES
# ============================================================

@app.route('/admin/inquiries')
@admin_login_required
def admin_inquiries():
    conn = get_db()
    if not conn:
        return render_template('admin/inquiries.html', inquiries=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.*, s.name as service_name, p.name as package_name
            FROM inquiries i
            LEFT JOIN services s ON s.id = i.service_id
            LEFT JOIN packages p ON p.id = i.package_id
            ORDER BY i.created_at DESC
        """)
        inquiries = cursor.fetchall()
        close_db(conn, cursor)
        return render_template('admin/inquiries.html', inquiries=inquiries)
    except Exception as e:
        print(f"Admin inquiries error: {e}")
        close_db(conn)
        return render_template('admin/inquiries.html', inquiries=[])

@app.route('/admin/inquiries/<int:inquiry_id>/status', methods=['POST'])
@admin_login_required
def admin_inquiry_status(inquiry_id):
    status = request.form.get('status')
    
    conn = get_db()
    if not conn:
        flash('Database error.', 'danger')
        return redirect('/admin/inquiries')
    
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE inquiries SET status = %s, updated_at = NOW() WHERE id = %s", (status, inquiry_id))
        conn.commit()
        close_db(conn, cursor)
        flash('Inquiry status updated!', 'success')
    except Exception as e:
        print(f"Inquiry status error: {e}")
        close_db(conn)
        flash('Error updating inquiry status.', 'danger')
    
    return redirect('/admin/inquiries')

@app.route('/admin/inquiries/delete/<int:inquiry_id>')
@admin_login_required
def admin_inquiry_delete(inquiry_id):
    conn = get_db()
    if not conn:
        flash('Database error.', 'danger')
        return redirect('/admin/inquiries')
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inquiries WHERE id = %s", (inquiry_id,))
        conn.commit()
        close_db(conn, cursor)
        flash('Inquiry deleted.', 'success')
    except Exception as e:
        print(f"Delete inquiry error: {e}")
        close_db(conn)
        flash('Error deleting inquiry.', 'danger')
    
    return redirect('/admin/inquiries')

# ============================================================
# ADMIN TESTIMONIALS
# ============================================================

@app.route('/admin/testimonials')
@admin_login_required
def admin_testimonials():
    conn = get_db()
    if not conn:
        return render_template('admin/testimonials.html', testimonials=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM testimonials ORDER BY created_at DESC")
        testimonials = cursor.fetchall()
        close_db(conn, cursor)
        return render_template('admin/testimonials.html', testimonials=testimonials)
    except Exception as e:
        print(f"Admin testimonials error: {e}")
        close_db(conn)
        return render_template('admin/testimonials.html', testimonials=[])

@app.route('/admin/testimonials/<int:testimonial_id>/approve')
@admin_login_required
def admin_testimonial_approve(testimonial_id):
    conn = get_db()
    if not conn:
        flash('Database error.', 'danger')
        return redirect('/admin/testimonials')
    
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE testimonials SET status = 'approved' WHERE id = %s", (testimonial_id,))
        conn.commit()
        close_db(conn, cursor)
        flash('Testimonial approved!', 'success')
    except Exception as e:
        print(f"Approve testimonial error: {e}")
        close_db(conn)
        flash('Error approving testimonial.', 'danger')
    
    return redirect('/admin/testimonials')

@app.route('/admin/testimonials/delete/<int:testimonial_id>')
@admin_login_required
def admin_testimonial_delete(testimonial_id):
    conn = get_db()
    if not conn:
        flash('Database error.', 'danger')
        return redirect('/admin/testimonials')
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM testimonials WHERE id = %s", (testimonial_id,))
        conn.commit()
        close_db(conn, cursor)
        flash('Testimonial deleted.', 'success')
    except Exception as e:
        print(f"Delete testimonial error: {e}")
        close_db(conn)
        flash('Error deleting testimonial.', 'danger')
    
    return redirect('/admin/testimonials')

# ============================================================
# ADMIN GALLERY
# ============================================================

@app.route('/admin/gallery')
@admin_login_required
def admin_gallery():
    conn = get_db()
    if not conn:
        return render_template('admin/gallery.html', gallery=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM gallery ORDER BY album, display_order")
        gallery = cursor.fetchall()
        close_db(conn, cursor)
        return render_template('admin/gallery.html', gallery=gallery)
    except Exception as e:
        print(f"Admin gallery error: {e}")
        close_db(conn)
        return render_template('admin/gallery.html', gallery=[])

@app.route('/admin/gallery/add', methods=['POST'])
@admin_login_required
def admin_gallery_add():
    title = request.form.get('title')
    description = request.form.get('description')
    album = request.form.get('album')
    display_order = request.form.get('display_order', 0)
    
    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            image_url = upload_image(file, 'gallery')
            if not image_url:
                flash('Failed to upload image.', 'danger')
                return redirect('/admin/gallery')
    
    conn = get_db()
    if not conn:
        flash('Database error.', 'danger')
        return redirect('/admin/gallery')
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO gallery (title, description, image, album, display_order, status)
            VALUES (%s, %s, %s, %s, %s, 'active')
        """, (title, description, image_url, album, int(display_order)))
        conn.commit()
        close_db(conn, cursor)
        flash('Gallery image added!', 'success')
    except Exception as e:
        print(f"Gallery add error: {e}")
        close_db(conn)
        flash('Error adding gallery image.', 'danger')
    
    return redirect('/admin/gallery')

@app.route('/admin/gallery/delete/<int:gallery_id>')
@admin_login_required
def admin_gallery_delete(gallery_id):
    conn = get_db()
    if not conn:
        flash('Database error.', 'danger')
        return redirect('/admin/gallery')
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM gallery WHERE id = %s", (gallery_id,))
        conn.commit()
        close_db(conn, cursor)
        flash('Gallery image deleted.', 'success')
    except Exception as e:
        print(f"Delete gallery error: {e}")
        close_db(conn)
        flash('Error deleting gallery image.', 'danger')
    
    return redirect('/admin/gallery')

# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
