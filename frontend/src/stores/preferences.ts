import { defineStore } from 'pinia'

const FONT_SIZE_KEY = 'rssreader.readerFontSize'
const THEME_KEY = 'rssreader.readerTheme'
const APPEARANCE_MODE_KEY = 'rssreader.appearanceMode'
const PALETTE_KEY = 'rssreader.appearancePalette'
const APPEARANCE_EXPANDED_KEY = 'rssreader.appearanceExpanded'
const SURFACE_KEY = 'rssreader.readerSurface'
const LINE_HEIGHT_KEY = 'rssreader.readerLineHeight'
const CONTENT_WIDTH_KEY = 'rssreader.readerContentWidth'
const STARTUP_SYNC_KEY = 'rssreader.startupSyncEnabled'
const TIMED_SYNC_KEY = 'rssreader.timedSyncEnabled'
const TIMED_SYNC_INTERVAL_KEY = 'rssreader.timedSyncIntervalMinutes'
const LAST_STARTUP_SYNC_KEY = 'rssreader.lastStartupSyncAt'
const CUSTOM_PALETTE_KEY = 'rssreader.customPalette'

export type ReaderTheme = 'light' | 'dark'
export type ReaderSurface = 'paper' | 'mist' | 'night'
export type AppearanceMode = 'light' | 'dark'
export type AppearancePalette =
  | 'mono'
  | 'blue'
  | 'classic'
  | 'indigo'
  | 'slate'
  | 'fog'
  | 'teal'
  | 'green'
  | 'sage'
  | 'gold'
  | 'amber'
  | 'peach'
  | 'rose'
  | 'blush'
  | 'orchid'
  | 'violet'
  | 'custom'

export interface CustomPalette {
  appBg: string
  appSurface: string
  appSurfaceStrong: string
  appBorder: string
  appShadow: string
  darkAppBg: string
  darkAppSurface: string
  darkAppSurfaceStrong: string
  darkAppBorder: string
  darkAppShadow: string
  accentLight: string
  accentDark: string
}

function storedFontSize() {
  const raw = localStorage.getItem(FONT_SIZE_KEY)
  if (raw === null) {
    return 16
  }
  const value = Number(raw)
  return Number.isFinite(value) && value > 0 ? value : 16
}

function storedTheme(): ReaderTheme {
  return localStorage.getItem(THEME_KEY) === 'dark' ? 'dark' : 'light'
}

function storedAppearanceMode(): AppearanceMode {
  const raw = localStorage.getItem(APPEARANCE_MODE_KEY)
  if (raw === 'light' || raw === 'dark') {
    return raw
  }
  return 'light'
}

function storedPalette(): AppearancePalette {
  const raw = localStorage.getItem(PALETTE_KEY)
  if (
    raw === 'mono' || raw === 'blue' || raw === 'classic' || raw === 'indigo' || raw === 'slate' ||
    raw === 'fog' || raw === 'teal' || raw === 'green' || raw === 'sage' ||
    raw === 'gold' || raw === 'amber' || raw === 'peach' || raw === 'rose' ||
    raw === 'blush' || raw === 'orchid' || raw === 'violet' || raw === 'custom'
  ) {
    return raw
  }
  return 'mono'
}

function defaultCustomPalette(): CustomPalette {
  return {
    appBg: '#eff6ff',
    appSurface: '#ffffff',
    appSurfaceStrong: '#f7fbff',
    appBorder: '#c8dafc',
    appShadow: '0 18px 44px rgba(74, 124, 202, 0.16)',
    darkAppBg: '#1f2520',
    darkAppSurface: '#2b332c',
    darkAppSurfaceStrong: '#364039',
    darkAppBorder: '#4a574c',
    darkAppShadow: '0 18px 40px rgba(0, 0, 0, 0.32)',
    accentLight: '#3b82f6',
    accentDark: '#9bbcf3'
  }
}

