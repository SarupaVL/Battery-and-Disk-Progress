# 🎨 Visual Guide - Battery & Disk Dashboard

## Dashboard Sections Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  NEURAL CORE ONLINE          [⚡ BATTERY] [💾 DISK]  AC    08:30:15 │
└─────────────────────────────────────────────────────────────────────┘

BATTERY VIEW (When ⚡ BATTERY tab is selected):

┌────────────────────┐  ┌──────────────────────┐
│  BATTERY CORE      │  │  SYSTEM STATUS       │
│        ⚡           │  │  ✓ CHARGING          │
│   57.0% CHARGE     │  │  Last: 08:30:14      │
│   ~60 min          │  │  Data: 100 points    │
│                    │  │                      │
│  [57% gauge ring]  │  │                      │
└────────────────────┘  └──────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ BATTERY      │  │ TEMPERATURE  │  │ POWER DRAW   │  │ SESSIONS     │
│ HEALTH       │  │              │  │              │  │              │
│ 96%          │  │ 35°C         │  │ 15.2W        │  │ 1            │
│              │  │              │  │              │  │              │
│ ████████████ │  │              │  │              │  │              │
│ Design: 50k  │  │              │  │              │  │              │
│ Current: 48k │  │              │  │              │  │              │
│ Cycles: 127  │  │              │  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘

┌────────────────────────────────────────────────────────────────────┐
│ TIME SERIES ANALYSIS                                        📉     │
│                                                                    │
│ 100% ┐                                                            │
│      │                    ╱╲    ╱╲                               │
│  57% ├─────────────────╱──╲──╱──╲───────────                     │
│      │           ╱╲ ╱╲╱    ╲╱    ╲                               │
│   0% └─────────────────────────────────────────                  │
│      Now                                    -30 min              │
│                                                                    │
│ Battery %: Red line showing history...                           │
└────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════

DISK VIEW (When 💾 DISK tab is selected):

┌────────────────────┐  ┌──────────────────────┐
│   DISK CORE        │  │    DISK STATUS       │
│        💾           │  │  Total: 482 GB       │
│   66.4% USED       │  │  Used:  320 GB       │
│   135.93 GB free   │  │  Free:  162 GB       │
│                    │  │                      │
│  [66% gauge ring]  │  │  (status metrics)    │
└────────────────────┘  └──────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ GROWTH       │  │ READ RATE    │  │ WRITE RATE   │  │ READ OPS     │
│ FORECAST     │  │              │  │              │  │              │
│ 0.12 GB/day  │  │ 120 KB/s     │  │ 1.2 MB/s     │  │ 20.5 /s      │
│ > 1 year     │  │              │  │              │  │              │
│ to full      │  │              │  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘

┌──────────┐
│WRITE OPS │
│ 21.3 /s  │
│          │
└──────────┘

┌────────────────────────────────────────────────────────────────────┐
│ TOP DISK WRITERS                                          ⚙️       │
├─────────────────────────┬────────┬──────────────────────────────┤
│ Process                 │ PID    │ Write Rate                   │
├─────────────────────────┼────────┼──────────────────────────────┤
│ Antigravity.exe         │ 3660   │ 5.97 MB                      │
│ zen.exe                 │ 14580  │ 3.08 MB                      │
│ Discord.exe             │ 23584  │ 7.94 MB                      │
│ NVDisplay.Container.exe │ 3824   │ 20.0 MB                      │
│ language_server_win...  │ 13428  │ 1.13 MB                      │
│ ... 5 more processes    │        │                              │
└─────────────────────────┴────────┴──────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│ DISK USAGE HISTORY                                          📊     │
│                                                                    │
│ 100% ┐                                                            │
│      │                                                            │
│  66% ├─────────────────────────────────────────────────────      │
│      │                                                            │
│   0% └─────────────────────────────────────────────────────      │
│      Now                                    -30 min              │
│                                                                    │
│ Disk Usage %: Orange line showing trend (mostly flat = stable)   │
└────────────────────────────────────────────────────────────────────┘
```

---

## Color Scheme

### Battery Indicators
- **Green** (70%+): Good health
- **Cyan/Blue** (30-70%): Normal range  
- **Orange/Yellow** (15-30%): Caution
- **Red** (<15%): Low battery warning

### Disk Indicators  
- **Cyan/Green** (<50%): Plenty of space
- **Orange/Yellow** (50-75%): Monitor closely
- **Red** (75%+): Getting full, consider cleanup

### UI Elements
- **Cyan (#00f3ff)**: Battery-related elements
- **Orange (#ff6b00)**: Disk-related elements
- **White/Gray**: Text and labels

---

## Interactive Elements

### Tabs
```
[⚡ BATTERY] [💾 DISK]
      ↑        ↑
   Click to switch views
