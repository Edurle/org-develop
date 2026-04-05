import { defineConfig, presetUno, presetAttributify } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetAttributify(),
  ],
  theme: {
    colors: {
      primary: { DEFAULT: '#2563eb', light: '#3b82f6', dark: '#1d4ed8' },
      accent: '#06b6d4',
      surface: '#f0f4f8',
    },
    boxShadow: {
      'glass-xs': '0 1px 3px rgba(37,99,235,0.04)',
      'glass-sm': '0 4px 12px rgba(37,99,235,0.06)',
      'glass-md': '0 8px 24px rgba(37,99,235,0.08)',
      'glass-lg': '0 16px 40px rgba(37,99,235,0.12)',
    },
  },
  shortcuts: {
    'glass-card': 'bg-white/70 backdrop-blur-xl border border-blue-500/8 rounded-[14px] shadow-glass-sm transition-all duration-200',
    'glass-nav': 'bg-white/85 backdrop-blur-2xl border-b border-blue-500/6',
    'btn-primary': 'bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-[10px] font-semibold shadow-[0_2px_8px_rgba(37,99,235,0.3)] hover:shadow-[0_4px_16px_rgba(37,99,235,0.4)] hover:-translate-y-px transition-all duration-150 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed',
    'btn-secondary': 'bg-white text-blue-600 border border-blue-500/20 rounded-[10px] font-medium hover:border-blue-500/40 transition-all duration-150 cursor-pointer',
    'btn-ghost': 'bg-blue-50 text-blue-600 rounded-[10px] font-medium hover:bg-blue-100 transition-all duration-150 cursor-pointer',
    'btn-danger': 'bg-gradient-to-br from-red-500 to-red-600 text-white rounded-[10px] font-semibold shadow-[0_2px_8px_rgba(239,68,68,0.3)] hover:shadow-[0_4px_16px_rgba(239,68,68,0.4)] hover:-translate-y-px transition-all duration-150 cursor-pointer',
    'badge-base': 'px-2.5 py-1 rounded-full text-xs font-semibold border inline-flex items-center',
    'input-glass': 'w-full px-3.5 py-2.5 bg-white/70 backdrop-blur-sm border border-blue-500/12 rounded-[10px] text-sm outline-none focus:border-blue-500/30 focus:ring-2 focus:ring-blue-500/10 transition-all duration-150',
    'select-glass': 'w-full px-3.5 py-2.5 bg-white/70 backdrop-blur-sm border border-blue-500/12 rounded-[10px] text-sm outline-none focus:border-blue-500/30 focus:ring-2 focus:ring-blue-500/10 transition-all duration-150 cursor-pointer',
  },
})
