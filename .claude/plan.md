# Seventh Sky Snap — UI Enhancement & Interactive Polaroid Plan

## Overview
Implementasi visi desain UI premium untuk Seventh Sky Snap: enhanced camera view dengan overlay transparan, premium capture flow, puzzle-to-polaroid transition, dan Interactive Polaroid Mode dengan two-hand gesture control.

---

## Phase 1: Config & Foundation (`config.py`)

**Tujuan**: Update konfigurasi untuk mendukung seluruh fitur baru.

- Tambah warna branding Seventh Sky:
  - `COLOR_SKY_BLUE = (79, 195, 247)` — #4FC3F7
  - `COLOR_SKY_PURPLE = (139, 92, 246)` — #8B5CF6
  - `COLOR_HAND_SKELETON = (255, 255, 255)` — putih untuk skeleton
- Tambah state baru: `STATE_INTERACTIVE_POLAROID = "interactive_polaroid"`
- Tambah konfigurasi polaroid interaction:
  - `POLAROID_SMOOTH_FACTOR = 0.08` — interpolasi untuk smooth movement
  - `POLAROID_SCALE_MIN = 0.3`
  - `POLAROID_SCALE_MAX = 2.0`
  - `POLAROID_IDLE_TIMEOUT = 5.0` — detik sebelum auto-save
- Update `num_hands=2` di detector config
- Tambah status bar message mapping per state

---

## Phase 2: Hand Detector — Two-Hand Support (`hand_tracking/detector.py`)

**Tujuan**: Upgrade dari 1 hand ke 2 hands detection.

- Ubah `num_hands=1` → `num_hands=2`
- Refactor `detect()` untuk mengembalikan list of hands, bukan single hand
- Tambah struktur data `self.all_hands` — list of dict per hand:
  ```python
  {
      'landmarks': [(x,y,z), ...],  # 21 landmarks
      'handedness': 'Left' | 'Right',
      'landmarks_px': [(px,py), ...]  # pixel coords
  }
  ```
- Update `get_landmark_pixels()` untuk mendukung multi-hand
- Backward compatibility: `self.landmarks` tetap ada (hand pertama)

---

## Phase 3: Gesture Recognizer — Two-Hand Gestures (`hand_tracking/gestures.py`)

**Tujuan**: Tambah gesture recognition untuk two-hand interactions.

- Tambah method `update_two_hands(left_landmarks, right_landmarks)` yang menghitung:
  - `midpoint`: titik tengah antara kedua tangan (normalized)
  - `rotation_angle`: sudut rotasi dari garis imajiner kiri-kanan (atan2)
  - `hand_distance`: jarak antara kedua tangan (untuk scale)
- Tambah smoothing buffer untuk midpoint, angle, dan distance
- Tambah method:
  - `get_midpoint_pixels(w, h)` → (px, py)
  - `get_rotation_angle()` → float (degrees)
  - `get_hand_distance()` → float (normalized)
  - `is_two_hand_active()` → bool

---

## Phase 4: Enhanced Camera View (`ui/menu.py` — CameraView)

**Tujuan**: Upgrade tampilan kamera sesuai visi desain.

### 4a: Status Bar Dinamis
- Buat `StatusBar` class di `ui/menu.py`
- Render di top-center dengan background semi-transparan
- Mapping state → text:
  - `camera_ready` → "Searching for Hands..."
  - `tracking` → "Hands Detected — Adjust Frame"
  - `capture_countdown` → "Hold Gesture — Capture in {N}"
  - `image_processing` → "Processing Image..."
  - `puzzle_mode` → "Solve the Puzzle"
  - `solved` → "Puzzle Completed!"
  - `interactive_polaroid` → "Free Mode — Move • Tilt • Scale"
- Warna text berubah sesuai state (sky blue untuk active, dim untuk searching)

### 4b: Hand Skeleton Transparan
- Update `draw_hand_landmarks()` di CameraView:
  - Garis connections: warna putih dengan alpha 60-70% (~150-180)
  - Titik landmark: putih dengan alpha 70%, radius lebih kecil (3px)
  - Garis lebih tipis: 1px (dari 2px)
