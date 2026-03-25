from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from config import DOCS_DIR, log
import random, os

def get_font(size):
    for font_path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/Arial.ttf",
    ]:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            continue
    return ImageFont.load_default()

class DocumentGenerator:
    def __init__(self, name, university, address, nim, city):
        self.name       = name
        self.university = university
        self.address    = address
        self.nim        = nim
        self.city       = city
        self.today      = datetime.now().strftime("%B %d, %Y")
        self.expiry     = (datetime.now() + timedelta(days=365)).strftime("%B %d, %Y")
        self.semester   = "Even Semester 2025/2026"

    def _header(self, draw, width):
        draw.rectangle([0, 0, width, 280], fill='#003580')
        draw.text((80, 35),  self.university.upper(), fill='white',   font=get_font(65))
        draw.text((80, 160), f"{self.city}, Indonesia", fill='#FFD700', font=get_font(44))

    # ── ENROLLMENT LETTER (A4, Best Doc) ──────────
    def enrollment_letter(self):
        img  = Image.new('RGB', (2480, 3508), 'white')
        draw = ImageDraw.Draw(img)
        self._header(draw, 2480)

        # Title
        draw.text((120, 320), "STUDENT ENROLLMENT VERIFICATION LETTER",
                  fill='black', font=get_font(60))
        draw.text((120, 410), "SURAT KETERANGAN AKTIF MAHASISWA",
                  fill='#555', font=get_font(48))
        draw.rectangle([120, 480, 2360, 486], fill='#003580')

        ref = f"{random.randint(1000,9999)}/UN{random.randint(10,99)}/AK/{datetime.now().year}"
        draw.text((120, 510), f"Ref No: {ref}    Date: {self.today}", fill='black', font=get_font(42))

        lines = [
            "",
            "TO WHOM IT MAY CONCERN",
            "",
            "We hereby certify that:",
            "",
            f"  Full Name    : {self.name}",
            f"  NIM          : {self.nim}",
            f"  Program      : S1 Teknik Informatika (Computer Science)",
            f"  Faculty      : Faculty of Computer Science & IT",
            f"  University   : {self.university}",
            f"  Semester     : {self.semester}",
            f"  Status       : ACTIVE STUDENT",
            f"  Address      : {self.address}",
            f"  Valid Until  : {self.expiry}",
            "",
            "is currently registered as an ACTIVE STUDENT at",
            f"{self.university}.",
            "",
            "This letter is issued for student verification and",
            "academic benefit application purposes.",
        ]
        y = 610
        for line in lines:
            draw.text((120, y), line, fill='black', font=get_font(44))
            y += 72

        # Signature + Stamp
        draw.text((120, y+60),  f"{self.city}, {self.today}",  fill='black', font=get_font(42))
        draw.text((120, y+130), "Academic Registrar",          fill='black', font=get_font(42))
        draw.text((120, y+200), self.university,               fill='black', font=get_font(42))
        draw.ellipse([1800, y+60, 2200, y+460], outline='#003580', width=10)
        draw.text((1830, y+220), "OFFICIAL",  fill='#003580', font=get_font(50))
        draw.text((1870, y+300), "STAMP",     fill='#003580', font=get_font(50))

        path = f"{DOCS_DIR}/enrollment_letter.jpg"
        img.save(path, "JPEG", quality=98, dpi=(300, 300))
        log.info(f"✅ Enrollment letter generated")
        return path

    # ── STUDENT ID CARD ───────────────────────────
    def student_id(self):
        img  = Image.new('RGB', (2480, 1580), 'white')
        draw = ImageDraw.Draw(img)
        self._header(draw, 2480)

        draw.text((80, 160), "KARTU TANDA MAHASISWA / STUDENT ID CARD",
                  fill='#FFD700', font=get_font(48))

        fields = [
            ("Nama / Name",      self.name),
            ("NIM",              self.nim),
            ("Program Studi",    "S1 Teknik Informatika"),
            ("Universitas",      self.university),
            ("Alamat / Address", self.address),
            ("Berlaku / Valid",  f"{self.today} — {self.expiry}"),
            ("Status",           "MAHASISWA AKTIF / ACTIVE STUDENT ✓"),
        ]
        y = 360
        for label, value in fields:
            draw.text((80,  y), label,       fill='#555', font=get_font(40))
            draw.text((620, y), f": {value}", fill='black', font=get_font(44))
            draw.rectangle([80, y+68, 2400, y+70], fill='#EEEEEE')
            y += 120

        path = f"{DOCS_DIR}/student_id.jpg"
        img.save(path, "JPEG", quality=98, dpi=(300, 300))
        log.info("✅ Student ID generated")
        return path

    # ── TRANSCRIPT ────────────────────────────────
    def transcript(self):
        img  = Image.new('RGB', (2480, 3508), 'white')
        draw = ImageDraw.Draw(img)
        self._header(draw, 2480)
        draw.text((80, 160), "TRANSKRIP AKADEMIK / ACADEMIC TRANSCRIPT",
                  fill='#FFD700', font=get_font(48))

        # Student info
        y = 320
        for label, val in [("Nama", self.name), ("NIM", self.nim),
                            ("Program", "S1 Teknik Informatika"),
                            ("Tanggal", self.today)]:
            draw.text((80, y),  label,       fill='#555', font=get_font(42))
            draw.text((420, y), f": {val}",   fill='black', font=get_font(42))
            y += 68

        # BAN-PT accreditation
        draw.rectangle([80, y+10, 2400, y+90], fill='#E8F4E8')
        draw.text((100, y+20),
            f"Akreditasi BAN-PT: A (Unggul) | No. {random.randint(1000,9999)}/BAN-PT/{datetime.now().year}",
            fill='#006600', font=get_font(38))
        y += 120

        # Table header
        cols    = ["No", "Kode", "Mata Kuliah",                    "SKS", "Nilai", "Bobot"]
        x_cols  = [80,   200,    480,                               1700,  1950,    2200]
        draw.rectangle([80, y, 2400, y+70], fill='#003580')
        for i, h in enumerate(cols):
            draw.text((x_cols[i]+5, y+10), h, fill='white', font=get_font(38))
        y += 70

        courses = [
            ("MIF101","Algoritma dan Pemrograman",        3,"A", 4.0),
            ("MIF102","Matematika Diskrit",                3,"A-",3.7),
            ("MIF201","Struktur Data",                     3,"A", 4.0),
            ("MIF202","Basis Data",                        3,"B+",3.3),
            ("MIF203","Jaringan Komputer",                 3,"A", 4.0),
            ("MIF301","Rekayasa Perangkat Lunak",          3,"A-",3.7),
            ("MIF302","Pemrograman Web",                   3,"A", 4.0),
            ("MIF303","Kecerdasan Buatan",                 3,"B+",3.3),
            ("MIF401","Sistem Operasi",                    3,"A", 4.0),
            ("MIF402","Pengembangan Aplikasi Mobile",      3,"A-",3.7),
        ]
        total_sks   = sum(c[2] for c in courses)
        total_bobot = sum(c[2]*c[4] for c in courses)
        ipk = round(total_bobot / total_sks, 2)

        for i, (code, name, sks, grade, bobot) in enumerate(courses):
            bg = '#F9F9F9' if i % 2 == 0 else 'white'
            draw.rectangle([80, y, 2400, y+65], fill=bg)
            for j, val in enumerate([str(i+1), code, name, str(sks), grade, str(bobot)]):
                draw.text((x_cols[j]+5, y+10), val, fill='black', font=get_font(36))
            y += 65

        draw.rectangle([80, y+20, 2400, y+100], fill='#FFF8E1')
        draw.text((100, y+28),
            f"Total SKS: {total_sks}    |    IPK / GPA: {ipk} / 4.00    |    Predikat: Cumlaude",
            fill='black', font=get_font(42))

        path = f"{DOCS_DIR}/transcript.jpg"
        img.save(path, "JPEG", quality=98, dpi=(300, 300))
        log.info("✅ Transcript generated")
        return path

    def generate_all(self):
        return {
            "enrollment_letter": self.enrollment_letter(),  # Best first
            "student_id":        self.student_id(),
            "transcript":        self.transcript()
        }