function storedCustomPalette(): CustomPalette {
  const fallback = defaultCustomPalette()
  const raw = localStorage.getItem(CUSTOM_PALETTE_KEY)
  if (!raw) return fallback
  try {
    const parsed = JSON.parse(raw) as Partial<CustomPalette>
    return {
      appBg: parsed.appBg || fallback.appBg,
      appSurface: parsed.appSurface || fallback.appSurface,
      appSurfaceStrong: parsed.appSurfaceStrong || fallback.appSurfaceStrong,
      appBorder: parsed.appBorder || fallback.appBorder,
      appShadow: parsed.appShadow || fallback.appShadow,
      darkAppBg: parsed.darkAppBg || fallback.darkAppBg,
      darkAppSurface: parsed.darkAppSurface || fallback.darkAppSurface,
      darkAppSurfaceStrong: parsed.darkAppSurfaceStrong || fallback.darkAppSurfaceStrong,
      darkAppBorder: parsed.darkAppBorder || fallback.darkAppBorder,
      darkAppShadow: parsed.darkAppShadow || fallback.darkAppShadow,
      accentLight: parsed.accentLight || fallback.accentLight,
      accentDark: parsed.accentDark || fallback.accentDark
    }
  } catch {
    return fallback
  }
}

function storedAppearanceExpanded() {
  const raw = localStorage.getItem(APPEARANCE_EXPANDED_KEY)
  if (raw === null) {
    return true
  }
  return raw === 'true'
}

function storedSurface(): ReaderSurface {
  const raw = localStorage.getItem(SURFACE_KEY)
  if (raw === 'mist' || raw === 'night') {
    return raw
  }
  return 'paper'
}

function storedBoolean(key: string, fallback: boolean) {
  const raw = localStorage.getItem(key)
  if (raw === null) {
    return fallback
  }
  return raw === 'true'
}

function storedSyncInterval() {
  const raw = localStorage.getItem(TIMED_SYNC_INTERVAL_KEY)
  if (raw === null) {
    return 60
  }
  const value = Number(raw)
  return Number.isFinite(value) && value >= 5 ? value : 60
}

function storedLineHeight() {
  const raw = localStorage.getItem(LINE_HEIGHT_KEY)
  if (raw === null) {
    return 1.75
  }
  const value = Number(raw)
  return Number.isFinite(value) && value >= 1.4 && value <= 2.2 ? value : 1.75
}

function storedContentWidth() {
  const raw = localStorage.getItem(CONTENT_WIDTH_KEY)
  if (raw === null) {
    return 760
  }
  const value = Number(raw)
  return Number.isFinite(value) && value >= 640 && value <= 1040 ? value : 760
}

