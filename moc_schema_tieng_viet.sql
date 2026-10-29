-- =====================================================================
-- MỘC — Website quản lý đặt món & đặt bàn nhà hàng
-- PostgreSQL DDL — Phiên bản tiếng Việt
-- Đối tượng: PostgreSQL 15+ (GENERATED ALWAYS AS IDENTITY, ENUM, PostGIS)
-- =====================================================================

-- ---------------------------------------------------------------------
-- 0. MỞ RỘNG (EXTENSIONS)
-- ---------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS postgis;      -- cho bang_an.toa_do (GIS)
CREATE EXTENSION IF NOT EXISTS pgcrypto;     -- tiện cho token/hash nếu cần

-- ---------------------------------------------------------------------
-- 0.1 KIỂU ENUM — thay cho varchar tự do để enforce FSM/nghiệp vụ
-- ---------------------------------------------------------------------
CREATE TYPE kieu_gioi_tinh        AS ENUM ('nam','nu','khac');
CREATE TYPE trang_thai_ban        AS ENUM ('trong','dang_giu','da_dat','dang_phuc_vu','bao_tri');
CREATE TYPE hinh_thuc_dat_ban     AS ENUM ('chi_giu_cho','dat_ban_va_goi_mon','dat_ban_goi_mon_chinh_sua');
CREATE TYPE trang_thai_dat_ban    AS ENUM ('cho_thanh_toan','da_xac_nhan','khach_da_den','hoan_tat','da_huy','khach_khong_den');
CREATE TYPE trang_thai_coc        AS ENUM ('chua_thanh_toan','dang_xu_ly','thanh_cong','that_bai','da_hoan_tien','hoan_tien_mot_phan');
CREATE TYPE moc_huy_dat_ban       AS ENUM ('truoc_24h','tu_6_den_24h','trong_6h','khach_khong_den');
CREATE TYPE trang_thai_don_hang   AS ENUM ('cho_tiep_nhan','da_xac_nhan','dang_che_bien','san_sang','hoan_tat','da_huy');
CREATE TYPE hinh_thuc_don_hang    AS ENUM ('giao_hang','tu_den_lay');
CREATE TYPE loai_thanh_toan       AS ENUM ('don_hang','tien_coc');
CREATE TYPE trang_thai_thanh_toan AS ENUM ('cho_xu_ly','thanh_cong','that_bai','da_hoan_tien');
CREATE TYPE kieu_giam_gia         AS ENUM ('phan_tram','so_tien_co_dinh');
CREATE TYPE trang_thai_gio_hang   AS ENUM ('dang_su_dung','da_thanh_toan','bo_do');
CREATE TYPE trang_thai_bai_viet   AS ENUM ('nhap','da_dang','luu_tru');
CREATE TYPE trang_thai_hoi_thoai  AS ENUM ('mo','dong');
CREATE TYPE loai_tin_nhan         AS ENUM ('van_ban','hinh_anh','he_thong');
CREATE TYPE loai_tuong_tac        AS ENUM ('xem','them_gio_hang','dat_mon','danh_gia','yeu_thich');
CREATE TYPE loai_giao_dich_kho    AS ENUM ('nhap','xuat','dieu_chinh');

-- ---------------------------------------------------------------------
-- 0.2 HÀM TRIGGER dùng chung cho cap_nhat_luc
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_cap_nhat_thoi_gian() RETURNS trigger AS $$
BEGIN
  NEW.cap_nhat_luc := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- 1. RBAC — VAI TRÒ / QUYỀN HẠN / NGƯỜI DÙNG