- Gunakan pygame.Surface dengan SRCALPHA untuk transparansi

### 4c: Capture Frame Dashed Lines
- Update `draw_frame_overlay()`:
  - Ganti solid border dengan dashed line effect (putus-putus putih)
  - Implementasi: gambar segmen pendek dengan gap
  - Corner accents tetap solid dengan warna sky blue

### 4d: Info Panels (Bottom-Left & Bottom-Right)
- Buat `InfoPanel` class di `ui/menu.py`
- **Bottom-Left Panel**:
  - Gesture: "{gesture_name}"
  - Frame Size: "{size_label}" (Small/Medium/Large)
  - Hands: "{count} Detected"
- **Bottom-Right Panel**:
  - FPS: "{fps}"
  - Resolution: "{w}x{h}"
- Font kecil (14px), warna putih transparan (alpha ~150)
- Background pill semi-transparan

---

## Phase 5: Premium Capture Flow (`app.py`, `ui/animation.py`)

**Tujuan**: Efek visual premium saat capture.

### 5a: Camera Freeze Effect
- Di `_capture_photo()`: simpan frame saat capture
- Selama 0.5 detik, draw frame yang sama (freeze) tanpa update kamera
- Tambah state micro `STATE_CAPTURE_FREEZE` atau handle di `STATE_IMAGE_PROCESSING`

### 5b: White Flash Effect
- Buat `ShutterFlash` class di `ui/animation.py`
- Trigger setelah freeze: surface putih penuh layar, alpha 200 → 0 dalam 0.3 detik
- Easing: ease_out_cubic

### 5c: Fade Transition ke Puzzle
- Gunakan `Transition` yang sudah ada
- Fade out hitam → fade in ke puzzle mode
- Total durasi ~0.8 detik

---

## Phase 6: Puzzle Solved → Polaroid Presentation (`app.py`, `ui/animation.py`)

**Tujuan**: Transisi dari puzzle solved ke polaroid presentation.

### 6a: Puzzle Border Fade Animation
- Saat solved, animasi semua piece border → alpha 0 dalam 1 detik
- Tambah `fade_borders` method di PuzzleBoard
- Setelah borders hilang, piece images merge menjadi satu

### 6b: Zoom + Flash Effect
- Setelah merge: zoom in 1.05x selama 0.5 detik
- Trigger shutter flash + sound
- Easing: ease_out_cubic

### 6c: Polaroid Frame Slide-Up
- Buat `PolaroidReveal` class di `ui/animation.py`
- Animasi polaroid dari bawah layar ke tengah
- Durasi: 0.8 detik, easing: ease_out_cubic
- Shadow bertambah saat polaroid muncul

### 6d: Transisi ke Interactive Mode
- Setelah polaroid terlihat penuh (1.5 detik), auto-transition ke `STATE_INTERACTIVE_POLAROID`

---

## Phase 7: Interactive Polaroid Mode (NEW — `ui/polaroid_interaction.py`)

**Tujuan**: Mode interaksi dua tangan dengan polaroid.

### 7a: Buat `PolaroidInteraction` class
- Properties:
  - `x, y` — posisi polaroid (pixel)
  - `rotation` — sudut rotasi (degrees)
  - `scale` — ukuran (multiplier)
  - `target_x, target_y, target_rotation, target_scale` — target untuk smoothing
- Method:
  - `update(dt, midpoint, angle, distance)` — update target dari gesture data
  - `update_smoothing(dt)` — interpolasi ke target
  - `draw(surface, polaroid_surface)` — render polaroid dengan transform
  - `is_idle()` — cek apakah polaroid sudah diam cukup lama
  - `save_result()` — simpan polaroid final

### 7b: Transform Logic
- **Translation**: midpoint dua tangan → posisi polaroid di layar
  - midpoint normalized (0-1) → pixel coords → offset dari center