export const usePreferencesStore = defineStore('preferences', {
  state: () => ({
    readerFontSize: storedFontSize(),
    readerTheme: storedTheme(),
    appearanceMode: storedAppearanceMode(),
    appearancePalette: storedPalette(),
    customPalette: storedCustomPalette(),
    appearanceExpanded: storedAppearanceExpanded(),
    readerSurface: storedSurface(),
    readerLineHeight: storedLineHeight(),
    readerContentWidth: storedContentWidth(),
    startupSyncEnabled: storedBoolean(STARTUP_SYNC_KEY, true),
    timedSyncEnabled: storedBoolean(TIMED_SYNC_KEY, false),
    timedSyncIntervalMinutes: storedSyncInterval()
  }),
  actions: {
    applyPreferences() {
      const resolvedTheme = this.resolveReaderTheme()
      const palette = this.appearancePalette === 'custom'
        ? this.customPalette
        : appearancePalettes[this.appearancePalette]
      const surfaceBg = resolvedTheme === 'dark' ? palette.darkAppBg : palette.appBg
      const surfaceCard = resolvedTheme === 'dark' ? palette.darkAppSurface : palette.appSurface
      const surfaceStrong = resolvedTheme === 'dark' ? palette.darkAppSurfaceStrong : palette.appSurfaceStrong
      const surfaceBorder = resolvedTheme === 'dark' ? palette.darkAppBorder : palette.appBorder
      const shadow = resolvedTheme === 'dark' ? palette.darkAppShadow : palette.appShadow
      document.documentElement.style.setProperty('--reader-font-size', `${this.readerFontSize}px`)
      document.documentElement.style.setProperty('--reader-line-height', String(this.readerLineHeight))
      document.documentElement.style.setProperty('--reader-content-width', `${this.readerContentWidth}px`)
      document.documentElement.style.setProperty('--app-bg', surfaceBg)
      document.documentElement.style.setProperty('--app-surface', surfaceCard)
      document.documentElement.style.setProperty('--app-surface-strong', surfaceStrong)
      document.documentElement.style.setProperty('--app-border', surfaceBorder)
      document.documentElement.style.setProperty('--app-shadow', shadow)
      document.documentElement.style.setProperty(
        '--theme-accent',
        resolvedTheme === 'dark' ? palette.accentDark : palette.accentLight
      )
      document.body.classList.toggle('theme-dark', resolvedTheme === 'dark')
      document.body.dataset.readerSurface = resolvedTheme === 'dark' ? 'night' : 'mist'
      document.body.dataset.appearanceMode = this.appearanceMode
      document.body.dataset.appearancePalette = this.appearancePalette
    },
    resolveReaderTheme(): ReaderTheme {
      return this.appearanceMode
    },
    setReaderFontSize(value: number) {
      this.readerFontSize = value
      localStorage.setItem(FONT_SIZE_KEY, String(value))
      this.applyPreferences()
    },
    setAppearanceMode(value: AppearanceMode) {
      this.appearanceMode = value
      this.readerTheme = value
      localStorage.setItem(APPEARANCE_MODE_KEY, value)
      localStorage.setItem(THEME_KEY, this.readerTheme)
      this.applyPreferences()
    },
    setAppearancePalette(value: AppearancePalette) {
      this.appearancePalette = value
      localStorage.setItem(PALETTE_KEY, value)
      this.applyPreferences()
    },
    setCustomPalette(patch: Partial<CustomPalette>) {
      this.customPalette = {
        ...this.customPalette,
        ...patch
      }
      localStorage.setItem(CUSTOM_PALETTE_KEY, JSON.stringify(this.customPalette))
      this.appearancePalette = 'custom'
      localStorage.setItem(PALETTE_KEY, 'custom')
      this.applyPreferences()
    },
    setAppearanceExpanded(value: boolean) {
      this.appearanceExpanded = value
      localStorage.setItem(APPEARANCE_EXPANDED_KEY, String(value))
    },
    setReaderTheme(value: ReaderTheme) {
      this.readerTheme = value
      localStorage.setItem(THEME_KEY, value)
      this.applyPreferences()
    },
    setReaderSurface(value: ReaderSurface) {
      this.readerSurface = value
      localStorage.setItem(SURFACE_KEY, value)
      this.applyPreferences()
    },
    setReaderLineHeight(value: number) {
      const normalized = Number.isFinite(value) && value >= 1.4 && value <= 2.2 ? Number(value.toFixed(2)) : 1.75
      this.readerLineHeight = normalized
      localStorage.setItem(LINE_HEIGHT_KEY, String(normalized))
      this.applyPreferences()
    },
    setReaderContentWidth(value: number) {
      const normalized = Number.isFinite(value) && value >= 640 && value <= 1040 ? Math.round(value) : 760
      this.readerContentWidth = normalized
      localStorage.setItem(CONTENT_WIDTH_KEY, String(normalized))
      this.applyPreferences()
    },
    setStartupSyncEnabled(value: boolean) {
      this.startupSyncEnabled = value
      localStorage.setItem(STARTUP_SYNC_KEY, String(value))
    },
    setTimedSyncEnabled(value: boolean) {
      this.timedSyncEnabled = value
      localStorage.setItem(TIMED_SYNC_KEY, String(value))
    },
    setTimedSyncIntervalMinutes(value: number) {
      const normalized = Number.isFinite(value) && value >= 5 ? Math.floor(value) : 60
      this.timedSyncIntervalMinutes = normalized
      localStorage.setItem(TIMED_SYNC_INTERVAL_KEY, String(normalized))
    },
    shouldRunStartupSync(cooldownMs = 10 * 60 * 1000) {
      const raw = localStorage.getItem(LAST_STARTUP_SYNC_KEY)
      const lastSyncAt = raw ? Number(raw) : 0
      return !Number.isFinite(lastSyncAt) || Date.now() - lastSyncAt >= cooldownMs
    },
    recordStartupSync(timestamp = Date.now()) {
      localStorage.setItem(LAST_STARTUP_SYNC_KEY, String(timestamp))
    }
  }
})