```
- **Blue glow** when active
- **Orange glow** when active  
- Smooth transition between views

### Charts
- **Hover** to see exact values at each point
- **Tooltip shows**: Value, timestamp
- **Auto-scales** based on data range
- **Updates** every 2 seconds in real-time

### Gauge Rings
- **Animated** when values change
- **Color gradient** indicates status
- **Center text** shows percentage and additional info
- **Background ring** shows scale (0-100%)

---

## Status Indicators

### Battery Status Badge
```
✓ CHARGING      - AC power connected, battery increasing
✓ FULL          - AC power, battery at 99%+  
✓ DISCHARGING   - On battery, losing charge normally
✓ LOW POWER     - Battery below 15%, urgent action needed
✓ STANDBY       - No recent activity
```

### Top Disk Writers Table
- **Process Name**: Executable file name (what's writing to disk)
- **PID**: Process ID (useful for Task Manager lookup)
- **Write Rate**: Amount of data written (in bytes)

---

## Real-Time Updates

Every element updates **automatically every 2 seconds**:

1. ⚡ Battery percentage
2. 💾 Disk usage
3. 📊 All charts
4. 📈 Growth calculations  
5. ⚙️ Process list
6. 🕐 Timestamp

**No clicking needed!** Just watch the metrics flow in real-time.

---

## Key Metrics Explained

### Battery
| Item | What It Means |
|------|---------------|
| **57.0% CHARGE** | Battery currently at 57% capacity |
| **~60 min** | Estimated time until fully drained |
| **96% Health** | Battery at 96% of design capacity (good!) |
| **12.5V** | Current battery voltage |
| **35°C** | Battery temperature (normal: 25-40°C) |
| **15.2W** | Current power draw from battery |

### Disk
| Item | What It Means |
|------|---------------|
| **66.4% USED** | 66.4% of disk is occupied |
| **320 GB Used** | Total space consumed by files |
| **162 GB Free** | Space available for new files |
| **482 GB Total** | Total disk capacity |
| **0.12 GB/day** | Average disk growth per day |
| **>1 year** | Days until disk is full at current rate |
| **120 KB/s READ** | Speed of reading data from disk |
| **1.2 MB/s WRITE** | Speed of writing data to disk |

---

## Why Colors Change

### Battery Gauge
```
Green    ████████████   70%+  ✓ Great condition
Blue     ████████      30-70% ✓ Normal operation  
Orange   ████          15-30% ⚠ Getting low
Red      ██            <15%   🔴 Critical!
```

### Disk Gauge
```
Green    ████████████   <50%   ✓ Plenty of space
Orange   ████████       50-75% ⚠ Monitor
Red      ██████████     75%+   🔴 Getting full!
```

### Top Bar Glow
- **Cyan glow**: Charging (AC power)
- **Yellow glow**: Discharging (on battery)
- **Red glow**: Low power (<15%)

---

## Tips & Tricks

1. **Bookmark the page**: Save http://localhost:3000 to browser bookmarks
2. **Full-screen mode**: Press F11 for distraction-free monitoring
3. **Check processes**: Use disk top-writers to identify disk hogs
4. **Track trends**: Watch the charts over hours for patterns
5. **Plan ahead**: Monitor growth forecast to know when cleanup is needed

---

**Everything is live. Everything updates. Everything just works.** 🚀
