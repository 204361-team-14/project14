# CS Building Services — Vue + Flask API + PostgreSQL + Docker

โครงสร้างนี้ย้ายระบบจาก Flask Template + SQLite เดิม ไปเป็น:

```text
Vue 3 + Vite
      ↓ REST API
Flask Backend
      ↓
PostgreSQL

Docker Compose: frontend + backend + db
```

ระบบล็อกอินถูกเอาออกทั้งหมดตามเวอร์ชันล่าสุด

## ฟีเจอร์ที่ย้ายมาแล้ว

- แจ้งซ่อม / แจ้งทำความสะอาด
- แนบรูปภาพ
- QR ห้องเป็นค่าเริ่มต้น แต่ผู้ใช้แก้ไขห้องได้ก่อนส่ง
- Dashboard ฝั่งเจ้าหน้าที่
- ค้นหา/กรองคำขอบริการ
- หน้ารายละเอียดคำขอ
- เปลี่ยนสถานะคำขอ
- หมายเหตุเจ้าหน้าที่ + ประวัติ
- ลบคำขอได้เมื่อสถานะ `completed`
- ของหาย-ของได้คืนแบบ **ผู้พบสิ่งของเป็นคนแจ้งเท่านั้น**
- เจ้าของของหายค้นหารายการที่มีผู้พบ
- เจ้าหน้าที่จัดการสถานะของที่เก็บได้
- จัดการห้อง / เปิดปิดห้อง / QR Code
- ไม่มี Login / Register / Google SSO

## โครงสร้าง

```text
cs_building_services_vue_postgres_docker/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── assets/main.css
│   │   ├── components/
│   │   └── views/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.js
└── scripts/
    └── migrate_sqlite_to_postgres.py
```

## วิธีรันด้วย Docker

1. ติดตั้ง Docker Desktop
2. คัดลอก `.env.example` เป็น `.env`
3. แก้ `POSTGRES_PASSWORD`
4. ถ้าจะสแกน QR จากมือถือ ให้แก้ `PUBLIC_BASE_URL` เป็น IP LAN ของเครื่อง เช่น:

```env
PUBLIC_BASE_URL=http://192.168.1.50:8080
SECRET_KEY=ใส่รหัสลับของคุณตรงนี้ (แนะนำให้เป็นรหัสสุ่มยาวๆ)
```

5. รัน:

```bash
docker compose up --build
```

6. เปิด:

```text
http://localhost:8080
```

Staff:

```text
http://localhost:8080/staff/dashboard
```

## หยุดระบบ

```bash
docker compose down
```

ถ้าต้องการลบข้อมูล PostgreSQL และ uploads ทั้งหมดด้วย:

```bash
docker compose down -v
```

## ย้ายข้อมูล SQLite เดิมเข้า PostgreSQL

หากต้องการเก็บข้อมูลจาก `database.db` เดิม ให้เปิด PostgreSQL ก่อน แล้วรัน migration script

### กรณีใช้ Docker PostgreSQL

รัน DB ก่อน:

```bash
docker compose up -d db backend
```

ติดตั้ง dependency สำหรับ script บนเครื่อง:

```bash
pip install "psycopg[binary]>=3.2,<4.0"
```

Windows CMD:

```bat
set DATABASE_URL=postgresql://cs_user:YOUR_PASSWORD@localhost:5432/cs_building_services
python scripts\migrate_sqlite_to_postgres.py C:\path\to\database.db
```

Docker Compose ชุดนี้ expose PostgreSQL ที่ port `5432` ไว้สำหรับ migration อยู่แล้ว หาก port นี้ชนกับ PostgreSQL ที่ติดตั้งในเครื่อง ให้เปลี่ยน `POSTGRES_PORT` ใน `.env` เช่น `5433` แล้วแก้ DATABASE_URL ให้ตรงกัน

## Development แบบไม่ใช้ Docker

### Backend

```bash
cd backend
pip install -r requirements.txt
set DATABASE_URL=postgresql://cs_user:cs_password@localhost:5432/cs_building_services
set PUBLIC_BASE_URL=http://localhost:5173
python app.py
```

Backend: `http://localhost:5000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

Vite proxy จะส่ง `/api`, `/uploads`, `/room` ไป Flask port 5000 ให้อัตโนมัติ

## หมายเหตุ QR Code

QR จะใช้ `PUBLIC_BASE_URL` ในการสร้าง URL ดังนั้นถ้าทดสอบด้วยมือถือ ห้ามใช้ `localhost` เพราะมือถือจะมอง localhost เป็นมือถือเอง ต้องใช้ IP LAN ของคอม เช่น `192.168.1.x` แทน


## รูปภาพจากระบบเก่า

Migration script จะปรับค่า `image_path` จากรูปแบบเดิม เช่น `uploads/example.jpg` ให้เป็น `example.jpg` สำหรับ backend ใหม่ แต่ไฟล์รูปจริงต้องคัดลอกจากโฟลเดอร์ `static/uploads/` เดิมเข้า volume `uploads_data` ด้วยถ้าต้องการเก็บรูปเก่าไว้