export const appearancePalettes: Record<AppearancePalette, {
  appBg: string
  appSurface: string
  appSurfaceStrong: string
  appBorder: string
  appShadow: string
  darkAppBg: string
  darkAppSurface: string
  darkAppSurfaceStrong: string
  darkAppBorder: string
  darkAppShadow: string
  accentLight: string
  accentDark: string
}> = {
  mono: { appBg: '#f3f4f6', appSurface: '#ffffff', appSurfaceStrong: '#f8f9fb', appBorder: '#d8dde6', appShadow: '0 18px 42px rgba(90, 98, 112, 0.10)', darkAppBg: '#1f2022', darkAppSurface: '#27292d', darkAppSurfaceStrong: '#31343a', darkAppBorder: '#484d57', darkAppShadow: '0 18px 40px rgba(0, 0, 0, 0.34)', accentLight: '#4b5563', accentDark: '#d1d5db' },
  blue: { appBg: '#edf3ff', appSurface: '#ffffff', appSurfaceStrong: '#f6f9ff', appBorder: '#d7e3fb', appShadow: '0 20px 50px rgba(46, 102, 199, 0.12)', darkAppBg: '#202428', darkAppSurface: '#272d34', darkAppSurfaceStrong: '#303842', darkAppBorder: '#465363', darkAppShadow: '0 18px 40px rgba(0, 0, 0, 0.34)', accentLight: '#1f5fd1', accentDark: '#9bbcf3' },
  classic: { appBg: '#eff3fb', appSurface: '#ffffff', appSurfaceStrong: '#f6f7fa', appBorder: '#dbe2f1', appShadow: '0 18px 40px rgba(70, 94, 130, 0.12)', darkAppBg: '#202226', darkAppSurface: '#2b2f35', darkAppSurfaceStrong: '#343840', darkAppBorder: '#495361', darkAppShadow: '0 18px 40px rgba(0, 0, 0, 0.34)', accentLight: '#2f5fb7', accentDark: '#a8bfef' },
  indigo: { appBg: '#eef2ff', appSurface: '#ffffff', appSurfaceStrong: '#f5f6ff', appBorder: '#d9def8', appShadow: '0 18px 44px rgba(76, 98, 170, 0.12)', darkAppBg: '#21232a', darkAppSurface: '#2b3039', darkAppSurfaceStrong: '#353c48', darkAppBorder: '#4a5669', darkAppShadow: '0 18px 40px rgba(0, 0, 0, 0.34)', accentLight: '#4664be', accentDark: '#b2c0f6' },
  slate: { appBg: '#eef1f8', appSurface: '#ffffff', appSurfaceStrong: '#f5f7fb', appBorder: '#d6dceb', appShadow: '0 18px 44px rgba(83, 94, 122, 0.12)', darkAppBg: '#212327', darkAppSurface: '#2c3036', darkAppSurfaceStrong: '#373d46', darkAppBorder: '#4d5764', darkAppShadow: '0 18px 40px rgba(0, 0, 0, 0.34)', accentLight: '#61718d', accentDark: '#bcc6db' },
  fog: { appBg: '#edf4f6', appSurface: '#ffffff', appSurfaceStrong: '#f4f8f9', appBorder: '#d3e1e5', appShadow: '0 18px 44px rgba(82, 106, 112, 0.12)', darkAppBg: '#212526', darkAppSurface: '#2b3132', darkAppSurfaceStrong: '#363e40', darkAppBorder: '#4d595c', darkAppShadow: '0 18px 40px rgba(0, 0, 0, 0.34)', accentLight: '#56747c', accentDark: '#b8d0d7' },
  teal: { appBg: '#edf9f7', appSurface: '#ffffff', appSurfaceStrong: '#f3fcfb', appBorder: '#d2ece7', appShadow: '0 18px 44px rgba(41, 132, 122, 0.14)', darkAppBg: '#202423', darkAppSurface: '#2a2f2e', darkAppSurfaceStrong: '#343a39', darkAppBorder: '#4c5755', darkAppShadow: '0 18px 40px rgba(0, 0, 0, 0.34)', accentLight: '#147f77', accentDark: '#95e5db' },
  green: { appBg: '#eff8eb', appSurface: '#ffffff', appSurfaceStrong: '#f4fbf2', appBorder: '#d7eacc', appShadow: '0 18px 44px rgba(77, 129, 58, 0.14)', darkAppBg: '#212320', darkAppSurface: '#2b2f2b', darkAppSurfaceStrong: '#353a35', darkAppBorder: '#4d564c', darkAppShadow: '0 18px 40px rgba(0, 0, 0, 0.34)', accentLight: '#4c8e38', accentDark: '#bde99b' },
  sage: { appBg: '#f2f6ee', appSurface: '#ffffff', appSurfaceStrong: '#f6faf4', appBorder: '#dde6d5', appShadow: '0 18px 44px rgba(100, 113, 88, 0.14)', darkAppBg: '#222320', darkAppSurface: '#2c2f2c', darkAppSurfaceStrong: '#363936', darkAppBorder: '#4f564e', darkAppShadow: '0 18px 40px rgba(0, 0, 0, 0.34)', accentLight: '#718065', accentDark: '#cad5c1' },
  gold: { appBg: '#fff8de', appSurface: '#ffffff', appSurfaceStrong: '#fffbee', appBorder: '#f0df97', appShadow: '0 18px 44px rgba(171, 146, 19, 0.16)', darkAppBg: '#25231d', darkAppSurface: '#302d27', darkAppSurfaceStrong: '#3b3830', darkAppBorder: '#575146', darkAppShadow: '0 18px 40px rgba(0, 0, 0, 0.34)', accentLight: '#a99100', accentDark: '#ffe38a' },
  amber: { appBg: '#fff1e6', appSurface: '#ffffff', appSurfaceStrong: '#fff7f1', appBorder: '#f2d3b8', appShadow: '0 18px 44px rgba(170, 106, 43, 0.16)', darkAppBg: '#25211f', darkAppSurface: '#302b29', darkAppSurfaceStrong: '#3c3632', darkAppBorder: '#584d47', darkAppShadow: '0 18px 40px rgba(0, 0, 0, 0.34)', accentLight: '#bc6f28', accentDark: '#ffc08c' },
  peach: { appBg: '#fff0ea', appSurface: '#ffffff', appSurfaceStrong: '#fff7f3', appBorder: '#f3d7ca', appShadow: '0 18px 44px rgba(150, 111, 91, 0.16)', darkAppBg: '#252120', darkAppSurface: '#302c2b', darkAppSurfaceStrong: '#3b3735', darkAppBorder: '#574f4b', darkAppShadow: '0 18px 40px rgba(0, 0, 0, 0.34)', accentLight: '#9d715d', accentDark: '#e9c6b4' },
  rose: { appBg: '#fff0f4', appSurface: '#ffffff', appSurfaceStrong: '#fff6f8', appBorder: '#f0d0db', appShadow: '0 18px 44px rgba(162, 82, 108, 0.16)', darkAppBg: '#252022', darkAppSurface: '#302a2d', darkAppSurfaceStrong: '#3b3438', darkAppBorder: '#574b50', darkAppShadow: '0 18px 40px rgba(0, 0, 0, 0.34)', accentLight: '#b85e81', accentDark: '#f3adc1' },
  blush: { appBg: '#fff0f2', appSurface: '#ffffff', appSurfaceStrong: '#fff7f8', appBorder: '#efd5dc', appShadow: '0 18px 44px rgba(134, 101, 112, 0.16)', darkAppBg: '#252123', darkAppSurface: '#302b2d', darkAppSurfaceStrong: '#3b3638', darkAppBorder: '#564f51', darkAppShadow: '0 18px 40px rgba(0, 0, 0, 0.34)', accentLight: '#92727d', accentDark: '#ddc0c8' },
  orchid: { appBg: '#fdf0fb', appSurface: '#ffffff', appSurfaceStrong: '#fff7fd', appBorder: '#edd6ea', appShadow: '0 18px 44px rgba(137, 84, 142, 0.16)', darkAppBg: '#242024', darkAppSurface: '#2f2a30', darkAppSurfaceStrong: '#3a353b', darkAppBorder: '#554d56', darkAppShadow: '0 18px 40px rgba(0, 0, 0, 0.34)', accentLight: '#9b62aa', accentDark: '#e2a7e7' },
  violet: { appBg: '#f5efff', appSurface: '#ffffff', appSurfaceStrong: '#faf6ff', appBorder: '#dfd1f7', appShadow: '0 18px 44px rgba(110, 85, 162, 0.16)', darkAppBg: '#232126', darkAppSurface: '#2e2b32', darkAppSurfaceStrong: '#39363f', darkAppBorder: '#534f5a', darkAppShadow: '0 18px 40px rgba(0, 0, 0, 0.34)', accentLight: '#7053b9', accentDark: '#c6acf8' },
  custom: defaultCustomPalette()
}