- **Rotation**: atan2(right_hand.y - left_hand.y, right_hand.x - left_hand.x)
  - Convert ke degrees, smooth dengan interpolation
- **Scale**: distance antara dua tangan
  - Map dari hand_distance ke scale factor (0.3x - 2.0x)
  - Clamp ke min/max

### 7c: Smoothing / Interpolation
- Semua transform target diterapkan via lerp:
  ```python
  self.x += (self.target_x - self.x) * smooth_factor
  self.y += (self.target_y - self.y) * smooth_factor
  self.rotation += (self.target_rotation - self.rotation) * smooth_factor
  self.scale += (self.target_scale - self.scale) * smooth_factor
  ```
- `smooth_factor` = 0.08 (bisa di-adjust)

### 7d: Draw Polaroid dengan Transform
- Buat surface polaroid
- Rotate surface: `pygame.transform.rotate(polaroid, angle)`
- Scale surface: `pygame.transform.smoothscale(rotated, (w*scale, h*scale))`
- Draw shadow di bawah polaroid
- Draw di posisi (x, y) yang sudah di-smooth

### 7e: Idle Detection & Auto-Save
- Track waktu terakhir ada interaksi
- Jika idle > 5 detik, animasi polaroid kembali ke center
- Setelah centered, auto-save ke folder `saved/`
- Tampilkan notifikasi "Photo Saved!" selama 2 detik
- Kembali ke idle state

---

## Phase 8: State Machine Update (`app.py`)

**Tujuan**: Integrasi semua fase ke state machine.

### New State Flow:
```
idle → camera_ready → tracking → capture_countdown
  → [capture_freeze] → [shutter_flash] → image_processing
  → puzzle_mode → solved
  → [puzzle_merge] → [polaroid_reveal]
  → interactive_polaroid → [idle_timeout] → idle
```

### Update `app.py`:
- Tambah state handlers untuk:
  - `STATE_INTERACTIVE_POLAROID` — update/draw polaroid interaction
- Update `draw()` untuk render polaroid mode
- Update `handle_events()` — ESC di interactive mode → save & return
- Update `_return_to_idle()` — cleanup polaroid interaction state

---

## Phase 9: Bug Fix & Polish

### 9a: Fix Duplicated Code di `board.py`
- Hapus duplikasi lines 191-200 (cursor drawing code duplikat)

### 9b: Update `README.md`
- Tambah dokumentasi Interactive Polaroid Mode
- Update state machine diagram
- Tambah gesture controls untuk two-hand interaction

---

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `config.py` | Edit | Tambah warna, state, polaroid config |
| `hand_tracking/detector.py` | Edit | Two-hand detection support |
| `hand_tracking/gestures.py` | Edit | Two-hand gesture recognition |
| `ui/menu.py` | Edit | StatusBar, InfoPanel, enhanced CameraView, dashed frame |
| `ui/animation.py` | Edit | ShutterFlash, PolaroidReveal classes |
| `ui/polaroid_interaction.py` | **New** | Interactive Polaroid Mode logic |
| `app.py` | Edit | State machine integration, new state handlers |
| `puzzle/board.py` | Edit | Fix duplicated code, add border fade |
| `README.md` | Edit | Update documentation |

---

## Implementation Order

1. `config.py` — foundation
2. `hand_tracking/detector.py` — two-hand detection
3. `hand_tracking/gestures.py` — two-hand gestures
4. `ui/menu.py` — enhanced camera view (status bar, skeleton, info panels, dashed frame)
5. `ui/animation.py` — shutter flash, polaroid reveal
6. `ui/polaroid_interaction.py` — new file for interactive polaroid
7. `puzzle/board.py` — fix bug, border fade
8. `app.py` — integrate everything into state machine
9. `README.md` — documentation update

---

## Testing Strategy
- Run aplikasi setelah setiap phase
- Test hand detection dengan 2 tangan
- Test semua state transitions
- Test polaroid interaction (translate, rotate, scale)
- Test idle timeout & auto-save
- Test ESC exit dari setiap state