-- =====================================================================
CREATE TABLE vai_tro (
  id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ten          VARCHAR(50)  NOT NULL UNIQUE,
  mo_ta        TEXT,
  tao_luc      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  cap_nhat_luc TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_vai_tro_cap_nhat BEFORE UPDATE ON vai_tro
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

CREATE TABLE quyen_han (
  id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ten          VARCHAR(100) NOT NULL UNIQUE,
  ma_quyen     VARCHAR(100) NOT NULL UNIQUE,   -- ví dụ: 'don_hang.doi_trang_thai'
  mo_ta        TEXT,
  tao_luc      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  cap_nhat_luc TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_quyen_han_cap_nhat BEFORE UPDATE ON quyen_han
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

CREATE TABLE vai_tro_quyen_han (
  vai_tro_id   BIGINT NOT NULL REFERENCES vai_tro(id)  ON DELETE CASCADE,
  quyen_han_id BIGINT NOT NULL REFERENCES quyen_han(id) ON DELETE CASCADE,
  PRIMARY KEY (vai_tro_id, quyen_han_id)
);

CREATE TABLE nguoi_dung (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ten_dang_nhap   VARCHAR(50)  NOT NULL UNIQUE,
  thu_dien_tu     VARCHAR(255) NOT NULL UNIQUE,
  so_dien_thoai   VARCHAR(20)  UNIQUE,
  mat_khau_hash   TEXT NOT NULL,
  ho_ten          VARCHAR(150) NOT NULL,
  anh_dai_dien    TEXT,
  ngay_sinh       DATE,
  gioi_tinh       kieu_gioi_tinh,
  con_hoat_dong   BOOLEAN     NOT NULL DEFAULT true,
  dang_nhap_luc   TIMESTAMPTZ,
  tao_luc         TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_nguoi_dung_email ON nguoi_dung(thu_dien_tu);
CREATE TRIGGER trg_nguoi_dung_cap_nhat BEFORE UPDATE ON nguoi_dung
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

CREATE TABLE nguoi_dung_vai_tro (
  nguoi_dung_id BIGINT NOT NULL REFERENCES nguoi_dung(id) ON DELETE CASCADE,
  vai_tro_id    BIGINT NOT NULL REFERENCES vai_tro(id)    ON DELETE CASCADE,
  PRIMARY KEY (nguoi_dung_id, vai_tro_id)
);

-- =====================================================================
-- 2. CHI NHÁNH & BÀN ĂN (GIS)
-- =====================================================================
CREATE TABLE chi_nhanh (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ten             VARCHAR(150) NOT NULL,
  dia_chi         TEXT         NOT NULL,
  so_dien_thoai   VARCHAR(20),
  toa_do_gis      geography(Point, 4326) NOT NULL,   -- (kinh_do, vi_do) — PostGIS
  con_hoat_dong   BOOLEAN     NOT NULL DEFAULT true,
  tao_luc         TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_chi_nhanh_toa_do ON chi_nhanh USING GIST (toa_do_gis);
CREATE TRIGGER trg_chi_nhanh_cap_nhat BEFORE UPDATE ON chi_nhanh
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

CREATE TABLE ban_an (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  chi_nhanh_id    BIGINT      NOT NULL REFERENCES chi_nhanh(id) ON DELETE CASCADE,
  so_ban          VARCHAR(20) NOT NULL,
  khu_vuc         VARCHAR(50),                         -- ví dụ: Trong nhà, Ngoài trời, VIP
  suc_chua        INT         NOT NULL CHECK (suc_chua > 0),
  trang_thai      trang_thai_ban NOT NULL DEFAULT 'trong',
  tao_luc         TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (chi_nhanh_id, so_ban)
);
CREATE INDEX idx_ban_an_chi_nhanh_trang_thai ON ban_an(chi_nhanh_id, trang_thai);
CREATE TRIGGER trg_ban_an_cap_nhat BEFORE UPDATE ON ban_an
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

-- =====================================================================
-- 3. DANH MỤC, THẺ TAG, NGUYÊN LIỆU, MÓN ĂN
-- =====================================================================
CREATE TABLE danh_muc (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ten             VARCHAR(100) NOT NULL,
  duong_dan       VARCHAR(120) NOT NULL UNIQUE,
  mo_ta           TEXT,
  anh_dai_dien    TEXT,
  con_hoat_dong   BOOLEAN     NOT NULL DEFAULT true,
  tao_luc         TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_danh_muc_cap_nhat BEFORE UPDATE ON danh_muc
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

CREATE TABLE the_mon_an (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ten             VARCHAR(50)  NOT NULL,
  duong_dan       VARCHAR(60)  NOT NULL UNIQUE,
  tao_luc         TIMESTAMPTZ  NOT NULL DEFAULT now(),
  cap_nhat_luc    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE nguyen_lieu (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ten             VARCHAR(150) NOT NULL,
  don_vi          VARCHAR(20)  NOT NULL,              -- 'g','kg','ml','l','cái'...
  ton_kho_hien_tai NUMERIC(14,3) NOT NULL DEFAULT 0 CHECK (ton_kho_hien_tai >= 0),
  ton_kho_toi_thieu NUMERIC(14,3) NOT NULL DEFAULT 0 CHECK (ton_kho_toi_thieu >= 0),
  con_hoat_dong   BOOLEAN      NOT NULL DEFAULT true,
  tao_luc         TIMESTAMPTZ  NOT NULL DEFAULT now(),
  cap_nhat_luc    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_nguyen_lieu_cap_nhat BEFORE UPDATE ON nguyen_lieu
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

CREATE TABLE mon_an (
  id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  danh_muc_id        BIGINT      NOT NULL REFERENCES danh_muc(id) ON DELETE RESTRICT,
  ten                VARCHAR(150) NOT NULL,
  duong_dan          VARCHAR(180) NOT NULL UNIQUE,
  mo_ta_ngan         TEXT,
  mo_ta_chi_tiet     TEXT,
  don_gia            NUMERIC(12,2) NOT NULL CHECK (don_gia >= 0),
  do_cay             SMALLINT    NOT NULL DEFAULT 0 CHECK (do_cay BETWEEN 0 AND 3),
  la_mon_chay        BOOLEAN     NOT NULL DEFAULT false,
  con_hang           BOOLEAN     NOT NULL DEFAULT true,    -- hết hàng tạm thời
  hien_thi           BOOLEAN     NOT NULL DEFAULT true,    -- ẩn/hiện trên menu
  noi_bat            BOOLEAN     NOT NULL DEFAULT false,   -- badge thủ công (Mới, Nổi bật)
  quan_ly_kho        BOOLEAN     NOT NULL DEFAULT false,   -- có quản lý theo nguyên liệu không
  ton_kho_cache      INT,                                  -- cache tồn kho cho món KHÔNG track theo nguyên liệu
  diem_danh_gia      NUMERIC(2,1) NOT NULL DEFAULT 0 CHECK (diem_danh_gia BETWEEN 0 AND 5),
  so_luot_danh_gia   INT         NOT NULL DEFAULT 0,
  tao_luc            TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_mon_an_danh_muc ON mon_an(danh_muc_id);
CREATE INDEX idx_mon_an_tim_kiem ON mon_an USING GIN (to_tsvector('simple', ten || ' ' || coalesce(mo_ta_ngan,'')));
CREATE TRIGGER trg_mon_an_cap_nhat BEFORE UPDATE ON mon_an
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

CREATE TABLE hinh_anh_mon_an (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  mon_an_id       BIGINT      NOT NULL REFERENCES mon_an(id) ON DELETE CASCADE,
  duong_dan_anh   TEXT        NOT NULL,
  la_anh_chinh    BOOLEAN     NOT NULL DEFAULT false,
  thu_tu          INT         NOT NULL DEFAULT 0,
  tao_luc         TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_hinh_anh_mon_an ON hinh_anh_mon_an(mon_an_id);

CREATE TABLE mon_an_the (
  mon_an_id   BIGINT NOT NULL REFERENCES mon_an(id)    ON DELETE CASCADE,
  the_id      BIGINT NOT NULL REFERENCES the_mon_an(id) ON DELETE CASCADE,
  PRIMARY KEY (mon_an_id, the_id)
);

CREATE TABLE dinh_muc_nguyen_lieu (
  id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  mon_an_id         BIGINT      NOT NULL REFERENCES mon_an(id)     ON DELETE CASCADE,
  nguyen_lieu_id    BIGINT      NOT NULL REFERENCES nguyen_lieu(id) ON DELETE RESTRICT,
  so_luong_can      NUMERIC(14,3) NOT NULL CHECK (so_luong_can > 0),
  tao_luc           TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (mon_an_id, nguyen_lieu_id)
);

CREATE TABLE lich_su_xuat_nhap_kho (
  id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nguyen_lieu_id    BIGINT      NOT NULL REFERENCES nguyen_lieu(id) ON DELETE RESTRICT,
  loai_giao_dich    loai_giao_dich_kho NOT NULL,
  so_luong          NUMERIC(14,3) NOT NULL,
  ton_kho_truoc     NUMERIC(14,3) NOT NULL,
  ton_kho_sau       NUMERIC(14,3) NOT NULL,
  loai_tham_chieu   VARCHAR(30),    -- 'don_hang','nhap_hang','dieu_chinh_thu_cong'...
  id_tham_chieu     BIGINT,         -- polymorphic, không FK cứng
  ghi_chu           TEXT,
  tao_boi           BIGINT REFERENCES nguoi_dung(id) ON DELETE SET NULL,
  tao_luc           TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_kho_nguyen_lieu ON lich_su_xuat_nhap_kho(nguyen_lieu_id, tao_luc);

-- =====================================================================
-- 4. GIỎ HÀNG
-- =====================================================================
CREATE TABLE gio_hang (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nguoi_dung_id   BIGINT      NOT NULL REFERENCES nguoi_dung(id) ON DELETE CASCADE,
  trang_thai      trang_thai_gio_hang NOT NULL DEFAULT 'dang_su_dung',
  tao_luc         TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc    TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- chỉ 1 giỏ "dang_su_dung" cho mỗi người dùng tại một thời điểm
CREATE UNIQUE INDEX uq_gio_hang_active ON gio_hang(nguoi_dung_id) WHERE trang_thai = 'dang_su_dung';
CREATE TRIGGER trg_gio_hang_cap_nhat BEFORE UPDATE ON gio_hang
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

CREATE TABLE chi_tiet_gio_hang (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  gio_hang_id     BIGINT      NOT NULL REFERENCES gio_hang(id) ON DELETE CASCADE,
  mon_an_id       BIGINT      NOT NULL REFERENCES mon_an(id)   ON DELETE RESTRICT,
  so_luong        INT         NOT NULL CHECK (so_luong > 0),
  don_gia_luc_dat NUMERIC(12,2) NOT NULL,   -- snapshot giá tại thời điểm thêm giỏ
  ghi_chu         TEXT,
  tao_luc         TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (gio_hang_id, mon_an_id)
);
CREATE TRIGGER trg_chi_tiet_gio_hang_cap_nhat BEFORE UPDATE ON chi_tiet_gio_hang
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

-- =====================================================================
-- 5. CHÍNH SÁCH ĐẶT CỌC & HUỶ
-- =====================================================================
CREATE TABLE chinh_sach_dat_coc (
  id                         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  chi_nhanh_id               BIGINT REFERENCES chi_nhanh(id) ON DELETE CASCADE,  -- NULL = áp dụng toàn hệ thống
  phan_tram_coc              NUMERIC(5,2) NOT NULL CHECK (phan_tram_coc BETWEEN 0 AND 100),
  thoi_gian_giu_cho_phut     INT NOT NULL DEFAULT 10 CHECK (thoi_gian_giu_cho_phut > 0),
  han_thanh_toan_phut        INT NOT NULL DEFAULT 15 CHECK (han_thanh_toan_phut > 0),
  con_ap_dung                BOOLEAN NOT NULL DEFAULT true,
  tao_luc                    TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc               TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_chinh_sach_coc_cap_nhat BEFORE UPDATE ON chinh_sach_dat_coc
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

CREATE TABLE quy_tac_huy_dat_coc (
  id                    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  chinh_sach_id         BIGINT NOT NULL REFERENCES chinh_sach_dat_coc(id) ON DELETE CASCADE,
  moc_thoi_gian         moc_huy_dat_ban NOT NULL,
  phan_tram_hoan_tien   NUMERIC(5,2) NOT NULL CHECK (phan_tram_hoan_tien BETWEEN 0 AND 100),
  UNIQUE (chinh_sach_id, moc_thoi_gian)
);

-- =====================================================================
-- 6. ĐẶT BÀN
-- =====================================================================
CREATE TABLE dat_ban (
  id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nguoi_dung_id     BIGINT NOT NULL REFERENCES nguoi_dung(id) ON DELETE RESTRICT,
  chi_nhanh_id      BIGINT NOT NULL REFERENCES chi_nhanh(id)  ON DELETE RESTRICT,
  ban_an_id         BIGINT NOT NULL REFERENCES ban_an(id)      ON DELETE RESTRICT,
  ma_dat_ban        VARCHAR(20) NOT NULL UNIQUE,
  ngay_dat          DATE        NOT NULL,
  gio_bat_dau       TIME        NOT NULL,
  gio_ket_thuc      TIME,
  so_luong_khach    INT         NOT NULL CHECK (so_luong_khach > 0),
  hinh_thuc         hinh_thuc_dat_ban NOT NULL,
  trang_thai        trang_thai_dat_ban NOT NULL DEFAULT 'cho_thanh_toan',
  yeu_cau_dat_coc   BOOLEAN     NOT NULL DEFAULT false,
  so_tien_coc       NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (so_tien_coc >= 0),
  trang_thai_coc    trang_thai_coc NOT NULL DEFAULT 'chua_thanh_toan',
  thanh_toan_coc_luc TIMESTAMPTZ,
  ten_khach         VARCHAR(150) NOT NULL,
  sdt_khach         VARCHAR(20)  NOT NULL,
  ghi_chu           TEXT,
  huy_luc           TIMESTAMPTZ,
  ly_do_huy         TEXT,
  phien_ban         INT         NOT NULL DEFAULT 0,   -- optimistic locking
  tao_luc           TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc      TIMESTAMPTZ NOT NULL DEFAULT now(),
  -- chi_giu_cho thì không được yêu cầu cọc
  CONSTRAINT kiem_tra_chi_giu_cho CHECK (
    hinh_thuc <> 'chi_giu_cho' OR (yeu_cau_dat_coc = false AND so_tien_coc = 0)
  )
);
CREATE INDEX idx_dat_ban_chi_nhanh_ngay ON dat_ban(chi_nhanh_id, ngay_dat, gio_bat_dau);
CREATE INDEX idx_dat_ban_nguoi_dung ON dat_ban(nguoi_dung_id);
CREATE INDEX idx_dat_ban_ban_an_ngay ON dat_ban(ban_an_id, ngay_dat);
CREATE TRIGGER trg_dat_ban_cap_nhat BEFORE UPDATE ON dat_ban
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

CREATE TABLE mon_an_trong_dat_ban (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  dat_ban_id      BIGINT NOT NULL REFERENCES dat_ban(id) ON DELETE CASCADE,
  mon_an_id       BIGINT NOT NULL REFERENCES mon_an(id)  ON DELETE RESTRICT,
  so_luong        INT    NOT NULL CHECK (so_luong > 0),
  don_gia_luc_dat NUMERIC(12,2) NOT NULL,
  tao_luc         TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (dat_ban_id, mon_an_id)
);
CREATE TRIGGER trg_mon_dat_ban_cap_nhat BEFORE UPDATE ON mon_an_trong_dat_ban
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

-- =====================================================================
-- 7. KHUYẾN MÃI
-- =====================================================================
CREATE TABLE khuyen_mai (
  id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ma_giam_gia         VARCHAR(50)  NOT NULL UNIQUE,
  ten                 VARCHAR(150) NOT NULL,
  mo_ta               TEXT,
  kieu_giam           kieu_giam_gia NOT NULL,
  gia_tri_giam        NUMERIC(12,2) NOT NULL CHECK (gia_tri_giam >= 0),
  don_hang_toi_thieu  NUMERIC(12,2) DEFAULT 0,
  giam_toi_da         NUMERIC(12,2),                    -- trần giảm khi kieu_giam = phan_tram
  bat_dau_luc         TIMESTAMPTZ  NOT NULL,
  ket_thuc_luc        TIMESTAMPTZ  NOT NULL,
  gioi_han_su_dung    INT,                              -- NULL = không giới hạn
  so_lan_da_dung      INT          NOT NULL DEFAULT 0,
  con_hoat_dong       BOOLEAN      NOT NULL DEFAULT true,
  tao_luc             TIMESTAMPTZ  NOT NULL DEFAULT now(),
  cap_nhat_luc        TIMESTAMPTZ  NOT NULL DEFAULT now(),
  CHECK (ket_thuc_luc > bat_dau_luc)
);
CREATE TRIGGER trg_khuyen_mai_cap_nhat BEFORE UPDATE ON khuyen_mai
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

CREATE TABLE ma_khuyen_mai (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  khuyen_mai_id   BIGINT NOT NULL REFERENCES khuyen_mai(id) ON DELETE CASCADE,
  ma              VARCHAR(50) NOT NULL UNIQUE,
  gioi_han        INT,
  da_dung         INT         NOT NULL DEFAULT 0,
  con_hoat_dong   BOOLEAN     NOT NULL DEFAULT true,
  tao_luc         TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_ma_km_cap_nhat BEFORE UPDATE ON ma_khuyen_mai
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

-- =====================================================================
-- 8. ĐƠN HÀNG — máy trạng thái hữu hạn (FSM)
-- =====================================================================
CREATE TABLE don_hang (
  id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ma_don_hang       VARCHAR(20)  NOT NULL UNIQUE,    -- mã hiển thị cho khách vd: "MOC482910"
  nguoi_dung_id     BIGINT NOT NULL REFERENCES nguoi_dung(id) ON DELETE RESTRICT,
  chi_nhanh_id      BIGINT REFERENCES chi_nhanh(id) ON DELETE SET NULL,
  dat_ban_id        BIGINT REFERENCES dat_ban(id)   ON DELETE SET NULL,
  hinh_thuc         hinh_thuc_don_hang NOT NULL,
  trang_thai        trang_thai_don_hang NOT NULL DEFAULT 'cho_tiep_nhan',
  ten_khach         VARCHAR(150) NOT NULL,
  sdt_khach         VARCHAR(20)  NOT NULL,
  dia_chi_giao      TEXT,                             -- bắt buộc khi hinh_thuc = giao_hang
  ghi_chu           TEXT,
  tien_hang         NUMERIC(12,2) NOT NULL CHECK (tien_hang >= 0),
  tien_giam         NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (tien_giam >= 0),
  tong_tien         NUMERIC(12,2) NOT NULL CHECK (tong_tien >= 0),
  khuyen_mai_id     BIGINT REFERENCES khuyen_mai(id) ON DELETE SET NULL,
  tao_luc           TIMESTAMPTZ  NOT NULL DEFAULT now(),
  cap_nhat_luc      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  CONSTRAINT kiem_tra_giao_hang_can_dia_chi CHECK (
    hinh_thuc <> 'giao_hang' OR dia_chi_giao IS NOT NULL
  )
);
CREATE INDEX idx_don_hang_nguoi_dung ON don_hang(nguoi_dung_id, tao_luc DESC);
CREATE INDEX idx_don_hang_trang_thai ON don_hang(trang_thai);
CREATE TRIGGER trg_don_hang_cap_nhat BEFORE UPDATE ON don_hang
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

CREATE TABLE chi_tiet_don_hang (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  don_hang_id     BIGINT NOT NULL REFERENCES don_hang(id) ON DELETE CASCADE,
  mon_an_id       BIGINT NOT NULL REFERENCES mon_an(id)   ON DELETE RESTRICT,
  so_luong        INT    NOT NULL CHECK (so_luong > 0),
  don_gia_luc_dat NUMERIC(12,2) NOT NULL,
  thanh_tien      NUMERIC(12,2) NOT NULL,
  tao_luc         TIMESTAMPTZ   NOT NULL DEFAULT now(),
  cap_nhat_luc    TIMESTAMPTZ   NOT NULL DEFAULT now()
);
CREATE INDEX idx_chi_tiet_don_hang ON chi_tiet_don_hang(don_hang_id);
CREATE TRIGGER trg_chi_tiet_dh_cap_nhat BEFORE UPDATE ON chi_tiet_don_hang
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

-- lịch sử chuyển trạng thái đơn hàng — FSM audit log
CREATE TABLE lich_su_trang_thai_don (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  don_hang_id     BIGINT NOT NULL REFERENCES don_hang(id) ON DELETE CASCADE,
  tu_trang_thai   trang_thai_don_hang,
  sang_trang_thai trang_thai_don_hang NOT NULL,
  doi_boi         BIGINT REFERENCES nguoi_dung(id) ON DELETE SET NULL,
  ghi_chu         TEXT,
  tao_luc         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_lich_su_trang_thai ON lich_su_trang_thai_don(don_hang_id, tao_luc);

-- =====================================================================
-- 9. THANH TOÁN — hỗ trợ cả đơn hàng lẫn tiền cọc đặt bàn
-- =====================================================================
CREATE TABLE thanh_toan (
  id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nguoi_dung_id     BIGINT NOT NULL REFERENCES nguoi_dung(id) ON DELETE RESTRICT,
  don_hang_id       BIGINT REFERENCES don_hang(id) ON DELETE CASCADE,
  dat_ban_id        BIGINT REFERENCES dat_ban(id)  ON DELETE CASCADE,
  loai_thanh_toan   loai_thanh_toan NOT NULL,            -- 'don_hang' | 'tien_coc'
  phuong_thuc       VARCHAR(30) NOT NULL,                -- 'tien_mat','chuyen_khoan','vnpay',...
  so_tien           NUMERIC(12,2) NOT NULL CHECK (so_tien > 0),
  ma_giao_dich      VARCHAR(100),                        -- vnp_TxnRef hoặc mã ngân hàng
  trang_thai        trang_thai_thanh_toan NOT NULL DEFAULT 'cho_xu_ly',
  thanh_toan_luc    TIMESTAMPTZ,
  hoan_tien_luc     TIMESTAMPTZ,
  tao_luc           TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc      TIMESTAMPTZ NOT NULL DEFAULT now(),
  -- đúng 1 trong 2 phải được set, khớp với loai_thanh_toan
  CONSTRAINT kiem_tra_muc_tieu_thanh_toan CHECK (
    (loai_thanh_toan = 'don_hang' AND don_hang_id IS NOT NULL AND dat_ban_id IS NULL) OR
    (loai_thanh_toan = 'tien_coc' AND dat_ban_id IS NOT NULL AND don_hang_id IS NULL)
  )
);
CREATE INDEX idx_thanh_toan_don_hang ON thanh_toan(don_hang_id);
CREATE INDEX idx_thanh_toan_dat_ban ON thanh_toan(dat_ban_id);
CREATE TRIGGER trg_thanh_toan_cap_nhat BEFORE UPDATE ON thanh_toan
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

CREATE TABLE lich_su_dung_khuyen_mai (
  id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  khuyen_mai_id     BIGINT NOT NULL REFERENCES khuyen_mai(id)   ON DELETE CASCADE,
  ma_khuyen_mai_id  BIGINT REFERENCES ma_khuyen_mai(id)          ON DELETE SET NULL,
  nguoi_dung_id     BIGINT NOT NULL REFERENCES nguoi_dung(id)   ON DELETE CASCADE,
  don_hang_id       BIGINT NOT NULL REFERENCES don_hang(id)      ON DELETE CASCADE,
  so_tien_giam      NUMERIC(12,2) NOT NULL CHECK (so_tien_giam >= 0),
  tao_luc           TIMESTAMPTZ   NOT NULL DEFAULT now(),
  UNIQUE (don_hang_id, khuyen_mai_id)
);
CREATE INDEX idx_ls_khuyen_mai_nguoi_dung ON lich_su_dung_khuyen_mai(nguoi_dung_id);

-- =====================================================================
-- 10. BÀI VIẾT (BLOG) & ĐÁNH GIÁ
-- =====================================================================
CREATE TABLE danh_muc_bai_viet (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ten             VARCHAR(100) NOT NULL,
  duong_dan       VARCHAR(120) NOT NULL UNIQUE,
  mo_ta           TEXT,
  tao_luc         TIMESTAMPTZ  NOT NULL DEFAULT now(),
  cap_nhat_luc    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE bai_viet (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  danh_muc_id     BIGINT REFERENCES danh_muc_bai_viet(id) ON DELETE SET NULL,
  tac_gia_id      BIGINT NOT NULL REFERENCES nguoi_dung(id) ON DELETE RESTRICT,
  tieu_de         VARCHAR(200) NOT NULL,
  duong_dan       VARCHAR(220) NOT NULL UNIQUE,
  anh_dai_dien    TEXT,
  noi_dung        TEXT        NOT NULL,
  trang_thai      trang_thai_bai_viet NOT NULL DEFAULT 'nhap',
  dang_luc        TIMESTAMPTZ,
  tao_luc         TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_bai_viet_trang_thai ON bai_viet(trang_thai, dang_luc DESC);
CREATE TRIGGER trg_bai_viet_cap_nhat BEFORE UPDATE ON bai_viet
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

CREATE TABLE danh_gia (
  id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nguoi_dung_id       BIGINT NOT NULL REFERENCES nguoi_dung(id)      ON DELETE CASCADE,
  mon_an_id           BIGINT NOT NULL REFERENCES mon_an(id)           ON DELETE CASCADE,
  don_hang_id         BIGINT NOT NULL REFERENCES don_hang(id)         ON DELETE CASCADE,
  chi_tiet_don_hang_id BIGINT NOT NULL REFERENCES chi_tiet_don_hang(id) ON DELETE CASCADE,
  diem_danh_gia       SMALLINT NOT NULL CHECK (diem_danh_gia BETWEEN 1 AND 5),
  nhan_xet            TEXT,
  hien_thi            BOOLEAN  NOT NULL DEFAULT true,
  tao_luc             TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc        TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (chi_tiet_don_hang_id)   -- 1 món trong 1 đơn chỉ được đánh giá 1 lần
);
CREATE INDEX idx_danh_gia_mon_an ON danh_gia(mon_an_id);
CREATE TRIGGER trg_danh_gia_cap_nhat BEFORE UPDATE ON danh_gia
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

-- =====================================================================
-- 11. CHAT THỜI GIAN THỰC
-- =====================================================================
CREATE TABLE hoi_thoai (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  khach_hang_id   BIGINT NOT NULL REFERENCES nguoi_dung(id) ON DELETE CASCADE,
  nhan_vien_id    BIGINT REFERENCES nguoi_dung(id) ON DELETE SET NULL,
  trang_thai      trang_thai_hoi_thoai NOT NULL DEFAULT 'mo',
  tin_nhan_cuoi_luc TIMESTAMPTZ,
  tao_luc         TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_hoi_thoai_khach ON hoi_thoai(khach_hang_id);
CREATE INDEX idx_hoi_thoai_nhan_vien ON hoi_thoai(nhan_vien_id);
CREATE TRIGGER trg_hoi_thoai_cap_nhat BEFORE UPDATE ON hoi_thoai
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

CREATE TABLE tin_nhan (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  hoi_thoai_id    BIGINT NOT NULL REFERENCES hoi_thoai(id)    ON DELETE CASCADE,
  nguoi_gui_id    BIGINT NOT NULL REFERENCES nguoi_dung(id)   ON DELETE CASCADE,
  loai_tin_nhan   loai_tin_nhan NOT NULL DEFAULT 'van_ban',
  noi_dung        TEXT    NOT NULL,
  da_doc          BOOLEAN NOT NULL DEFAULT false,
  doc_luc         TIMESTAMPTZ,
  tao_luc         TIMESTAMPTZ NOT NULL DEFAULT now(),
  cap_nhat_luc    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_tin_nhan_hoi_thoai ON tin_nhan(hoi_thoai_id, tao_luc);
CREATE TRIGGER trg_tin_nhan_cap_nhat BEFORE UPDATE ON tin_nhan
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

-- =====================================================================
-- 12. THÔNG BÁO
-- =====================================================================
CREATE TABLE thong_bao (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nguoi_dung_id   BIGINT NOT NULL REFERENCES nguoi_dung(id) ON DELETE CASCADE,
  loai            VARCHAR(50) NOT NULL,     -- 'trang_thai_don','dat_ban','khuyen_mai','chat'...
  tieu_de         VARCHAR(200) NOT NULL,
  noi_dung        TEXT         NOT NULL,
  loai_tham_chieu VARCHAR(30),              -- polymorphic
  id_tham_chieu   BIGINT,
  da_doc          BOOLEAN      NOT NULL DEFAULT false,
  doc_luc         TIMESTAMPTZ,
  tao_luc         TIMESTAMPTZ  NOT NULL DEFAULT now(),
  cap_nhat_luc    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_thong_bao_nguoi_dung ON thong_bao(nguoi_dung_id, da_doc, tao_luc DESC);
CREATE TRIGGER trg_thong_bao_cap_nhat BEFORE UPDATE ON thong_bao
  FOR EACH ROW EXECUTE FUNCTION trg_cap_nhat_thoi_gian();

-- =====================================================================
-- 13. AI GỢI Ý MÓN ĂN (Content-Based Filtering + TF-IDF)
-- =====================================================================
CREATE TABLE tuong_tac_mon_an (
  id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nguoi_dung_id     BIGINT NOT NULL REFERENCES nguoi_dung(id) ON DELETE CASCADE,
  mon_an_id         BIGINT NOT NULL REFERENCES mon_an(id)      ON DELETE CASCADE,
  loai_tuong_tac    loai_tuong_tac NOT NULL,
  trong_so          NUMERIC(5,2) NOT NULL DEFAULT 1,   -- trọng số để tính user profile vector
  tao_luc           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_tuong_tac_nguoi_dung ON tuong_tac_mon_an(nguoi_dung_id, tao_luc DESC);
CREATE INDEX idx_tuong_tac_mon_an ON tuong_tac_mon_an(mon_an_id);

CREATE TABLE goi_y_mon_an (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nguoi_dung_id   BIGINT NOT NULL REFERENCES nguoi_dung(id) ON DELETE CASCADE,
  mon_an_id       BIGINT NOT NULL REFERENCES mon_an(id)     ON DELETE CASCADE,
  diem_tuong_dong NUMERIC(5,4) NOT NULL CHECK (diem_tuong_dong BETWEEN 0 AND 1),  -- cosine similarity
  ly_do_goi_y     TEXT,
  phien_ban_model VARCHAR(30),
  tao_luc         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (nguoi_dung_id, mon_an_id, phien_ban_model)
);
CREATE INDEX idx_goi_y_nguoi_dung ON goi_y_mon_an(nguoi_dung_id, diem_tuong_dong DESC);

-- =====================================================================
-- HẾT SCHEMA
-- =====================================================================
