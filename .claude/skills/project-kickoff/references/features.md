# Feature Templates & Story Point Guide

## Story Point Scale (Fibonacci)

**Valid SP values:** `0.5 | 1 | 2 | 3 | 5 | 8 | 13 | 21`

| SP | Complexity | Effort | Example |
|----|------------|--------|---------|
| 0.5 | Trivial | < 2h | Compare slider, Share button, static UI element |
| 1 | Simple | 2-4h | Single API call (restore, enhance), picker, download, simple CRUD |
| 2 | Moderate | 4-8h | Music library, scheduler, multi-entity, complex data/UI |
| 3 | Complex | 1-2d | Notification service, video export, real-time tracker |
| 5 | Very Complex | 2-3d | Payment integration, complex editor, real-time sync |
| 8 | Epic | 3-5d | Full auth system, social features, chat module |
| 13 | System Set | 1-2w | Complete system feature bundle (ads + sub + analytics + i18n) |
| 21 | MVP | 2-4w | Full minimum viable product |

> **Rule:** Every feature MUST use a Fibonacci SP value. No 1.5, 4, 6, 7, etc.

---

## MVP Structure

```
Must Have: ~21 SP
├── Core Features: ~8 SP
└── System Features: 13 SP (default)

Nice Have: ~3-5 SP (optional, attract users)

TOTAL MVP: 21-26 SP
```

### Rules:
1. **Every SP MUST be Fibonacci:** `0.5 | 1 | 2 | 3 | 5 | 8 | 13 | 21`
2. **Basic UI** (compare, share) = 0.5 SP
3. **Simple API** (push/receive, picker, download) = 1 SP
4. **Moderate** (complex data/UI, scheduler) = 2 SP
5. **Complex** (notification, video, real-time) = 3 SP
6. **Very Complex** (payment, editor, sync) = 5 SP
7. **System features** required = 13 SP (includes Dev VIP Toggle)
8. If exceeds 21 SP → classify Must Have / Nice Have

---

## System Features (Default - 13 SP)

| Feature | Description | SP |
|---------|-------------|-----|
| First Open SDK | Show ads on first app open | 3 |
| Ad in app | Banner, interstitial, rewarded ads | 3 |
| Subscription | Premium package | 1 |
| Remote Config | Fetch config from Firebase | 1 |
| Event Tracking | Firebase Analytics | 1 |
| Multiple Language | VI, EN, ... | 1 |
| Service in house | API processing | 1 |
| Report | Report inappropriate results | 1 |
| Dev VIP Toggle | Fake VIP in Settings (appDev only) | 1 |
| **TOTAL** | | **13** |

### Dev VIP Toggle Implementation

```kotlin
// build.gradle.kts
flavorDimensions += "environment"
productFlavors {
    create("appDev") {
        dimension = "environment"
        booleanBuildConfig("IS_DEV", true)
    }
    create("appProduct") {
        dimension = "environment"
        booleanBuildConfig("IS_DEV", false)
    }
}
```

```kotlin
// SettingsScreen.kt
if (BuildConfig.IS_DEV) {
    // Show VIP toggle switch
    SwitchPreference(
        title = "Fake VIP Account",
        checked = isFakeVip,
        onCheckedChange = { viewModel.setFakeVip(it) }
    )
}
```

> ⚠️ **Note:** This toggle is only visible in `appDev` builds. Production builds (`appProduct`) will not show this option.

---

## Example 1: Image Restoration MVP (26 SP)

### Must Have (22 SP)
**Core (9 SP):**
| Feature | SP |
|---------|-----|
| Photo Restore | 1 |
| Photo Upscale | 1 |
| Photo Enhance | 1 |
| Photo Picker | 1 |
| Download | 1 |
| Compare | 0.5 |
| Share | 0.5 |
| Music Library | 2 |
| Filter Preset | 1 |

**System (13 SP):** Default

### Nice Have (4 SP)
| Feature | SP |
|---------|-----|
| Image with sound | 3 |
| Batch process | 1 |

**TOTAL: 26 SP**

---

## Example 2: Image Enhancement MVP (26 SP)

### Must Have (22 SP)
**Core (9 SP):**
| Feature | SP |
|---------|-----|
| Photo Enhance | 1 |
| Photo Upscale | 1 |
| Photo Sharpen | 1 |
| Color Correction | 1 |
| Denoise | 1 |
| Photo Picker | 1 |
| Download | 1 |
| Compare | 0.5 |
| Share | 0.5 |
| Filter Preset | 1 |

**System (13 SP):** Default

### Nice Have (4 SP)
| Feature | SP |
|---------|-----|
| Music Library | 2 |
| Image with sound | 2 |

**TOTAL: 26 SP**

---

## Example 3: Pet Health Care MVP (28 SP)

### Must Have (24 SP)
**Core (11 SP):**
| Feature | SP |
|---------|-----|
| Pet Profile | 1 |
| Health Log | 1 |
| Reminders | 3 |
| Photo Picker | 1 |
| Download/Export | 1 |
| Dashboard | 2 |
| Share | 0.5 |
| Weight Tracker | 2 |

**System (13 SP):** Default

*Note: No Compare feature - not applicable for this usecase*

### Nice Have (4 SP)
| Feature | SP |
|---------|-----|
| Food Schedule | 2 |
| Multi-pet | 2 |

**TOTAL: 28 SP**

---

## Common Core Features by Category

### Photo/Image (0.5-1 SP)
- Photo Restore, Upscale, Enhance, Sharpen (1)
- Color Correction, Denoise, Filter (1)
- Photo Picker, Download (1)
- Compare (0.5), Share (0.5) — basic UI only
- Compare **only for before/after usecases** (Restore, Enhance, Beauty)

### Image Generation & AI (1-3 SP)
- AI Photo Generate / Text-to-Image (1) — single API call
- AI Background Remove / Replace (1)
- AI Face Swap (1)
- AI Style Transfer / Artistic Filter (1)
- AI Object Remove / Inpainting (1)
- Makeup / Beauty on-device (5) — local ML model, real-time preview
- AI Avatar / Profile Pic Generate (1)
- Batch AI Process (3) — queue multiple images
- Prompt Input UI (1) — text field + style selector for gen

### Video Generation & AI (2-5 SP)
- AI Video Generate / Text-to-Video (2) — single API call + progress
- Image-to-Video / Animate Photo (2)
- AI Video Effect / Filter (2)
- Video Transition / Slideshow Maker (3) — multi-clip timeline
- Music Library (2)
- Image with Sound (3) — combine image + audio + export
- Video Maker / Editor (3) — trim, merge, overlay
- AI Lip Sync / Talking Photo (3)
- Video Template / Preset (2) — pre-built video styles

### Data/CRUD (1-2 SP)
- Profile, Log, Export (1)
- Dashboard, Tracker (2)

### Complex (3-5 SP)
- Reminders/Notification (3)
- Scheduler (2)
- Multi-entity management (2)
- Payment integration (5)
- Real-time sync (5)
- Complex editor (5)
