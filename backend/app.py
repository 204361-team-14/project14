from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

import psycopg
import qrcode
import jwt
from flask import Flask, jsonify, redirect, request, send_file, send_from_directory
from flask_cors import CORS
from functools import wraps
from psycopg.rows import dict_row
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = Path(os.environ.get("UPLOAD_FOLDER", BASE_DIR / "uploads"))
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://cs_user:cs_password@localhost:5432/cs_building_services",
)
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8080").rstrip("/")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_IMAGES_PER_ITEM = 6

REQUEST_STATUSES = {
    "pending": "รอดำเนินการ",
    "in_progress": "กำลังดำเนินการ",
    "completed": "เสร็จสิ้น",
    "cancelled": "ยกเลิก",
}

LOST_FOUND_STATUSES = {
    "open": "กำลังประกาศ",
    "matched": "พบรายการที่ตรงกัน",
    "returned": "คืนเจ้าของแล้ว",
    "closed": "ปิดรายการ",
}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

# เพิ่มตั้งค่า SECRET_KEY สำหรับสร้าง Token
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("ยังไม่ได้ตั้งค่า SECRET_KEY ใน Environment Variables")

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
CORS(app, resources={r"/api/*": {"origins": "*"}})


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        elif request.args.get('token'): 
            token = request.args.get('token')
            
        if not token:
            return jsonify({'message': 'กรุณาเข้าสู่ระบบ'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            request.current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'เซสชันหมดอายุ กรุณาล็อกอินใหม่'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token ไม่ถูกต้อง'}), 401
            
        return f(*args, **kwargs)
        
    return decorated


def get_db():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS rooms (
                    id BIGSERIAL PRIMARY KEY,
                    building TEXT NOT NULL,
                    floor TEXT NOT NULL,
                    room_number TEXT NOT NULL,
                    room_name TEXT,
                    qr_code TEXT NOT NULL UNIQUE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(building, floor, room_number)
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'technician',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS service_requests (
                    id BIGSERIAL PRIMARY KEY,
                    service_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    urgency TEXT NOT NULL,
                    building TEXT NOT NULL,
                    floor TEXT NOT NULL,
                    room TEXT NOT NULL,
                    room_id BIGINT REFERENCES rooms(id) ON DELETE SET NULL,
                    problem_date DATE,
                    problem_time TIME,
                    image_path TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    assigned_to BIGINT REFERENCES users(id) ON DELETE SET NULL,
                    completion_image_path TEXT,
                    staff_note TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS service_request_images (
                    id BIGSERIAL PRIMARY KEY,
                    request_id BIGINT NOT NULL
                        REFERENCES service_requests(id)
                        ON DELETE CASCADE,
                    image_path TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS request_history (
                    id BIGSERIAL PRIMARY KEY,
                    request_id BIGINT NOT NULL REFERENCES service_requests(id) ON DELETE CASCADE,
                    action TEXT NOT NULL,
                    detail TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS lost_found_items (
                    id BIGSERIAL PRIMARY KEY,
                    report_type TEXT NOT NULL DEFAULT 'found',
                    item_name TEXT NOT NULL,
                    category TEXT,
                    description TEXT NOT NULL,
                    location TEXT,
                    event_date DATE,
                    contact_name TEXT,
                    contact_info TEXT,
                    image_path TEXT,
                    status TEXT NOT NULL DEFAULT 'open',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS lost_found_images (
                    id BIGSERIAL PRIMARY KEY,
                    item_id BIGINT NOT NULL
                        REFERENCES lost_found_items(id)
                        ON DELETE CASCADE,
                    image_path TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute("SELECT id FROM users WHERE username = 'admin'")
            if not cur.fetchone():
                hashed_pw = generate_password_hash('admin123')
                cur.execute(
                    """
                    INSERT INTO users (username, password_hash, role) 
                    VALUES (%s, %s, %s)
                    """,
                    ('admin', hashed_pw, 'admin')
                )


def serialize_row(row):
    if row is None:
        return None
    result = dict(row)
    for key, value in result.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat(sep=" ", timespec="seconds")
        elif hasattr(value, "isoformat"):
            result[key] = value.isoformat()
    return result


def save_uploaded_image(file_storage, prefix):
    if not file_storage or not file_storage.filename:
        return None

    filename = secure_filename(file_storage.filename)
    if "." not in filename:
        raise ValueError("ไฟล์รูปภาพไม่มีนามสกุล")

    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("รองรับเฉพาะไฟล์ PNG, JPG, JPEG และ WEBP")

    file_storage.stream.seek(0, 2)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > MAX_IMAGE_SIZE:
        raise ValueError("รูปภาพต้องมีขนาดไม่เกิน 5 MB")

    unique = datetime.now().strftime("%Y%m%d%H%M%S%f")
    stored_name = f"{prefix}_{unique}.{ext}"
    file_storage.save(UPLOAD_FOLDER / stored_name)
    return stored_name


def get_uploaded_image_files():
    files = []

    for field_name in ("images", "images[]", "image"):
        files.extend(request.files.getlist(field_name))

    unique_files = []
    seen = set()

    for file_storage in files:
        if not file_storage or not file_storage.filename:
            continue

        key = (
            file_storage.filename,
            getattr(file_storage, "content_length", None),
            id(file_storage),
        )

        if key in seen:
            continue

        seen.add(key)
        unique_files.append(file_storage)

    return unique_files


def save_uploaded_images(files, prefix):
    valid_files = [
        file_storage
        for file_storage in files
        if file_storage and file_storage.filename
    ]

    if len(valid_files) > MAX_IMAGES_PER_ITEM:
        raise ValueError(
            f"แนบรูปได้สูงสุด {MAX_IMAGES_PER_ITEM} รูปต่อรายการ"
        )

    stored = []
    try:
        for file_storage in valid_files:
            stored_name = save_uploaded_image(file_storage, prefix)
            if stored_name:
                stored.append(stored_name)
    except Exception:
        for stored_name in stored:
            delete_uploaded_image(stored_name)
        raise

    return stored


def get_request_images(conn, request_id, legacy_image=None):
    rows = conn.execute(
        """
        SELECT image_path
        FROM service_request_images
        WHERE request_id = %s
        ORDER BY id
        """,
        (request_id,),
    ).fetchall()

    images = [row["image_path"] for row in rows]

    if not images and legacy_image:
        images = [legacy_image]

    return images


def get_lost_found_images(conn, item_id, legacy_image=None):
    rows = conn.execute(
        """
        SELECT image_path
        FROM lost_found_images
        WHERE item_id = %s
        ORDER BY id
        """,
        (item_id,),
    ).fetchall()

    images = [row["image_path"] for row in rows]

    if not images and legacy_image:
        images = [legacy_image]

    return images


def delete_uploaded_image(filename):
    if not filename:
        return
    try:
        path = UPLOAD_FOLDER / Path(filename).name
        if path.exists() and path.is_file():
            path.unlink()
    except OSError:
        pass

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.current_user.get('role') != 'admin':
            if request.path.endswith('/qr'):
                return "ไม่มีสิทธิ์เข้าถึง", 403
            return jsonify({'message': 'ไม่มีสิทธิ์เข้าถึง'}), 403
        return f(*args, **kwargs)
    return decorated
    

@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"message": "กรุณากรอกชื่อผู้ใช้งานและรหัสผ่าน"}), 400

    with get_db() as conn:
        user = conn.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = %s",
            (username,)
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            token = jwt.encode({
                "user_id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "exp": datetime.utcnow() + timedelta(hours=8)
            }, app.config['SECRET_KEY'], algorithm="HS256")
            
            return jsonify({"token": token, "message": "เข้าสู่ระบบสำเร็จ"}), 200
        else:
            return jsonify({"message": "ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง"}), 401

@app.get("/api/health")
def health():
    return jsonify({"ok": True})


@app.get("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.get("/room/<qr_code>")
def room_qr_entry(qr_code):
    with get_db() as conn:
        room = conn.execute(
            "SELECT qr_code FROM rooms WHERE qr_code = %s AND is_active = TRUE",
            (qr_code,),
        ).fetchone()

    if room is None:
        return "ไม่พบห้องนี้ หรือ QR Code ถูกปิดใช้งาน", 404

    # QR เก่า (/room/<รหัส>) ยังใช้ได้: พาไปหน้าแจ้งซ่อม หรือแจ้งทำความสะอาดถ้าระบุ ?service=cleaning
    page = "cleaning" if request.args.get("service") == "cleaning" else "repair"
    return redirect(f"{PUBLIC_BASE_URL}/request/{page}?room={qr_code}")


@app.get("/api/rooms/resolve/<qr_code>")
def resolve_room(qr_code):
    with get_db() as conn:
        room = conn.execute(
            """
            SELECT id, building, floor, room_number, room_name, qr_code
            FROM rooms
            WHERE qr_code = %s AND is_active = TRUE
            """,
            (qr_code,),
        ).fetchone()

    if room is None:
        return jsonify({"success": False, "message": "ไม่พบห้องนี้ หรือ QR Code ถูกปิดใช้งาน"}), 404

    return jsonify({"success": True, "room": serialize_row(room)})


@app.post("/api/requests")
def create_request():
    required = ["service_type", "description", "urgency", "problem_date"]
    missing = [key for key in required if not request.form.get(key, "").strip()]
    if missing:
        return jsonify({"success": False, "message": "กรุณากรอกข้อมูลให้ครบถ้วน"}), 400

    building = request.form.get("building", "").strip()
    floor = request.form.get("floor", "").strip()
    room = request.form.get("room", "").strip()
    if not building or not floor or not room:
        return jsonify({"success": False, "message": "กรุณาระบุอาคาร ชั้น และห้องให้ครบถ้วน"}), 400

    try:
        uploaded_images = save_uploaded_images(
            get_uploaded_image_files(),
            "request",
        )
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400

    image_path = uploaded_images[0] if uploaded_images else None

    now = datetime.now()

    with get_db() as conn:
        matched_room = conn.execute(
            """
            SELECT id
            FROM rooms
            WHERE is_active = TRUE
              AND building = %s
              AND floor = %s
              AND room_number = %s
            LIMIT 1
            """,
            (building, floor, room),
        ).fetchone()
        room_id = matched_room["id"] if matched_room else None

        item = conn.execute(
            """
            INSERT INTO service_requests (
                service_type, description, urgency,
                building, floor, room, room_id,
                problem_date, problem_time,
                image_path, status, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULLIF(%s, '')::time,
                    %s, 'pending', %s, %s)
            RETURNING id
            """,
            (
                request.form["service_type"].strip(),
                request.form["description"].strip(),
                request.form["urgency"].strip(),
                building,
                floor,
                room,
                room_id,
                request.form["problem_date"].strip(),
                request.form.get("problem_time", "").strip(),
                image_path,
                now,
                now,
            ),
        ).fetchone()

        conn.execute(
            """
            INSERT INTO request_history (request_id, action, detail, created_at)
            VALUES (%s, 'created', 'สร้างคำขอบริการ', %s)
            """,
            (item["id"], now),
        )

        for stored_name in uploaded_images:
            conn.execute(
                """
                INSERT INTO service_request_images (
                    request_id,
                    image_path,
                    created_at
                )
                VALUES (%s, %s, %s)
                """,
                (item["id"], stored_name, now),
            )

    return jsonify({
        "success": True,
        "request_id": item["id"],
        "created_at": now.isoformat(sep=" ", timespec="seconds"),
    })


@app.get("/api/staff/dashboard")
@token_required
@admin_required
def staff_dashboard():
    with get_db() as conn:
        stats = {
            "all": conn.execute("SELECT COUNT(*) AS count FROM service_requests").fetchone()["count"],
            "pending": conn.execute("SELECT COUNT(*) AS count FROM service_requests WHERE status='pending'").fetchone()["count"],
            "in_progress": conn.execute("SELECT COUNT(*) AS count FROM service_requests WHERE status='in_progress'").fetchone()["count"],
            "completed": conn.execute("SELECT COUNT(*) AS count FROM service_requests WHERE status='completed'").fetchone()["count"],
            "lost_found_open": conn.execute(
                "SELECT COUNT(*) AS count FROM lost_found_items WHERE report_type='found' AND status IN ('open','matched')"
            ).fetchone()["count"],
        }

        latest_requests = conn.execute(
            "SELECT * FROM service_requests ORDER BY id DESC LIMIT 6"
        ).fetchall()
        latest_lost_found = conn.execute(
            "SELECT * FROM lost_found_items WHERE report_type='found' ORDER BY id DESC LIMIT 5"
        ).fetchall()

    return jsonify(
        {
            "stats": stats,
            "latest_requests": [serialize_row(row) for row in latest_requests],
            "latest_lost_found": [serialize_row(row) for row in latest_lost_found],
            "request_statuses": REQUEST_STATUSES,
            "lost_found_statuses": LOST_FOUND_STATUSES,
        }
    )


@app.get("/api/staff/requests")
@token_required
def list_requests():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    service_type = request.args.get("service_type", "").strip()
    urgency = request.args.get("urgency", "").strip()

    sql = """
        SELECT s.*, u.username as assigned_to_name 
        FROM service_requests s 
        LEFT JOIN users u ON s.assigned_to = u.id 
        WHERE TRUE
    """
    params = []
    role = request.current_user.get('role')
    if role == 'maid':
        sql += " AND s.service_type = 'แจ้งทำความสะอาด'"  
    elif role == 'technician':
        sql += " AND s.service_type = 'แจ้งซ่อม'"

    if q:
        like = f"%{q}%"
        sql += " AND (description ILIKE %s OR building ILIKE %s OR room ILIKE %s OR CAST(id AS TEXT) ILIKE %s)"
        params.extend([like, like, like, like])
    if status in REQUEST_STATUSES:
        sql += " AND status = %s"
        params.append(status)
    if service_type:
        sql += " AND service_type = %s"
        params.append(service_type)
    if urgency:
        sql += " AND urgency = %s"
        params.append(urgency)

    sql += " ORDER BY id DESC"

    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()

        base_count_sql = "SELECT COUNT(*) AS count FROM service_requests WHERE TRUE"
        if role == 'maid':
            base_count_sql += " AND service_type = 'แจ้งทำความสะอาด'" 
        elif role == 'technician':
            base_count_sql += " AND service_type = 'แจ้งซ่อม'"

        stats = {
            "all": conn.execute(base_count_sql).fetchone()["count"],
            "pending": conn.execute("SELECT COUNT(*) AS count FROM service_requests WHERE status='pending'").fetchone()["count"],
            "in_progress": conn.execute("SELECT COUNT(*) AS count FROM service_requests WHERE status='in_progress'").fetchone()["count"],
            "completed": conn.execute("SELECT COUNT(*) AS count FROM service_requests WHERE status='completed'").fetchone()["count"],
        }

    return jsonify(
        {
            "requests": [serialize_row(row) for row in rows],
            "stats": stats,
            "statuses": REQUEST_STATUSES,
        }
    )


@app.get("/api/staff/requests/<int:request_id>")
@token_required
def request_detail(request_id):
    with get_db() as conn:
        item = conn.execute(
            """
            SELECT s.*, u.username as assigned_to_name 
            FROM service_requests s 
            LEFT JOIN users u ON s.assigned_to = u.id 
            WHERE s.id = %s
            """,
            (request_id,),
        ).fetchone()

        if item is None:
            return jsonify({"message": "ไม่พบคำขอบริการนี้"}), 404

        history = conn.execute(
            "SELECT * FROM request_history WHERE request_id = %s ORDER BY id DESC",
            (request_id,),
        ).fetchall()

        request_data = serialize_row(item)
        request_data["images"] = get_request_images(
            conn,
            request_id,
            item.get("image_path"),
        )

    return jsonify(
        {
            "request": request_data,
            "history": [serialize_row(row) for row in history],
            "statuses": REQUEST_STATUSES,
        }
    )


@app.patch("/api/staff/requests/<int:request_id>/status")
@token_required
def update_request_status(request_id):
    data = request.get_json(silent=True) or {}
    new_status = data.get("status", "")
    if new_status not in REQUEST_STATUSES:
        return jsonify({"message": "สถานะไม่ถูกต้อง"}), 400

    role = request.current_user.get('role')
    if role in ['maid', 'technician'] and new_status == 'cancelled':
        return jsonify({"message": "คุณไม่มีสิทธิ์ยกเลิกงานนี้ กรุณาติดต่อแอดมิน"}), 403

    now = datetime.now()
    with get_db() as conn:
        item = conn.execute(
            "SELECT status FROM service_requests WHERE id = %s",
            (request_id,),
        ).fetchone()
        if item is None:
            return jsonify({"message": "ไม่พบคำขอบริการนี้"}), 404

        old_status = item["status"] or "pending"
        conn.execute(
            "UPDATE service_requests SET status=%s, updated_at=%s WHERE id=%s",
            (new_status, now, request_id),
        )
        conn.execute(
            """
            INSERT INTO request_history (request_id, action, detail, created_at)
            VALUES (%s, 'status', %s, %s)
            """,
            (
                request_id,
                f"{REQUEST_STATUSES.get(old_status, old_status)} → {REQUEST_STATUSES[new_status]}",
                now,
            ),
        )

    return jsonify({"success": True})


@app.patch("/api/staff/requests/<int:request_id>/note")
@token_required
def update_request_note(request_id):
    data = request.get_json(silent=True) or {}
    note = str(data.get("staff_note", "")).strip()
    now = datetime.now()

    with get_db() as conn:
        exists = conn.execute(
            "SELECT id FROM service_requests WHERE id = %s",
            (request_id,),
        ).fetchone()
        if exists is None:
            return jsonify({"message": "ไม่พบคำขอบริการนี้"}), 404

        conn.execute(
            "UPDATE service_requests SET staff_note=%s, updated_at=%s WHERE id=%s",
            (note, now, request_id),
        )
        conn.execute(
            """
            INSERT INTO request_history (request_id, action, detail, created_at)
            VALUES (%s, 'note', %s, %s)
            """,
            (request_id, note or "ล้างหมายเหตุเจ้าหน้าที่", now),
        )

    return jsonify({"success": True})


@app.delete("/api/staff/requests/<int:request_id>")
@token_required
@admin_required
def delete_completed_request(request_id):
    with get_db() as conn:
        item = conn.execute(
            "SELECT id, status, image_path FROM service_requests WHERE id = %s",
            (request_id,),
        ).fetchone()

        if item is None:
            return jsonify({"message": "ไม่พบคำขอบริการนี้"}), 404

        if (item["status"] or "pending") != "completed":
            return jsonify({"message": "ลบได้เฉพาะคำขอที่ดำเนินการเสร็จสิ้นแล้ว"}), 400

        image_paths = get_request_images(
            conn,
            request_id,
            item.get("image_path"),
        )

        conn.execute(
            "DELETE FROM service_requests WHERE id = %s",
            (request_id,),
        )

    for image_path in set(image_paths):
        delete_uploaded_image(image_path)

    return jsonify({"success": True})


@app.get("/api/lost-found")
def public_lost_found():
    q = request.args.get("q", "").strip()
    sql = "SELECT * FROM lost_found_items WHERE report_type='found' AND status != 'closed'"
    params = []

    if q:
        like = f"%{q}%"
        sql += " AND (item_name ILIKE %s OR description ILIKE %s OR location ILIKE %s OR category ILIKE %s)"
        params.extend([like, like, like, like])

    sql += " ORDER BY id DESC"

    with get_db() as conn:
        items = conn.execute(sql, params).fetchall()

        serialized_items = []
        for row in items:
            item_data = serialize_row(row)
            item_data["images"] = get_lost_found_images(
                conn,
                row["id"],
                row.get("image_path"),
            )
            serialized_items.append(item_data)

    return jsonify(
        {
            "items": serialized_items,
            "statuses": LOST_FOUND_STATUSES,
        }
    )


@app.get("/api/lost-found/<int:item_id>")
def public_lost_found_detail(item_id):
    with get_db() as conn:
        item = conn.execute(
            """
            SELECT *
            FROM lost_found_items
            WHERE id = %s
              AND report_type = 'found'
              AND status != 'closed'
            """,
            (item_id,),
        ).fetchone()

        if item is None:
            return jsonify({"message": "ไม่พบรายการนี้"}), 404

        item_data = serialize_row(item)
        item_data["images"] = get_lost_found_images(
            conn,
            item_id,
            item.get("image_path"),
        )

    return jsonify({
        "item": item_data,
        "statuses": LOST_FOUND_STATUSES,
    })


@app.post("/api/lost-found")
def create_lost_found():
    item_name = request.form.get("item_name", "").strip()
    description = request.form.get("description", "").strip()
    if not item_name or not description:
        return jsonify({"success": False, "message": "กรุณากรอกข้อมูลที่จำเป็นให้ครบ"}), 400

    try:
        uploaded_images = save_uploaded_images(
            get_uploaded_image_files(),
            "lostfound",
        )
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400

    image_path = uploaded_images[0] if uploaded_images else None

    now = datetime.now()

    with get_db() as conn:
        item = conn.execute(
            """
            INSERT INTO lost_found_items (
                report_type, item_name, category, description, location,
                event_date, contact_name, contact_info, image_path,
                status, created_at, updated_at
            )
            VALUES ('found', %s, %s, %s, %s, NULLIF(%s, '')::date, %s, %s, %s,
                    'open', %s, %s)
            RETURNING id
            """,
            (
                item_name,
                request.form.get("category", "").strip(),
                description,
                request.form.get("location", "").strip(),
                request.form.get("event_date", "").strip(),
                request.form.get("contact_name", "").strip(),
                request.form.get("contact_info", "").strip(),
                image_path,
                now,
                now,
            ),
        ).fetchone()

        for stored_name in uploaded_images:
            conn.execute(
                """
                INSERT INTO lost_found_images (
                    item_id,
                    image_path,
                    created_at
                )
                VALUES (%s, %s, %s)
                """,
                (item["id"], stored_name, now),
            )

    return jsonify({"success": True, "item_id": item["id"]})


@app.get("/api/staff/lost-found")
@token_required
@admin_required
def staff_lost_found():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()

    sql = "SELECT * FROM lost_found_items WHERE report_type='found'"
    params = []

    if q:
        like = f"%{q}%"
        sql += " AND (item_name ILIKE %s OR description ILIKE %s OR location ILIKE %s OR category ILIKE %s)"
        params.extend([like, like, like, like])
    if status in LOST_FOUND_STATUSES:
        sql += " AND status = %s"
        params.append(status)

    sql += " ORDER BY id DESC"

    with get_db() as conn:
        items = conn.execute(sql, params).fetchall()

    return jsonify(
        {
            "items": [serialize_row(row) for row in items],
            "statuses": LOST_FOUND_STATUSES,
        }
    )


@app.get("/api/staff/lost-found/<int:item_id>")
@token_required
@admin_required
def staff_lost_found_detail(item_id):
    with get_db() as conn:
        item = conn.execute(
            "SELECT * FROM lost_found_items WHERE id=%s AND report_type='found'",
            (item_id,),
        ).fetchone()

    if item is None:
        return jsonify({"message": "ไม่พบรายการนี้"}), 404

    with get_db() as conn:
        item_data = serialize_row(item)
        item_data["images"] = get_lost_found_images(
            conn,
            item_id,
            item.get("image_path"),
        )

    return jsonify({
        "item": item_data,
        "statuses": LOST_FOUND_STATUSES,
    })


@app.patch("/api/staff/lost-found/<int:item_id>/status")
@token_required
@admin_required
def update_lost_found_status(item_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status", "")
    if status not in LOST_FOUND_STATUSES:
        return jsonify({"message": "สถานะไม่ถูกต้อง"}), 400

    now = datetime.now()
    with get_db() as conn:
        item = conn.execute(
            "SELECT id FROM lost_found_items WHERE id=%s AND report_type='found'",
            (item_id,),
        ).fetchone()
        if item is None:
            return jsonify({"message": "ไม่พบรายการนี้"}), 404

        conn.execute(
            "UPDATE lost_found_items SET status=%s, updated_at=%s WHERE id=%s",
            (status, now, item_id),
        )

    return jsonify({"success": True})


@app.get("/api/staff/rooms")
@token_required
@admin_required
def list_rooms():
    with get_db() as conn:
        rooms = conn.execute(
            "SELECT * FROM rooms ORDER BY building, floor, room_number"
        ).fetchall()

    return jsonify({"rooms": [serialize_row(row) for row in rooms]})


@app.post("/api/staff/rooms")
@token_required
@admin_required
def create_room():
    data = request.get_json(silent=True) or {}
    building = str(data.get("building", "")).strip()
    floor = str(data.get("floor", "")).strip()
    room_number = str(data.get("room_number", "")).strip()
    room_name = str(data.get("room_name", "")).strip()

    if not building or not floor or not room_number:
        return jsonify({"message": "กรุณากรอกอาคาร ชั้น และเลขห้องให้ครบ"}), 400

    qr_code = uuid.uuid4().hex[:12]
    now = datetime.now()

    try:
        with get_db() as conn:
            room = conn.execute(
                """
                INSERT INTO rooms (
                    building, floor, room_number, room_name,
                    qr_code, is_active, created_at
                )
                VALUES (%s, %s, %s, %s, %s, TRUE, %s)
                RETURNING *
                """,
                (building, floor, room_number, room_name, qr_code, now),
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        return jsonify({"message": "มีห้องนี้อยู่ในระบบแล้ว"}), 409

    return jsonify({"success": True, "room": serialize_row(room)}), 201


@app.patch("/api/staff/rooms/<int:room_id>/toggle")
@token_required
@admin_required
def toggle_room(room_id):
    with get_db() as conn:
        room = conn.execute(
            "SELECT * FROM rooms WHERE id=%s",
            (room_id,),
        ).fetchone()
        if room is None:
            return jsonify({"message": "ไม่พบห้องนี้"}), 404

        updated = conn.execute(
            "UPDATE rooms SET is_active = NOT is_active WHERE id=%s RETURNING *",
            (room_id,),
        ).fetchone()

    return jsonify({"success": True, "room": serialize_row(updated)})


@app.get("/api/staff/rooms/<int:room_id>/qr")
@token_required
@admin_required
def room_qr_image(room_id):
    with get_db() as conn:
        room = conn.execute(
            "SELECT * FROM rooms WHERE id=%s",
            (room_id,),
        ).fetchone()

    if room is None:
        return "ไม่พบห้องนี้", 404

    # ?service=repair (ค่าเริ่มต้น) หรือ ?service=cleaning -> QR ชี้ไปหน้าฟอร์มนั้นโดยตรงพร้อมรหัสห้อง
    service = "cleaning" if request.args.get("service") == "cleaning" else "repair"
    target_url = f"{PUBLIC_BASE_URL}/request/{service}?room={room['qr_code']}"
    img = qrcode.make(target_url)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    download = request.args.get("download") == "1"
    filename = f"QR_{room['building']}_{room['floor']}_{room['room_number']}_{service}.png"
    return send_file(
        buffer,
        mimetype="image/png",
        as_attachment=download,
        download_name=filename,
    )


@app.get("/api/staff/users")
@token_required
@admin_required
def list_users():
    with get_db() as conn:
        users = conn.execute(
            "SELECT id, username, email, role, created_at FROM users ORDER BY id ASC"
        ).fetchall()
        
    return jsonify({"users": [serialize_row(row) for row in users]})


@app.post("/api/staff/users")
@token_required
@admin_required
def create_user():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", "")).strip()
    role = str(data.get("role", "technician")).strip()

    if not username or not password:
        return jsonify({"message": "กรุณากรอกชื่อผู้ใช้งานและรหัสผ่าน"}), 400

    if len(password) < 6:
        return jsonify({"message": "รหัสผ่านต้องมีความยาวอย่างน้อย 6 ตัวอักษร"}), 400

    if role not in ['admin', 'technician', 'maid']:
        return jsonify({"message": "ตำแหน่งไม่ถูกต้อง"}), 400

    hashed_pw = generate_password_hash(password)

    try:
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO users (username, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
                """,
                (username, email, hashed_pw, role)
            )
    except psycopg.errors.UniqueViolation:
        return jsonify({"message": "มีชื่อผู้ใช้งานนี้อยู่ในระบบแล้ว กรุณาใช้ชื่ออื่น"}), 409

    return jsonify({"success": True}), 201


@app.put("/api/staff/users/<int:user_id>")
@token_required
@admin_required
def edit_staff_user(user_id):
    data = request.get_json(silent=True) or {}
    new_username = str(data.get("username", "")).strip()
    new_email = str(data.get("email", "")).strip()
    new_password = str(data.get("password", "")).strip()

    if not new_username:
        return jsonify({"message": "กรุณากรอกชื่อผู้ใช้งาน"}), 400

    with get_db() as conn:
        target_user = conn.execute("SELECT username FROM users WHERE id = %s", (user_id,)).fetchone()
        
        if not target_user:
            return jsonify({"message": "ไม่พบผู้ใช้งานนี้"}), 404

        if target_user["username"] == 'admin' and new_username != 'admin':
            return jsonify({"message": "ไม่อนุญาตให้เปลี่ยนชื่อบัญชีของ admin หลักได้"}), 403

        try:
            if new_password:
                if len(new_password) < 6:
                    return jsonify({"message": "รหัสผ่านต้องมีความยาวอย่างน้อย 6 ตัวอักษร"}), 400
                hashed_pw = generate_password_hash(new_password)
                conn.execute(
                    "UPDATE users SET username = %s, email = %s, password_hash = %s WHERE id = %s",
                    (new_username, new_email, hashed_pw, user_id)
                )
            else:
                conn.execute(
                    "UPDATE users SET username = %s, email = %s WHERE id = %s",
                    (new_username, new_email, user_id)
                )
        except psycopg.errors.UniqueViolation:
            return jsonify({"message": "ชื่อผู้ใช้งานนี้ถูกใช้ไปแล้ว กรุณาตั้งชื่ออื่น"}), 409

    return jsonify({"success": True})


@app.patch("/api/staff/users/<int:user_id>/role")
@token_required
@admin_required
def update_user_role(user_id):
    data = request.get_json(silent=True) or {}
    role = str(data.get("role", "")).strip()
    if role not in ['admin', 'technician', 'maid']:
        return jsonify({"message": "ตำแหน่งไม่ถูกต้อง"}), 400

    with get_db() as conn:
        conn.execute(
            "UPDATE users SET role = %s WHERE id = %s",
            (role, user_id)
        )
    return jsonify({"success": True})


@app.delete("/api/staff/users/<int:user_id>")
@token_required
@admin_required
def delete_staff_user(user_id):
    with get_db() as conn:
        user = conn.execute("SELECT username FROM users WHERE id = %s", (user_id,)).fetchone()
        
        if not user:
            return jsonify({"message": "ไม่พบผู้ใช้งานนี้"}), 404
            
        if user["username"] == request.current_user['username']:
            return jsonify({"message": "ไม่สามารถลบบัญชีตัวเองขณะล็อกอินได้"}), 403
            
        conn.execute("DELETE FROM users WHERE id = %s", (user_id,))
    return jsonify({"success": True})

@app.get("/api/staff/list")
@token_required
def get_staff_list():
    with get_db() as conn:
        # ดึงเฉพาะคนที่ไม่ได้เป็นแอดมิน เพื่อเอาไปแสดงใน Dropdown จ่ายงาน
        staff = conn.execute(
            "SELECT id, username, role FROM users WHERE role IN ('technician', 'maid') ORDER BY role, username"
        ).fetchall()
    return jsonify({"staff": [serialize_row(row) for row in staff]})

@app.patch("/api/staff/requests/<int:request_id>/assign")
@token_required
@admin_required
def assign_request(request_id):
    data = request.get_json(silent=True) or {}
    staff_id = data.get("staff_id") # ถ้าส่งมาเป็น null คือการยกเลิกการจ่ายงาน
    
    now = datetime.now()
    with get_db() as conn:
        conn.execute(
            "UPDATE service_requests SET assigned_to=%s, updated_at=%s WHERE id=%s",
            (staff_id, now, request_id)
        )
        
        # บันทึกประวัติ
        if staff_id:
            staff = conn.execute("SELECT username FROM users WHERE id=%s", (staff_id,)).fetchone()
            detail = f"มอบหมายงานให้ {staff['username']}" if staff else "มอบหมายงาน"
        else:
            detail = "ยกเลิกการมอบหมายงาน"
            
        conn.execute(
            "INSERT INTO request_history (request_id, action, detail, created_at) VALUES (%s, 'assign', %s, %s)",
            (request_id, detail, now)
        )
        
    return jsonify({"success": True})

@app.post("/api/staff/requests/<int:request_id>/complete")
@token_required
def complete_request(request_id):
    try:
        # ใช้ฟังก์ชันเซฟไฟล์รูปเดิมที่เรามีอยู่แล้ว
        uploaded_images = save_uploaded_images(get_uploaded_image_files(), "proof")
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
        
    image_path = uploaded_images[0] if uploaded_images else None
    
    now = datetime.now()
    with get_db() as conn:
        # อัปเดตสถานะเป็น completed และบันทึกชื่อไฟล์รูป
        conn.execute(
            """
            UPDATE service_requests 
            SET status='completed', completion_image_path=%s, updated_at=%s 
            WHERE id=%s
            """,
            (image_path, now, request_id)
        )
        # บันทึกประวัติ
        conn.execute(
            """
            INSERT INTO request_history (request_id, action, detail, created_at) 
            VALUES (%s, 'status', 'เสร็จสิ้น (แนบรูปหลักฐาน)', %s)
            """,
            (request_id, now)
        )
    return jsonify({"success": True})

@app.errorhandler(413)
def too_large(_):
    return jsonify({"success": False, "message": "ไฟล์มีขนาดใหญ่เกินกำหนด"}), 413


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=os.environ.get("FLASK_DEBUG") == "1")